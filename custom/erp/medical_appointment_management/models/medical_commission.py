# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class MedicalCommission(models.Model):
    _name = 'medical.commission'
    _description = 'Medical Staff Commission'
    _order = 'create_date desc, id desc'

    name = fields.Char(string='Reference', required=True, default=lambda self: _('New'))
    appointment_id = fields.Many2one(
        'medical.appointment',
        string='Appointment',
        ondelete='cascade',
        index=True
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Medical Staff',
        index=True
    )
    user_id = fields.Many2one(
        'res.users',
        string='User',
        default=lambda self: self.env.user
    )
    role = fields.Selection([
        ('sales', 'Sales Representative'),
        ('reception', 'Receptionist'),
        ('nurse', 'Triage Nurse'),
        ('doctor', 'Doctor / Provider'),
    ], string='Role', required=True, default='sales')

    amount = fields.Monetary(
        string='Commission Amount',
        currency_field='currency_id',
        default=0.0
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )
    status = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('earned', 'Earned'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft')

    notes = fields.Text(string='Notes')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('medical.commission') or f"COM/{fields.Date.today().year}/{self.env['ir.sequence'].next_by_code('medical.appointment.seq') or '0001'}"
        return super().create(vals_list)
