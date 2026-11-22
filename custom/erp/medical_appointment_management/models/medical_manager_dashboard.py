# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime, timedelta
import pytz


class MedicalManagerDashboard(models.Model):
    _name = 'medical.manager.dashboard'
    _description = 'Medical Center Manager Operations Dashboard'

    name = fields.Char(string='Title', default='Manager Operations Dashboard', required=True)
    company_id = fields.Many2one('res.company', string='Clinic / Company', default=lambda self: self.env.company, required=True)
    dashboard_date = fields.Date(string="Operating Date", compute='_compute_metrics')

    # Executive Operational KPIs
    kpi_appointments_today = fields.Integer(string="Total Appointments Today", compute='_compute_metrics')
    kpi_completed_in_progress = fields.Integer(string="Completed & In Progress", compute='_compute_metrics')
    kpi_cancelled_no_show = fields.Integer(string="Cancelled & No-Show", compute='_compute_metrics')
    kpi_tomorrow_unconfirmed = fields.Integer(string="Tomorrow Unconfirmed", compute='_compute_metrics')
    kpi_new_leads_today = fields.Integer(string="New Leads Today", compute='_compute_metrics')
    kpi_overdue_leads = fields.Integer(string="Overdue Sales Leads", compute='_compute_metrics')
    kpi_patients_registered = fields.Integer(string="Total Registered Patients", compute='_compute_metrics')
    kpi_doctor_conflicts_count = fields.Integer(string="Doctor Scheduling Conflicts", compute='_compute_metrics')
    kpi_revenue_today = fields.Float(string="Revenue Today", compute='_compute_metrics')

    dashboard_html = fields.Html(string='Executive Operational Summary', compute='_compute_metrics', sanitize=False)

    def _get_timezone(self):
        tz_name = self.env.user.tz or self.company_id.partner_id.tz or 'UTC'
        try:
            return pytz.timezone(tz_name)
        except Exception:
            return pytz.UTC

    @api.depends('company_id')
    def _compute_metrics(self):
        Appointment = self.env['medical.appointment']
        Lead = self.env['crm.lead']
        Partner = self.env['res.partner']
        Invoice = self.env['account.move']

        for rec in self:
            tz = rec._get_timezone()
            now_dt = datetime.now(tz)
            today = now_dt.date()
            tomorrow = today + timedelta(days=1)
            rec.dashboard_date = today

            # Appointments
            today_apts = Appointment.search([
                ('appointment_date', '=', today),
                ('company_id', '=', rec.company_id.id)
            ])
            rec.kpi_appointments_today = len(today_apts)
            rec.kpi_completed_in_progress = len(today_apts.filtered(lambda a: a.status in ('in_consultation', 'completed')))
            rec.kpi_cancelled_no_show = len(today_apts.filtered(lambda a: a.status in ('cancelled', 'no_show')))

            # Conflicts
            conflicts = today_apts.filtered(lambda a: a.has_conflict or a.conflict_override)
            rec.kpi_doctor_conflicts_count = len(conflicts)

            # Tomorrow unconfirmed
            tomorrow_apts = Appointment.search([
                ('appointment_date', '=', tomorrow),
                ('company_id', '=', rec.company_id.id),
                ('status', '!=', 'cancelled')
            ])
            rec.kpi_tomorrow_unconfirmed = len(tomorrow_apts.filtered(lambda a: a.confirmation_call_status in ('pending', False)))

            # Leads
            today_leads = Lead.search([
                ('company_id', 'in', [False, rec.company_id.id]),
                ('create_date', '>=', datetime.combine(today, datetime.min.time())),
            ])
            rec.kpi_new_leads_today = len(today_leads)
            overdue_leads = Lead.search([
                ('company_id', 'in', [False, rec.company_id.id]),
                ('active', '=', True),
                ('probability', '<', 100),
                ('next_followup_date', '<', today)
            ])
            rec.kpi_overdue_leads = len(overdue_leads)

            # Registered Patients
            patients = Partner.search([
                ('is_patient', '=', True),
                ('patient_number', '!=', False)
            ])
            rec.kpi_patients_registered = len(patients)

            # Today Revenue
            today_invoices = Invoice.search([
                ('company_id', '=', rec.company_id.id),
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
                ('invoice_date', '=', today)
            ])
            rec.kpi_revenue_today = sum(today_invoices.mapped('amount_total'))

            # Render HTML summary
            rec.dashboard_html = rec._generate_dashboard_html(
                today, tomorrow, today_apts, conflicts, overdue_leads, today_invoices
            )

    def _generate_dashboard_html(self, today, tomorrow, today_apts, conflicts, overdue_leads, today_invoices):
        currency_symbol = self.company_id.currency_id.symbol or '$'
        tz_str = self.env.user.tz or self.company_id.partner_id.tz or 'UTC'

        # Doctor workload table
        doctors = today_apts.mapped('doctor_id')
        doctor_rows = []
        for doc in doctors:
            doc_apts = today_apts.filtered(lambda a: a.doctor_id == doc)
            comp = len(doc_apts.filtered(lambda a: a.status == 'completed'))
            in_prog = len(doc_apts.filtered(lambda a: a.status == 'in_consultation'))
            wait = len(doc_apts.filtered(lambda a: a.status in ('checked_in', 'ready_for_doctor')))
            canc = len(doc_apts.filtered(lambda a: a.status in ('cancelled', 'no_show')))
            doctor_rows.append(f"""
                <tr>
                    <td class="fw-semibold">{doc.name}</td>
                    <td class="text-center"><span class="badge bg-secondary">{len(doc_apts)}</span></td>
                    <td class="text-center"><span class="badge bg-success">{comp}</span></td>
                    <td class="text-center"><span class="badge bg-primary">{in_prog}</span></td>
                    <td class="text-center"><span class="badge bg-warning">{wait}</span></td>
                    <td class="text-center"><span class="badge bg-danger">{canc}</span></td>
                </tr>
            """)
        doctor_table_html = "".join(doctor_rows) if doctor_rows else "<tr><td colspan='6' class='text-center text-muted py-3'>No consultations scheduled today</td></tr>"

        html = f"""
        <div class="container-fluid p-3" style="background-color: #f8fafc; border-radius: 8px;">
            <!-- Header bar -->
            <div class="d-flex justify-content-between align-items-center mb-4 pb-2 border-bottom">
                <div>
                    <h3 class="fw-bold mb-1" style="color: #0f172a;">📊 Medical Center Executive Operations</h3>
                    <p class="text-muted mb-0">System Overview &bull; Clinic: <b>{self.company_id.name}</b> &bull; Date: <b>{today.strftime('%A, %d %B %Y')}</b> ({tz_str})</p>
                </div>
            </div>

            <!-- KPI Row 1: Appointments & Revenue -->
            <div class="row g-3 mb-4">
                <div class="col-12 col-sm-6 col-xl-3">
                    <div class="card shadow-sm border-0 h-100 p-3" style="background: linear-gradient(135deg, #1e3a8a, #3b82f6); color: white; border-radius: 10px;">
                        <span class="small text-uppercase fw-semibold" style="opacity: 0.85;">Total Bookings Today</span>
                        <h2 class="fw-bold my-2">{self.kpi_appointments_today}</h2>
                        <div class="d-flex justify-content-between small" style="opacity: 0.9;">
                            <span>Active / Done: {self.kpi_completed_in_progress}</span>
                            <span>Cancelled: {self.kpi_cancelled_no_show}</span>
                        </div>
                    </div>
                </div>
                <div class="col-12 col-sm-6 col-xl-3">
                    <div class="card shadow-sm border-0 h-100 p-3" style="background: linear-gradient(135deg, #065f46, #10b981); color: white; border-radius: 10px;">
                        <span class="small text-uppercase fw-semibold" style="opacity: 0.85;">Revenue Today (Invoiced)</span>
                        <h2 class="fw-bold my-2">{currency_symbol} {self.kpi_revenue_today:,.2f}</h2>
                        <span class="small" style="opacity: 0.9;">Posted patient invoices</span>
                    </div>
                </div>
                <div class="col-12 col-sm-6 col-xl-3">
                    <div class="card shadow-sm border-0 h-100 p-3" style="background: linear-gradient(135deg, #9a3412, #f97316); color: white; border-radius: 10px;">
                        <span class="small text-uppercase fw-semibold" style="opacity: 0.85;">Tomorrow's Confirmations</span>
                        <h2 class="fw-bold my-2">{self.kpi_tomorrow_unconfirmed}</h2>
                        <span class="small" style="opacity: 0.9;">Unconfirmed appointments</span>
                    </div>
                </div>
                <div class="col-12 col-sm-6 col-xl-3">
                    <div class="card shadow-sm border-0 h-100 p-3" style="background: linear-gradient(135deg, #4c1d95, #8b5cf6); color: white; border-radius: 10px;">
                        <span class="small text-uppercase fw-semibold" style="opacity: 0.85;">Registered Patients</span>
                        <h2 class="fw-bold my-2">{self.kpi_patients_registered}</h2>
                        <span class="small" style="opacity: 0.9;">Total registered MRNs</span>
                    </div>
                </div>
            </div>

            <!-- KPI Row 2: Sales & Quality Operations -->
            <div class="row g-3 mb-4">
                <div class="col-12 col-sm-6 col-xl-3">
                    <div class="card shadow-sm border-0 h-100 p-3" style="border-left: 4px solid #3b82f6 !important;">
                        <span class="text-muted small text-uppercase fw-semibold">New Leads Today</span>
                        <h3 class="fw-bold my-2 text-primary">{self.kpi_new_leads_today}</h3>
                        <span class="small text-muted">Incoming patient inquiries</span>
                    </div>
                </div>
                <div class="col-12 col-sm-6 col-xl-3">
                    <div class="card shadow-sm border-0 h-100 p-3" style="border-left: 4px solid #ef4444 !important;">
                        <span class="text-muted small text-uppercase fw-semibold">Overdue Sales Follow-ups</span>
                        <h3 class="fw-bold my-2 text-danger">{self.kpi_overdue_leads}</h3>
                        <span class="small text-muted">Leads needing call action</span>
                    </div>
                </div>
                <div class="col-12 col-sm-6 col-xl-3">
                    <div class="card shadow-sm border-0 h-100 p-3" style="border-left: 4px solid #eab308 !important;">
                        <span class="text-muted small text-uppercase fw-semibold">Doctor Schedule Conflicts</span>
                        <h3 class="fw-bold my-2 text-warning">{self.kpi_doctor_conflicts_count}</h3>
                        <span class="small text-muted">Detected or overridden</span>
                    </div>
                </div>
                <div class="col-12 col-sm-6 col-xl-3">
                    <div class="card shadow-sm border-0 h-100 p-3" style="border-left: 4px solid #10b981 !important;">
                        <span class="text-muted small text-uppercase fw-semibold">Completed Consultations</span>
                        <h3 class="fw-bold my-2 text-success">{len(today_apts.filtered(lambda a: a.status == 'completed'))}</h3>
                        <span class="small text-muted">Finished doctor visits</span>
                    </div>
                </div>
            </div>

            <!-- Doctor Workload Summary Table -->
            <div class="card border-0 shadow-sm mb-4">
                <div class="card-header bg-white py-3 border-bottom">
                    <h5 class="fw-bold mb-0">👨‍⚕️ Doctor Workload &amp; Consultations Today</h5>
                </div>
                <div class="table-responsive">
                    <table class="table table-hover align-middle mb-0">
                        <thead class="table-light">
                            <tr>
                                <th>Doctor</th>
                                <th class="text-center">Total Bookings</th>
                                <th class="text-center">Completed</th>
                                <th class="text-center">In Progress</th>
                                <th class="text-center">Waiting Room</th>
                                <th class="text-center">Cancelled / No-Show</th>
                            </tr>
                        </thead>
                        <tbody>
                            {doctor_table_html}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        """
        return html

    def action_view_all_today_appointments(self):
        self.ensure_one()
        return {
            'name': _("All Appointments Today (%s)") % self.dashboard_date,
            'type': 'ir.actions.act_window',
            'res_model': 'medical.appointment',
            'view_mode': 'list,calendar,form',
            'domain': [('appointment_date', '=', self.dashboard_date)],
            'context': {'default_appointment_date': self.dashboard_date},
        }

    def action_view_overdue_leads(self):
        self.ensure_one()
        return {
            'name': _("Overdue Sales Leads"),
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'view_mode': 'list,kanban,form',
            'domain': [('active', '=', True), ('probability', '<', 100), ('next_followup_date', '<', fields.Date.today())],
        }

    def action_view_doctor_conflicts(self):
        self.ensure_one()
        return {
            'name': _("Doctor Schedule Conflicts"),
            'type': 'ir.actions.act_window',
            'res_model': 'medical.appointment',
            'view_mode': 'list,form',
            'domain': [('appointment_date', '=', self.dashboard_date), '|', ('has_conflict', '=', True), ('conflict_override', '=', True)],
        }

    def action_view_today_invoices(self):
        self.ensure_one()
        return {
            'name': _("Today's Patient Invoices"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('invoice_date', '=', self.dashboard_date), ('move_type', '=', 'out_invoice')],
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
                'name': 'Manager Operations Dashboard',
                'company_id': self.env.company.id,
            })
        dashboard.action_refresh()
        return {
            'name': _('Manager Operations Dashboard'),
            'type': 'ir.actions.act_window',
            'res_model': 'medical.manager.dashboard',
            'res_id': dashboard.id,
            'view_mode': 'form',
            'target': 'current',
        }
