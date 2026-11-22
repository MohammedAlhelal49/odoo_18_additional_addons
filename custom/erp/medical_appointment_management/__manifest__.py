{
    'name': 'Medical Center Appointment Management',
    'version': '18.0.1.0',
    'category': 'Healthcare/Appointments',
    'sequence': 27,
    'summary': 'Clinical appointment lifecycle with role-based workflow (Sales → Reception → Nurse → Doctor)',
    'description': """
Medical Center Appointment Management
======================================

Implements the complete appointment lifecycle for medical centers with multi-role workflow:

1. **Sales Representative**: Lead → Appointment Booking
   - Book appointment with doctor selection
   - Track appointment source (Lead attribution)
   - Commission tracking (pending on booking)

2. **Receptionist**: Confirmation → Check-in → Invoicing
   - Day-before confirmation calls
   - Patient check-in and arrival status
   - Automatic invoice generation
   - Cash/card payment integration
   - Commission tracking (pending on check-in)

3. **Triage Nurse**: Vitals Recording → Ready for Doctor
   - Patient vitals (BP, temp, SpO2, BMI, blood sugar)
   - Triage notes and observations
   - Mark ready for doctor
   - Commission tracking (pending on ready)

4. **Physician/Doctor**: Consultation → Completion
   - Start consultation (auto-generate MRN, convert lead to patient)
   - Clinical findings and diagnosis
   - Prescriptions and treatment plan
   - Follow-up scheduling
   - Complete consultation (finalize commissions)

5. **Commission Accounting**:
   - Sales commission (5% on booking)
   - Reception fee (on check-in)
   - Nurse triage fee (on ready for doctor)
   - Doctor provider fee (on completion)
   - Auto-settlement tracking

Features:
* Multi-status appointment lifecycle
* Appointment conflict checking
* Automated lead-to-patient conversion on consultation start
* Medical record number (MRN) generation
* Vitals and biometrics tracking with auto-calculations
* Commission lifecycle management
* Activity notifications at each handoff
* Audit trail for all status changes
    """,
    'author': 'Medical Center',
    'website': 'https://www.medical-center.example.com',
    'depends': [
        'hr',
        'resource',
        'calendar',
        'crm',
        'sale',
        'account',
        'medical_employee_management',
        'medical_crm_lead_extension',
    ],
    'data': [
        'security/appointment_groups.xml',
        'security/ir.model.access.csv',
        'security/appointment_record_rules.xml',
        'data/appointment_status_data.xml',
        'data/appointment_sequences.xml',
        'wizard/appointment_from_lead_wizard_views.xml',
        'wizard/crm_lead_log_call_wizard_views.xml',
        'wizard/medical_appointment_cancel_wizard_views.xml',
        'wizard/medical_appointment_reschedule_wizard_views.xml',
        'views/crm_lead_call_log_views.xml',
        'views/crm_lead_views_appointment.xml',
        'views/medical_service_views.xml',
        'views/medical_appointment_views.xml',
        'views/medical_appointment_document_views.xml',
        'views/medical_patient_views.xml',
        'views/res_config_settings_views.xml',
        'report/medical_staff_performance_report_templates.xml',
        'views/medical_staff_target_views.xml',
        'views/medical_staff_performance_views.xml',
        'views/medical_appointment_menus.xml',
        'views/medical_dashboard_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'post_init_hook': 'post_init_hook',
}
