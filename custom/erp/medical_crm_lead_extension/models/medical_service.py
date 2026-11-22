from odoo import fields, models


class MedicalService(models.Model):
    _name = 'medical.service'
    _description = 'Medical Service Catalog'

    name = fields.Char(string='Service Name', required=True)
    code = fields.Char(string='Service Code')
    description = fields.Text(string='Description')
