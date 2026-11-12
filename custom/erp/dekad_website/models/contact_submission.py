# -*- coding: utf-8 -*-
from odoo import fields, models


class DekadContactSubmission(models.Model):
    _name = 'dekad.contact.submission'
    _description = 'Dekad Website Submission'
    _order = 'create_date desc'
    _rec_name = 'name'

    submission_type = fields.Selection([
        ('contact', 'Contact Message'),
        ('demo', 'Demo Request'),
        ('consultation', 'Consultation Request'),
        ('newsletter', 'Newsletter Subscription'),
    ], string='Type', default='contact', required=True)

    name = fields.Char(string='Full Name', required=True)
    email = fields.Char(string='Email Address', required=True)
    phone = fields.Char(string='Phone Number')
    company = fields.Char(string='Company Name')
    service = fields.Selection([
        ('odoo-consultancy', 'Odoo Consultancy'),
        ('odoo-implementation', 'Odoo Implementation'),
        ('odoo-integration', 'Odoo Integration'),
        ('odoo-support', 'Odoo Support'),
        ('odoo-migration', 'Odoo Migration'),
        ('odoo-web-design', 'Odoo Web Design'),
    ], string='Service Interested In')
    message = fields.Text(string='Message')
    state = fields.Selection([
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('done', 'Done'),
    ], string='Status', default='new', required=True)