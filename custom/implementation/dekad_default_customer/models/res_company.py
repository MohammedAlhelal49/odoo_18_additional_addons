# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    dekad_default_customer_id = fields.Many2one(
        comodel_name='res.partner',
        string='Default Customer',
        help='This customer will be automatically set on new Customer '
             'Invoices / Credit Notes when the Customer field is left empty.',
    )