# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, timedelta
import io
import base64


class MedicalStaffPerformanceDashboard(models.TransientModel):
    _name = 'medical.staff.performance.dashboard'
    _description = 'Staff Performance Reports and Analytics Dashboard'

    # Filter Criteria
    date_range_preset = fields.Selection([
        ('current_month', 'Current Month'),
        ('last_month', 'Last Month'),
        ('current_year', 'This Year'),
        ('custom', 'Custom Date Range'),
    ], string='Date Range', default='current_month')

    start_date = fields.Date(
        string='Start Date',
        required=True,
        default=lambda self: date.today().replace(day=1)
    )
    end_date = fields.Date(
        string='End Date',
        required=True,
        default=fields.Date.context_today
    )

    @api.onchange('date_range_preset')
    def _onchange_date_range_preset(self):
        today = date.today()
        if self.date_range_preset == 'current_month':
            self.start_date = today.replace(day=1)
            self.end_date = today
        elif self.date_range_preset == 'last_month':
            first_this_month = today.replace(day=1)
            last_month_end = first_this_month - timedelta(days=1)
            self.start_date = last_month_end.replace(day=1)
            self.end_date = last_month_end
        elif self.date_range_preset == 'current_year':
            self.start_date = today.replace(month=1, day=1)
            self.end_date = today

    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee / Staff Member',
        domain="[('medical_employee_type', '!=', False)]",
        help='Select a specific staff member or leave empty for all employees'
    )
    department_id = fields.Many2one(
        'hr.department',
        string='Department / Team',
        help='Filter by department or clinical team'
    )
    role = fields.Selection([
        ('all', 'All Medical Roles'),
        ('doctor', 'Doctor'),
        ('sales', 'Sales Employee'),
        ('receptionist', 'Receptionist'),
        ('nurse', 'Nurse'),
    ], string='Role / Function', default='all')

    appointment_status = fields.Selection([
        ('all', 'All Appointment Statuses'),
        ('scheduled', 'Scheduled / Confirmed'),
        ('in_consultation', 'In Progress / Consultation'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No-Show'),
    ], string='Appointment Status', default='all')

    comparison_type = fields.Selection([
        ('previous_period', 'Previous Period (Same Duration)'),
        ('previous_year', 'Same Period Previous Year'),
        ('custom', 'Custom Comparison Range'),
    ], string='Comparison Period', default='previous_period', required=True)

    comparison_start_date = fields.Date(string='Comparison Start Date')
    comparison_end_date = fields.Date(string='Comparison End Date')

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )

    # Overall KPI Summary - Current Period
    total_revenue = fields.Float(string='Total Revenue', readonly=True)
    total_appointments = fields.Integer(string='Total Appointments', readonly=True)
    completed_appointments = fields.Integer(string='Completed Appointments', readonly=True)
    in_progress_appointments = fields.Integer(string='In-Progress Appointments', readonly=True)
    cancelled_appointments = fields.Integer(string='Cancelled Appointments', readonly=True)
    cancellation_rate = fields.Float(string='Cancellation Rate (%)', readonly=True)
    no_show_appointments = fields.Integer(string='No-Show Appointments', readonly=True)
    no_show_rate = fields.Float(string='No-Show Rate (%)', readonly=True)
    total_leads = fields.Integer(string='Total Leads', readonly=True)
    converted_leads = fields.Integer(string='Converted Leads', readonly=True)
    lead_conversion_rate = fields.Float(string='Lead Conversion Rate (%)', readonly=True)
    avg_revenue_per_completed = fields.Float(string='Avg Revenue / Completed', readonly=True)

    # Overall KPI Summary - Comparison Period
    prev_total_revenue = fields.Float(string='Previous Period Revenue', readonly=True)
    prev_total_appointments = fields.Integer(string='Previous Appointments', readonly=True)
    prev_completed_appointments = fields.Integer(string='Previous Completed Appointments', readonly=True)
    prev_cancelled_appointments = fields.Integer(string='Previous Cancelled Appointments', readonly=True)
    prev_cancellation_rate = fields.Float(string='Previous Cancellation Rate (%)', readonly=True)
    prev_no_show_appointments = fields.Integer(string='Previous No-Show Appointments', readonly=True)
    prev_no_show_rate = fields.Float(string='Previous No-Show Rate (%)', readonly=True)
    prev_total_leads = fields.Integer(string='Previous Total Leads', readonly=True)
    prev_converted_leads = fields.Integer(string='Previous Converted Leads', readonly=True)
    prev_lead_conversion_rate = fields.Float(string='Previous Conversion Rate (%)', readonly=True)
    prev_avg_revenue_per_completed = fields.Float(string='Previous Avg Revenue / Completed', readonly=True)

    # Overall Growth & Rate Differences
    revenue_growth = fields.Float(string='Revenue Growth (%)', readonly=True)
    revenue_growth_amount = fields.Float(string='Revenue Growth ($)', readonly=True)
    appointment_growth = fields.Float(string='Appointment Growth (%)', readonly=True)
    completed_growth = fields.Float(string='Completed Growth (%)', readonly=True)
    conversion_rate_change_pp = fields.Float(string='Conversion Rate Change (pp)', readonly=True)
    cancellation_rate_change_pp = fields.Float(string='Cancellation Rate Change (pp)', readonly=True)
    no_show_rate_change_pp = fields.Float(string='No-Show Rate Change (pp)', readonly=True)

    # Detailed Staff Performance Table Lines
    line_ids = fields.One2many(
        'medical.staff.performance.line',
        'dashboard_id',
        string='Employee Performance Breakdown'
    )

    # Visual Analytics & Charts HTML
    dashboard_html = fields.Html(
        string='Analytics & Charts',
        readonly=True,
        sanitize=False
    )

    # Excel Download Export helper
    export_file = fields.Binary(string='Export File', readonly=True)
    export_filename = fields.Char(string='Export Filename', readonly=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        # Calculate comparison dates for the default range
        s_date = res.get('start_date') or date.today().replace(day=1)
        e_date = res.get('end_date') or date.today()
        comp_type = res.get('comparison_type') or 'previous_period'
        comp_s, comp_e = self._calculate_comparison_dates_static(s_date, e_date, comp_type)
        res['comparison_start_date'] = comp_s
        res['comparison_end_date'] = comp_e

        user = self.env.user
        is_admin_or_mgr = (
            user._is_admin() or user._is_system() or
            user.has_group('medical_employee_management.group_medical_doctor_manager') or
            user.has_group('medical_employee_management.group_medical_sales_manager') or
            user.has_group('medical_employee_management.group_medical_nurse_manager') or
            user.has_group('medical_employee_management.group_medical_receptionist_manager') or
            user.has_group('medical_employee_management.group_medical_security_manager')
        )
        if not is_admin_or_mgr:
            emp = self.env['hr.employee'].search([
                ('user_id', '=', user.id),
                ('medical_employee_type', '!=', False)
            ], limit=1)
            if emp:
                res['employee_id'] = emp.id
                res['role'] = emp.medical_employee_type

        return res

    def action_view_charts(self):
        """Open appointments in interactive Graph / Pivot view filtered by the dashboard parameters"""
        self.ensure_one()
        apt_domain = [
            ('appointment_date', '>=', self.start_date),
            ('appointment_date', '<=', self.end_date),
        ]
        if self.employee_id:
            emp = self.employee_id
            if emp.medical_employee_type == 'doctor':
                apt_domain.append(('doctor_id', '=', emp.id))
            elif emp.medical_employee_type == 'sales':
                apt_domain.extend(['|', '|', ('sales_employee_id', '=', emp.id), ('salesperson_id', '=', emp.user_id.id if emp.user_id else 0), ('created_by_sales', '=', emp.user_id.id if emp.user_id else 0)])
            elif emp.medical_employee_type == 'nurse':
                apt_domain.extend(['|', ('nurse_id', '=', emp.id), ('vitals_recorded_by', '=', emp.user_id.id if emp.user_id else 0)])
            elif emp.medical_employee_type == 'receptionist':
                apt_domain.extend(['|', ('receptionist_id', '=', emp.id), ('checked_in_by', '=', emp.user_id.id if emp.user_id else 0)])
        if self.appointment_status and self.appointment_status != 'all':
            if self.appointment_status == 'scheduled':
                apt_domain.append(('status', 'in', ['tentative', 'confirmed']))
            elif self.appointment_status == 'in_consultation':
                apt_domain.append(('status', 'in', ['checked_in', 'ready_for_doctor', 'in_consultation']))
            else:
                apt_domain.append(('status', '=', self.appointment_status))

        return {
            'name': _('Appointments Analysis (%s to %s)') % (self.start_date, self.end_date),
            'type': 'ir.actions.act_window',
            'res_model': 'medical.appointment',
            'view_mode': 'graph,pivot,list,form',
            'domain': apt_domain,
            'context': {
                'search_default_group_by_doctor': 1,
            }
        }

    @staticmethod
    def _calculate_comparison_dates_static(start_d, end_d, comp_type):
        if not start_d or not end_d:
            return False, False
        duration_days = (end_d - start_d).days + 1
        if comp_type == 'previous_period':
            comp_e = start_d - timedelta(days=1)
            comp_s = comp_e - timedelta(days=duration_days - 1)
            return comp_s, comp_e
        elif comp_type == 'previous_year':
            try:
                comp_s = start_d.replace(year=start_d.year - 1)
            except ValueError:
                comp_s = start_d - timedelta(days=365)
            try:
                comp_e = end_d.replace(year=end_d.year - 1)
            except ValueError:
                comp_e = end_d - timedelta(days=365)
            return comp_s, comp_e
        return start_d, end_d

    def _update_comparison_dates(self):
        for rec in self:
            if rec.comparison_type != 'custom':
                comp_s, comp_e = self._calculate_comparison_dates_static(rec.start_date, rec.end_date, rec.comparison_type)
                rec.comparison_start_date = comp_s
                rec.comparison_end_date = comp_e

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if not rec.dashboard_html:
                rec._update_comparison_dates()
                rec._compute_all_metrics()
        return records

    def action_apply_filters(self):
        """Applies filters, computes KPIs, populates lines, and renders charts"""
        self.ensure_one()
        self._update_comparison_dates()
        self._compute_all_metrics()
        return True

    def action_reset_filters(self):
        """Resets filters to default current month and recomputes"""
        self.ensure_one()
        today = date.today()
        self.start_date = today.replace(day=1)
        self.end_date = today
        self.employee_id = False
        self.department_id = False
        self.role = 'all'
        self.appointment_status = 'all'
        self.comparison_type = 'previous_period'
        self._update_comparison_dates()
        self._compute_all_metrics()
        return True

    # ==========================================
    # CORE CALCULATION ENGINE
    # ==========================================
    def _compute_all_metrics(self):
        self.ensure_one()
        # 1. Clear old lines
        self.line_ids.unlink()

        # 2. Gather active employees matching scope
        emp_domain = [('medical_employee_type', '!=', False)]
        if self.employee_id:
            emp_domain.append(('id', '=', self.employee_id.id))
        if self.department_id:
            emp_domain.append(('department_id', '=', self.department_id.id))
        if self.role and self.role != 'all':
            emp_domain.append(('medical_employee_type', '=', self.role))

        user = self.env.user
        is_admin_or_mgr = (
            user._is_admin() or user._is_system() or
            user.has_group('medical_employee_management.group_medical_doctor_manager') or
            user.has_group('medical_employee_management.group_medical_sales_manager') or
            user.has_group('medical_employee_management.group_medical_nurse_manager') or
            user.has_group('medical_employee_management.group_medical_receptionist_manager') or
            user.has_group('medical_employee_management.group_medical_security_manager')
        )
        if not is_admin_or_mgr:
            user_emp = self.env['hr.employee'].search([
                ('user_id', '=', user.id),
                ('medical_employee_type', '!=', False)
            ], limit=1)
            if user_emp:
                emp_domain = [('id', '=', user_emp.id)]

        employees = self.env['hr.employee'].search(emp_domain, order='medical_employee_type, name')

        # 3. Calculate Overall Current Period Metrics
        curr_overall = self._calculate_period_stats(
            self.start_date, self.end_date, self.employee_id, self.department_id, self.role, self.appointment_status
        )
        # 4. Calculate Overall Comparison Period Metrics
        comp_s = self.comparison_start_date or (self.start_date - timedelta(days=30))
        comp_e = self.comparison_end_date or (self.start_date - timedelta(days=1))
        prev_overall = self._calculate_period_stats(
            comp_s, comp_e, self.employee_id, self.department_id, self.role, self.appointment_status
        )

        # Set Current Overall KPI fields
        self.total_revenue = curr_overall['revenue']
        self.total_appointments = curr_overall['total_appointments']
        self.completed_appointments = curr_overall['completed_appointments']
        self.in_progress_appointments = curr_overall['in_progress_appointments']
        self.cancelled_appointments = curr_overall['cancelled_appointments']
        self.cancellation_rate = curr_overall['cancellation_rate']
        self.no_show_appointments = curr_overall['no_show_appointments']
        self.no_show_rate = curr_overall['no_show_rate']
        self.total_leads = curr_overall['total_leads']
        self.converted_leads = curr_overall['converted_leads']
        self.lead_conversion_rate = curr_overall['conversion_rate']
        self.avg_revenue_per_completed = curr_overall['avg_revenue_per_completed']

        # Set Comparison Overall KPI fields
        self.prev_total_revenue = prev_overall['revenue']
        self.prev_total_appointments = prev_overall['total_appointments']
        self.prev_completed_appointments = prev_overall['completed_appointments']
        self.prev_cancelled_appointments = prev_overall['cancelled_appointments']
        self.prev_cancellation_rate = prev_overall['cancellation_rate']
        self.prev_no_show_appointments = prev_overall['no_show_appointments']
        self.prev_no_show_rate = prev_overall['no_show_rate']
        self.prev_total_leads = prev_overall['total_leads']
        self.prev_converted_leads = prev_overall['converted_leads']
        self.prev_lead_conversion_rate = prev_overall['conversion_rate']
        self.prev_avg_revenue_per_completed = prev_overall['avg_revenue_per_completed']

        # Calculate Overall Growth & Differences
        self.revenue_growth = self._calculate_growth_percent(curr_overall['revenue'], prev_overall['revenue'])
        self.revenue_growth_amount = curr_overall['revenue'] - prev_overall['revenue']
        self.appointment_growth = self._calculate_growth_percent(curr_overall['total_appointments'], prev_overall['total_appointments'])
        self.completed_growth = self._calculate_growth_percent(curr_overall['completed_appointments'], prev_overall['completed_appointments'])
        self.conversion_rate_change_pp = round(curr_overall['conversion_rate'] - prev_overall['conversion_rate'], 1)
        self.cancellation_rate_change_pp = round(curr_overall['cancellation_rate'] - prev_overall['cancellation_rate'], 1)
        self.no_show_rate_change_pp = round(curr_overall['no_show_rate'] - prev_overall['no_show_rate'], 1)

        # 5. Calculate Per-Employee Breakdown Lines
        lines_data = []
        for emp in employees:
            curr_emp_stats = self._calculate_employee_stats(
                emp, self.start_date, self.end_date, self.appointment_status
            )
            prev_emp_stats = self._calculate_employee_stats(
                emp, comp_s, comp_e, self.appointment_status
            )

            # Growth & Rate Changes
            rev_growth = self._calculate_growth_percent(curr_emp_stats['revenue'], prev_emp_stats['revenue'])
            apt_growth = self._calculate_growth_percent(curr_emp_stats['total_appointments'], prev_emp_stats['total_appointments'])
            conv_pp = round(curr_emp_stats['conversion_rate'] - prev_emp_stats['conversion_rate'], 1)
            canc_pp = round(curr_emp_stats['cancellation_rate'] - prev_emp_stats['cancellation_rate'], 1)
            noshow_pp = round(curr_emp_stats['no_show_rate'] - prev_emp_stats['no_show_rate'], 1)

            # Match Target for Employee
            target = self._find_target_for_employee(emp, self.start_date, self.end_date)
            rev_target = target.revenue_target if target else 0.0
            rev_prog = round((curr_emp_stats['revenue'] / rev_target * 100.0), 1) if rev_target > 0 else (100.0 if curr_emp_stats['revenue'] > 0 else 0.0)
            comp_target = target.completed_appointment_target if target else 0
            comp_prog = round((curr_emp_stats['completed_appointments'] / comp_target * 100.0), 1) if comp_target > 0 else (100.0 if curr_emp_stats['completed_appointments'] > 0 else 0.0)
            conv_target = target.lead_conversion_target if target else 0.0
            conv_prog = round((curr_emp_stats['conversion_rate'] / conv_target * 100.0), 1) if conv_target > 0 else (100.0 if curr_emp_stats['conversion_rate'] > 0 else 0.0)

            # Determine Performance Trend (Improving, Stable, Declining)
            trend, badge = self._determine_trend(
                rev_growth, apt_growth, conv_pp, canc_pp, noshow_pp,
                curr_emp_stats['total_appointments'], prev_emp_stats['total_appointments']
            )

            lines_data.append({
                'dashboard_id': self.id,
                'employee_id': emp.id,
                'department_id': emp.department_id.id if emp.department_id else False,
                'role': emp.medical_employee_type or 'other',
                'assigned_leads': curr_emp_stats['assigned_leads'],
                'converted_leads': curr_emp_stats['converted_leads'],
                'conversion_rate': curr_emp_stats['conversion_rate'],
                'total_appointments': curr_emp_stats['total_appointments'],
                'completed_appointments': curr_emp_stats['completed_appointments'],
                'in_progress_appointments': curr_emp_stats['in_progress_appointments'],
                'cancelled_appointments': curr_emp_stats['cancelled_appointments'],
                'cancellation_rate': curr_emp_stats['cancellation_rate'],
                'no_show_appointments': curr_emp_stats['no_show_appointments'],
                'no_show_rate': curr_emp_stats['no_show_rate'],
                'total_revenue': curr_emp_stats['revenue'],
                'avg_revenue_per_completed': curr_emp_stats['avg_revenue_per_completed'],
                'prev_revenue': prev_emp_stats['revenue'],
                'revenue_growth': rev_growth,
                'prev_total_appointments': prev_emp_stats['total_appointments'],
                'prev_completed_appointments': prev_emp_stats['completed_appointments'],
                'appointment_growth': apt_growth,
                'prev_conversion_rate': prev_emp_stats['conversion_rate'],
                'conversion_rate_change_pp': conv_pp,
                'prev_cancellation_rate': prev_emp_stats['cancellation_rate'],
                'cancellation_rate_change_pp': canc_pp,
                'prev_no_show_rate': prev_emp_stats['no_show_rate'],
                'no_show_rate_change_pp': noshow_pp,
                'target_id': target.id if target else False,
                'revenue_target': rev_target,
                'revenue_target_progress': rev_prog,
                'completed_target': comp_target,
                'completed_target_progress': comp_prog,
                'conversion_target': conv_target,
                'conversion_target_progress': conv_prog,
                'performance_trend': trend,
                'trend_badge': badge,
            })

        if lines_data:
            self.env['medical.staff.performance.line'].create(lines_data)

        # 6. Render Visual Dashboard HTML with KPI cards and SVG Charts
        self.dashboard_html = self._build_dashboard_html(curr_overall, prev_overall, lines_data)

    def _find_target_for_employee(self, employee, start_d, end_d):
        Target = self.env['medical.staff.target']
        # 1. Exact employee target overlapping date range
        t = Target.search([
            ('target_type', '=', 'employee'),
            ('employee_id', '=', employee.id),
            ('date_start', '<=', end_d),
            ('date_end', '>=', start_d),
        ], limit=1)
        if t:
            return t
        # 2. Department target
        if employee.department_id:
            t = Target.search([
                ('target_type', '=', 'department'),
                ('department_id', '=', employee.department_id.id),
                ('date_start', '<=', end_d),
                ('date_end', '>=', start_d),
            ], limit=1)
            if t:
                return t
        # 3. Role target
        if employee.medical_employee_type:
            t = Target.search([
                ('target_type', '=', 'role'),
                ('role', '=', employee.medical_employee_type),
                ('date_start', '<=', end_d),
                ('date_end', '>=', start_d),
            ], limit=1)
            if t:
                return t
        return False

    @staticmethod
    def _calculate_growth_percent(curr, prev):
        """Calculates growth percentage with zero-handling"""
        if prev > 0:
            return round(((curr - prev) / prev) * 100.0, 1)
        elif prev == 0 and curr > 0:
            return 100.0
        return 0.0

    @staticmethod
    def _determine_trend(rev_growth, apt_growth, conv_pp, canc_pp, noshow_pp, curr_tot, prev_tot):
        """
        Determines Improving, Stable, or Declining trend.
        Note: Negative cancellation and no-show rate changes represent positive improvements!
        """
        if curr_tot == 0 and prev_tot == 0:
            return 'stable', '➡️ Stable'

        score = 0
        # Revenue Growth impact
        if rev_growth >= 3.0:
            score += 1
        elif rev_growth <= -3.0:
            score -= 1

        # Appointment Growth impact
        if apt_growth >= 3.0:
            score += 1
        elif apt_growth <= -3.0:
            score -= 1

        # Conversion rate change (pp)
        if conv_pp >= 1.0:
            score += 1
        elif conv_pp <= -1.0:
            score -= 1

        # Cancellation rate reduction (negative pp is good!)
        if canc_pp <= -1.0:
            score += 1
        elif canc_pp >= 1.0:
            score -= 1

        # No-show rate reduction (negative pp is good!)
        if noshow_pp <= -1.0:
            score += 1
        elif noshow_pp >= 1.0:
            score -= 1

        if score >= 1:
            return 'improving', '📈 Improving'
        elif score <= -1:
            return 'declining', '📉 Declining'
        return 'stable', '➡️ Stable'

    def _calculate_period_stats(self, start_d, end_d, emp, dept, role, status_filter):
        """Calculates distinct overall KPI statistics for the medical center without double-counting"""
        Appointment = self.env['medical.appointment']
        Lead = self.env['crm.lead']

        # Appointment Domain
        apt_domain = [
            ('appointment_date', '>=', start_d),
            ('appointment_date', '<=', end_d),
        ]
        if status_filter and status_filter != 'all':
            if status_filter == 'scheduled':
                apt_domain.append(('status', 'in', ['tentative', 'confirmed']))
            elif status_filter == 'in_consultation':
                apt_domain.append(('status', 'in', ['checked_in', 'ready_for_doctor', 'in_consultation']))
            else:
                apt_domain.append(('status', '=', status_filter))

        if emp:
            user_id = emp.user_id.id if emp.user_id else 0
            apt_domain.extend(['|', '|', '|', ('doctor_id', '=', emp.id), ('sales_employee_id', '=', emp.id), ('nurse_id', '=', emp.id), ('receptionist_id', '=', emp.id)])
        elif dept:
            apt_domain.extend(['|', '|', '|', ('doctor_id.department_id', '=', dept.id), ('sales_employee_id.department_id', '=', dept.id), ('nurse_id.department_id', '=', dept.id), ('receptionist_id.department_id', '=', dept.id)])
        elif role and role != 'all':
            if role == 'doctor':
                apt_domain.append(('doctor_id', '!=', False))
            elif role == 'sales':
                apt_domain.append(('sales_employee_id', '!=', False))
            elif role == 'nurse':
                apt_domain.extend(['|', ('nurse_id', '!=', False), ('vitals_recorded_by', '!=', False)])
            elif role == 'receptionist':
                apt_domain.extend(['|', ('receptionist_id', '!=', False), ('checked_in_by', '!=', False)])

        appointments = Appointment.search(apt_domain)

        total_appointments = len(appointments)
        completed_appointments = len(appointments.filtered(lambda a: a.status == 'completed'))
        in_progress_appointments = len(appointments.filtered(lambda a: a.status in ['checked_in', 'ready_for_doctor', 'in_consultation']))
        cancelled_appointments = len(appointments.filtered(lambda a: a.status == 'cancelled'))
        no_show_appointments = len(appointments.filtered(lambda a: a.status == 'no_show'))

        # Revenue calculation: Confirmed revenue from appointments
        revenue = 0.0
        for apt in appointments:
            if apt.status in ['cancelled', 'no_show']:
                continue
            if apt.invoice_id and apt.invoice_id.state == 'posted':
                revenue += apt.invoice_id.amount_total
            elif apt.status == 'completed':
                revenue += apt.appointment_total or 0.0

        cancellation_rate = round((cancelled_appointments / total_appointments * 100.0), 1) if total_appointments > 0 else 0.0
        no_show_rate = round((no_show_appointments / total_appointments * 100.0), 1) if total_appointments > 0 else 0.0
        avg_rev = round((revenue / completed_appointments), 2) if completed_appointments > 0 else 0.0

        # Leads Domain
        lead_domain = [
            ('create_date', '>=', datetime.combine(start_d, datetime.min.time())),
            ('create_date', '<=', datetime.combine(end_d, datetime.max.time())),
        ]
        if emp:
            lead_domain.extend(['|', ('medical_staff_id', '=', emp.id), ('user_id', '=', emp.user_id.id if emp.user_id else 0)])
        leads = Lead.search(lead_domain)
        total_leads = len(leads)
        converted_leads = len(leads.filtered(lambda l: l.appointment_count > 0 or (l.partner_id and l.partner_id.is_patient) or (hasattr(l, 'probability') and l.probability == 100)))
        conv_rate = round((converted_leads / total_leads * 100.0), 1) if total_leads > 0 else 0.0

        return {
            'revenue': round(revenue, 2),
            'total_appointments': total_appointments,
            'completed_appointments': completed_appointments,
            'in_progress_appointments': in_progress_appointments,
            'cancelled_appointments': cancelled_appointments,
            'cancellation_rate': cancellation_rate,
            'no_show_appointments': no_show_appointments,
            'no_show_rate': no_show_rate,
            'total_leads': total_leads,
            'converted_leads': converted_leads,
            'conversion_rate': conv_rate,
            'avg_revenue_per_completed': avg_rev,
        }

    def _calculate_employee_stats(self, emp, start_d, end_d, status_filter):
        """Calculates specific performance metrics attributed to a single employee according to their role"""
        Appointment = self.env['medical.appointment']
        Lead = self.env['crm.lead']

        # Attribution criteria based on employee role
        role = emp.medical_employee_type or 'other'
        apt_domain = [
            ('appointment_date', '>=', start_d),
            ('appointment_date', '<=', end_d),
        ]
        if status_filter and status_filter != 'all':
            if status_filter == 'scheduled':
                apt_domain.append(('status', 'in', ['tentative', 'confirmed']))
            elif status_filter == 'in_consultation':
                apt_domain.append(('status', 'in', ['checked_in', 'ready_for_doctor', 'in_consultation']))
            else:
                apt_domain.append(('status', '=', status_filter))

        if role == 'doctor':
            user_id = emp.user_id.id if emp.user_id else 0
            apt_domain.extend(['|', ('doctor_id', '=', emp.id), ('doctor_user_id', '=', user_id)])
        elif role == 'sales':
            user_id = emp.user_id.id if emp.user_id else 0
            apt_domain.extend(['|', '|', ('sales_employee_id', '=', emp.id), ('salesperson_id', '=', user_id), ('created_by_sales', '=', user_id)])
        elif role == 'receptionist':
            user_id = emp.user_id.id if emp.user_id else 0
            apt_domain.extend(['|', ('receptionist_id', '=', emp.id), ('checked_in_by', '=', user_id)])
        elif role == 'nurse':
            user_id = emp.user_id.id if emp.user_id else 0
            apt_domain.extend(['|', ('nurse_id', '=', emp.id), ('vitals_recorded_by', '=', user_id)])
        else:
            apt_domain.extend(['|', ('doctor_id', '=', emp.id), ('sales_employee_id', '=', emp.id)])

        appointments = Appointment.search(apt_domain)
        tot_apt = len(appointments)
        comp_apt = len(appointments.filtered(lambda a: a.status == 'completed'))
        in_prog_apt = len(appointments.filtered(lambda a: a.status in ['checked_in', 'ready_for_doctor', 'in_consultation']))
        canc_apt = len(appointments.filtered(lambda a: a.status == 'cancelled'))
        noshow_apt = len(appointments.filtered(lambda a: a.status == 'no_show'))

        # Revenue attributed to employee
        revenue = 0.0
        for apt in appointments:
            if apt.status in ['cancelled', 'no_show']:
                continue
            if apt.invoice_id and apt.invoice_id.state == 'posted':
                revenue += apt.invoice_id.amount_total
            elif apt.status == 'completed':
                revenue += apt.appointment_total or 0.0

        canc_rate = round((canc_apt / tot_apt * 100.0), 1) if tot_apt > 0 else 0.0
        noshow_rate = round((noshow_apt / tot_apt * 100.0), 1) if tot_apt > 0 else 0.0
        avg_rev = round((revenue / comp_apt), 2) if comp_apt > 0 else 0.0

        # Leads attributed
        lead_domain = [
            ('create_date', '>=', datetime.combine(start_d, datetime.min.time())),
            ('create_date', '<=', datetime.combine(end_d, datetime.max.time())),
        ]
        emp_user_id = emp.user_id.id if emp.user_id else 0
        lead_domain.extend(['|', ('medical_staff_id', '=', emp.id), ('user_id', '=', emp_user_id)])
        leads = Lead.search(lead_domain)
        tot_leads = len(leads)
        conv_leads = len(leads.filtered(lambda l: l.appointment_count > 0 or (l.partner_id and l.partner_id.is_patient) or (hasattr(l, 'probability') and l.probability == 100)))
        conv_rate = round((conv_leads / tot_leads * 100.0), 1) if tot_leads > 0 else 0.0

        return {
            'revenue': round(revenue, 2),
            'total_appointments': tot_apt,
            'completed_appointments': comp_apt,
            'in_progress_appointments': in_prog_apt,
            'cancelled_appointments': canc_apt,
            'cancellation_rate': canc_rate,
            'no_show_appointments': noshow_apt,
            'no_show_rate': noshow_rate,
            'assigned_leads': tot_leads,
            'converted_leads': conv_leads,
            'conversion_rate': conv_rate,
            'avg_revenue_per_completed': avg_rev,
        }

    # ==========================================
    # DASHBOARD HTML & SVG VISUALS GENERATOR
    # ==========================================
    def _build_dashboard_html(self, curr, prev, lines_data):
        """Constructs modern, responsive HTML with SVG visual analytics charts"""
        currency_symbol = self.company_id.currency_id.symbol or '$'

        # Revenue pill badge
        rev_growth_val = self.revenue_growth
        rev_badge_cls = 'badge-success' if rev_growth_val >= 0 else 'badge-danger'
        rev_badge_arrow = '▲' if rev_growth_val >= 0 else '▼'

        # Appt pill badge
        apt_growth_val = self.appointment_growth
        apt_badge_cls = 'badge-success' if apt_growth_val >= 0 else 'badge-danger'
        apt_badge_arrow = '▲' if apt_growth_val >= 0 else '▼'

        # Cancellation rate change pill (negative is good!)
        canc_pp = self.cancellation_rate_change_pp
        canc_badge_cls = 'badge-success' if canc_pp <= 0 else 'badge-danger'
        canc_badge_text = f"{'▼' if canc_pp <= 0 else '▲'} {abs(canc_pp)} pp"

        # No show rate change pill (negative is good!)
        noshow_pp = self.no_show_rate_change_pp
        noshow_badge_cls = 'badge-success' if noshow_pp <= 0 else 'badge-danger'
        noshow_badge_text = f"{'▼' if noshow_pp <= 0 else '▲'} {abs(noshow_pp)} pp"

        # Conversion rate pill
        conv_pp = self.conversion_rate_change_pp
        conv_badge_cls = 'badge-success' if conv_pp >= 0 else 'badge-danger'
        conv_badge_text = f"{'▲' if conv_pp >= 0 else '▼'} {abs(conv_pp)} pp"

        # 1. Appointment Status Breakdown Bars / Donut
        tot_apt = curr['total_appointments'] or 1
        comp_pct = round((curr['completed_appointments'] / tot_apt) * 100, 1)
        inprog_pct = round((curr['in_progress_appointments'] / tot_apt) * 100, 1)
        canc_pct = round((curr['cancelled_appointments'] / tot_apt) * 100, 1)
        noshow_pct = round((curr['no_show_appointments'] / tot_apt) * 100, 1)
        sched_count = max(0, curr['total_appointments'] - curr['completed_appointments'] - curr['in_progress_appointments'] - curr['cancelled_appointments'] - curr['no_show_appointments'])
        sched_pct = round((sched_count / tot_apt) * 100, 1)

        # 2. Employee Revenue Bars
        sorted_by_rev = sorted(lines_data, key=lambda x: x['total_revenue'], reverse=True)[:6]
        max_rev = max([x['total_revenue'] for x in sorted_by_rev] or [1.0])
        if max_rev == 0:
            max_rev = 1.0

        emp_rev_bars_html = ""
        for item in sorted_by_rev:
            bar_pct = min(100.0, round((item['total_revenue'] / max_rev) * 100.0, 1))
            emp_name = self.env['hr.employee'].browse(item['employee_id']).name or 'Staff'
            emp_rev_bars_html += f"""
            <div style="margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; font-size: 13px; font-weight: 600; margin-bottom: 4px;">
                    <span>{emp_name} <small style="color: #6c757d; font-weight: 400;">({item['role'].capitalize()})</small></span>
                    <span>{currency_symbol}{item['total_revenue']:,.2f}</span>
                </div>
                <div style="background: #e9ecef; border-radius: 6px; height: 12px; overflow: hidden; display: flex;">
                    <div style="width: {bar_pct}%; background: linear-gradient(90deg, #0d6efd, #0dcaf0); border-radius: 6px;"></div>
                </div>
            </div>
            """

        if not emp_rev_bars_html:
            emp_rev_bars_html = "<div style='color: #6c757d; padding: 20px; text-align: center;'>No staff revenue data recorded for this period.</div>"

        # 3. Employee Improvement / Growth Cards
        top_improvers = sorted(lines_data, key=lambda x: x['revenue_growth'], reverse=True)[:4]
        improvers_html = ""
        for imp in top_improvers:
            emp_name = self.env['hr.employee'].browse(imp['employee_id']).name or 'Staff'
            trend_color = '#198754' if imp['performance_trend'] == 'improving' else ('#0d6efd' if imp['performance_trend'] == 'stable' else '#dc3545')
            improvers_html += f"""
            <div style="background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong style="font-size: 13px;">{emp_name}</strong>
                    <span style="font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 12px; color: #fff; background-color: {trend_color};">
                        {imp['trend_badge']}
                    </span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-top: 6px; font-size: 12px; color: #4b5563;">
                    <span>Revenue: {currency_symbol}{imp['total_revenue']:,.2f} ({imp['revenue_growth']:+.1f}%)</span>
                    <span>Completed: {imp['completed_appointments']} ({imp['appointment_growth']:+.1f}%)</span>
                </div>
            </div>
            """

        if not improvers_html:
            improvers_html = "<div style='color: #6c757d; padding: 20px; text-align: center;'>No staff trend data available.</div>"

        # Assemble full HTML
        html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #212529; padding: 10px 0;">
            <!-- KPI CARDS GRID -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 14px; margin-bottom: 20px;">
                <!-- Card 1: Total Revenue -->
                <div style="background: #ffffff; border-radius: 10px; padding: 16px; border: 1px solid #e2e8f0; box-shadow: 0 2px 4px rgba(0,0,0,0.03);">
                    <div style="font-size: 12px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">Total Revenue</div>
                    <div style="font-size: 24px; font-weight: 700; color: #0f172a; margin: 4px 0;">{currency_symbol}{curr['revenue']:,.2f}</div>
                    <div style="font-size: 12px; display: flex; align-items: center; gap: 6px;">
                        <span style="color: {'#16a34a' if rev_growth_val >= 0 else '#dc2626'}; font-weight: 600;">{rev_badge_arrow} {abs(rev_growth_val):.1f}%</span>
                        <span style="color: #94a3b8;">vs prev ({currency_symbol}{prev['revenue']:,.2f})</span>
                    </div>
                </div>

                <!-- Card 2: Total Appointments -->
                <div style="background: #ffffff; border-radius: 10px; padding: 16px; border: 1px solid #e2e8f0; box-shadow: 0 2px 4px rgba(0,0,0,0.03);">
                    <div style="font-size: 12px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">Total Appointments</div>
                    <div style="font-size: 24px; font-weight: 700; color: #0f172a; margin: 4px 0;">{curr['total_appointments']}</div>
                    <div style="font-size: 12px; display: flex; align-items: center; gap: 6px;">
                        <span style="color: {'#16a34a' if apt_growth_val >= 0 else '#dc2626'}; font-weight: 600;">{apt_badge_arrow} {abs(apt_growth_val):.1f}%</span>
                        <span style="color: #94a3b8;">vs prev ({prev['total_appointments']})</span>
                    </div>
                </div>

                <!-- Card 3: Completed Appointments -->
                <div style="background: #ffffff; border-radius: 10px; padding: 16px; border: 1px solid #e2e8f0; box-shadow: 0 2px 4px rgba(0,0,0,0.03);">
                    <div style="font-size: 12px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">Completed Sessions</div>
                    <div style="font-size: 24px; font-weight: 700; color: #16a34a; margin: 4px 0;">{curr['completed_appointments']}</div>
                    <div style="font-size: 12px; color: #64748b;">
                        Avg {currency_symbol}{curr['avg_revenue_per_completed']:,.2f} / completed
                    </div>
                </div>

                <!-- Card 4: Cancellation Rate -->
                <div style="background: #ffffff; border-radius: 10px; padding: 16px; border: 1px solid #e2e8f0; box-shadow: 0 2px 4px rgba(0,0,0,0.03);">
                    <div style="font-size: 12px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">Cancellation Rate</div>
                    <div style="font-size: 24px; font-weight: 700; color: #e11d48; margin: 4px 0;">{curr['cancellation_rate']}%</div>
                    <div style="font-size: 12px; display: flex; align-items: center; gap: 6px;">
                        <span style="color: {'#16a34a' if canc_pp <= 0 else '#dc2626'}; font-weight: 600;">{canc_badge_text}</span>
                        <span style="color: #94a3b8;">({curr['cancelled_appointments']} cancelled)</span>
                    </div>
                </div>

                <!-- Card 5: No-Show Rate -->
                <div style="background: #ffffff; border-radius: 10px; padding: 16px; border: 1px solid #e2e8f0; box-shadow: 0 2px 4px rgba(0,0,0,0.03);">
                    <div style="font-size: 12px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">No-Show Rate</div>
                    <div style="font-size: 24px; font-weight: 700; color: #f59e0b; margin: 4px 0;">{curr['no_show_rate']}%</div>
                    <div style="font-size: 12px; display: flex; align-items: center; gap: 6px;">
                        <span style="color: {'#16a34a' if noshow_pp <= 0 else '#dc2626'}; font-weight: 600;">{noshow_badge_text}</span>
                        <span style="color: #94a3b8;">({curr['no_show_appointments']} no-show)</span>
                    </div>
                </div>

                <!-- Card 6: Lead Conversion Rate -->
                <div style="background: #ffffff; border-radius: 10px; padding: 16px; border: 1px solid #e2e8f0; box-shadow: 0 2px 4px rgba(0,0,0,0.03);">
                    <div style="font-size: 12px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">Lead Conversion</div>
                    <div style="font-size: 24px; font-weight: 700; color: #0284c7; margin: 4px 0;">{curr['conversion_rate']}%</div>
                    <div style="font-size: 12px; display: flex; align-items: center; gap: 6px;">
                        <span style="color: {'#16a34a' if conv_pp >= 0 else '#dc2626'}; font-weight: 600;">{conv_badge_text}</span>
                        <span style="color: #94a3b8;">({curr['converted_leads']}/{curr['total_leads']} leads)</span>
                    </div>
                </div>
            </div>

            <!-- VISUAL CHARTS SECTION -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 16px; margin-bottom: 24px;">
                <!-- Chart A: Appointment Status Distribution -->
                <div style="background: #ffffff; border-radius: 10px; padding: 18px; border: 1px solid #e2e8f0; box-shadow: 0 2px 4px rgba(0,0,0,0.03);">
                    <h5 style="margin: 0 0 14px 0; font-size: 14px; font-weight: 700; color: #1e293b;">Appointment Status Breakdown</h5>
                    
                    <!-- Progress Bar Multi-Segment -->
                    <div style="height: 20px; border-radius: 10px; overflow: hidden; display: flex; background: #f1f5f9; margin-bottom: 14px;">
                        <div style="width: {comp_pct}%; background: #10b981;" title="Completed: {curr['completed_appointments']}"></div>
                        <div style="width: {inprog_pct}%; background: #06b6d4;" title="In Progress: {curr['in_progress_appointments']}"></div>
                        <div style="width: {sched_pct}%; background: #3b82f6;" title="Scheduled: {sched_count}"></div>
                        <div style="width: {canc_pct}%; background: #ef4444;" title="Cancelled: {curr['cancelled_appointments']}"></div>
                        <div style="width: {noshow_pct}%; background: #f59e0b;" title="No-Show: {curr['no_show_appointments']}"></div>
                    </div>

                    <!-- Legend -->
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 12px;">
                        <div style="display: flex; align-items: center; gap: 6px;">
                            <span style="width: 10px; height: 10px; border-radius: 50%; background: #10b981; display: inline-block;"></span>
                            <span>Completed: <strong>{curr['completed_appointments']}</strong> ({comp_pct}%)</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 6px;">
                            <span style="width: 10px; height: 10px; border-radius: 50%; background: #06b6d4; display: inline-block;"></span>
                            <span>In Progress: <strong>{curr['in_progress_appointments']}</strong> ({inprog_pct}%)</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 6px;">
                            <span style="width: 10px; height: 10px; border-radius: 50%; background: #3b82f6; display: inline-block;"></span>
                            <span>Scheduled: <strong>{sched_count}</strong> ({sched_pct}%)</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 6px;">
                            <span style="width: 10px; height: 10px; border-radius: 50%; background: #ef4444; display: inline-block;"></span>
                            <span>Cancelled: <strong>{curr['cancelled_appointments']}</strong> ({canc_pct}%)</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 6px;">
                            <span style="width: 10px; height: 10px; border-radius: 50%; background: #f59e0b; display: inline-block;"></span>
                            <span>No-Show: <strong>{curr['no_show_appointments']}</strong> ({noshow_pct}%)</span>
                        </div>
                    </div>
                </div>

                <!-- Chart B: Employee Revenue Comparison -->
                <div style="background: #ffffff; border-radius: 10px; padding: 18px; border: 1px solid #e2e8f0; box-shadow: 0 2px 4px rgba(0,0,0,0.03);">
                    <h5 style="margin: 0 0 14px 0; font-size: 14px; font-weight: 700; color: #1e293b;">Top Staff by Confirmed Revenue</h5>
                    {emp_rev_bars_html}
                </div>

                <!-- Chart C: Employee Improvement & Trajectory -->
                <div style="background: #ffffff; border-radius: 10px; padding: 18px; border: 1px solid #e2e8f0; box-shadow: 0 2px 4px rgba(0,0,0,0.03);">
                    <h5 style="margin: 0 0 14px 0; font-size: 14px; font-weight: 700; color: #1e293b;">Staff Performance Trends</h5>
                    {improvers_html}
                </div>
            </div>
        </div>
        """
        return html

    # ==========================================
    # EXCEL EXPORT GENERATION
    # ==========================================
    def action_export_excel(self):
        """Generates a multi-sheet formatted Excel workbook using xlsxwriter"""
        self.ensure_one()
        output = io.BytesIO()
        import xlsxwriter

        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        # Formats
        title_fmt = workbook.add_format({'bold': True, 'font_size': 14, 'color': '#1e293b'})
        sub_fmt = workbook.add_format({'italic': True, 'font_size': 10, 'color': '#64748b'})
        header_fmt = workbook.add_format({
            'bold': True, 'bg_color': '#0d6efd', 'color': '#ffffff',
            'border': 1, 'align': 'center', 'valign': 'vcenter'
        })
        kpi_label_fmt = workbook.add_format({'bold': True, 'bg_color': '#f8f9fa', 'border': 1})
        num_fmt = workbook.add_format({'border': 1, 'align': 'right', 'num_format': '#,##0'})
        curr_fmt = workbook.add_format({'border': 1, 'align': 'right', 'num_format': '$#,##0.00'})
        pct_fmt = workbook.add_format({'border': 1, 'align': 'right', 'num_format': '0.0%'})
        text_fmt = workbook.add_format({'border': 1, 'align': 'left'})

        # SHEET 1: Overall Summary
        ws_sum = workbook.add_worksheet('Executive KPI Summary')
        ws_sum.write(0, 0, 'Medical Center - Staff Performance & Analytics Report', title_fmt)
        ws_sum.write(1, 0, f'Reporting Period: {self.start_date} to {self.end_date} | Comparison: {self.comparison_start_date} to {self.comparison_end_date}', sub_fmt)

        headers_sum = ['Metric', 'Current Period', 'Comparison Period', 'Growth / Difference']
        for col_idx, h in enumerate(headers_sum):
            ws_sum.write(3, col_idx, h, header_fmt)

        kpis = [
            ('Total Confirmed Revenue', self.total_revenue, self.prev_total_revenue, f"{self.revenue_growth:+.1f}%"),
            ('Total Appointments', self.total_appointments, self.prev_total_appointments, f"{self.appointment_growth:+.1f}%"),
            ('Completed Appointments', self.completed_appointments, self.prev_completed_appointments, f"{self.completed_growth:+.1f}%"),
            ('In-Progress Appointments', self.in_progress_appointments, '-', '-'),
            ('Cancelled Appointments', self.cancelled_appointments, self.prev_cancelled_appointments, '-'),
            ('Cancellation Rate (%)', self.cancellation_rate / 100.0, self.prev_cancellation_rate / 100.0, f"{self.cancellation_rate_change_pp:+.1f} pp"),
            ('No-Show Appointments', self.no_show_appointments, self.prev_no_show_appointments, '-'),
            ('No-Show Rate (%)', self.no_show_rate / 100.0, self.prev_no_show_rate / 100.0, f"{self.no_show_rate_change_pp:+.1f} pp"),
            ('Total Assigned Leads', self.total_leads, self.prev_total_leads, '-'),
            ('Converted Leads', self.converted_leads, self.prev_converted_leads, '-'),
            ('Lead Conversion Rate (%)', self.lead_conversion_rate / 100.0, self.prev_lead_conversion_rate / 100.0, f"{self.conversion_rate_change_pp:+.1f} pp"),
            ('Avg Revenue / Completed Session', self.avg_revenue_per_completed, self.prev_avg_revenue_per_completed, '-'),
        ]

        row = 4
        for label, curr_v, prev_v, diff_v in kpis:
            ws_sum.write(row, 0, label, kpi_label_fmt)
            if isinstance(curr_v, float) and 'Revenue' in label:
                ws_sum.write(row, 1, curr_v, curr_fmt)
                ws_sum.write(row, 2, prev_v if isinstance(prev_v, (int, float)) else 0.0, curr_fmt)
            elif isinstance(curr_v, float) and 'Rate' in label:
                ws_sum.write(row, 1, curr_v, pct_fmt)
                ws_sum.write(row, 2, prev_v if isinstance(prev_v, (int, float)) else 0.0, pct_fmt)
            else:
                ws_sum.write(row, 1, curr_v, num_fmt)
                ws_sum.write(row, 2, prev_v, num_fmt)
            ws_sum.write(row, 3, diff_v, text_fmt)
            row += 1

        ws_sum.set_column(0, 0, 35)
        ws_sum.set_column(1, 3, 22)

        # SHEET 2: Employee Performance Table
        ws_emp = workbook.add_worksheet('Employee Performance')
        emp_headers = [
            'Staff Name', 'Department', 'Role', 'Assigned Leads', 'Converted Leads',
            'Conversion Rate', 'Total Appts', 'Completed', 'Cancellation Rate', 'No-Show Rate',
            'Revenue', 'Avg Rev / Session', 'Revenue Growth', 'Appt Growth', 'Target Revenue',
            'Target Progress', 'Performance Trend'
        ]
        for col_idx, h in enumerate(emp_headers):
            ws_emp.write(0, col_idx, h, header_fmt)

        row = 1
        for line in self.line_ids:
            ws_emp.write(row, 0, line.employee_id.name or '', text_fmt)
            ws_emp.write(row, 1, line.department_id.name or '', text_fmt)
            ws_emp.write(row, 2, line.role.capitalize() if line.role else '', text_fmt)
            ws_emp.write(row, 3, line.assigned_leads, num_fmt)
            ws_emp.write(row, 4, line.converted_leads, num_fmt)
            ws_emp.write(row, 5, line.conversion_rate / 100.0, pct_fmt)
            ws_emp.write(row, 6, line.total_appointments, num_fmt)
            ws_emp.write(row, 7, line.completed_appointments, num_fmt)
            ws_emp.write(row, 8, line.cancellation_rate / 100.0, pct_fmt)
            ws_emp.write(row, 9, line.no_show_rate / 100.0, pct_fmt)
            ws_emp.write(row, 10, line.total_revenue, curr_fmt)
            ws_emp.write(row, 11, line.avg_revenue_per_completed, curr_fmt)
            ws_emp.write(row, 12, f"{line.revenue_growth:+.1f}%", text_fmt)
            ws_emp.write(row, 13, f"{line.appointment_growth:+.1f}%", text_fmt)
            ws_emp.write(row, 14, line.revenue_target, curr_fmt)
            ws_emp.write(row, 15, f"{line.revenue_target_progress:.1f}%", text_fmt)
            ws_emp.write(row, 16, line.trend_badge or '', text_fmt)
            row += 1

        ws_emp.set_column(0, 0, 24)
        ws_emp.set_column(1, 2, 18)
        ws_emp.set_column(3, 16, 16)

        # SHEET 3: Detailed Appointments List
        ws_apt = workbook.add_worksheet('Appointments Detail')
        apt_headers = [
            'Appointment Ref', 'Date', 'Time', 'Patient Name', 'Doctor',
            'Triage Nurse', 'Sales Rep', 'Receptionist', 'Medical Service',
            'Status', 'Total Fee ($)', 'Commission ($)'
        ]
        for col_idx, h in enumerate(apt_headers):
            ws_apt.write(0, col_idx, h, header_fmt)

        apt_domain = [
            ('appointment_date', '>=', self.start_date),
            ('appointment_date', '<=', self.end_date),
        ]
        if self.employee_id:
            emp = self.employee_id
            if emp.medical_employee_type == 'doctor':
                apt_domain.append(('doctor_id', '=', emp.id))
            elif emp.medical_employee_type == 'sales':
                apt_domain.extend(['|', '|', ('sales_employee_id', '=', emp.id), ('salesperson_id', '=', emp.user_id.id if emp.user_id else 0), ('created_by_sales', '=', emp.user_id.id if emp.user_id else 0)])
            elif emp.medical_employee_type == 'nurse':
                apt_domain.extend(['|', ('nurse_id', '=', emp.id), ('vitals_recorded_by', '=', emp.user_id.id if emp.user_id else 0)])
            elif emp.medical_employee_type == 'receptionist':
                apt_domain.extend(['|', ('receptionist_id', '=', emp.id), ('checked_in_by', '=', emp.user_id.id if emp.user_id else 0)])

        apts = self.env['medical.appointment'].search(apt_domain, order='appointment_date desc, id desc')
        row = 1
        for a in apts:
            ws_apt.write(row, 0, a.name or '', text_fmt)
            ws_apt.write(row, 1, str(a.appointment_date or ''), text_fmt)
            ws_apt.write(row, 2, f"{int(a.appointment_time):02d}:{int((a.appointment_time % 1) * 60):02d}" if a.appointment_time else '', text_fmt)
            ws_apt.write(row, 3, a.patient_id.name or '', text_fmt)
            ws_apt.write(row, 4, a.doctor_id.name or '', text_fmt)
            ws_apt.write(row, 5, a.nurse_id.name or (a.vitals_recorded_by.name if a.vitals_recorded_by else ''), text_fmt)
            ws_apt.write(row, 6, a.sales_employee_id.name or (a.salesperson_id.name if a.salesperson_id else ''), text_fmt)
            ws_apt.write(row, 7, a.receptionist_id.name or (a.checked_in_by.name if a.checked_in_by else ''), text_fmt)
            ws_apt.write(row, 8, a.service_id.name or a.medical_service or '', text_fmt)
            ws_apt.write(row, 9, dict(a._fields['status'].selection).get(a.status, a.status), text_fmt)
            ws_apt.write(row, 10, a.appointment_total or 0.0, curr_fmt)
            ws_apt.write(row, 11, a.commission_amount or 0.0, curr_fmt)
            row += 1

        ws_apt.set_column(0, 1, 16)
        ws_apt.set_column(2, 2, 10)
        ws_apt.set_column(3, 8, 20)
        ws_apt.set_column(9, 11, 15)

        workbook.close()
        output.seek(0)
        file_data = output.read()
        output.close()

        filename = f"Medical_Staff_Performance_{self.start_date}_{self.end_date}.xlsx"
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(file_data),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'res_model': self._name,
            'res_id': self.id,
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    def action_export_pdf(self):
        """Prints formal PDF performance report"""
        self.ensure_one()
        return self.env.ref('medical_appointment_management.action_report_medical_staff_performance').report_action(self)

    def action_view_targets(self):
        """Opens the Performance Targets management view"""
        return {
            'name': _('Medical Staff Performance Targets'),
            'type': 'ir.actions.act_window',
            'res_model': 'medical.staff.target',
            'view_mode': 'list,form',
            'target': 'current',
        }


class MedicalStaffPerformanceLine(models.TransientModel):
    _name = 'medical.staff.performance.line'
    _description = 'Employee Performance Report Line'
    _order = 'total_revenue desc, completed_appointments desc'

    dashboard_id = fields.Many2one(
        'medical.staff.performance.dashboard',
        string='Dashboard',
        ondelete='cascade',
        required=True
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True
    )
    department_id = fields.Many2one(
        'hr.department',
        string='Department'
    )
    role = fields.Selection([
        ('doctor', 'Doctor'),
        ('sales', 'Sales Employee'),
        ('receptionist', 'Receptionist'),
        ('nurse', 'Nurse'),
        ('other', 'Other'),
    ], string='Role')

    # Current Period Metrics
    assigned_leads = fields.Integer(string='Assigned Leads')
    converted_leads = fields.Integer(string='Converted Leads')
    conversion_rate = fields.Float(string='Conv. Rate (%)')

    total_appointments = fields.Integer(string='Total Appts')
    completed_appointments = fields.Integer(string='Completed')
    in_progress_appointments = fields.Integer(string='In Progress')
    cancelled_appointments = fields.Integer(string='Cancelled')
    cancellation_rate = fields.Float(string='Cancel Rate (%)')
    no_show_appointments = fields.Integer(string='No-Show')
    no_show_rate = fields.Float(string='No-Show Rate (%)')

    total_revenue = fields.Float(string='Total Revenue ($)')
    avg_revenue_per_completed = fields.Float(string='Avg Rev / Session')

    # Comparison Period Metrics
    prev_revenue = fields.Float(string='Prev Revenue ($)')
    revenue_growth = fields.Float(string='Rev Growth (%)')
    prev_total_appointments = fields.Integer(string='Prev Total Appts')
    prev_completed_appointments = fields.Integer(string='Prev Completed')
    appointment_growth = fields.Float(string='Appt Growth (%)')

    prev_conversion_rate = fields.Float(string='Prev Conv Rate (%)')
    conversion_rate_change_pp = fields.Float(string='Conv Δ (pp)')
    prev_cancellation_rate = fields.Float(string='Prev Cancel Rate (%)')
    cancellation_rate_change_pp = fields.Float(string='Cancel Δ (pp)')
    prev_no_show_rate = fields.Float(string='Prev No-Show Rate (%)')
    no_show_rate_change_pp = fields.Float(string='No-Show Δ (pp)')

    # Targets & Progress
    target_id = fields.Many2one('medical.staff.target', string='Active Target')
    revenue_target = fields.Float(string='Target Revenue')
    revenue_target_progress = fields.Float(string='Rev Target %')
    completed_target = fields.Integer(string='Target Completed')
    completed_target_progress = fields.Float(string='Appt Target %')
    conversion_target = fields.Float(string='Target Conv %')
    conversion_target_progress = fields.Float(string='Conv Target %')

    # Trajectory & Status
    performance_trend = fields.Selection([
        ('improving', 'Improving'),
        ('stable', 'Stable'),
        ('declining', 'Declining'),
    ], string='Trend', default='stable')
    trend_badge = fields.Char(string='Trajectory')
