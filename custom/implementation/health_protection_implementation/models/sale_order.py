from odoo import api, fields, models

from .account_move import hp_address_line


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    hp_date = fields.Date(string='Date', copy=False,
                          help="Date printed on the quotation / sales order instead of the quotation, order and expiration dates.")
    hp_po_number = fields.Char(string='PO No', copy=False,
                               help="Customer purchase order number, printed on the quotation / sales order.")
    hp_invoice_number = fields.Char(string='Invoice No', compute='_compute_hp_invoice_number',
                                    help="First (oldest) non-cancelled customer invoice created from this order.")

    @api.depends('invoice_ids.name', 'invoice_ids.state', 'invoice_ids.move_type')
    def _compute_hp_invoice_number(self):
        for order in self:
            invoices = order.invoice_ids.filtered(
                lambda m: m.move_type == 'out_invoice' and m.state != 'cancel' and m.name and m.name != '/'
            ).sorted(lambda m: (m.invoice_date or m.date or fields.Date.today(), m.id))
            order.hp_invoice_number = invoices[:1].name or False

    def hp_partner_address_line(self):
        self.ensure_one()
        return hp_address_line(self.partner_id)

    def hp_show_portal_qr(self):
        self.ensure_one()
        return self.state != 'cancel'
