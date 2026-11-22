# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from datetime import date, timedelta


class TestAppointmentBooking(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Doctor employee
        cls.doctor = cls.env['hr.employee'].create({
            'name': 'Dr. Marcus Vance',
            'medical_employee_type': 'doctor',
            'is_appointment_provider': True,
            'medical_specialization': 'Cardiology',
        })

        # Medical Service
        cls.service = cls.env['medical.service'].create({
            'name': 'Cardiology Consultation',
            'code': 'TEST-CARD',
            'price': 250.0,
            'discount': 10.0,
            'duration': 1.0,  # 1 hour
            'period_between_sessions': 14,
            'active': True,
        })

        # Patient partner
        cls.patient = cls.env['res.partner'].create({
            'name': 'David Miller',
            'phone': '+971559876543',
            'email': 'david.miller@example.com',
        })

        # CRM Lead
        cls.lead = cls.env['crm.lead'].create({
            'name': 'Consultation Inquiry - David Miller',
            'partner_id': cls.patient.id,
            'source_type': 'paid',
            'source_platform': 'instagram',
            'campaign_name': 'Heart Health Month',
            'advertisement_name': 'IG Story Ad 01',
            'medical_service_id': cls.service.id,
        })

    def test_book_appointment_from_lead_preserves_attribution(self):
        """Appointment created from lead preserves lead source, platform, campaign, ad, and partner"""
        target_date = date.today() + timedelta(days=5)
        wizard = self.env['appointment.from.lead.wizard'].create({
            'lead_id': self.lead.id,
            'partner_id': self.patient.id,
            'doctor_id': self.doctor.id,
            'service_id': self.service.id,
            'appointment_date': target_date,
            'start_time': 10.0,  # 10:00 AM
            'duration': 1.0,
            'notes': 'Patient requested morning slot',
        })
        wizard.action_create_appointment()

        appointment = self.env['medical.appointment'].search([('crm_lead_id', '=', self.lead.id)], limit=1)
        self.assertTrue(appointment, "Appointment record must exist")
        self.assertEqual(appointment.partner_id, self.patient)
        self.assertEqual(appointment.doctor_id, self.doctor)
        self.assertEqual(appointment.service_id, self.service)
        self.assertEqual(appointment.appointment_date, target_date)
        self.assertEqual(appointment.start_time, 10.0)
        self.assertEqual(appointment.end_time, 11.0)
        self.assertEqual(appointment.status, 'tentative')

        # Check attribution preservation
        self.assertEqual(appointment.source_type, 'paid')
        self.assertEqual(appointment.source_platform, 'instagram')
        self.assertEqual(appointment.campaign_name, 'Heart Health Month')
        self.assertEqual(appointment.advertisement_name, 'IG Story Ad 01')

        # Check lead links
        self.assertIn(appointment, self.lead.appointment_ids)
        self.assertEqual(self.lead.appointment_count, 1)

    def test_scheduling_conflict_blocking(self):
        """Overlapping appointments for the same doctor should be blocked by conflict engine"""
        target_date = date.today() + timedelta(days=6)

        # Booking 1: 09:00 - 10:00
        apt1 = self.env['medical.appointment'].create({
            'partner_id': self.patient.id,
            'doctor_id': self.doctor.id,
            'service_id': self.service.id,
            'appointment_date': target_date,
            'start_time': 9.0,
            'duration': 1.0,
            'status': 'confirmed',
        })
        self.assertFalse(apt1.has_conflict)

        # Booking 2 overlapping: 09:30 - 10:30 without override must fail
        with self.assertRaises(ValidationError) as ctx:
            self.env['medical.appointment'].create({
                'partner_id': self.patient.id,
                'doctor_id': self.doctor.id,
                'service_id': self.service.id,
                'appointment_date': target_date,
                'start_time': 9.5,
                'duration': 1.0,
                'status': 'tentative',
            })
        self.assertTrue("already booked" in str(ctx.exception) or "Conflict" in str(ctx.exception))

    def test_scheduling_conflict_override(self):
        """Authorized conflict override succeeds when reason is supplied"""
        target_date = date.today() + timedelta(days=7)

        # First booking
        self.env['medical.appointment'].create({
            'partner_id': self.patient.id,
            'doctor_id': self.doctor.id,
            'service_id': self.service.id,
            'appointment_date': target_date,
            'start_time': 14.0,
            'duration': 1.0,
            'status': 'confirmed',
        })

        # Overlap with override but missing reason must fail
        with self.assertRaises(ValidationError):
            self.env['medical.appointment'].create({
                'partner_id': self.patient.id,
                'doctor_id': self.doctor.id,
                'service_id': self.service.id,
                'appointment_date': target_date,
                'start_time': 14.5,
                'duration': 1.0,
                'conflict_override': True,
                'conflict_override_reason': '',  # Empty
            })

        # Overlap with valid reason succeeds and records approver
        apt2 = self.env['medical.appointment'].create({
            'partner_id': self.patient.id,
            'doctor_id': self.doctor.id,
            'service_id': self.service.id,
            'appointment_date': target_date,
            'start_time': 14.5,
            'duration': 1.0,
            'conflict_override': True,
            'conflict_override_reason': 'Emergency VIP follow-up approved by medical director',
        })
        self.assertTrue(apt2.conflict_override_by_id)

    def test_cancelled_appointment_does_not_block_slot(self):
        """A cancelled appointment should not prevent re-booking the slot"""
        target_date = date.today() + timedelta(days=8)
        apt1 = self.env['medical.appointment'].create({
            'partner_id': self.patient.id,
            'doctor_id': self.doctor.id,
            'service_id': self.service.id,
            'appointment_date': target_date,
            'start_time': 11.0,
            'duration': 1.0,
            'status': 'tentative',
        })
        apt1.write({
            'status': 'cancelled',
            'cancellation_reason': 'Patient had to travel abroad',
        })

        # Now booking the exact same time slot should succeed without conflict
        apt2 = self.env['medical.appointment'].create({
            'partner_id': self.patient.id,
            'doctor_id': self.doctor.id,
            'service_id': self.service.id,
            'appointment_date': target_date,
            'start_time': 11.0,
            'duration': 1.0,
            'status': 'tentative',
        })
        self.assertFalse(apt2.has_conflict)

    def test_status_workflow_and_audit_log(self):
        """Test status transitions (tentative -> confirmed -> completed) and audit logging"""
        target_date = date.today() + timedelta(days=9)
        apt = self.env['medical.appointment'].create({
            'partner_id': self.patient.id,
            'doctor_id': self.doctor.id,
            'service_id': self.service.id,
            'appointment_date': target_date,
            'start_time': 15.0,
            'duration': 1.0,
            'status': 'tentative',
        })

        # Confirm
        apt.action_confirm()
        self.assertEqual(apt.status, 'confirmed')

        # Complete
        apt.action_complete()
        self.assertEqual(apt.status, 'completed')
        self.assertTrue(apt.completed_date)

        # Audit trail must have recorded transitions
        self.assertGreaterEqual(len(apt.status_history_ids), 2)

    def test_session_interval_warning(self):
        """Clinical session interval warning triggers when booking sooner than period_between_sessions"""
        date1 = date.today() + timedelta(days=10)
        date2 = date1 + timedelta(days=5)  # Only 5 days later, but service requires 14 days!

        # First appointment confirmed
        self.env['medical.appointment'].create({
            'partner_id': self.patient.id,
            'doctor_id': self.doctor.id,
            'service_id': self.service.id,
            'appointment_date': date1,
            'start_time': 9.0,
            'duration': 1.0,
            'status': 'confirmed',
        })

        # Second appointment 5 days later
        apt2 = self.env['medical.appointment'].create({
            'partner_id': self.patient.id,
            'doctor_id': self.doctor.id,
            'service_id': self.service.id,
            'appointment_date': date2,
            'start_time': 11.0,
            'duration': 1.0,
            'status': 'tentative',
        })
        self.assertTrue(apt2.interval_warning, "Clinical warning should be populated")
        self.assertIn("14 days", apt2.interval_warning)

    def test_book_appointment_with_multiple_services_direct(self):
        """Appointment created with multiple services calculates combined price, duration, and commission"""
        service2 = self.env['medical.service'].create({
            'name': 'ECG Diagnostic Test',
            'code': 'TEST-ECG',
            'price': 100.0,
            'discount': 0.0,
            'duration': 0.5,
            'period_between_sessions': 7,
            'active': True,
        })

        target_date = date.today() + timedelta(days=8)
        # Service 1: 250 - 10% = 225.0, duration = 1.0 hr
        # Service 2: 100 - 0% = 100.0, duration = 0.5 hr
        # Total Price = 325.0, Total Duration = 1.5 hr
        apt = self.env['medical.appointment'].create({
            'partner_id': self.patient.id,
            'doctor_id': self.doctor.id,
            'service_ids': [(6, 0, [self.service.id, service2.id])],
            'appointment_date': target_date,
            'start_time': 10.0,
            'duration': 1.5,
            'commission_rate': 10.0,
        })

        self.assertEqual(len(apt.service_ids), 2)
        self.assertEqual(apt.service_id, self.service, "service_id should be synced to primary service")
        self.assertEqual(apt.service_price, 325.0, "Total service price must be the sum of all service net prices")
        self.assertEqual(apt.commission_amount, 32.5, "Commission must be 10% of 325.0")
        self.assertEqual(apt.end_time, 11.5)

    def test_book_appointment_with_multiple_services_from_wizard(self):
        """Booking wizard with multiple services calculates total price, duration, and creates multi-service appointment"""
        service2 = self.env['medical.service'].create({
            'name': 'Echocardiogram',
            'code': 'TEST-ECHO',
            'price': 300.0,
            'discount': 20.0,  # 300 - 20% = 240.0
            'duration': 1.0,
            'period_between_sessions': 30,
            'active': True,
        })

        target_date = date.today() + timedelta(days=9)
        wizard = self.env['appointment.from.lead.wizard'].create({
            'lead_id': self.lead.id,
            'partner_id': self.patient.id,
            'doctor_id': self.doctor.id,
            'service_ids': [(6, 0, [self.service.id, service2.id])],
            'appointment_date': target_date,
            'start_time': 14.0,
            'duration': 2.0,
        })

        # Service 1 net = 225.0, Service 2 net = 240.0 -> Total = 465.0
        self.assertEqual(wizard.total_service_price, 465.0)
        self.assertEqual(wizard.service_id, self.service)

        action = wizard.action_create_appointment()
        apt_id = action.get('res_id')
        apt = self.env['medical.appointment'].browse(apt_id)

        self.assertTrue(apt.exists())
        self.assertEqual(len(apt.service_ids), 2)
        self.assertIn(self.service, apt.service_ids)
        self.assertIn(service2, apt.service_ids)
        self.assertEqual(apt.service_price, 465.0)
        self.assertEqual(apt.duration, 2.0)
        self.assertEqual(apt.end_time, 16.0)

    def test_lead_assign_salesperson_from_medical_staff(self):
        """Assigning a medical staff employee or user to a lead synchronizes both and allows booking"""
        sales_group = self.env.ref('medical_employee_management.group_medical_sales')
        sales_user = self.env['res.users'].create({
            'name': 'Medical Sales Rep 1',
            'login': 'medical_sales_rep_1@example.com',
            'email': 'salesrep1@example.com',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id, sales_group.id])],
        })
        sales_emp = self.env['hr.employee'].search([('user_id', '=', sales_user.id)], limit=1)
        if not sales_emp:
            sales_emp = self.env['hr.employee'].create({
                'name': 'Sara Medical Sales',
                'medical_employee_type': 'sales',
                'user_id': sales_user.id,
            })
        else:
            sales_emp.write({'medical_employee_type': 'sales'})

        test_lead = self.env['crm.lead'].create({
            'name': 'Inquiry for Laser Treatment',
            'partner_id': self.patient.id,
            'medical_staff_id': sales_emp.id,
        })

        # Verification: user_id automatically synced to sales_user
        self.assertEqual(test_lead.user_id, sales_user, "Sales user must be auto-synced from medical staff employee")
        self.assertEqual(test_lead.medical_staff_id, sales_emp)

        # Book appointment from this lead
        wizard = self.env['appointment.from.lead.wizard'].create({
            'lead_id': test_lead.id,
            'partner_id': self.patient.id,
            'doctor_id': self.doctor.id,
            'service_ids': [(6, 0, [self.service.id])],
            'appointment_date': date.today() + timedelta(days=12),
            'start_time': 11.0,
            'duration': 1.0,
        })
        action = wizard.action_create_appointment()
        apt = self.env['medical.appointment'].browse(action.get('res_id'))

        self.assertEqual(apt.salesperson_id, sales_user, "Appointment salesperson must match lead medical sales user")
        self.assertEqual(apt.sales_employee_id, sales_emp, "Appointment sales employee must match lead medical staff")

    def test_lead_non_medical_salesperson_rejected(self):
        """Assigning a non-medical user as salesperson on a lead must be blocked by validation"""
        non_medical_user = self.env['res.users'].create({
            'name': 'Accounting User',
            'login': 'accounting_user_test@example.com',
            'email': 'accounting@example.com',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])],
        })

        with self.assertRaises(ValidationError):
            self.env['crm.lead'].create({
                'name': 'Invalid Salesperson Lead',
                'partner_id': self.patient.id,
                'user_id': non_medical_user.id,
            })

    def test_patient_arrival_auto_invoicing_and_payment_modal(self):
        """When patient arrives (check-in), invoice is automatically created and payment modal is returned"""
        apt = self.env['medical.appointment'].create({
            'partner_id': self.patient.id,
            'doctor_id': self.doctor.id,
            'service_ids': [(6, 0, [self.service.id])],
            'appointment_date': date.today(),
            'start_time': 10.0,
            'duration': 1.0,
            'status': 'confirmed',
            'allow_backdated_entry': True,
        })
        self.assertFalse(apt.invoice_id)
        self.assertEqual(apt.invoice_status, 'no')

        # Patient arrives at clinic
        pay_action = apt.action_check_in()

        # Appointment status is checked in
        self.assertEqual(apt.status, 'checked_in')
        # Invoice automatically created and posted
        self.assertTrue(apt.invoice_id, "Invoice must be automatically created upon check-in")
        self.assertEqual(apt.invoice_id.state, 'posted', "Invoice must be posted upon check-in")
        self.assertEqual(apt.invoice_id.move_type, 'out_invoice')
        self.assertEqual(apt.invoice_id.partner_id, self.patient)
        self.assertEqual(apt.invoice_status, 'posted')
        self.assertGreater(apt.invoice_amount, 0.0)

        # Payment modal action returned for immediate collection
        self.assertTrue(pay_action, "action_check_in should return payment wizard action")
        self.assertEqual(pay_action.get('res_model'), 'account.payment.register')

    def test_patient_arrival_one_click_cash_payment(self):
        """Patient arrival allows 1-click cash payment reconciliation"""
        # Ensure a cash journal exists
        cash_journal = self.env['account.journal'].search([
            ('type', '=', 'cash'),
            ('company_id', '=', self.env.company.id)
        ], limit=1)
        if not cash_journal:
            cash_account = self.env['account.account'].search([
                ('account_type', '=', 'asset_cash'),
                ('company_id', '=', self.env.company.id)
            ], limit=1)
            cash_journal = self.env['account.journal'].create({
                'name': 'Test Cash',
                'type': 'cash',
                'code': 'TCASH',
                'company_id': self.env.company.id,
                'default_account_id': cash_account.id if cash_account else False,
            })

        apt = self.env['medical.appointment'].create({
            'partner_id': self.patient.id,
            'doctor_id': self.doctor.id,
            'service_ids': [(6, 0, [self.service.id])],
            'appointment_date': date.today(),
            'start_time': 14.0,
            'duration': 1.0,
            'status': 'confirmed',
            'allow_backdated_entry': True,
        })

        apt.action_check_in()
        self.assertTrue(apt.invoice_id)
        self.assertEqual(apt.invoice_status, 'posted')

        # 1-Click Cash Direct Pay
        res = apt.action_pay_cash_direct()
        self.assertTrue(res)
        apt.invoice_id.invalidate_recordset()
        apt.invalidate_recordset()

        self.assertIn(apt.invoice_id.payment_state, ('paid', 'in_payment'))
        self.assertEqual(apt.invoice_status, 'paid')
        self.assertEqual(apt.invoice_residual, 0.0)



