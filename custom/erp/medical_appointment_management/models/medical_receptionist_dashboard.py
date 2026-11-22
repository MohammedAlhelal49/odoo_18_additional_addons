# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime, timedelta
import pytz


class MedicalReceptionistDashboard(models.Model):
    _name = 'medical.receptionist.dashboard'
    _description = 'Medical Reception Desk Dashboard'

    name = fields.Char(string='Title', default='Reception Desk Dashboard', required=True)
    company_id = fields.Many2one('res.company', string='Clinic / Company', default=lambda self: self.env.company, required=True)
    today_date = fields.Date(string="Today's Date", compute='_compute_metrics')
    tomorrow_date = fields.Date(string="Tomorrow's Date", compute='_compute_metrics')

    # Dashboard Counters
    kpi_today_total = fields.Integer(string="Today's Total Appointments", compute='_compute_metrics')
    kpi_tomorrow_pending = fields.Integer(string="Pending Confirmations (Tomorrow)", compute='_compute_metrics')
    kpi_patients_waiting = fields.Integer(string="Patients Waiting", compute='_compute_metrics')
    kpi_patients_arrived = fields.Integer(string="Patients Arrived", compute='_compute_metrics')
    kpi_cancellations_today = fields.Integer(string="Cancellations Today", compute='_compute_metrics')

    dashboard_html = fields.Html(string='Live Dashboard View', compute='_compute_metrics', sanitize=False)

    def _get_timezone(self):
        tz_name = self.env.user.tz or self.company_id.partner_id.tz or 'UTC'
        try:
            return pytz.timezone(tz_name)
        except Exception:
            return pytz.UTC

    @api.depends('company_id')
    def _compute_metrics(self):
        Appointment = self.env['medical.appointment']
        for rec in self:
            tz = rec._get_timezone()
            now_dt = datetime.now(tz)
            today = now_dt.date()
            tomorrow = today + timedelta(days=1)

            rec.today_date = today
            rec.tomorrow_date = tomorrow

            # Today's appointments
            today_apts = Appointment.search([
                ('appointment_date', '=', today),
                ('company_id', '=', rec.company_id.id)
            ])
            rec.kpi_today_total = len(today_apts)
            rec.kpi_patients_waiting = len(today_apts.filtered(lambda a: a.status in ('checked_in', 'ready_for_doctor')))
            rec.kpi_patients_arrived = len(today_apts.filtered(lambda a: a.status in ('checked_in', 'ready_for_doctor', 'in_consultation', 'completed')))
            rec.kpi_cancellations_today = len(today_apts.filtered(lambda a: a.status == 'cancelled' or a.confirmation_call_status == 'rescheduled'))

            # Tomorrow's appointments pending confirmation
            tomorrow_apts = Appointment.search([
                ('appointment_date', '=', tomorrow),
                ('company_id', '=', rec.company_id.id),
                ('status', '!=', 'cancelled')
            ])
            rec.kpi_tomorrow_pending = len(tomorrow_apts.filtered(lambda a: a.confirmation_call_status in ('pending', False)))

            # Render responsive HTML card view
            rec.dashboard_html = rec._generate_dashboard_html(today, tomorrow, today_apts, tomorrow_apts)

    def _generate_dashboard_html(self, today, tomorrow, today_apts, tomorrow_apts):
        tz_str = self.env.user.tz or self.company_id.partner_id.tz or 'UTC'
        html = f"""
        <div class="container-fluid p-3" style="background-color: #f8f9fa; border-radius: 8px;">
            <!-- Header bar -->
            <div class="d-flex justify-content-between align-items-center mb-4 pb-2 border-bottom">
                <div>
                    <h3 class="fw-bold mb-1" style="color: #1e293b;">🏢 Reception Desk Operations</h3>
                    <p class="text-muted mb-0">Live schedule management &bull; Timezone: <b>{tz_str}</b> &bull; Today: <b>{today.strftime('%A, %d %B %Y')}</b></p>
                </div>
                <div>
                    <span class="badge bg-primary fs-6 px-3 py-2">Tomorrow: {tomorrow.strftime('%d %b %Y')}</span>
                </div>
            </div>

            <!-- KPI Summary Cards -->
            <div class="row g-3 mb-4">
                <div class="col-12 col-sm-6 col-xl-2">
                    <div class="card shadow-sm border-0 h-100 text-center p-3" style="border-left: 4px solid #3b82f6 !important;">
                        <span class="text-muted small text-uppercase fw-semibold">Today's Bookings</span>
                        <h2 class="fw-bold my-2 text-primary">{self.kpi_today_total}</h2>
                        <span class="small text-muted">All scheduled visits</span>
                    </div>
                </div>
                <div class="col-12 col-sm-6 col-xl-2">
                    <div class="card shadow-sm border-0 h-100 text-center p-3" style="border-left: 4px solid #f59e0b !important;">
                        <span class="text-muted small text-uppercase fw-semibold">Pending Confirmation</span>
                        <h2 class="fw-bold my-2 text-warning">{self.kpi_tomorrow_pending}</h2>
                        <span class="small text-muted">Tomorrow's visits to call</span>
                    </div>
                </div>
                <div class="col-12 col-sm-6 col-xl-2">
                    <div class="card shadow-sm border-0 h-100 text-center p-3" style="border-left: 4px solid #06b6d4 !important;">
                        <span class="text-muted small text-uppercase fw-semibold">Patients Waiting</span>
                        <h2 class="fw-bold my-2 text-info">{self.kpi_patients_waiting}</h2>
                        <span class="small text-muted">In clinic waiting room</span>
                    </div>
                </div>
                <div class="col-12 col-sm-6 col-xl-2">
                    <div class="card shadow-sm border-0 h-100 text-center p-3" style="border-left: 4px solid #10b981 !important;">
                        <span class="text-muted small text-uppercase fw-semibold">Patients Arrived</span>
                        <h2 class="fw-bold my-2 text-success">{self.kpi_patients_arrived}</h2>
                        <span class="small text-muted">Checked-in or seen</span>
                    </div>
                </div>
                <div class="col-12 col-sm-6 col-xl-2">
                    <div class="card shadow-sm border-0 h-100 text-center p-3" style="border-left: 4px solid #ef4444 !important;">
                        <span class="text-muted small text-uppercase fw-semibold">Cancellations</span>
                        <h2 class="fw-bold my-2 text-danger">{self.kpi_cancellations_today}</h2>
                        <span class="small text-muted">Cancelled or rescheduled</span>
                    </div>
                </div>
                <div class="col-12 col-sm-6 col-xl-2">
                    <div class="card shadow-sm border-0 h-100 text-center p-3" style="border-left: 4px solid #8b5cf6 !important;">
                        <span class="text-muted small text-uppercase fw-semibold">Tomorrow Total</span>
                        <h2 class="fw-bold my-2 text-purple" style="color: #8b5cf6;">{len(tomorrow_apts)}</h2>
                        <span class="small text-muted">Total booked tomorrow</span>
                    </div>
                </div>
            </div>

            <!-- Fast Action Buttons -->
            <div class="card border-0 shadow-sm mb-4">
                <div class="card-body p-3">
                    <div class="d-flex flex-wrap gap-2">
                        <a role="button" class="btn btn-outline-primary fw-medium" href="#action_view_today_appointments">
                            📅 View Today's Appointments ({self.kpi_today_total})
                        </a>
                        <a role="button" class="btn btn-outline-warning fw-medium" href="#action_view_tomorrow_confirmations">
                            📞 Tomorrow's Confirmations Queue ({len(tomorrow_apts)})
                        </a>
                        <a role="button" class="btn btn-outline-info fw-medium" href="#action_view_waiting_room">
                            🪑 Waiting Room Queue ({self.kpi_patients_waiting})
                        </a>
                        <a role="button" class="btn btn-outline-danger fw-medium" href="#action_view_cancellations_today">
                            ❌ Today's Cancellations ({self.kpi_cancellations_today})
                        </a>
                    </div>
                </div>
            </div>
        </div>
        """
        return html

    def action_view_today_appointments(self):
        self.ensure_one()
        return {
            'name': _("Today's Appointments (%s)") % self.today_date,
            'type': 'ir.actions.act_window',
            'res_model': 'medical.appointment',
            'view_mode': 'list,form',
            'domain': [('appointment_date', '=', self.today_date)],
            'context': {'default_appointment_date': self.today_date},
        }

    def action_view_tomorrow_confirmations(self):
        self.ensure_one()
        return {
            'name': _("Tomorrow's Confirmations Queue (%s)") % self.tomorrow_date,
            'type': 'ir.actions.act_window',
            'res_model': 'medical.appointment',
            'view_mode': 'list,form',
            'domain': [('appointment_date', '=', self.tomorrow_date), ('status', '!=', 'cancelled')],
            'context': {
                'default_appointment_date': self.tomorrow_date,
                'search_default_pending_confirmation': 1,
            },
        }

    def action_view_waiting_room(self):
        self.ensure_one()
        return {
            'name': _("Waiting Room & Check-in"),
            'type': 'ir.actions.act_window',
            'res_model': 'medical.appointment',
            'view_mode': 'list,form',
            'domain': [('appointment_date', '=', self.today_date), ('status', 'in', ['checked_in', 'ready_for_doctor'])],
            'context': {'default_appointment_date': self.today_date},
        }

    def action_view_cancellations_today(self):
        self.ensure_one()
        return {
            'name': _("Today's Cancellations & Reschedules"),
            'type': 'ir.actions.act_window',
            'res_model': 'medical.appointment',
            'view_mode': 'list,form',
            'domain': [('appointment_date', '=', self.today_date), ('status', '=', 'cancelled')],
            'context': {'default_appointment_date': self.today_date},
        }

    def action_refresh(self):
        for rec in self:
            rec._compute_metrics()
        return True

    @api.model
    def action_open_dashboard(self):
        dashboard = self.search([('company_id', '=', self.env.company.id)], limit=1)
        if not dashboard:
            dashboard = self.create({
                'name': 'Reception Desk Dashboard',
                'company_id': self.env.company.id,
            })
        dashboard.action_refresh()
        return {
            'name': _('Reception Operations Dashboard'),
            'type': 'ir.actions.act_window',
            'res_model': 'medical.receptionist.dashboard',
            'res_id': dashboard.id,
            'view_mode': 'form',
            'target': 'current',
        }
