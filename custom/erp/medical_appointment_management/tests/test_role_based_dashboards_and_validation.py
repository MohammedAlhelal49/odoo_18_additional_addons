# -*- coding: utf-8 -*-

from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, AccessError
from datetime import date, datetime, timedelta
import pytz


class TestRoleBasedDashboardsAndValidation(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Groups
        cls.group_manager = cls.env.ref('medical_appointment_management.group_medical_appointment_manager')
        cls.group_doctor = cls.env.ref('medical_employee_management.group_medical_doctor')
        cls.group_nurse = cls.env.ref('medical_employee_management.group_medical_nurse')
        cls.group_receptionist = cls.env.ref('medical_employee_management.group_medical_receptionist')
        cls.group_sales = cls.env.ref('medical_employee_management.group_medical_sales')

        # Users
        cls.doctor_user = cls.env['res.users'].create({
            'name': 'Dr. Robert Specialist',
            'login': 'dr_robert_specialist@test.clinic',
            'email': 'dr.robert@test.clinic',
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id, cls.group_doctor.id])],
        })
        cls.nurse_user = cls.env['res.users'].create({
            'name': 'Nurse Emma Triage',
            'login': 'nurse_emma_triage@test.clinic',
            'email': 'nurse.emma@test.clinic',
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id, cls.group_nurse.id])],
        })
        cls.sales_user = cls.env['res.users'].create({
            'name': 'Sales Rep Alice',
            'login': 'sales_alice_rep@test.clinic',
            'email': 'sales.alice@test.clinic',
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id, cls.group_sales.id])],
        })

        # Employees
        cls.doctor_emp = cls.env['hr.employee'].search([('user_id', '=', cls.doctor_user.id)], limit=1)
        if not cls.doctor_emp:
            cls.doctor_emp = cls.env['hr.employee'].create({
                'name': 'Dr. Robert Specialist',
                'medical_employee_type': 'doctor',
                'user_id': cls.doctor_user.id,
            })
        else:
            cls.doctor_emp.write({'name': 'Dr. Robert Specialist', 'medical_employee_type': 'doctor'})

        cls.nurse_emp = cls.env['hr.employee'].search([('user_id', '=', cls.nurse_user.id)], limit=1)
        if not cls.nurse_emp:
            cls.nurse_emp = cls.env['hr.employee'].create({
                'name': 'Nurse Emma Triage',
                'medical_employee_type': 'nurse',
                'user_id': cls.nurse_user.id,
            })
        else:
            cls.nurse_emp.write({'name': 'Nurse Emma Triage', 'medical_employee_type': 'nurse'})

        cls.sales_emp = cls.env['hr.employee'].search([('user_id', '=', cls.sales_user.id)], limit=1)
        if not cls.sales_emp:
            cls.sales_emp = cls.env['hr.employee'].create({
                'name': 'Sales Rep Alice',
                'medical_employee_type': 'sales',
                'user_id': cls.sales_user.id,
            })
        else:
            cls.sales_emp.write({'name': 'Sales Rep Alice', 'medical_employee_type': 'sales'})

        # Patient Partner
        cls.patient = cls.env['res.partner'].create({
            'name': 'Test Patient Jordan',
            'phone': '+971501112233',
            'email': 'jordan.patient@example.com',
            'is_patient': True,
            'patient_number': 'MRN-TEST-9999',
            'blood_group': 'O+',
            'allergies': 'Penicillin',
        })

        # Service
        cls.service = cls.env['medical.service'].create({
            'name': 'Cardiology Comprehensive Evaluation',
            'code': 'SRV-CARDIO-COMP',
            'price': 500.0,
            'duration': 1.0,
            'period_between_sessions': 14,
            'active': True,
        })

    # =========================================================================
    # 1. Appointment Creation & Validation Tests (Section 6)
    # =========================================================================

    def test_past_date_appointment_rejected(self):
        """Reject appointments scheduled in the past unless authorized via backdated entry"""
        past_date = date.today() - timedelta(days=2)

        # 1. Past date without backdated authorization must fail
        with self.assertRaises(ValidationError) as ctx:
            self.env['medical.appointment'].create({
                'partner_id': self.patient.id,
                'doctor_id': self.doctor_emp.id,
                'service_ids': [(6, 0, [self.service.id])],
                'appointment_date': past_date,
                'start_time': 10.0,
                'duration': 1.0,
                'allow_backdated_entry': False,
            })
        self.assertIn("The appointment start time must be in the future", str(ctx.exception))

        # 2. Authorized backdated entry succeeds
        apt_backdated = self.env['medical.appointment'].create({
            'partner_id': self.patient.id,
            'doctor_id': self.doctor_emp.id,
            'service_ids': [(6, 0, [self.service.id])],
            'appointment_date': past_date,
            'start_time': 10.0,
            'duration': 1.0,
            'allow_backdated_entry': True,
        })
        self.assertTrue(apt_backdated.id)
        self.assertTrue(apt_backdated.allow_backdated_entry)

    def test_time_bounds_validation(self):
        """Require valid start and end times, and end_time > start_time"""
        future_date = date.today() + timedelta(days=5)

        # 1. Negative or out-of-range start time
        with self.assertRaises(ValidationError) as ctx:
            self.env['medical.appointment'].create({
                'partner_id': self.patient.id,
                'doctor_id': self.doctor_emp.id,
                'service_ids': [(6, 0, [self.service.id])],
                'appointment_date': future_date,
                'start_time': 24.5,
                'duration': 1.0,
            })
        self.assertIn("between 00:00 and 23:59", str(ctx.exception))

        # 2. Duration <= 0
        with self.assertRaises(ValidationError) as ctx:
            self.env['medical.appointment'].create({
                'partner_id': self.patient.id,
                'doctor_id': self.doctor_emp.id,
                'service_ids': [(6, 0, [self.service.id])],
                'appointment_date': future_date,
                'start_time': 10.0,
                'duration': 0.0,
            })
        self.assertIn("greater than zero", str(ctx.exception))

    def test_doctor_overlap_validation_and_exclusion_of_cancelled(self):
        """
        Overlap condition: new_start < existing_end AND new_end > existing_start
        Reject overlapping bookings; cancelled appointments must be excluded from conflict check.
        """
        future_date = date.today() + timedelta(days=7)

        # Booking 1: 10:00 to 11:00
        apt1 = self.env['medical.appointment'].create({
            'partner_id': self.patient.id,
            'doctor_id': self.doctor_emp.id,
            'service_ids': [(6, 0, [self.service.id])],
            'appointment_date': future_date,
            'start_time': 10.0,
            'duration': 1.0,
            'status': 'confirmed',
        })
        self.assertFalse(apt1.has_conflict)

        # Booking 2: partial overlap 10:30 to 11:30 without override must fail
        with self.assertRaises(ValidationError) as ctx:
            self.env['medical.appointment'].create({
                'partner_id': self.patient.id,
                'doctor_id': self.doctor_emp.id,
                'service_ids': [(6, 0, [self.service.id])],
                'appointment_date': future_date,
                'start_time': 10.5,
                'duration': 1.0,
                'status': 'tentative',
            })
        self.assertIn("The doctor is already booked during this period", str(ctx.exception))

        # Booking 3: exactly adjacent (11:00 to 12:00) must succeed
        apt3 = self.env['medical.appointment'].create({
            'partner_id': self.patient.id,
            'doctor_id': self.doctor_emp.id,
            'service_ids': [(6, 0, [self.service.id])],
            'appointment_date': future_date,
            'start_time': 11.0,
            'duration': 1.0,
            'status': 'confirmed',
        })
        self.assertTrue(apt3.id)
        self.assertFalse(apt3.has_conflict)

        # Cancel Booking 1 -> Schedule slot is released!
        apt1.write({'status': 'cancelled'})

        # Now re-booking during 10:00 - 11:00 succeeds cleanly!
        apt_rebooked = self.env['medical.appointment'].create({
            'partner_id': self.patient.id,
            'doctor_id': self.doctor_emp.id,
            'service_ids': [(6, 0, [self.service.id])],
            'appointment_date': future_date,
            'start_time': 10.0,
            'duration': 1.0,
            'status': 'confirmed',
        })
        self.assertTrue(apt_rebooked.id)
        self.assertFalse(apt_rebooked.has_conflict)

    def test_doctor_working_hours_validation(self):
        """Validate doctor working hours when resource calendar attendances are configured"""
        future_date = date.today() + timedelta(days=8)
        weekday = str(future_date.weekday())

        # Create calendar with morning attendance 08:00 - 14:00 on this weekday
        calendar = self.env['resource.calendar'].create({
            'name': 'Doctor Morning Shift',
            'attendance_ids': [(0, 0, {
                'name': 'Shift',
                'dayofweek': weekday,
                'hour_from': 8.0,
                'hour_to': 14.0,
                'day_period': 'morning',
            })],
        })
        self.doctor_emp.resource_calendar_id = calendar

        # 1. Appointment at 16:00 is outside doctor's working hours
        with self.assertRaises(ValidationError) as ctx:
            self.env['medical.appointment'].create({
                'partner_id': self.patient.id,
                'doctor_id': self.doctor_emp.id,
                'service_ids': [(6, 0, [self.service.id])],
                'appointment_date': future_date,
                'start_time': 16.0,
                'duration': 1.0,
            })
        self.assertIn("The selected time is outside the doctor's working hours", str(ctx.exception))

        # 2. Appointment at 10:00 is inside working hours -> succeeds
        apt_in_hours = self.env['medical.appointment'].create({
            'partner_id': self.patient.id,
            'doctor_id': self.doctor_emp.id,
            'service_ids': [(6, 0, [self.service.id])],
            'appointment_date': future_date,
            'start_time': 10.0,
            'duration': 1.0,
        })
        self.assertTrue(apt_in_hours.id)

        # Cleanup calendar
        self.doctor_emp.resource_calendar_id = False

    def test_doctor_approved_leave_validation(self):
        """Validate doctor approved leaves in hr.leave"""
        future_date = date.today() + timedelta(days=10)

        # Ensure doctor has active working schedule on that date
        calendar = self.env['resource.calendar'].create({
            'name': 'Doctor Daily Schedule',
            'attendance_ids': [(0, 0, {
                'name': f'Shift {day}',
                'dayofweek': str(day),
                'hour_from': 8.0,
                'hour_to': 18.0,
                'day_period': 'morning',
            }) for day in range(7)],
        })
        self.doctor_emp.resource_calendar_id = calendar

        # Create approved leave for doctor on future_date
        leave_type = self.env['hr.leave.type'].search([('requires_allocation', '=', 'no')], limit=1)
        if not leave_type:
            leave_type = self.env['hr.leave.type'].create({
                'name': 'Annual Medical Leave Test',
                'requires_allocation': 'no',
                'leave_validation_type': 'no_validation',
            })

        leave = self.env['hr.leave'].sudo().create({
            'name': 'Doctor Conference Leave',
            'employee_id': self.doctor_emp.id,
            'holiday_status_id': leave_type.id,
            'request_date_from': future_date,
            'request_date_to': future_date,
            'date_from': datetime.combine(future_date, datetime.min.time()),
            'date_to': datetime.combine(future_date, datetime.max.time()),
            'number_of_days': 1,
        })
        leave.action_validate()
        self.assertEqual(leave.state, 'validate')

        # Booking during approved leave must fail
        with self.assertRaises(ValidationError) as ctx:
            self.env['medical.appointment'].create({
                'partner_id': self.patient.id,
                'doctor_id': self.doctor_emp.id,
                'service_ids': [(6, 0, [self.service.id])],
                'appointment_date': future_date,
                'start_time': 10.0,
                'duration': 1.0,
            })
        self.assertIn("The doctor is unavailable during this period", str(ctx.exception))
        self.doctor_emp.resource_calendar_id = False

    # =========================================================================
    # 2. Automatic Task Assignment Tests (Section 7)
    # =========================================================================

    def test_new_lead_creates_sales_contact_activity(self):
        """Event: New lead created -> Automatic sales contact task (call activity)"""
        lead = self.env['crm.lead'].create({
            'name': 'VIP Patient Inquiry for Rhinoplasty',
            'partner_name': 'Sarah Connor',
            'phone': '+971552223344',
            'user_id': self.sales_user.id,
            'medical_staff_id': self.sales_emp.id,
        })

        call_acts = lead.activity_ids.filtered(lambda a: 'Initial' in (a.summary or ''))
        self.assertTrue(call_acts, "Initial sales contact activity must be automatically created on lead creation")
        self.assertEqual(call_acts.user_id, self.sales_user)
        self.assertEqual(call_acts.date_deadline, date.today())

    def test_appointment_scheduled_for_tomorrow_creates_confirmation_activity(self):
        """Event: Appointment scheduled for tomorrow -> Automatic reception confirmation task"""
        tomorrow = date.today() + timedelta(days=1)

        apt = self.env['medical.appointment'].create({
            'partner_id': self.patient.id,
            'doctor_id': self.doctor_emp.id,
            'service_ids': [(6, 0, [self.service.id])],
            'appointment_date': tomorrow,
            'start_time': 11.0,
            'duration': 1.0,
            'status': 'tentative',
            'salesperson_id': self.sales_user.id,
        })

        confirm_acts = apt.activity_ids.filtered(lambda a: 'Confirm' in (a.summary or ''))
        self.assertTrue(confirm_acts, "Reception confirmation activity must be created for tomorrow's appointment")
        self.assertEqual(confirm_acts.date_deadline, date.today())

    def test_patient_arrival_and_triage_notifies_doctor(self):
        """Event: Patient arrival and nurse triage completion automatically notify the doctor"""
        tomorrow = date.today() + timedelta(days=1)
        apt = self.env['medical.appointment'].create({
            'partner_id': self.patient.id,
            'doctor_id': self.doctor_emp.id,
            'service_ids': [(6, 0, [self.service.id])],
            'appointment_date': tomorrow,
            'start_time': 14.0,
            'duration': 1.0,
            'status': 'confirmed',
        })

        # 1. Patient arrives (Check-in)
        apt.action_check_in()
        self.assertEqual(apt.status, 'checked_in')
        arrival_acts = apt.activity_ids.filtered(lambda a: 'Arrived' in (a.summary or ''))
        self.assertTrue(arrival_acts, "Doctor must receive arrival notification task upon patient check-in")
        self.assertEqual(arrival_acts.user_id, self.doctor_user)

        # 2. Nurse completes triage & vitals
        apt.action_ready_for_doctor()
        self.assertEqual(apt.status, 'ready_for_doctor')
        ready_acts = apt.activity_ids.filtered(lambda a: 'Ready' in (a.summary or ''))
        self.assertTrue(ready_acts, "Doctor must receive patient ready notification task upon nurse triage completion")
        self.assertEqual(ready_acts.user_id, self.doctor_user)

    def test_appointment_cancelled_unlinks_activities(self):
        """Event: Appointment cancelled -> Pending activities are cleared and slot released"""
        tomorrow = date.today() + timedelta(days=1)
        apt = self.env['medical.appointment'].create({
            'partner_id': self.patient.id,
            'doctor_id': self.doctor_emp.id,
            'service_ids': [(6, 0, [self.service.id])],
            'appointment_date': tomorrow,
            'start_time': 15.0,
            'duration': 1.0,
            'status': 'tentative',
        })
        self.assertTrue(apt.activity_ids)

        # Cancel appointment
        apt.write({
            'status': 'cancelled',
            'cancellation_reason': 'Patient emergency cancellation',
        })
        self.assertFalse(apt.activity_ids, "All pending tasks must be automatically cleaned up on cancellation")

    # =========================================================================
    # 3. Sales Representative Tracking & Filters (Section 1)
    # =========================================================================

    def test_sales_lead_overdue_and_call_summary_computation(self):
        """Sales rep overdue tracking and call outcome sync"""
        yesterday = date.today() - timedelta(days=1)
        lead = self.env['crm.lead'].create({
            'name': 'Dermatology Follow-up Lead',
            'partner_name': 'Alex Mercer',
            'phone': '+971509988776',
            'user_id': self.sales_user.id,
            'medical_staff_id': self.sales_emp.id,
            'next_followup_date': yesterday,
        })
        self.assertTrue(lead.is_overdue, "Lead with past next_followup_date must be computed as is_overdue=True")

        # Log a call attempt
        self.env['crm.lead.call_log'].create({
            'lead_id': lead.id,
            'outcome': 'followup_required',
            'notes': 'Spoke with client, requested quote on Saturday',
            'next_followup_date': date.today() + timedelta(days=3),
        })

        lead.invalidate_recordset()
        self.assertEqual(lead.last_call_outcome, 'followup_required')
        self.assertFalse(lead.is_overdue, "Lead with future next_followup_date must not be overdue")

    # =========================================================================
    # 4. Receptionist Dashboard Counters (Section 2)
    # =========================================================================

    def test_receptionist_dashboard_metrics(self):
        """Verify Receptionist Dashboard live KPI counters"""
        today = date.today()
        tomorrow = today + timedelta(days=1)

        # Create today's test appointments (1 waiting, 1 confirmed)
        apt_today1 = self.env['medical.appointment'].create({
            'partner_id': self.patient.id,
            'doctor_id': self.doctor_emp.id,
            'service_ids': [(6, 0, [self.service.id])],
            'appointment_date': today,
            'start_time': 9.0,
            'duration': 1.0,
            'status': 'checked_in',
            'allow_backdated_entry': True,
        })
        apt_today2 = self.env['medical.appointment'].create({
            'partner_id': self.patient.id,
            'doctor_id': self.doctor_emp.id,
            'service_ids': [(6, 0, [self.service.id])],
            'appointment_date': today,
            'start_time': 11.0,
            'duration': 1.0,
            'status': 'confirmed',
            'allow_backdated_entry': True,
        })

        dashboard = self.env['medical.receptionist.dashboard'].create({
            'name': 'Test Reception Dashboard',
            'company_id': self.env.company.id,
        })
        dashboard.action_refresh()

        self.assertGreaterEqual(dashboard.kpi_today_total, 2)
        self.assertGreaterEqual(dashboard.kpi_patients_waiting, 1)
        self.assertIn("Reception Desk Operations", dashboard.dashboard_html)

    # =========================================================================
    # 5. Doctor & Nurse Permissions & Actions (Section 3, 5, 8)
    # =========================================================================

    def test_doctor_start_consultation_converts_lead_to_patient(self):
        """When doctor starts consultation, lead is automatically converted to registered patient"""
        lead = self.env['crm.lead'].create({
            'name': 'New Lead First Visit',
            'contact_name': 'Hannah Abbott',
            'phone': '+971521234567',
            'user_id': self.sales_user.id,
            'medical_staff_id': self.sales_emp.id,
        })

        tomorrow = date.today() + timedelta(days=1)
        apt = self.env['medical.appointment'].create({
            'crm_lead_id': lead.id,
            'doctor_id': self.doctor_emp.id,
            'service_ids': [(6, 0, [self.service.id])],
            'appointment_date': tomorrow,
            'start_time': 16.0,
            'duration': 1.0,
            'status': 'ready_for_doctor',
        })

        # Doctor starts consultation
        apt.with_user(self.doctor_user).action_start_consultation()

        self.assertEqual(apt.status, 'in_consultation')
        self.assertTrue(apt.partner_id, "Patient partner must be created or linked")
        self.assertTrue(apt.partner_id.is_patient)
        self.assertTrue(apt.partner_id.patient_number, "Official MRN must be assigned upon starting consultation")
        self.assertEqual(lead.partner_id, apt.partner_id)

    def test_manager_dashboard_metrics(self):
        """Manager Operations Dashboard aggregates operational summary correctly"""
        dashboard = self.env['medical.manager.dashboard'].create({
            'name': 'Test Manager Dashboard',
            'company_id': self.env.company.id,
        })
        dashboard.action_refresh()

        self.assertGreaterEqual(dashboard.kpi_appointments_today, 0)
        self.assertIn("Medical Center Executive Operations", dashboard.dashboard_html)

    def test_appointment_calendar_time_slotting_and_synchronization(self):
        """
        Verify that appointments appear on exact time slots in the calendar rather than all-day header:
        1. appointment_datetime_start and appointment_datetime_end are exact datetimes matching start_time and end_time.
        2. Calendar view arch utilizes appointment_datetime_start and appointment_datetime_end.
        3. Inverse methods update appointment_date, start_time, duration when dragged on calendar.
        4. default_get pre-fills appointment_date and start_time when clicking on a calendar time slot.
        """
        future_date = date.today() + timedelta(days=6)
        # Create appointment at 10:30 with 1.5h duration (10:30 to 12:00)
        apt = self.env['medical.appointment'].create({
            'partner_id': self.patient.id,
            'doctor_id': self.doctor_emp.id,
            'service_ids': [(6, 0, [self.service.id])],
            'appointment_date': future_date,
            'start_time': 10.5,
            'duration': 1.5,
            'status': 'confirmed',
        })

        # 1. Verify exact datetime computation
        self.assertTrue(apt.appointment_datetime_start, "Start datetime must be computed")
        self.assertTrue(apt.appointment_datetime_end, "End datetime must be computed")

        tz = apt._get_medical_center_tz()
        utc_start = pytz.UTC.localize(apt.appointment_datetime_start)
        local_start = utc_start.astimezone(tz)

        self.assertEqual(local_start.date(), future_date)
        self.assertEqual(local_start.hour, 10)
        self.assertEqual(local_start.minute, 30)

        utc_end = pytz.UTC.localize(apt.appointment_datetime_end)
        local_end = utc_end.astimezone(tz)
        self.assertEqual(local_end.hour, 12)
        self.assertEqual(local_end.minute, 0)

        # 2. Verify Calendar View configuration
        cal_view = self.env.ref('medical_appointment_management.view_medical_appointment_calendar')
        self.assertIn('date_start="appointment_datetime_start"', cal_view.arch)
        self.assertIn('date_stop="appointment_datetime_end"', cal_view.arch)

        # 3. Simulate dragging on calendar (updating appointment_datetime_start via write)
        new_local_start = datetime.combine(future_date, datetime.min.time()).replace(hour=14, minute=0)
        new_utc_start = tz.localize(new_local_start).astimezone(pytz.UTC).replace(tzinfo=None)
        apt.write({'appointment_datetime_start': new_utc_start})

        self.assertEqual(apt.start_time, 14.0, "start_time must update to 14.0 upon calendar drag")
        self.assertEqual(apt.end_time, 15.5, "end_time must reflect updated start_time + duration")

        # 4. Simulate clicking on calendar slot (default_get with context)
        click_dt = new_utc_start
        defaults = self.env['medical.appointment'].with_context(
            default_appointment_datetime_start=fields.Datetime.to_string(click_dt)
        ).default_get(['appointment_date', 'start_time', 'duration'])
        self.assertEqual(defaults.get('appointment_date'), future_date)
        self.assertEqual(defaults.get('start_time'), 14.0)

    def test_manager_subordinate_hierarchy_and_admin_override(self):
        """
        Verify role-based hierarchical visibility and override:
        1. Doctor Manager can see appointments of doctors reporting to them.
        2. Regular Doctor cannot see appointments of other doctors.
        3. Sales Manager can see CRM leads and booked appointments of sales reps reporting to them.
        4. Regular Sales Rep cannot see leads of other sales reps.
        5. System Admin / Owner has unrestricted access to all appointments with override capability.
        """
        group_doc_mgr = self.env.ref('medical_employee_management.group_medical_doctor_manager')
        group_sales_mgr = self.env.ref('medical_employee_management.group_medical_sales_manager')

        # 1. Create Doctor Manager
        doc_mgr_user = self.env['res.users'].create({
            'name': 'Dr. Chief Manager',
            'login': 'chief_doc_mgr@test.clinic',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id, group_doc_mgr.id])],
        })
        doc_mgr_emp = self.env['hr.employee'].create({
            'name': 'Dr. Chief Manager',
            'medical_employee_type': 'doctor',
            'is_medical_manager': True,
            'is_appointment_provider': True,
            'user_id': doc_mgr_user.id,
        })

        # Set self.doctor_emp's manager to doc_mgr_emp
        self.doctor_emp.parent_id = doc_mgr_emp.id

        # Create appointment for self.doctor_emp
        future_date = date.today() + timedelta(days=5)
        sub_apt = self.env['medical.appointment'].create({
            'partner_id': self.patient.id,
            'doctor_id': self.doctor_emp.id,
            'service_ids': [(6, 0, [self.service.id])],
            'appointment_date': future_date,
            'start_time': 10.0,
            'duration': 1.0,
            'status': 'confirmed',
        })

        # Doctor Manager searches appointments -> can see sub_apt
        mgr_apts = self.env['medical.appointment'].with_user(doc_mgr_user).search([('id', '=', sub_apt.id)])
        self.assertEqual(len(mgr_apts), 1, "Doctor Manager must see appointments of subordinate doctors reporting to them")

        # Independent regular doctor cannot see sub_apt
        other_doc_user = self.env['res.users'].create({
            'name': 'Dr. Independent Other',
            'login': 'other_doc@test.clinic',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id, self.group_doctor.id])],
        })
        self.env['hr.employee'].create({
            'name': 'Dr. Independent Other',
            'medical_employee_type': 'doctor',
            'is_appointment_provider': True,
            'user_id': other_doc_user.id,
        })
        other_apts = self.env['medical.appointment'].with_user(other_doc_user).search([('id', '=', sub_apt.id)])
        self.assertEqual(len(other_apts), 0, "Regular doctor must NOT see appointments of other doctors")

        # 2. Sales Manager Hierarchy
        sales_mgr_user = self.env['res.users'].create({
            'name': 'Sales Head Frank',
            'login': 'sales_head_frank@test.clinic',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id, group_sales_mgr.id])],
        })
        sales_mgr_emp = self.env['hr.employee'].create({
            'name': 'Sales Head Frank',
            'medical_employee_type': 'sales',
            'is_medical_manager': True,
            'user_id': sales_mgr_user.id,
        })
        self.sales_emp.parent_id = sales_mgr_emp.id

        # Subordinate lead assigned to self.sales_user / self.sales_emp
        sub_lead = self.env['crm.lead'].create({
            'name': 'Subordinate VIP Inquiry',
            'partner_name': 'Subordinate Patient',
            'user_id': self.sales_user.id,
            'medical_staff_id': self.sales_emp.id,
        })

        # Sales Manager can see subordinate lead
        mgr_leads = self.env['crm.lead'].with_user(sales_mgr_user).search([('id', '=', sub_lead.id)])
        self.assertEqual(len(mgr_leads), 1, "Sales Manager must see leads assigned to subordinate sales reps")

        # Another independent regular sales rep cannot see sub_lead
        other_sales_user = self.env['res.users'].create({
            'name': 'Other Sales Rep Tim',
            'login': 'other_sales_tim@test.clinic',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id, self.group_sales.id])],
        })
        other_sales_leads = self.env['crm.lead'].with_user(other_sales_user).search([('id', '=', sub_lead.id)])
        self.assertEqual(len(other_sales_leads), 0, "Regular sales rep must NOT see leads of other sales reps")

        # 3. System Admin / Owner Full Visibility
        admin_user = self.env.ref('base.user_admin')
        admin_apts = self.env['medical.appointment'].with_user(admin_user).search([('id', '=', sub_apt.id)])
        self.assertEqual(len(admin_apts), 1, "System Admin must see all appointments")
        admin_leads = self.env['crm.lead'].with_user(admin_user).search([('id', '=', sub_lead.id)])
        self.assertEqual(len(admin_leads), 1, "System Admin must see all CRM leads")
