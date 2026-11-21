from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    invoice_company = fields.Char(
        string='Invoice Company',
        help="Overrides the customer partner shown on the report if specified."
    )
    invoice_trn = fields.Char(
        string='Invoice TRN',
        help="Overrides the tax registration number shown on the report if specified."
    )
