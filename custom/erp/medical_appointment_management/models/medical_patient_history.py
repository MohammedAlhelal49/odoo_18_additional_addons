# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class MedicalPatientHistory(models.Model):
    _name = 'medical.patient.history'
    _description = 'Patient Medical Interaction Timeline'
    _auto = False
    _order = 'date desc, id desc'

    patient_id = fields.Many2one('res.partner', string='Patient', readonly=True)
    date = fields.Datetime(string='Date & Time', readonly=True)
    entry_type = fields.Selection([
        ('appointment', 'Appointment Booking'),
        ('consultation', 'Doctor Consultation'),
        ('call', 'Phone Call / Outreach'),
        ('lead', 'CRM Inquiry / Lead'),
        ('cancellation', 'Cancellation / No-Show'),
    ], string='Interaction Type', readonly=True)
    responsible_name = fields.Char(string='Responsible Staff / Doctor', readonly=True)
    doctor_id = fields.Many2one('hr.employee', string='Doctor', readonly=True)
    summary = fields.Char(string='Summary', readonly=True)
    clinical_details = fields.Text(
        string='Clinical Details & Diagnosis',
        readonly=True,
        groups='medical_employee_management.group_medical_doctor,medical_employee_management.group_medical_nurse,base.group_system'
    )
    status = fields.Char(string='Status', readonly=True)
    appointment_id = fields.Many2one('medical.appointment', string='Appointment', readonly=True)
    lead_id = fields.Many2one('crm.lead', string='CRM Lead', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)

        # Check if required tables exist before creating the view
        required_tables = ['medical_appointment', 'hr_employee', 'medical_service', 'crm_lead_call_log', 'crm_lead', 'crm_stage']
        for table in required_tables:
            self.env.cr.execute(f"""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_name = '{table}'
                )
            """)
            if not self.env.cr.fetchone()[0]:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Skipping medical_patient_history view creation: table '{table}' does not exist yet")
                return

        self.env.cr.execute(f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                -- 1. Appointments & Consultations
                SELECT
                    (apt.id * 10 + 1) AS id,
                    apt.partner_id AS patient_id,
                    (apt.appointment_date + (apt.start_time || ' hours')::interval) AS date,
                    CASE
                        WHEN apt.status IN ('in_consultation', 'completed') THEN 'consultation'
                        WHEN apt.status IN ('cancelled', 'no_show') THEN 'cancellation'
                        ELSE 'appointment'
                    END::varchar AS entry_type,
                    COALESCE(emp.name, 'Medical Staff')::varchar AS responsible_name,
                    apt.doctor_id AS doctor_id,
                    CONCAT('Appointment: ', apt.name, ' - ', COALESCE(srv.name, 'Medical Service'))::varchar AS summary,
                    CASE
                        WHEN apt.status IN ('cancelled', 'no_show') THEN CONCAT('Cancellation Reason: ', COALESCE(apt.cancellation_reason, 'None recorded'))
                        ELSE COALESCE(apt.diagnosis, apt.treatment_plan, apt.doctor_notes, '')
                    END::text AS clinical_details,
                    apt.status::varchar AS status,
                    apt.id AS appointment_id,
                    apt.crm_lead_id AS lead_id
                FROM medical_appointment apt
                LEFT JOIN hr_employee emp ON apt.doctor_id = emp.id
                LEFT JOIN medical_service srv ON apt.service_id = srv.id
                WHERE apt.partner_id IS NOT NULL

                UNION ALL

                -- 2. CRM Calls
                SELECT
                    (cl.id * 10 + 2) AS id,
                    cl.partner_id AS patient_id,
                    cl.call_date AS date,
                    'call'::varchar AS entry_type,
                    COALESCE(pu.name, u.login, 'Sales Caller')::varchar AS responsible_name,
                    NULL::integer AS doctor_id,
                    CONCAT('Phone Call: ', COALESCE(cl.outcome, 'Contacted'), CASE WHEN cl.notes IS NOT NULL THEN CONCAT(' - ', cl.notes) ELSE '' END)::varchar AS summary,
                    cl.notes::text AS clinical_details,
                    cl.outcome::varchar AS status,
                    NULL::integer AS appointment_id,
                    cl.lead_id AS lead_id
                FROM crm_lead_call_log cl
                LEFT JOIN res_users u ON cl.called_by_id = u.id
                LEFT JOIN res_partner pu ON u.partner_id = pu.id
                WHERE cl.partner_id IS NOT NULL

                UNION ALL

                -- 3. CRM Leads / Inquiries
                SELECT
                    (lead.id * 10 + 3) AS id,
                    lead.partner_id AS patient_id,
                    lead.create_date AS date,
                    'lead'::varchar AS entry_type,
                    COALESCE(pu.name, u.login, 'Lead Owner')::varchar AS responsible_name,
                    NULL::integer AS doctor_id,
                    CONCAT('CRM Lead / Inquiry: ', lead.name, CASE WHEN lead.campaign_name IS NOT NULL THEN CONCAT(' (Campaign: ', lead.campaign_name, ')') ELSE '' END)::varchar AS summary,
                    NULL::text AS clinical_details,
                    COALESCE(stg.name->>'en_US', stg.name::text, 'New')::varchar AS status,
                    NULL::integer AS appointment_id,
                    lead.id AS lead_id
                FROM crm_lead lead
                LEFT JOIN res_users u ON lead.user_id = u.id
                LEFT JOIN res_partner pu ON u.partner_id = pu.id
                LEFT JOIN crm_stage stg ON lead.stage_id = stg.id
                WHERE lead.partner_id IS NOT NULL
            )
        """)
