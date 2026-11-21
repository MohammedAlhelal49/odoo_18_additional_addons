# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    dekad_default_customer_id = fields.Many2one(
        related='company_id.dekad_default_customer_id',
        string='Default Customer',
        readonly=False,
        help='This customer will be automatically set on new Customer '
             'Invoices / Credit Notes when the Customer field is left empty.',
    )