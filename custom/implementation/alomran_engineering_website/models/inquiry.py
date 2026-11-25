# -*- coding: utf-8 -*-
from odoo import api, fields, models

from .project import EMIRATES


class AlomranEngInquiry(models.Model):
    _name = 'alomran.eng.inquiry'
    _description = 'Al Omran Website Inquiry'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    name = fields.Char(string='Full Name', required=True, tracking=True)
    phone = fields.Char(required=True)
    email = fields.Char()
    service = fields.Char(string='Service Requested')
    emirate = fields.Selection(EMIRATES)
    message = fields.Text()
    lang = fields.Char(string='Website Language')
    source_page = fields.Char()
    lead_id = fields.Integer(string='CRM Lead ID', readonly=True,
                             help='Set when the CRM app is installed and a lead was created.')
    state = fields.Selection([
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('quoted', 'Quotation Sent'),
        ('won', 'Won'),
        ('lost', 'Lost'),
    ], default='new', required=True, tracking=True)

    @api.model
    def create_from_website(self, vals):
        """Create the inquiry and, when CRM is installed, a matching lead."""
        inquiry = self.sudo().create(vals)
        if 'crm.lead' in self.env:
            emirate = dict(EMIRATES).get(vals.get('emirate'), '')
            lead = self.env['crm.lead'].sudo().create({
                'name': 'Website: %s — %s' % (vals.get('service') or 'Consultation', vals['name']),
                'contact_name': vals['name'],
                'phone': vals.get('phone'),
                'email_from': vals.get('email'),
                'description': '\n'.join(filter(None, [
                    vals.get('message'),
                    emirate and 'Emirate: %s' % emirate,
                    vals.get('source_page') and 'Page: %s' % vals['source_page'],
                ])),
                'type': 'lead',
            })
            inquiry.lead_id = lead.id
        return inquiry
