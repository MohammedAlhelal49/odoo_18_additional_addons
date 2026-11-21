# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PosOrder(models.Model):
    _inherit = 'pos.order'

    account_move_name = fields.Char(
        string='Invoice Number',
        compute='_compute_account_move_name',
    )

    @api.depends('account_move')
    def _compute_account_move_name(self):
        for order in self:
            order.account_move_name = order.account_move.name if order.account_move else ''