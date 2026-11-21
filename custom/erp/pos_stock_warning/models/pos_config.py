from odoo import models, fields, api


class PosConfig(models.Model):
    _inherit = "pos.config"

    stock_restriction_enabled = fields.Boolean(
        string="Restriction based on QTY",
        default=False,
        help="Enable stock quantity restriction in POS",
    )
    stock_restriction_type = fields.Selection(
        selection=[
            ("alert", "Alert"),
            ("block", "Block"),
        ],
        string="Restriction Type",
        default=False,
    )

    # pos.config._load_pos_data_fields بترجع [] من الـ mixin
    # وبالتالي search_read([]) بيرجع كل الحقول تلقائياً
    # الحقول الجديدة بتتحمل تلقائياً لأنها معرفة على الموديل
    # ما في حاجة لأي override إضافي