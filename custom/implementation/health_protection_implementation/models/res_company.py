from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    stamp = fields.Image(string='Stamp', max_width=512, max_height=512,
                         help='Printed above the footer of all external documents.')
    hp_bank_account = fields.Char(string='Bank Acc No / IBAN No',
                                  help='Printed under the payment terms on quotations, sales orders and invoices.')


class BaseDocumentLayout(models.TransientModel):
    _inherit = 'base.document.layout'

    # The layout preview renders the external layouts with this wizard as `company`
    stamp = fields.Image(related='company_id.stamp', readonly=True)
