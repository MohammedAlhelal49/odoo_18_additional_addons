# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo.tools.translate import html_translate

CATEGORIES = [
    ('villa', 'Villas'),
    ('residential', 'Residential Buildings'),
    ('commercial', 'Commercial'),
    ('interior', 'Interior & Fit-Out'),
    ('landscape', 'Landscape & Urban'),
    ('public', 'Public & Community'),
]

EMIRATES = [
    ('abu_dhabi', 'Abu Dhabi'),
    ('al_ain', 'Al Ain'),
    ('dubai', 'Dubai'),
    ('sharjah', 'Sharjah'),
    ('ajman', 'Ajman'),
    ('uaq', 'Umm Al Quwain'),
    ('rak', 'Ras Al Khaimah'),
    ('fujairah', 'Fujairah'),
]


class AlomranEngProject(models.Model):
    _name = 'alomran.eng.project'
    _description = 'Al Omran Portfolio Project'
    _order = 'sequence, id desc'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    category = fields.Selection(CATEGORIES, required=True, default='villa')
    emirate = fields.Selection(EMIRATES, default='al_ain')
    location = fields.Char(translate=True, help='e.g. Al Jimi, Al Ain')
    year = fields.Char()
    area = fields.Char(string='Built-up Area', help='Free text, e.g. "1,250 m²"')
    scope = fields.Char(string='Scope of Work', translate=True,
                        help='Short list, e.g. "Architecture · Structure · MEP · Supervision"')
    summary = fields.Text(translate=True, help='One or two sentences shown on the project card.')
    description = fields.Html(translate=html_translate, sanitize=True)
    image = fields.Image(string='Cover Image', max_width=1920, max_height=1920)
    gallery_ids = fields.One2many('alomran.eng.project.image', 'project_id', string='Gallery')
    is_featured = fields.Boolean(string='Featured on Home', default=False)
    is_published = fields.Boolean(string='Published', default=True)
    active = fields.Boolean(default=True)

    def website_url(self):
        self.ensure_one()
        return '/projects/%s' % self.id

    def action_open_website(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_url', 'url': self.website_url(), 'target': 'self'}


class AlomranEngProjectImage(models.Model):
    _name = 'alomran.eng.project.image'
    _description = 'Al Omran Project Gallery Image'
    _order = 'sequence, id'

    project_id = fields.Many2one('alomran.eng.project', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    name = fields.Char(string='Caption', translate=True)
    image = fields.Image(required=True, max_width=1920, max_height=1920)
