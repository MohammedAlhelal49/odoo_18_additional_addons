import re

from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    hp_item_code = fields.Char(string='Item Code', related='product_id.default_code', readonly=True)
    hp_batch_number = fields.Char(string='Batch Number', copy=False)
    hp_expiry_date = fields.Char(string='Expiry Date', copy=False)

    def hp_name_without_code(self):
        self.ensure_one()
        return re.sub(r'^\s*\[[^\]]*\]\s*', '', self.name or '')

    def _prepare_invoice_line(self, **optional_values):
        res = super()._prepare_invoice_line(**optional_values)
        res.update({
            'hp_batch_number': self.hp_batch_number,
            'hp_expiry_date': self.hp_expiry_date,
        })
        return res
