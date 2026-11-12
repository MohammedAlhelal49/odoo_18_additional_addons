from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    related_customer_id = fields.Many2one('res.partner', string='Related Customer')
    related_project_id = fields.Many2one('project.project', string='Related Project')
    related_date = fields.Datetime(string='Date')
