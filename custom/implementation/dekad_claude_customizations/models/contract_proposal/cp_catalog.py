from odoo import fields, models


class DekadCpSupportPlan(models.Model):
    _name = 'dekad.cp.support.plan'
    _description = 'Annual Support Plan (Technical Proposal catalogue)'
    _order = 'sequence, hours_per_year, id'

    name = fields.Char(string='Plan', required=True, translate=True)
    sequence = fields.Integer(default=10)
    hours_per_year = fields.Integer(string='Hours per Year', required=True)
    active = fields.Boolean(default=True)

