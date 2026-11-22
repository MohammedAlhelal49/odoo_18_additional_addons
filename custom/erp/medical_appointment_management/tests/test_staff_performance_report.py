# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError
from datetime import date, datetime, timedelta


class TestStaffPerformanceReport(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env.company

        # 1. Create Medical Departments
        cls.dept_doctor = cls.env['hr.department'].create({'name': 'Clinical Medicine'})
        cls.dept_sales = cls.env['hr.department'].create({'name': 'Medical Sales & Intake'})
        cls.dept_reception = cls.env['hr.department'].create({'name': 'Front Desk & Reception'})

        # 2. Create Users
        cls.user_doctor = cls.env['res.users'].create({
            'name': 'Dr. Robert Carter',
            'login': 'dr_carter_perf',
            'email': 'carter@medical.test',
            'groups_id': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('medical_employee_management.group_medical_doctor').id,
            ])]
        })
        cls.user_sales = cls.env['res.users'].create({
            'name': 'Sarah Jenkins',
            'login': 'sarah_sales_perf',
            'email': 'sarah@medical.test',
            'groups_id': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('medical_employee_management.group_medical_sales').id,
            ])]
        })
        cls.user_reception = cls.env['res.users'].create({
            'name': 'Lucy Receptionist',
            'login': 'lucy_recep_perf',
            'email': 'lucy@medical.test',
            'groups_id': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('medical_employee_management.group_medical_receptionist').id,
            ])]
        })

        # 3. Create or Update Medical Employees
        def _get_or_create_employee(user, vals):
            emp = cls.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
            if emp:
                emp.write(vals)
                return emp
            vals['user_id'] = user.id
            return cls.env['hr.employee'].create(vals)

        cls.emp_doctor = _get_or_create_employee(cls.user_doctor, {
            'name': 'Dr. Robert Carter',
            'department_id': cls.dept_doctor.id,
            'medical_employee_type': 'doctor',
            'is_appointment_provider': True,
        })
        cls.emp_sales = _get_or_create_employee(cls.user_sales, {
            'name': 'Sarah Jenkins',
            'department_id': cls.dept_sales.id,
            'medical_employee_type': 'sales',
        })
        cls.emp_reception = _get_or_create_employee(cls.user_reception, {
            'name': 'Lucy Receptionist',
            'department_id': cls.dept_reception.id,
            'medical_employee_type': 'receptionist',
        })

        # 4. Create Medical Services
        cls.service_consult = cls.env['medical.service'].create({
            'name': 'General Consultation',
            'price': 200.0,
            'duration': 1.0,
        })
        cls.service_procedure = cls.env['medical.service'].create({
            'name': 'Minor Surgery Procedure',
            'price': 800.0,
            'duration': 2.0,
        })

        # 5. Create Patients / Customers
        cls.patient_a = cls.env['res.partner'].create({
            'name': 'Alice Patient',
            'email': 'alice@example.com',
            'phone': '+155510101',
            'is_patient': True,
        })
        cls.patient_b = cls.env['res.partner'].create({
            'name': 'Bob Patient',
            'email': 'bob@example.com',
            'phone': '+155520202',
            'is_patient': True,
        })
        cls.patient_c = cls.env['res.partner'].create({
            'name': 'Charlie Patient',
            'email': 'charlie@example.com',
            'phone': '+155530303',
            'is_patient': True,
        })

        # Base dates for test scenarios (isolated to avoid data pollution)
        cls.curr_start = date(2029, 5, 1)
        cls.curr_end = date(2029, 5, 31)
        cls.prev_start = date(2029, 4, 1)
        cls.prev_end = date(2029, 4, 30)

    def test_01_target_creation_and_constraints(self):
        """Test Target creation, automatic naming, date constraints, and role constraints"""
        target = self.env['medical.staff.target'].create({
            'target_type': 'employee',
            'employee_id': self.emp_doctor.id,
            'date_start': self.curr_start,
            'date_end': self.curr_end,
            'revenue_target': 10000.0,
            'completed_appointment_target': 25,
            'lead_conversion_target': 40.0,
            'max_cancellation_rate': 8.0,
            'max_no_show_rate': 4.0,
        })
        self.assertTrue(target.name)
        self.assertIn('Dr. Robert Carter', target.name)

        # Invalid date constraint (end < start)
        with self.assertRaises(ValidationError):
            self.env['medical.staff.target'].create({
                'target_type': 'employee',
                'employee_id': self.emp_doctor.id,
                'date_start': self.curr_end,
                'date_end': self.curr_start - timedelta(days=10),
            })

        # Missing assignment constraint
        with self.assertRaises(ValidationError):
            self.env['medical.staff.target'].create({
                'target_type': 'department',
                'department_id': False,
                'date_start': self.curr_start,
                'date_end': self.curr_end,
            })

    def test_02_revenue_and_appointment_counting_accuracy(self):
        """
        Verify that completed appointments generate confirmed revenue,
        while cancelled and no-show appointments contribute $0 revenue,
        and that each appointment is strictly counted once (no double counting).
        """
        # Appointment 1: Completed ($200)
        apt1 = self.env['medical.appointment'].create({
            'partner_id': self.patient_a.id,
            'doctor_id': self.emp_doctor.id,
            'sales_employee_id': self.emp_sales.id,
            'service_ids': [(6, 0, [self.service_consult.id])],
            'appointment_date': self.curr_start,
            'start_time': 9.0,
            'duration': 1.0,
            'status': 'completed',
        })

        # Appointment 2: Completed ($800)
        apt2 = self.env['medical.appointment'].create({
            'partner_id': self.patient_b.id,
            'doctor_id': self.emp_doctor.id,
            'sales_employee_id': self.emp_sales.id,
            'service_ids': [(6, 0, [self.service_procedure.id])],
            'appointment_date': self.curr_start,
            'start_time': 11.0,
            'duration': 2.0,
            'status': 'completed',
        })

        # Appointment 3: Cancelled ($0 revenue)
        apt3 = self.env['medical.appointment'].create({
            'partner_id': self.patient_c.id,
            'doctor_id': self.emp_doctor.id,
            'sales_employee_id': self.emp_sales.id,
            'service_ids': [(6, 0, [self.service_consult.id])],
            'appointment_date': self.curr_start,
            'start_time': 14.0,
            'duration': 1.0,
            'status': 'cancelled',
        })

        # Appointment 4: No-Show ($0 revenue)
        apt4 = self.env['medical.appointment'].create({
            'partner_id': self.patient_a.id,
            'doctor_id': self.emp_doctor.id,
            'sales_employee_id': self.emp_sales.id,
            'service_ids': [(6, 0, [self.service_consult.id])],
            'appointment_date': self.curr_start,
            'start_time': 16.0,
            'duration': 1.0,
            'status': 'no_show',
        })

        # Initialize Dashboard
        dash = self.env['medical.staff.performance.dashboard'].create({
            'start_date': self.curr_start,
            'end_date': self.curr_end,
            'comparison_type': 'custom',
            'comparison_start_date': self.prev_start,
            'comparison_end_date': self.prev_end,
        })
        dash.action_apply_filters()

        # Check Overall KPIs
        self.assertEqual(dash.total_appointments, 4)
        self.assertEqual(dash.completed_appointments, 2)
        self.assertEqual(dash.cancelled_appointments, 1)
        self.assertEqual(dash.no_show_appointments, 1)
        # Expected Revenue: 200 + 800 = 1000.0 (cancelled and no-show must NOT add anything)
        self.assertEqual(dash.total_revenue, 1000.0)
        self.assertEqual(dash.cancellation_rate, 25.0)  # 1/4 = 25%
        self.assertEqual(dash.no_show_rate, 25.0)       # 1/4 = 25%
        self.assertEqual(dash.avg_revenue_per_completed, 500.0) # 1000 / 2 = 500.0

    def test_03_employee_role_attribution(self):
        """
        Verify that Doctor, Sales Staff, and Receptionist receive correct attributed metrics:
        - Doctor gets appointment revenue & completed counts
        - Sales staff gets assigned leads, converted leads, and booked appointments
        """
        lead1 = self.env['crm.lead'].create({
            'name': 'New Patient Lead A',
            'medical_staff_id': self.emp_sales.id,
            'user_id': self.user_sales.id,
            'partner_id': self.patient_a.id,
        })
        self.env.cr.execute(
            "UPDATE crm_lead SET create_date = %s WHERE id = %s",
            (datetime.combine(self.curr_start, datetime.min.time()) + timedelta(hours=1), lead1.id)
        )
        lead1.invalidate_recordset(['create_date'])
        # Create an appointment booked by Sales and executed by Doctor
        apt = self.env['medical.appointment'].create({
            'crm_lead_id': lead1.id,
            'partner_id': self.patient_a.id,
            'doctor_id': self.emp_doctor.id,
            'sales_employee_id': self.emp_sales.id,
            'service_ids': [(6, 0, [self.service_consult.id])],
            'appointment_date': self.curr_start,
            'start_time': 10.0,
            'duration': 1.0,
            'status': 'completed',
        })

        dash = self.env['medical.staff.performance.dashboard'].create({
            'start_date': self.curr_start,
            'end_date': self.curr_end,
            'comparison_type': 'custom',
            'comparison_start_date': self.prev_start,
            'comparison_end_date': self.prev_end,
        })
        dash.action_apply_filters()

        doc_line = dash.line_ids.filtered(lambda l: l.employee_id == self.emp_doctor)
        sales_line = dash.line_ids.filtered(lambda l: l.employee_id == self.emp_sales)

        self.assertTrue(doc_line)
        self.assertTrue(sales_line)

        # Doctor stats
        self.assertEqual(doc_line.completed_appointments, 1)
        self.assertEqual(doc_line.total_revenue, 200.0)

        # Sales stats
        self.assertEqual(sales_line.assigned_leads, 1)
        self.assertEqual(sales_line.converted_leads, 1)
        self.assertEqual(sales_line.conversion_rate, 100.0)
        self.assertEqual(sales_line.total_appointments, 1)

    def test_04_comparison_periods_and_zero_handling(self):
        """
        Verify growth percentages, percentage-point changes,
        and safe handling when previous period has zero records (no division by zero).
        """
        # Create appointment in current period only (previous period has 0)
        apt = self.env['medical.appointment'].create({
            'partner_id': self.patient_a.id,
            'doctor_id': self.emp_doctor.id,
            'sales_employee_id': self.emp_sales.id,
            'service_ids': [(6, 0, [self.service_consult.id])],
            'appointment_date': self.curr_start,
            'start_time': 9.0,
            'duration': 1.0,
            'status': 'completed',
        })

        dash = self.env['medical.staff.performance.dashboard'].create({
            'start_date': self.curr_start,
            'end_date': self.curr_end,
            'comparison_type': 'custom',
            'comparison_start_date': self.prev_start,
            'comparison_end_date': self.prev_end,
        })
        dash.action_apply_filters()

        # Previous period has 0 appointments and 0 revenue
        self.assertEqual(dash.prev_total_appointments, 0)
        self.assertEqual(dash.prev_total_revenue, 0.0)

        # Zero handling: Growth should be +100.0% when prev=0 and curr > 0, never crashing
        self.assertEqual(dash.revenue_growth, 100.0)
        self.assertEqual(dash.appointment_growth, 100.0)

    def test_05_cancellation_reduction_treated_as_positive_improvement(self):
        """
        Verify that a reduction in cancellation rate (negative percentage points)
        is interpreted as positive improvement and leads to an 'Improving' trend.
        """
        # Previous period: high cancellations (e.g. 50% cancellation rate)
        apt_prev1 = self.env['medical.appointment'].create({
            'partner_id': self.patient_a.id,
            'doctor_id': self.emp_doctor.id,
            'sales_employee_id': self.emp_sales.id,
            'service_ids': [(6, 0, [self.service_consult.id])],
            'appointment_date': self.prev_start,
            'start_time': 9.0,
            'duration': 1.0,
            'status': 'completed',
        })
        apt_prev2 = self.env['medical.appointment'].create({
            'partner_id': self.patient_b.id,
            'doctor_id': self.emp_doctor.id,
            'sales_employee_id': self.emp_sales.id,
            'service_ids': [(6, 0, [self.service_consult.id])],
            'appointment_date': self.prev_start,
            'start_time': 11.0,
            'duration': 1.0,
            'status': 'cancelled',
        })

        # Current period: 100% completed, 0% cancelled (cancellation rate dropped by -50 pp!)
        apt_curr1 = self.env['medical.appointment'].create({
            'partner_id': self.patient_a.id,
            'doctor_id': self.emp_doctor.id,
            'sales_employee_id': self.emp_sales.id,
            'service_ids': [(6, 0, [self.service_consult.id])],
            'appointment_date': self.curr_start,
            'start_time': 9.0,
            'duration': 1.0,
            'status': 'completed',
        })
        apt_curr2 = self.env['medical.appointment'].create({
            'partner_id': self.patient_b.id,
            'doctor_id': self.emp_doctor.id,
            'sales_employee_id': self.emp_sales.id,
            'service_ids': [(6, 0, [self.service_consult.id])],
            'appointment_date': self.curr_start,
            'start_time': 11.0,
            'duration': 1.0,
            'status': 'completed',
        })

        dash = self.env['medical.staff.performance.dashboard'].create({
            'start_date': self.curr_start,
            'end_date': self.curr_end,
            'comparison_type': 'custom',
            'comparison_start_date': self.prev_start,
            'comparison_end_date': self.prev_end,
        })
        dash.action_apply_filters()

        doc_line = dash.line_ids.filtered(lambda l: l.employee_id == self.emp_doctor)
        self.assertTrue(doc_line)
        # Cancellation rate changed from 50.0% to 0.0% => -50.0 pp
        self.assertLess(doc_line.cancellation_rate_change_pp, 0)
        # Trend should be 'improving'
        self.assertEqual(doc_line.performance_trend, 'improving')

    def test_06_target_progress_matching(self):
        """
        Verify that configured targets in medical.staff.target
        are matched to employee performance lines and progress is computed.
        """
        target = self.env['medical.staff.target'].create({
            'target_type': 'employee',
            'employee_id': self.emp_doctor.id,
            'date_start': self.curr_start,
            'date_end': self.curr_end,
            'revenue_target': 1000.0,
            'completed_appointment_target': 2,
        })

        apt1 = self.env['medical.appointment'].create({
            'partner_id': self.patient_a.id,
            'doctor_id': self.emp_doctor.id,
            'sales_employee_id': self.emp_sales.id,
            'service_ids': [(6, 0, [self.service_consult.id])],  # 200.0
            'appointment_date': self.curr_start,
            'start_time': 9.0,
            'duration': 1.0,
            'status': 'completed',
        })

        dash = self.env['medical.staff.performance.dashboard'].create({
            'start_date': self.curr_start,
            'end_date': self.curr_end,
        })
        dash.action_apply_filters()

        doc_line = dash.line_ids.filtered(lambda l: l.employee_id == self.emp_doctor)
        self.assertEqual(doc_line.target_id, target)
        self.assertEqual(doc_line.revenue_target, 1000.0)
        # 200 / 1000 * 100 = 20.0%
        self.assertEqual(doc_line.revenue_target_progress, 20.0)
        # 1 / 2 * 100 = 50.0%
        self.assertEqual(doc_line.completed_target_progress, 50.0)

    def test_07_excel_and_pdf_export_actions(self):
        """
        Verify Excel export generates valid attachment and returns download action,
        and PDF action returns valid report action.
        """
        dash = self.env['medical.staff.performance.dashboard'].create({
            'start_date': self.curr_start,
            'end_date': self.curr_end,
        })
        dash.action_apply_filters()

        # Excel Export
        excel_action = dash.action_export_excel()
        self.assertEqual(excel_action.get('type'), 'ir.actions.act_url')
        self.assertIn('/web/content/', excel_action.get('url'))

        # PDF Export
        pdf_action = dash.action_export_pdf()
        self.assertEqual(pdf_action.get('type'), 'ir.actions.report')
        self.assertEqual(pdf_action.get('report_name'), 'medical_appointment_management.report_staff_performance_document')

    def test_08_privacy_and_access_control(self):
        """
        Verify that staff performance lines do not leak clinical notes, diagnoses,
        or patient confidential information.
        """
        dash = self.env['medical.staff.performance.dashboard'].create({
            'start_date': self.curr_start,
            'end_date': self.curr_end,
        })
        dash.action_apply_filters()

        # Ensure no clinical fields exist on performance lines
        self.assertFalse(hasattr(dash.line_ids, 'diagnosis'))
        self.assertFalse(hasattr(dash.line_ids, 'prescription'))
        self.assertFalse(hasattr(dash.line_ids, 'clinical_notes'))
        self.assertFalse(hasattr(dash.line_ids, 'doctor_notes'))
