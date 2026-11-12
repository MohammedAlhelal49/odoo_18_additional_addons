from odoo import fields, models


class OrchidaUnitCode(models.Model):
    _name = 'orchida.unit.code'
    _description = 'Orchida API Unit Codes (UN/ECE Rec 20/21)'
    _order = 'code'

    code = fields.Char(required=True, index=True)
    name = fields.Char(required=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('uniq_orchida_unit_code', 'unique(code)', 'Unit code must be unique.'),
    ]
