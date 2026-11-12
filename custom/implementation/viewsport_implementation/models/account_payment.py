from odoo import api, fields, models

from .purchase_order import amount_to_dirhams_text


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    receipt_voucher_no = fields.Char(string='Receipt Voucher No.', copy=False, readonly=True)
    receipt_payment_method = fields.Selection(
        [('cheque', 'Cheque'), ('bank_transfer', 'Bank Transfer'), ('cash', 'Cash')],
        string='Receipt Payment Method', compute='_compute_receipt_payment_method', store=True, readonly=False)
    receipt_bank_name = fields.Char(string='Bank Name')
    receipt_description = fields.Text(
        string='Receipt Description',
        help='Printed in the "Detail Breakdown" of the receipt voucher. Left empty, a description is built from the paid invoices.')

    @api.depends('journal_id')
    def _compute_receipt_payment_method(self):
        for pay in self:
            if not pay.receipt_payment_method or pay.receipt_payment_method != 'cheque':
                pay.receipt_payment_method = 'cash' if pay.journal_id.type == 'cash' else 'bank_transfer'

    def action_post(self):
        res = super().action_post()
        for pay in self.filtered(lambda p: p.payment_type == 'inbound' and p.partner_type == 'customer' and not p.receipt_voucher_no):
            pay.receipt_voucher_no = self.env['ir.sequence'].with_company(pay.company_id).next_by_code(
                'viewsport.receipt.voucher', sequence_date=pay.date)
        return res

    def _get_receipt_amount_in_words(self):
        self.ensure_one()
        if self.currency_id.name == 'AED':
            return amount_to_dirhams_text(self.amount)
        return self.currency_id.amount_to_text(self.amount)

    def _get_receipt_project(self):
        """Project analytic account of the paid invoices (account from a 'Project' plan first)."""
        self.ensure_one()
        account_ids = set()
        for line in self.reconciled_invoice_ids.invoice_line_ids:
            for key in (line.analytic_distribution or {}):
                account_ids.update(int(account_id) for account_id in key.split(','))
        accounts = self.env['account.analytic.account'].browse(sorted(account_ids)).exists()
        return (accounts.filtered(lambda a: 'project' in (a.plan_id.name or '').lower()) or accounts)[:1]

    def _get_receipt_installment_no(self):
        """Rank of this receipt among the posted customer receipts of the same partner."""
        self.ensure_one()
        previous = self.search_count([
            ('partner_id', '=', self.partner_id.id),
            ('payment_type', '=', 'inbound'),
            ('state', 'not in', ('draft', 'canceled')),
            '|', ('date', '<', self.date), '&', ('date', '=', self.date), ('id', '<', self.id),
        ])
        return previous + 1

    def _get_receipt_description(self):
        self.ensure_one()
        if self.receipt_description:
            return self.receipt_description
        invoices = self.reconciled_invoice_ids
        if not invoices:
            return 'Being payment received from %s.' % self.partner_id.name
        settlement = 'full settlement' if all(inv.payment_state in ('paid', 'in_payment') for inv in invoices) else 'partial payment'
        text = 'Being %s against Tax Invoice No.%s (Payment No.%02d)' % (
            settlement, ', '.join(invoices.mapped('name')), self._get_receipt_installment_no())
        project = self._get_receipt_project()
        if project:
            text += ' towards %s' % project.name.strip()
        return text + '.'
