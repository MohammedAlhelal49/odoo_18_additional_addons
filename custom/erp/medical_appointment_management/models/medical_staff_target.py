# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MedicalStaffTarget(models.Model):
    _name = 'medical.staff.target'
    _description = 'Medical Staff Performance Target & Goal'
    _order = 'date_start desc, target_type, name'

    name = fields.Char(
        string='Target Title',
        compute='_compute_name',
        store=True,
        readonly=False
    )
    target_type = fields.Selection([
        ('employee', 'Specific Employee'),
        ('department', 'Department / Team'),
        ('role', 'Medical Staff Role'),
    ], string='Target Type', default='employee', required=True)

    employee_id = fields.Many2one(
        'hr.employee',
        string='Staff Member',
        domain="[('medical_employee_type', '!=', False)]",
        index=True
    )
    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        index=True
    )
    role = fields.Selection([
        ('doctor', 'Doctor'),
        ('sales', 'Sales Employee'),
        ('receptionist', 'Receptionist'),
        ('nurse', 'Nurse'),
    ], string='Role')

    period_type = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
        ('custom', 'Custom Range'),
    ], string='Period Type', default='monthly', required=True)

    period_name = fields.Char(
        string='Period Label',
        help='e.g. October 2026, Q4 2026'
    )
    date_start = fields.Date(
        string='Start Date',
        required=True,
        default=fields.Date.context_today
    )
    date_end = fields.Date(
        string='End Date',
        required=True
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )
    active = fields.Boolean(default=True)
    notes = fields.Text(string='Notes / KPI Description')

    # Target KPI Goals
    revenue_target = fields.Float(
        string='Target Revenue',
        default=0.0,
        help='Target confirmed revenue for the period ($)'
    )
    completed_appointment_target = fields.Integer(
        string='Target Completed Appointments',
        default=0,
        help='Target number of completed appointments'
    )
    lead_conversion_target = fields.Float(
        string='Target Lead Conversion Rate (%)',
        default=0.0,
        help='Target lead-to-patient/appointment conversion rate'
    )
    max_cancellation_rate = fields.Float(
        string='Max Cancellation Rate (%)',
        default=10.0,
        help='Maximum acceptable appointment cancellation rate (%)'
    )
    max_no_show_rate = fields.Float(
        string='Max No-Show Rate (%)',
        default=5.0,
        help='Maximum acceptable appointment no-show rate (%)'
    )

    @api.depends('target_type', 'employee_id', 'department_id', 'role', 'period_name', 'date_start')
    def _compute_name(self):
        for rec in self:
            subject = ''
            if rec.target_type == 'employee' and rec.employee_id:
                subject = rec.employee_id.name
            elif rec.target_type == 'department' and rec.department_id:
                subject = rec.department_id.name
            elif rec.target_type == 'role' and rec.role:
                subject = dict(rec._fields['role'].selection).get(rec.role, rec.role)
            else:
                subject = _('General')

            period = rec.period_name or (rec.date_start.strftime('%B %Y') if rec.date_start else '')
            rec.name = f"{subject} - {period} Target" if period else f"{subject} Target"

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for rec in self:
            if rec.date_start and rec.date_end and rec.date_end < rec.date_start:
                raise ValidationError(_("Target End Date cannot be earlier than Start Date."))

    @api.constrains('target_type', 'employee_id', 'department_id', 'role')
    def _check_target_assignment(self):
        for rec in self:
            if rec.target_type == 'employee' and not rec.employee_id:
                raise ValidationError(_("Please select an employee for this target."))
            if rec.target_type == 'department' and not rec.department_id:
                raise ValidationError(_("Please select a department for this target."))
            if rec.target_type == 'role' and not rec.role:
                raise ValidationError(_("Please select a role for this target."))
