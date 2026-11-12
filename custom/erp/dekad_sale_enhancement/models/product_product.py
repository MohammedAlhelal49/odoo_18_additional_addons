from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    default_code_name = fields.Char(
        string="Reference and Name",
        compute="_compute_default_code_name",
        store=True
    )

    def _compute_default_code_name(self):
        for rec in self:
            code = f"[{rec.default_code}]" if rec.default_code else ""
            rec.default_code_name = f"{code} {rec.name}".strip()
