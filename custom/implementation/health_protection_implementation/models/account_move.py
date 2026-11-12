from odoo import api, fields, models


def hp_address_line(partner):
    """Customer address on one line, from the largest to the smallest part:
    Country, State, City, Street, Street 2. Empty when no street / city / state is filled."""
    if not (partner.street or partner.street2 or partner.city or partner.state_id):
        return ''
    parts = [partner.country_id.name, partner.state_id.name, partner.city, partner.street, partner.street2]
    return ', '.join(p.strip() for p in parts if p and p.strip())


class AccountMove(models.Model):
    _inherit = 'account.move'

    hp_po_number = fields.Char(string='PO No', compute='_compute_hp_po_number', store=True, readonly=False, copy=False,
                               help="Customer purchase order number: taken from the sales order(s) of this invoice, "
                                    "can be typed when the invoice has no sales order. Printed on the invoice.")

    @api.depends('invoice_line_ids.sale_line_ids.order_id.hp_po_number')
    def _compute_hp_po_number(self):
        for move in self:
            numbers = move.invoice_line_ids.sale_line_ids.order_id.filtered('hp_po_number').mapped('hp_po_number')
            if numbers:
                move.hp_po_number = ', '.join(dict.fromkeys(numbers))
            elif not move.hp_po_number:
                move.hp_po_number = False

    def hp_partner_address_line(self):
        self.ensure_one()
        return hp_address_line(self.partner_id)

    def hp_show_portal_qr(self):
        self.ensure_one()
        return self.state == 'posted' and self.move_type in ('out_invoice', 'out_refund')
