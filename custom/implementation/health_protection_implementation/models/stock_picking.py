from odoo import models

from .account_move import hp_address_line


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def do_print_picking(self):
        """Print button: Delivery Slip instead of Picking Operations."""
        self.write({'printed': True})
        return self.env.ref('stock.action_report_delivery').report_action(self)

    def hp_get_po_number(self):
        """Customer PO No: from the sales order, or from the invoice the delivery was created from
        (source_invoice_id, added by another module - may not exist)."""
        self.ensure_one()
        if self.sale_id.hp_po_number:
            return self.sale_id.hp_po_number
        if 'source_invoice_id' in self._fields:
            return self.source_invoice_id.hp_po_number or ''
        return ''

    def hp_get_delivery_note_no(self):
        """Delivery Note No: the number of the linked customer invoice (the invoice the delivery was created from,
        or else the sales order's invoice); the delivery reference when there is no invoice yet."""
        self.ensure_one()
        if 'source_invoice_id' in self._fields:
            invoice = self.source_invoice_id
            if invoice and invoice.state != 'cancel' and invoice.name and invoice.name != '/':
                return invoice.name
        return self.sale_id.hp_invoice_number or self.name

    def hp_partner_address_line(self, partner):
        self.ensure_one()
        return hp_address_line(partner)

    def hp_footer_qr_url(self):
        """Footer QR: portal link of the linked customer invoice (the one the delivery was created from), else of the
        sales order; no link (website) otherwise."""
        self.ensure_one()
        if 'source_invoice_id' in self._fields and self.source_invoice_id and self.source_invoice_id.hp_show_portal_qr():
            return self.source_invoice_id.hp_portal_url()
        if self.sale_id and self.sale_id.hp_show_portal_qr():
            return self.sale_id.hp_portal_url()
        return False
