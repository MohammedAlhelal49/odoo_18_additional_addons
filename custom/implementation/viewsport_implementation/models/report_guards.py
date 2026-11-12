"""Stop printing a Viewsport document on a record it does not describe
(e.g. a credit note layout on an invoice, a receipt voucher on a vendor payment)."""
from odoo import _, api, models
from odoo.exceptions import UserError

R = 'report.viewsport_implementation.'


class _VsGuardedReport(models.AbstractModel):
    _name = 'report.viewsport_implementation.vs_guard_mixin'
    _description = 'Viewsport report type guard'
    _table = 'vs_rpt_guard'

    _vs_model = None
    _vs_document = None

    def _vs_is_allowed(self, record):
        return True

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env[self._vs_model].browse(docids)
        wrong = docs.filtered(lambda r: not self._vs_is_allowed(r))
        if wrong:
            raise UserError(_('The "%(document)s" cannot be printed for: %(records)s',
                              document=self._vs_document, records=', '.join(wrong.mapped('display_name'))))
        return {'doc_ids': docs.ids, 'doc_model': self._vs_model, 'docs': docs, 'data': data}


class ReportTaxInvoice(models.AbstractModel):
    _name = R + 'report_tax_invoice_viewsport_document'
    _inherit = 'report.viewsport_implementation.vs_guard_mixin'
    _description = 'Viewsport Tax Invoice'
    _table = 'vs_rpt_tax_invoice'
    _vs_model = 'account.move'
    _vs_document = 'Tax Invoice'

    def _vs_is_allowed(self, move):
        return move.move_type == 'out_invoice'


class ReportProformaInvoice(models.AbstractModel):
    _name = R + 'report_proforma_invoice_viewsport_document'
    _inherit = R + 'report_tax_invoice_viewsport_document'
    _description = 'Viewsport Proforma Invoice'
    _table = 'vs_rpt_proforma'
    _vs_document = 'Proforma Invoice'


class ReportCommercialInvoice(models.AbstractModel):
    _name = R + 'report_commercial_invoice_viewsport_document'
    _inherit = R + 'report_tax_invoice_viewsport_document'
    _description = 'Viewsport Commercial Invoice'
    _table = 'vs_rpt_commercial'
    _vs_document = 'Commercial Invoice'


class ReportDebitNote(models.AbstractModel):
    _name = R + 'report_debit_note_viewsport_document'
    _inherit = R + 'report_tax_invoice_viewsport_document'
    _description = 'Viewsport Debit Note'
    _table = 'vs_rpt_debit_note'
    _vs_document = 'Debit Note'


class ReportCreditNote(models.AbstractModel):
    _name = R + 'report_credit_note_viewsport_document'
    _inherit = 'report.viewsport_implementation.vs_guard_mixin'
    _description = 'Viewsport Credit Note'
    _table = 'vs_rpt_credit_note'
    _vs_model = 'account.move'
    _vs_document = 'Credit Note'

    def _vs_is_allowed(self, move):
        return move.move_type == 'out_refund'


class ReportReceiptVoucher(models.AbstractModel):
    _name = R + 'report_receipt_voucher_viewsport_document'
    _inherit = 'report.viewsport_implementation.vs_guard_mixin'
    _description = 'Viewsport Receipt Voucher'
    _table = 'vs_rpt_receipt_voucher'
    _vs_model = 'account.payment'
    _vs_document = 'Receipt Voucher'

    def _vs_is_allowed(self, payment):
        return payment.payment_type == 'inbound' and payment.partner_type == 'customer'


class ReportDeliveryNote(models.AbstractModel):
    _name = R + 'report_delivery_note_viewsport_document'
    _inherit = 'report.viewsport_implementation.vs_guard_mixin'
    _description = 'Viewsport Delivery Note'
    _table = 'vs_rpt_delivery_note'
    _vs_model = 'stock.picking'
    _vs_document = 'Delivery Note'

    def _vs_is_allowed(self, picking):
        return picking.picking_type_code == 'outgoing'


class ReportDeliveryOrder(models.AbstractModel):
    _name = R + 'report_delivery_viewsport_document'
    _inherit = R + 'report_delivery_note_viewsport_document'
    _description = 'Viewsport Delivery Order'
    _table = 'vs_rpt_delivery_order'
    _vs_document = 'Delivery Order'


class ReportChequeAcknowledgement(models.AbstractModel):
    _name = R + 'report_cheque_ack_viewsport_document'
    _inherit = 'report.viewsport_implementation.vs_guard_mixin'
    _description = 'Viewsport Cheque Acknowledgement'
    _table = 'vs_rpt_cheque_ack'
    _vs_model = 'pdc.wizard'
    _vs_document = 'Cheque Acknowledgement'

    def _vs_is_allowed(self, cheque):
        return cheque.payment_type == 'send_money'
