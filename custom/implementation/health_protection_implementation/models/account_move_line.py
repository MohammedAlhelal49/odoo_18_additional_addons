import re

from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    hp_item_code = fields.Char(string='Item Code', related='product_id.default_code', readonly=True)
    hp_batch_number = fields.Char(string='Batch Number', copy=False)
    hp_expiry_date = fields.Char(string='Expiry Date', copy=False)
    hp_tax_amount = fields.Float(string='Tax Amount', compute='_compute_hp_tax_amount')

    def hp_name_without_code(self):
        self.ensure_one()
        return re.sub(r'^\s*\[[^\]]*\]\s*', '', self.name or '')

    def hp_analytic_names(self):
        self.ensure_one()
        ids = []
        for key in (self.analytic_distribution or {}):
            ids += [int(i) for i in str(key).split(',') if i.strip().isdigit()]
        return ', '.join(self.env['account.analytic.account'].browse(ids).mapped('name'))

    @api.depends('debit', 'credit', 'tax_line_id')
    def _compute_hp_tax_amount(self):
        for line in self:
            line.hp_tax_amount = (line.debit + line.credit) if line.tax_line_id else 0.0
