from odoo import api, fields, models, _
from datetime import datetime, timedelta


class MedicalDashboard(models.TransientModel):
    _name = 'medical.dashboard'
    _description = 'Medical Appointment Dashboard'

    # Summary Card Fields
    total_appointments = fields.Integer(compute='_compute_appointments', string='Total Appointments')
    completed_appointments = fields.Integer(compute='_compute_appointments', string='Completed')
    upcoming_appointments = fields.Integer(compute='_compute_appointments', string='Upcoming')
    cancelled_appointments = fields.Integer(compute='_compute_appointments', string='Cancelled')
    no_show_appointments = fields.Integer(compute='_compute_appointments', string='No-Show')

    total_revenue = fields.Monetary(compute='_compute_financial', string='Total Revenue', currency_field='company_currency_id')
    total_commission = fields.Monetary(compute='_compute_financial', string='Total Commission', currency_field='company_currency_id')

    # Previous Period Comparison
    total_appointments_prev = fields.Integer(compute='_compute_appointments', string='Prev Appointments')
    completed_appointments_prev = fields.Integer(compute='_compute_appointments', string='Prev Completed')
    total_revenue_prev = fields.Monetary(compute='_compute_financial', string='Prev Revenue', currency_field='company_currency_id')

    # Percentage Changes
    appointments_change_pct = fields.Float(compute='_compute_changes', string='Appointments Change %')
    completed_change_pct = fields.Float(compute='_compute_changes', string='Completed Change %')
    revenue_change_pct = fields.Float(compute='_compute_changes', string='Revenue Change %')

    # Date Range
    date_from = fields.Date(string='From Date', default=lambda self: fields.Date.today().replace(day=1))
    date_to = fields.Date(string='To Date', default=lambda self: fields.Date.today())

    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company, required=True)

    @api.depends('date_from', 'date_to')
    def _compute_appointments(self):
        for record in self:
            # Current period
            domain = [
                ('appointment_date', '>=', record.date_from),
                ('appointment_date', '<=', record.date_to),
            ]

            # Apply doctor filter if user is doctor
            if not self.env.user._is_admin():
                doctor = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)])
                if doctor:
                    domain.append(('doctor_id', '=', doctor.id))

            appointments = self.env['medical.appointment'].search(domain)
            record.total_appointments = len(appointments)
            record.completed_appointments = len(appointments.filtered(lambda a: a.status == 'completed'))
            record.upcoming_appointments = len(appointments.filtered(lambda a: a.status in ['tentative', 'confirmed']))
            record.cancelled_appointments = len(appointments.filtered(lambda a: a.status == 'cancelled'))
            record.no_show_appointments = len(appointments.filtered(lambda a: a.status == 'no_show'))

            # Previous period (same length)
            period_days = (record.date_to - record.date_from).days + 1
            prev_date_to = record.date_from - timedelta(days=1)
            prev_date_from = prev_date_to - timedelta(days=period_days - 1)

            domain_prev = [
                ('appointment_date', '>=', prev_date_from),
                ('appointment_date', '<=', prev_date_to),
            ]
            if not self.env.user._is_admin():
                doctor = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)])
                if doctor:
                    domain_prev.append(('doctor_id', '=', doctor.id))

            appointments_prev = self.env['medical.appointment'].search(domain_prev)
            record.total_appointments_prev = len(appointments_prev)
            record.completed_appointments_prev = len(appointments_prev.filtered(lambda a: a.status == 'completed'))

    @api.depends('date_from', 'date_to')
    def _compute_financial(self):
        for record in self:
            domain = [
                ('appointment_date', '>=', record.date_from),
                ('appointment_date', '<=', record.date_to),
                ('status', '=', 'completed'),
            ]

            if not self.env.user._is_admin():
                doctor = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)])
                if doctor:
                    domain.append(('doctor_id', '=', doctor.id))

            appointments = self.env['medical.appointment'].search(domain)
            record.total_revenue = sum(appointments.mapped('appointment_total'))
            record.total_commission = sum(appointments.mapped('commission_amount'))

            # Previous period
            period_days = (record.date_to - record.date_from).days + 1
            prev_date_to = record.date_from - timedelta(days=1)
            prev_date_from = prev_date_to - timedelta(days=period_days - 1)

            domain_prev = [
                ('appointment_date', '>=', prev_date_from),
                ('appointment_date', '<=', prev_date_to),
                ('status', '=', 'completed'),
            ]
            if not self.env.user._is_admin():
                doctor = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)])
                if doctor:
                    domain_prev.append(('doctor_id', '=', doctor.id))

            appointments_prev = self.env['medical.appointment'].search(domain_prev)
            record.total_revenue_prev = sum(appointments_prev.mapped('appointment_total'))

    @api.depends('total_appointments', 'total_appointments_prev', 'completed_appointments', 'completed_appointments_prev', 'total_revenue', 'total_revenue_prev')
    def _compute_changes(self):
        for record in self:
            # Appointments change
            if record.total_appointments_prev > 0:
                record.appointments_change_pct = ((record.total_appointments - record.total_appointments_prev) / record.total_appointments_prev) * 100
            else:
                record.appointments_change_pct = 0

            # Completed change
            if record.completed_appointments_prev > 0:
                record.completed_change_pct = ((record.completed_appointments - record.completed_appointments_prev) / record.completed_appointments_prev) * 100
            else:
                record.completed_change_pct = 0

            # Revenue change
            if record.total_revenue_prev > 0:
                record.revenue_change_pct = ((record.total_revenue - record.total_revenue_prev) / record.total_revenue_prev) * 100
            else:
                record.revenue_change_pct = 0
