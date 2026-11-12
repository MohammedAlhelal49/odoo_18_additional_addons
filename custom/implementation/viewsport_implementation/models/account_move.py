import calendar

from odoo import api, fields, models

from .purchase_order import amount_to_dirhams_text, vat_label


class AccountMove(models.Model):
    _inherit = 'account.move'

    invoice_period_start = fields.Date(
        string='Invoice Period From', compute='_compute_invoice_period', store=True, readonly=False)
    invoice_period_end = fields.Date(
        string='Invoice Period To', compute='_compute_invoice_period', store=True, readonly=False)
    contract_ref = fields.Char(string='Contract Ref. Number')
    invoice_attention = fields.Char(string='Attention', default='Finance Manager')
    vs_note_reason = fields.Text(
        string='Reason of Issuing / Return',
        help='Printed on the credit and debit notes, one reason per line.')
    payment_band = fields.Char(
        string='Payment Label',
        help='Blue band above the invoice lines, e.g. "Construction Progress Payment No [01]". '
             'Left empty, "Payment No [NN]" is printed with the rank of this invoice for the customer.')

    @api.depends('invoice_date')
    def _compute_invoice_period(self):
        """Default period: the calendar month of the invoice date (monthly service invoices)."""
        for move in self:
            if move.invoice_date and not move.invoice_period_start and not move.invoice_period_end:
                date = move.invoice_date
                move.invoice_period_start = date.replace(day=1)
                move.invoice_period_end = date.replace(day=calendar.monthrange(date.year, date.month)[1])

    def _get_invoice_period_label(self):
        self.ensure_one()
        if not (self.invoice_period_start and self.invoice_period_end):
            return '-'
        fmt = lambda d: d.strftime('%d-%b-%Y').upper()
        return '%s to %s' % (fmt(self.invoice_period_start), fmt(self.invoice_period_end))

    def _get_invoice_project(self):
        """Project analytic account of the invoice lines (account from a 'Project' plan first)."""
        self.ensure_one()
        account_ids = set()
        for line in self.invoice_line_ids:
            for key in (line.analytic_distribution or {}):
                account_ids.update(int(account_id) for account_id in key.split(','))
        accounts = self.env['account.analytic.account'].browse(sorted(account_ids)).exists()
        return (accounts.filtered(lambda a: 'project' in (a.plan_id.name or '').lower()) or accounts)[:1]

    def _get_contract_ref(self):
        self.ensure_one()
        if self.contract_ref:
            return self.contract_ref
        project = self._get_invoice_project()
        return project.custom_project_code or project.code or '-'

    def _get_payment_band(self):
        self.ensure_one()
        if self.payment_band:
            return self.payment_band
        previous = self.search_count([
            ('partner_id', '=', self.partner_id.id),
            ('move_type', '=', self.move_type),
            ('state', '=', 'posted'),
            '|', ('invoice_date', '<', self.invoice_date),
            '&', ('invoice_date', '=', self.invoice_date), ('id', '<', self.id),
        ]) if self.invoice_date else 0
        return 'Payment No [%02d]' % (previous + 1)

    def _get_original_invoice_ref(self):
        """Invoice a credit / debit note refers to."""
        self.ensure_one()
        origin = self.reversed_entry_id
        if not origin and 'debit_origin_id' in self._fields:
            origin = self.debit_origin_id
        return origin.name or self.invoice_origin or '-'

    def _vs_delivery_date(self):
        """Last delivery of the sales orders invoiced here (commercial invoice certification)."""
        self.ensure_one()
        if 'sale_order_ids' not in self.invoice_line_ids._fields and 'sale_line_ids' not in self.invoice_line_ids._fields:
            return False
        pickings = self.invoice_line_ids.sale_line_ids.order_id.picking_ids.filtered(lambda p: p.state == 'done' and p.date_done)
        return max(pickings.mapped('date_done')).date() if pickings else False

    def _get_report_bank_account(self):
        """Bank account printed on the invoice: the invoice recipient bank, else the first company account."""
        self.ensure_one()
        return self.partner_bank_id or self.company_id.partner_id.bank_ids[:1]

    def _vs_vat_label(self):
        lines = self.invoice_line_ids.filtered(lambda l: l.display_type == 'product')
        return vat_label([l.tax_ids for l in lines]) if lines else '5%'

    def _get_amount_in_words(self):
        self.ensure_one()
        if self.currency_id.name == 'AED':
            return amount_to_dirhams_text(self.amount_total)
        return self.currency_id.amount_to_text(self.amount_total)
