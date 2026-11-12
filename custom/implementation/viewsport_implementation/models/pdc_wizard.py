from odoo import fields, models

from .purchase_order import amount_to_dirhams_text


class PdcWizard(models.Model):
    _inherit = 'pdc.wizard'

    vs_ack_type = fields.Selection(
        [('vendor', 'Vendor Payment'), ('petty_cash', 'Petty Cash')],
        string='Acknowledgement Type', default='vendor',
        help='Petty Cash prints "General Manager" as the approver and the petty cash references, as on the template.')
    vs_detail = fields.Text(
        string='Detail Breakdown',
        help='Printed on the cheque acknowledgement. Left empty, it is written from the bills paid by this cheque.')

    def _vs_cheque_date(self):
        self.ensure_one()
        return self.due_date or self.payment_date

    def _vs_bills(self):
        self.ensure_one()
        return (self.invoice_ids | self.invoice_id).filtered(lambda m: m.move_type in ('in_invoice', 'in_refund'))

    def _vs_vendor_invoice_ref(self):
        """Vendor's own invoice numbers (Bill Reference), else the bill numbers."""
        self.ensure_one()
        return ', '.join(b.ref or b.name for b in self._vs_bills())

    def _vs_detail_text(self):
        self.ensure_one()
        if self.vs_detail:
            return self.vs_detail
        if self.vs_ack_type == 'petty_cash':
            return 'Issued cheque %s as petty cash fund to %s.' % (self.reference or '', self.partner_id.name or '')
        bills = self._vs_bills()
        if not bills:
            return self.memo or ''
        full = all(b.payment_state in ('paid', 'in_payment') for b in bills) or \
            abs(sum(bills.mapped('amount_total')) - self.payment_amount) < 0.01
        origins = [o for o in bills.mapped('invoice_origin') if o]
        text = '%s against %s' % ('100% Full Payment' if full else 'Partial Payment',
                                  ('PO#' + ', '.join(origins)) if origins else 'Bill No. ' + ', '.join(bills.mapped('name')))
        if self.memo:
            text += ', ' + self.memo
        return text + '.'

    def _vs_cheque_image(self):
        """Cheque photo: the PDC image, else the first image among the cheque attachments."""
        self.ensure_one()
        if self.pdc_image:
            return self.pdc_image
        image = self.attachment_ids.filtered(lambda a: (a.mimetype or '').startswith('image/'))[:1]
        return image.datas or False

    def _vs_amount_in_words(self):
        self.ensure_one()
        if self.currency_id.name == 'AED':
            return amount_to_dirhams_text(self.payment_amount)
        return self.currency_id.amount_to_text(self.payment_amount)
