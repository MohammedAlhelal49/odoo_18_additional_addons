# -*- coding: utf-8 -*-
from odoo import models

CUSTOMER_MOVE_TYPES = ('out_invoice', 'out_refund')


class AccountMove(models.Model):
    _inherit = 'account.move'

    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)

        if 'partner_id' not in fields_list or defaults.get('partner_id'):
            return defaults

        # move_type may come from the returned defaults or from the
        # action context (e.g. default_move_type=out_invoice when opening
        # the Customer Invoices menu).
        move_type = defaults.get('move_type') or self._context.get('default_move_type')

        if move_type in CUSTOMER_MOVE_TYPES:
            company_id = defaults.get('company_id') or self.env.company.id
            company = self.env['res.company'].browse(company_id)
            if company.dekad_default_customer_id:
                defaults['partner_id'] = company.dekad_default_customer_id.id

        return defaults