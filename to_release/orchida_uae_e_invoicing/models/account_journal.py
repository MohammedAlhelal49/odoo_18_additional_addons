from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    orchida_submit_einvoice = fields.Boolean(
        string="Submit to E-Invoice",
        default=True,
        help="If enabled, customer invoices and credit notes on this journal "
             "are validated and submitted to Orchida e-invoicing when confirmed.",
    )
