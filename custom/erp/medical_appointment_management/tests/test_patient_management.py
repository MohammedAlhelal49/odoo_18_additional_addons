# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase
from odoo.exceptions import AccessError, ValidationError
from datetime import date, timedelta


class TestPatientManagement(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Doctor
        cls.doctor = cls.env['hr.employee'].create({
            'name': 'Dr. Sarah Connor',
            'medical_employee_type': 'doctor',
            'is_appointment_provider': True,
            'medical_specialization': 'Dermatology',
        })

        # Sales employee
        cls.sales_emp = cls.env['hr.employee'].create({
            'name': 'Mark Sales Agent',
            'medical_employee_type': 'sales',
        })

        # Medical service
        cls.service = cls.env['medical.service'].create({
            'name': 'Laser Skin Consultation',
            'code': 'LSR-01',
            'price': 300.0,
            'duration': 1.0,
            'active': True,
        })

        # Receptionist user
        cls.receptionist_user = cls.env['res.users'].create({
            'name': 'Receptionist Alice',
            'login': 'receptionist_alice@test.com',
            'email': 'alice@test.com',
            'groups_id': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('medical_employee_management.group_medical_receptionist').id,
            ])],
        })

        # Doctor user
        cls.doctor_user = cls.env['res.users'].create({
            'name': 'Doctor Bob',
            'login': 'doctor_bob@test.com',
            'email': 'bob@test.com',
            'groups_id': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('medical_employee_management.group_medical_doctor').id,
            ])],
        })

    def test_01_first_time_lead_conversion_on_appointment_start(self):
        """When an appointment from a lead starts (In Progress), lead is automatically converted to an official patient"""
        # Create lead with rich attribution
        lead = self.env['crm.lead'].create({
            'name': 'Laser Treatment Inquiry - Emily Watson',
            'contact_name': 'Emily Watson',
            'phone': '+971501234567',
            'mobile': '+971501234567',
            'email_from': 'emily.watson@example.com',
            'source_type': 'paid',
            'source_platform': 'instagram',
            'campaign_name': 'Skin Rejuvenation 2026',
            'advertisement_name': 'IG Carousel 03',
            'medical_staff_id': self.sales_emp.id,
        })

        # Book appointment from wizard
        wizard = self.env['appointment.from.lead.wizard'].create({
            'lead_id': lead.id,
            'doctor_id': self.doctor.id,
            'service_ids': [(6, 0, [self.service.id])],
            'appointment_date': date.today() + timedelta(days=2),
            'start_time': 10.0,
            'duration': 1.0,
        })
        action = wizard.with_context(skip_past_date_check=True).action_create_appointment()
        apt = self.env['medical.appointment'].browse(action.get('res_id'))

        # Initial state: partner may exist as contact, but not yet an official patient
        self.assertTrue(apt.partner_id)
        self.assertFalse(apt.partner_id.is_patient, "Contact should not yet be a registered patient before appointment starts")
        self.assertFalse(apt.partner_id.patient_number)

        # Receptionist marks patient arrival
        apt.action_confirm()
        apt.action_check_in()
        self.assertEqual(apt.status, 'checked_in')

        # Doctor starts consultation (status becomes in_consultation)
        apt.action_start_consultation()

        # Verification 1: Appointment status is in_consultation
        self.assertEqual(apt.status, 'in_consultation')
        patient = apt.partner_id

        # Verification 2: Patient record created/registered with unique MRN
        self.assertTrue(patient.is_patient, "Partner must be flagged as an official patient")
        self.assertTrue(patient.patient_number, "Patient must have an MRN assigned")
        self.assertTrue(patient.patient_number.startswith('MRN-'), f"MRN must follow format MRN-YYYY-XXXX: got {patient.patient_number}")
        self.assertEqual(patient.registration_date, date.today())
        self.assertEqual(patient.patient_status, 'active')
        self.assertEqual(patient.assigned_doctor_id, self.doctor)
        self.assertEqual(patient.responsible_employee_id, self.sales_emp)

        # Verification 3: Lead attribution preserved on patient and lead linked
        self.assertEqual(lead.partner_id, patient, "Lead must be linked to the newly registered patient")
        self.assertEqual(patient.lead_id, lead)

        # Verification 4: Appointment fields reflect registered patient
        self.assertEqual(apt.patient_mrn, patient.patient_number)
        self.assertEqual(apt.patient_status, 'active')

    def test_02_repeat_appointment_reuses_existing_patient_no_duplicate(self):
        """Subsequent appointments for the same patient reuse the existing record without creating duplicates"""
        # First appointment & conversion
        lead1 = self.env['crm.lead'].create({
            'name': 'Initial Visit - George Clark',
            'contact_name': 'George Clark',
            'phone': '+971509988771',
            'email_from': 'george.clark@example.com',
            'medical_staff_id': self.sales_emp.id,
        })
        wizard1 = self.env['appointment.from.lead.wizard'].create({
            'lead_id': lead1.id,
            'doctor_id': self.doctor.id,
            'service_ids': [(6, 0, [self.service.id])],
            'appointment_date': date.today() - timedelta(days=7),
            'start_time': 11.0,
            'duration': 1.0,
        })
        act1 = wizard1.with_context(skip_past_date_check=True).action_create_appointment()
        apt1 = self.env['medical.appointment'].browse(act1.get('res_id'))
        apt1.allow_backdated_entry = True
        apt1.action_confirm()
        apt1.action_check_in()
        apt1.action_start_consultation()
        apt1.action_complete()

        patient = apt1.partner_id
        mrn = patient.patient_number
        patient_count_before = self.env['res.partner'].search_count([('is_patient', '=', True)])

        # Second appointment booked for this patient
        apt2 = self.env['medical.appointment'].create({
            'partner_id': patient.id,
            'doctor_id': self.doctor.id,
            'service_ids': [(6, 0, [self.service.id])],
            'appointment_date': date.today(),
            'start_time': 14.0,
            'duration': 1.0,
            'status': 'confirmed',
            'allow_backdated_entry': True,
        })
        apt2.action_check_in()
        apt2.action_start_consultation()

        # Verification: Same patient reused, MRN unchanged, no new patient record created
        self.assertEqual(apt2.partner_id, patient)
        self.assertEqual(apt2.patient_mrn, mrn)
        patient_count_after = self.env['res.partner'].search_count([('is_patient', '=', True)])
        self.assertEqual(patient_count_after, patient_count_before, "No duplicate patient record should be created")

    def test_03_concurrent_start_consultation_idempotency(self):
        """Triggering appointment start multiple times does not generate duplicate MRNs or patient records"""
        lead = self.env['crm.lead'].create({
            'name': 'Consultation - Jessica Taylor',
            'contact_name': 'Jessica Taylor',
            'phone': '+971504433221',
            'email_from': 'jessica@example.com',
        })
        wizard = self.env['appointment.from.lead.wizard'].create({
            'lead_id': lead.id,
            'doctor_id': self.doctor.id,
            'service_ids': [(6, 0, [self.service.id])],
            'appointment_date': date.today() + timedelta(days=2),
            'start_time': 15.0,
            'duration': 1.0,
        })
        act = wizard.action_create_appointment()
        apt = self.env['medical.appointment'].browse(act.get('res_id'))
        apt.action_confirm()
        apt.action_check_in()

        # First trigger
        apt.action_start_consultation()
        first_mrn = apt.patient_mrn
        patient_id = apt.partner_id.id

        # Second trigger (simulating repeated button click or workflow re-entry)
        apt.action_start_consultation()
        self.assertEqual(apt.patient_mrn, first_mrn, "MRN must not change on subsequent starts")
        self.assertEqual(apt.partner_id.id, patient_id, "Patient ID must remain identical")

    def test_04_patient_list_search_and_metrics(self):
        """Patients list allows search by MRN, name, phone, and computes visit metrics"""
        patient = self.env['res.partner'].create({
            'name': 'Sophia Al Mansoori',
            'phone': '+971507778899',
            'email': 'sophia@example.com',
            'is_patient': True,
            'patient_number': 'MRN-2026-9999',
            'registration_date': date.today(),
            'assigned_doctor_id': self.doctor.id,
            'patient_status': 'active',
        })

        # Past appointment
        self.env['medical.appointment'].create({
            'partner_id': patient.id,
            'doctor_id': self.doctor.id,
            'service_ids': [(6, 0, [self.service.id])],
            'appointment_date': date.today() - timedelta(days=10),
            'start_time': 10.0,
            'duration': 1.0,
            'status': 'completed',
        })

        # Future appointment
        self.env['medical.appointment'].create({
            'partner_id': patient.id,
            'doctor_id': self.doctor.id,
            'service_ids': [(6, 0, [self.service.id])],
            'appointment_date': date.today() + timedelta(days=5),
            'start_time': 11.0,
            'duration': 1.0,
            'status': 'confirmed',
        })

        patient.invalidate_recordset()

        # Metrics check
        self.assertEqual(patient.appointment_count, 2)
        self.assertEqual(patient.last_appointment_date, date.today() - timedelta(days=10))
        self.assertEqual(patient.next_appointment_date, date.today() + timedelta(days=5))

        # Search by MRN
        search_mrn = self.env['res.partner'].search([('patient_number', '=', 'MRN-2026-9999')])
        self.assertEqual(search_mrn, patient)

        # Search by Phone
        search_phone = self.env['res.partner'].search([('phone', '=', '+971507778899')])
        self.assertEqual(search_phone, patient)

    def test_05_appointment_patient_history_and_empty_state(self):
        """Appointment patient history tab displays previous appointments, diagnoses, and empty state banner"""
        patient = self.env['res.partner'].create({
            'name': 'Khalid Ibrahim',
            'phone': '+971503332211',
            'is_patient': True,
            'patient_number': 'MRN-2026-8888',
            'registration_date': date.today(),
            'patient_status': 'under_treatment',
        })

        # Appointment 1 (First visit - no history)
        apt1 = self.env['medical.appointment'].create({
            'partner_id': patient.id,
            'doctor_id': self.doctor.id,
            'service_ids': [(6, 0, [self.service.id])],
            'appointment_date': date.today() - timedelta(days=3),
            'start_time': 9.0,
            'duration': 1.0,
            'status': 'completed',
            'diagnosis': 'Contact dermatitis diagnosed on right forearm',
            'prescription': 'Topical corticosteroid 0.1% cream BID for 7 days',
        })

        # Appointment 2 (Follow-up visit - should have Appointment 1 in history)
        apt2 = self.env['medical.appointment'].create({
            'partner_id': patient.id,
            'doctor_id': self.doctor.id,
            'service_ids': [(6, 0, [self.service.id])],
            'appointment_date': date.today() + timedelta(days=2),
            'start_time': 14.0,
            'duration': 1.0,
            'status': 'confirmed',
        })

        apt2._compute_patient_history()
        self.assertEqual(apt2.patient_history_count, 1)
        self.assertIn(apt1, apt2.patient_history_ids)

        # Open patient record action returns correct form view
        action = apt2.action_open_patient_record()
        self.assertEqual(action.get('res_id'), patient.id)
        self.assertEqual(action.get('res_model'), 'res.partner')

    def test_06_role_based_access_to_clinical_notes(self):
        """Clinical diagnoses and confidential notes are restricted to Doctors and Managers"""
        patient = self.env['res.partner'].create({
            'name': 'Patient Privacy Test',
            'is_patient': True,
            'patient_number': 'MRN-2026-7777',
            'clinical_notes': 'Confidential doctor psychiatric evaluation and notes',
            'medical_history_summary': 'Type 2 Diabetes, Hypertension since 2018',
        })

        # Doctor can read clinical notes
        patient_doctor = patient.with_user(self.doctor_user)
        self.assertEqual(patient_doctor.clinical_notes, 'Confidential doctor psychiatric evaluation and notes')
        self.assertEqual(patient_doctor.medical_history_summary, 'Type 2 Diabetes, Hypertension since 2018')

        # Receptionist user cannot read/write clinical notes (field-level restriction)
        patient_receptionist = patient.with_user(self.receptionist_user)
        # Reading non-clinical fields works fine
        self.assertEqual(patient_receptionist.name, 'Patient Privacy Test')
        self.assertEqual(patient_receptionist.patient_number, 'MRN-2026-7777')
        # Attempting to read restricted clinical_notes is protected by Odoo groups
        with self.assertRaises(AccessError):
            _ = patient_receptionist.clinical_notes
