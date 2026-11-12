from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    contract_percent = fields.Float(
        string='% of Contract', compute='_compute_contract_percent', digits=(16, 2),
        help='Total of this invoice as a percentage of the total of its sales order (negative for a credit note).')

    def _compute_contract_percent(self):
        for move in self:
            order = move.line_ids.sale_line_ids.order_id[:1]
            sign = -1.0 if move.move_type == 'out_refund' else 1.0
            move.contract_percent = (
                sign * move.amount_total / order.amount_total * 100.0 if order.amount_total else 0.0)

    def action_open_contract_bill(self):
        self.ensure_one()
        return self.get_formview_action()


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    contract_has_invoices = fields.Boolean(compute='_compute_contract_payments')
    contract_invoice_ids = fields.Many2many(
        'account.move', string='Contract Invoices', compute='_compute_contract_payments')
    contract_invoiced_amount = fields.Monetary(
        string='Invoiced so far', compute='_compute_contract_payments', currency_field='currency_id')
    contract_remaining_amount = fields.Monetary(
        string='Remaining of the contract', compute='_compute_contract_payments', currency_field='currency_id')
    contract_invoiced_percent = fields.Float(
        string='Invoiced so far (%)', compute='_compute_contract_payments', digits=(16, 2))
    contract_remaining_percent = fields.Float(
        string='Remaining of the contract (%)', compute='_compute_contract_payments', digits=(16, 2))

    @api.depends('amount_total', 'invoice_ids.state', 'invoice_ids.amount_total')
    def _compute_contract_payments(self):
        for order in self:
            invoices = order.invoice_ids.filtered(
                lambda m: m.state != 'cancel' and m.move_type in ('out_invoice', 'out_refund'))
            invoiced = sum(i.amount_total if i.move_type == 'out_invoice' else -i.amount_total for i in invoices)
            total = order.amount_total
            remaining = max(total - invoiced, 0.0)
            order.contract_has_invoices = bool(invoices)
            order.contract_invoice_ids = invoices.sorted(lambda m: (m.invoice_date or m.date or m.create_date, m.id))
            order.contract_invoiced_amount = invoiced
            order.contract_remaining_amount = remaining
            order.contract_invoiced_percent = invoiced / total * 100.0 if total else 0.0
            order.contract_remaining_percent = remaining / total * 100.0 if total else 0.0
