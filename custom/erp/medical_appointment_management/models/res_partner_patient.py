# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import date


class ResPartnerPatient(models.Model):
    _inherit = 'res.partner'

    # Patient Identification & Metadata
    is_patient = fields.Boolean(
        string='Is Patient',
        default=False,
        index=True,
        tracking=True,
        help='Indicates whether this contact is an officially registered medical patient.'
    )
    patient_number = fields.Char(
        string='Medical Record Number (MRN)',
        readonly=True,
        copy=False,
        index=True,
        tracking=True,
        help='Unique Medical Record Number (MRN) assigned to this patient upon registration.'
    )
    registration_date = fields.Date(
        string='Registration Date',
        default=fields.Date.today,
        tracking=True,
        help='Date when this patient was registered in the medical center.'
    )
    patient_status = fields.Selection([
        ('active', 'Active'),
        ('under_treatment', 'Under Treatment'),
        ('follow_up', 'Under Follow-up'),
        ('discharged', 'Discharged'),
        ('inactive', 'Inactive'),
    ], string='Patient Status', default='active', tracking=True, index=True)

    # Provider & Staff Attribution
    assigned_doctor_id = fields.Many2one(
        'hr.employee',
        string='Assigned Doctor',
        domain="[('is_appointment_provider', '=', True)]",
        tracking=True,
        help='Primary or most recently assigned doctor responsible for this patient.'
    )
    responsible_employee_id = fields.Many2one(
        'hr.employee',
        string='Responsible Staff',
        domain="[('medical_employee_type', '!=', False)]",
        tracking=True,
        help='Medical staff employee who brought in or coordinates care for this patient.'
    )
    lead_id = fields.Many2one(
        'crm.lead',
        string='Originating CRM Lead',
        tracking=True,
        help='Initial CRM lead that resulted in this patient registration.'
    )
    source_type = fields.Selection(
        related='lead_id.source_type',
        string='Lead Source',
        readonly=True
    )
    source_platform = fields.Selection(
        related='lead_id.source_platform',
        string='Source Platform',
        readonly=True
    )
    campaign_name = fields.Char(
        related='lead_id.campaign_name',
        string='Campaign Name',
        readonly=True
    )
    advertisement_name = fields.Char(
        related='lead_id.advertisement_name',
        string='Advertisement Name',
        readonly=True
    )

    # Medical & Demographic Details
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ], string='Gender', tracking=True)
    date_of_birth = fields.Date(string='Date of Birth')
    blood_group = fields.Selection([
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ], string='Blood Group', tracking=True)
    allergies = fields.Text(string='Known Allergies', tracking=True)
    emergency_contact_name = fields.Char(string='Emergency Contact Name')
    emergency_contact_phone = fields.Char(string='Emergency Contact Phone')

    # Restricted Clinical Records (Doctors, Nurses & System Admins)
    clinical_notes = fields.Text(
        string='Confidential Clinical Notes',
        groups='medical_employee_management.group_medical_doctor,medical_employee_management.group_medical_nurse,base.group_system',
        help='Confidential doctor remarks, patient treatment background, or ongoing care directions.'
    )
    medical_history_summary = fields.Text(
        string='Past Medical History Summary',
        groups='medical_employee_management.group_medical_doctor,medical_employee_management.group_medical_nurse,base.group_system',
        help='Summary of pre-existing chronic conditions, surgeries, and family medical history.'
    )

    # Relational Fields
    appointment_ids = fields.One2many(
        'medical.appointment',
        'partner_id',
        string='Appointments'
    )
    appointment_count = fields.Integer(
        string='Appointment Count',
        compute='_compute_appointment_metrics',
        store=True
    )
    last_appointment_date = fields.Date(
        string='Last Appointment Date',
        compute='_compute_appointment_metrics',
        store=True,
        index=True
    )
    next_appointment_date = fields.Date(
        string='Next Appointment Date',
        compute='_compute_appointment_metrics',
        store=True,
        index=True
    )
    crm_lead_count = fields.Integer(
        string='CRM Leads Count',
        compute='_compute_crm_lead_count'
    )
    patient_history_ids = fields.One2many(
        'medical.patient.history',
        'patient_id',
        string='Patient History Timeline',
        readonly=True
    )

    @api.depends('appointment_ids.appointment_date', 'appointment_ids.status')
    def _compute_appointment_metrics(self):
        today = fields.Date.today()
        for partner in self:
            try:
                apts = partner.appointment_ids.filtered(lambda a: a.status != 'cancelled')
                partner.appointment_count = len(partner.appointment_ids)

                # Last appointment: latest appointment date <= today or in ('completed', 'in_consultation')
                past_apts = apts.filtered(
                    lambda a: (a.appointment_date and a.appointment_date <= today) or a.status in ('completed', 'in_consultation')
                )
                partner.last_appointment_date = max(past_apts.mapped('appointment_date')) if past_apts else False

                # Next appointment: earliest appointment date >= today with status in ('tentative', 'confirmed', 'checked_in')
                future_apts = apts.filtered(
                    lambda a: a.appointment_date and a.appointment_date >= today and a.status in ('tentative', 'confirmed', 'checked_in')
                )
                partner.next_appointment_date = min(future_apts.mapped('appointment_date')) if future_apts else False
            except Exception:
                # During module initialization, appointment table may not exist yet
                partner.appointment_count = 0
                partner.last_appointment_date = False
                partner.next_appointment_date = False

    def _compute_crm_lead_count(self):
        for partner in self:
            if hasattr(partner, 'crm_lead_ids'):
                partner.crm_lead_count = len(partner.sudo().crm_lead_ids)
            else:
                partner.crm_lead_count = self.env['crm.lead'].sudo().search_count([('partner_id', '=', partner.id)])

    def action_convert_to_patient(self, lead=None, doctor=None, employee=None):
        """
        Transactional, idempotent conversion of a partner/contact into an official patient.
        Ensures atomic MRN sequence generation without duplication.
        Preserves lead attribution (campaign, platform, source) and assigned staff.
        """
        self.ensure_one()
        if self.is_patient and self.patient_number:
            # Already registered patient
            return self

        mrn = self.patient_number or self.env['ir.sequence'].next_by_code('medical.patient.mrn')
        vals = {
            'is_patient': True,
            'patient_number': mrn,
            'registration_date': self.registration_date or fields.Date.today(),
            'patient_status': self.patient_status or 'active',
        }
        if doctor and not self.assigned_doctor_id:
            vals['assigned_doctor_id'] = doctor.id
        if employee and not self.responsible_employee_id:
            vals['responsible_employee_id'] = employee.id
        if lead and not self.lead_id:
            vals['lead_id'] = lead.id

            # Preserve lead attribution data if supported on partner
            for attr in ('source_type', 'source_platform', 'campaign_name', 'advertisement_name'):
                if hasattr(self, attr) and hasattr(lead, attr):
                    val = getattr(lead, attr)
                    if val and not getattr(self, attr):
                        vals[attr] = val

        self.sudo().write(vals)

        self.message_post(
            body=_("🎉 Contact officially registered as Medical Center Patient. Medical Record Number (MRN): <b>%s</b>.") % mrn
        )
        return self

    # Smart Button Actions
    def action_view_patient_appointments(self):
        """View all appointments for this patient"""
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('medical_appointment_management.action_medical_appointments')
        action['domain'] = [('partner_id', '=', self.id)]
        action['context'] = {
            'default_partner_id': self.id,
            'default_doctor_id': self.assigned_doctor_id.id if self.assigned_doctor_id else False,
        }
        return action

    def action_view_patient_leads(self):
        """View all CRM leads related to this patient"""
        self.ensure_one()
        action = self.env.ref('crm.crm_lead_action_pipeline').read()[0]
        action['domain'] = [('partner_id', '=', self.id)]
        action['context'] = {
            'default_partner_id': self.id,
            'active_model': 'res.partner',
            'active_id': self.id,
        }
        return action

    def action_book_new_appointment(self):
        """Open appointment booking wizard directly pre-populated for this patient"""
        self.ensure_one()
        return {
            'name': _('Book Appointment for %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'appointment.from.lead.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.id,
                'default_doctor_id': self.assigned_doctor_id.id if self.assigned_doctor_id else False,
                'default_appointment_date': fields.Date.today(),
            }
        }
