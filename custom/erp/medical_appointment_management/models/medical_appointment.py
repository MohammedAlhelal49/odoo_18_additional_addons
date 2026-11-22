from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, date, time, timedelta
import pytz


class MedicalAppointment(models.Model):
    _name = 'medical.appointment'
    _description = 'Medical Center Appointment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'appointment_date DESC, appointment_time DESC'

    # Core Identifiers
    name = fields.Char(
        string='Appointment ID',
        readonly=True,
        copy=False,
        tracking=True,
        help='Unique appointment reference'
    )

    # Patient / Lead Information
    patient_id = fields.Many2one(
        'res.partner',
        string='Patient',
        domain=[('is_patient', '=', True)],
        required=True,
        tracking=True,
        help='Patient/customer record'
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Patient / Partner',
        related='patient_id',
        readonly=False,
        store=True
    )

    lead_id = fields.Many2one(
        'crm.lead',
        string='Source Lead',
        readonly=True,
        help='CRM lead that generated this appointment'
    )

    crm_lead_id = fields.Many2one(
        'crm.lead',
        string='Source CRM Lead',
        related='lead_id',
        readonly=False,
        store=True
    )

    # Patient History
    patient_history_ids = fields.Many2many(
        'medical.appointment',
        compute='_compute_patient_history',
        string='Previous Appointments'
    )
    patient_history_count = fields.Integer(
        compute='_compute_patient_history',
        string='History Count'
    )

    @api.depends('patient_id', 'partner_id', 'appointment_date')
    def _compute_patient_history(self):
        for rec in self:
            patient = rec.patient_id or rec.partner_id
            if patient:
                origin_id = rec._origin.id if hasattr(rec, '_origin') and rec._origin else (rec.id or 0)
                domain = [
                    ('id', '!=', origin_id),
                    '|',
                    ('patient_id', '=', patient.id),
                    ('partner_id', '=', patient.id),
                ]
                if rec.appointment_date:
                    domain.append(('appointment_date', '<=', rec.appointment_date))
                history = self.env['medical.appointment'].search(domain, order='appointment_date desc, id desc')
                rec.patient_history_ids = history
                rec.patient_history_count = len(history)
            else:
                rec.patient_history_ids = False
                rec.patient_history_count = 0

    def action_open_patient_record(self):
        """Open the patient's full medical record card and interaction history"""
        self.ensure_one()
        patient = self.sudo().patient_id or self.sudo().partner_id
        if not patient:
            raise UserError(_("No patient is linked to this appointment."))
        return {
            'name': _('Patient Medical Record: %s') % patient.name,
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'res_id': patient.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'form_view_ref': 'medical_appointment_management.view_medical_patient_form',
                'default_is_patient': True,
            }
        }

    def _default_doctor_id(self):
        emp = self.env['hr.employee'].search([
            ('user_id', '=', self.env.user.id),
            ('medical_employee_type', '=', 'doctor')
        ], limit=1)
        return emp.id if emp else False

    # Medical Provider
    doctor_id = fields.Many2one(
        'hr.employee',
        string='Doctor / Provider',
        domain=[('medical_employee_type', '=', 'doctor')],
        default=lambda self: self._default_doctor_id(),
        required=True,
        tracking=True,
        help='Doctor assigned to this appointment'
    )

    doctor_user_id = fields.Many2one(
        'res.users',
        related='doctor_id.user_id',
        store=True,
        readonly=True,
        help='User account of assigned doctor'
    )

    # Medical Service / Specialization
    medical_service = fields.Char(
        string='Medical Service / Specialization',
        help='Type of service requested (e.g., Cardiology, Dentistry)'
    )

    service_id = fields.Many2one(
        'medical.service',
        string='Medical Service (Catalog)',
        help='Selected service from the medical services catalog'
    )

    service_ids = fields.Many2many(
        'medical.service',
        'medical_appointment_service_rel',
        'appointment_id',
        'service_id',
        string='Medical Services (Catalog)',
        help='Selected services from the medical services catalog'
    )

    notes = fields.Text(string='Internal Notes')
    special_requirements = fields.Text(string='Special Patient Requirements')

    calendar_display = fields.Char(
        string='Calendar Display',
        compute='_compute_calendar_display',
        store=True,
        help='Formatted display for calendar view: Time | Service | Patient'
    )

    @api.depends('start_time', 'appointment_time', 'service_id', 'medical_service', 'patient_id')
    def _compute_calendar_display(self):
        for appointment in self:
            time_str = ''
            if appointment.start_time:
                hours = int(appointment.start_time)
                minutes = round((appointment.start_time - hours) * 60)
                time_str = f"{hours:02d}:{minutes:02d}"
            elif appointment.appointment_time:
                hours = int(appointment.appointment_time)
                minutes = round((appointment.appointment_time - hours) * 60)
                time_str = f"{hours:02d}:{minutes:02d}"

            service_str = appointment.medical_service or (appointment.service_id.name if appointment.service_id else 'No Service')
            patient_str = appointment.patient_id.name if appointment.patient_id else 'No Patient'

            appointment.calendar_display = f"{time_str} | {service_str} | {patient_str}"

    @api.onchange('service_id')
    def _onchange_service_id(self):
        if self.service_id:
            self.medical_service = self.service_id.name
            if self.service_id not in self.service_ids:
                self.service_ids = [(4, self.service_id.id)]
            if self.service_id.duration:
                self.estimated_duration = self.service_id.duration
                self.duration = self.service_id.duration
            if self.service_id.final_price or self.service_id.price:
                self.appointment_total = self.service_id.final_price or self.service_id.price

    @api.onchange('service_ids')
    def _onchange_service_ids(self):
        if self.service_ids and not self.service_id:
            self.service_id = self.service_ids[0]
            self.medical_service = self.service_ids[0].name


    # Appointment Schedule
    appointment_date = fields.Date(
        string='Appointment Date',
        required=True,
        tracking=True,
        help='Date of the appointment'
    )

    start_time = fields.Float(string="Start Time (hours)", help="Appointment start time in decimal hours")

    appointment_time = fields.Float(
        string='Appointment Time',
        help='Time in decimal hours (e.g., 14.5 = 2:30 PM)'
    )

    estimated_duration = fields.Float(
        string='Estimated Duration (hours)',
        default=1.0,
        help='Expected consultation duration'
    )

    duration = fields.Float(
        string='Duration (hours)',
        related='estimated_duration',
        readonly=False,
        store=True
    )

    end_time = fields.Float(
        string='End Time (hours)',
        compute='_compute_end_time',
        store=True,
        help='Computed appointment end time in decimal hours'
    )

    appointment_datetime_start = fields.Datetime(
        string='Start Datetime',
        compute='_compute_appointment_datetimes',
        inverse='_inverse_appointment_datetime_start',
        store=True,
        index=True,
        help='Exact start timestamp in UTC synchronized with appointment_date and start_time'
    )

    appointment_datetime_end = fields.Datetime(
        string='End Datetime',
        compute='_compute_appointment_datetimes',
        inverse='_inverse_appointment_datetime_end',
        store=True,
        index=True,
        help='Exact end timestamp in UTC synchronized with appointment_date, start_time, and duration'
    )

    # Appointment Status Lifecycle
    status = fields.Selection([
        ('draft', 'Draft'),
        ('tentative', 'Tentative (Booked)'),
        ('confirmed', 'Confirmed'),
        ('checked_in', 'Checked In'),
        ('ready_for_doctor', 'Ready for Doctor'),
        ('in_consultation', 'In Consultation'),
        ('completed', 'Completed'),
        ('no_show', 'No Show'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='tentative', required=True, tracking=True)

    cancellation_reason = fields.Text(string='Cancellation Reason', tracking=True)

    # Dynamic Edit Lock Flags
    is_started = fields.Boolean(
        string='Is Started',
        compute='_compute_time_and_status_flags',
        search='_search_is_started',
        help='Indicates whether this appointment has started (by time or clinical status).'
    )
    is_time_passed = fields.Boolean(
        string='Is Time Passed',
        compute='_compute_time_and_status_flags',
        search='_search_is_time_passed',
        help='Indicates whether this appointment scheduled time has passed.'
    )

    # Role-Based Action Visibility & Time Windows
    can_doctor_start_consultation = fields.Boolean(
        compute='_compute_doctor_action_permissions',
        help='Doctor can start consultation (within 5 mins of appointment time)'
    )
    can_doctor_complete_consultation = fields.Boolean(
        compute='_compute_doctor_action_permissions',
        help='Doctor can complete consultation (after appointment time)'
    )
    can_receptionist_confirm = fields.Boolean(
        compute='_compute_receptionist_action_permissions',
        help='Receptionist can confirm (day before appointment)'
    )
    can_receptionist_checkin = fields.Boolean(
        compute='_compute_receptionist_action_permissions',
        help='Receptionist can check in (within 15 mins before appointment)'
    )
    can_nurse_mark_ready = fields.Boolean(
        compute='_compute_nurse_action_permissions',
        help='Nurse can mark ready (within 5 mins of appointment time)'
    )
    can_reschedule = fields.Boolean(
        compute='_compute_can_reschedule',
        help='Can reschedule (tentative/confirmed and not started/passed)'
    )
    minutes_remaining = fields.Integer(
        compute='_compute_minutes_remaining',
        help='Minutes until appointment starts (negative if past)'
    )
    appointment_status_display = fields.Char(
        compute='_compute_appointment_status_display',
        help='Real-time appointment countdown display'
    )
    action_message = fields.Char(
        compute='_compute_action_messages',
        help='Message to show user actions available or upcoming'
    )

    # Attribution & Tracking
    created_by_sales = fields.Many2one(
        'res.users',
        string='Sales Rep (Booked By)',
        default=lambda self: self.env.user,
        readonly=True,
        help='Sales representative who booked the appointment'
    )

    source_type = fields.Selection([
        ('paid', 'Paid Ads'),
        ('organic', 'Organic'),
        ('referral', 'Referral'),
        ('direct', 'Direct'),
        ('offline', 'Offline'),
        ('unknown', 'Unknown'),
    ], string='Source Type', default='unknown', help='Lead attribution source')

    marketing_platform = fields.Char(
        string='Marketing Platform',
        help='Platform source (Facebook, Google Ads, WhatsApp, etc.)'
    )

    campaign_name = fields.Char(string='Campaign Name')
    advertisement_name = fields.Char(string='Advertisement Name')

    sales_employee_id = fields.Many2one(
        'hr.employee',
        string='Sales Employee',
        domain="[('medical_employee_type', '=', 'sales')]",
        help='Medical staff employee who booked the lead/appointment'
    )

    salesperson_id = fields.Many2one(
        'res.users',
        string='Salesperson',
        related='created_by_sales',
        readonly=False,
        store=True
    )

    source_platform = fields.Char(
        string='Source Platform',
        related='marketing_platform',
        readonly=False,
        store=True
    )

    # Conflict Overrides
    conflict_override = fields.Boolean(
        string='Override Conflict',
        default=False,
        tracking=True,
        help='Flag set when scheduling conflict was supervisor-approved'
    )
    conflict_override_reason = fields.Text(
        string='Conflict Override Reason',
        tracking=True,
        help='Clinical justification or reason for overriding schedule conflict'
    )

    # Reception & Check-in
    confirmation_call_status = fields.Selection([
        ('pending', 'Pending Confirmation'),
        ('confirmed', 'Confirmed'),
        ('unable_to_reach', 'Unable to Reach'),
        ('declined', 'Declined'),
        ('rescheduled', 'Rescheduling Required'),
    ], string='Confirmation Status', tracking=True)

    checked_in_date = fields.Datetime(
        string='Check-in Time',
        readonly=True,
        help='When patient arrived'
    )

    checked_in_by = fields.Many2one(
        'res.users',
        string='Checked In By',
        readonly=True,
        help='Receptionist who checked in patient'
    )
    receptionist_id = fields.Many2one(
        'hr.employee',
        string='Receptionist',
        domain="[('medical_employee_type', '=', 'receptionist')]",
        tracking=True,
        help='Receptionist who checked in or managed this appointment'
    )

    # Nurse Vitals (Triage)
    vital_blood_pressure_systolic = fields.Integer(string='BP Systolic (mmHg)')
    vital_blood_pressure_diastolic = fields.Integer(string='BP Diastolic (mmHg)')
    vital_temperature = fields.Float(string='Temperature (°C)')
    vital_heart_rate = fields.Integer(string='Heart Rate (bpm)')
    vital_respiratory_rate = fields.Integer(string='Respiratory Rate (bpm)')
    vital_oxygen_saturation = fields.Float(string='O2 Saturation (SpO2 %)')
    vital_height = fields.Float(string='Height (cm)')
    vital_weight = fields.Float(string='Weight (kg)')
    vital_bmi = fields.Float(string='Body Mass Index (BMI)', compute='_compute_bmi', store=True)
    vital_blood_sugar = fields.Float(string='Blood Sugar (mg/dL)')

    nurse_notes = fields.Text(string='Nurse Triage Notes')
    vitals_recorded_by = fields.Many2one(
        'res.users',
        string='Vitals Recorded By',
        readonly=True,
        help='Nurse who recorded vitals'
    )
    nurse_id = fields.Many2one(
        'hr.employee',
        string='Triage Nurse',
        domain="[('medical_employee_type', '=', 'nurse')]",
        tracking=True,
        help='Nurse who recorded vitals / triaged the patient'
    )

    # Clinical Documentation (Doctor)
    diagnosis = fields.Text(string='Diagnosis & Clinical Findings')
    prescription = fields.Text(string='Prescriptions & Medications')
    treatment_plan = fields.Text(string='Treatment Plan & Instructions')
    doctor_notes = fields.Text(string='Doctor Notes (Confidential)')

    consultation_started_date = fields.Datetime(
        string='Consultation Started',
        readonly=True
    )

    consultation_completed_date = fields.Datetime(
        string='Consultation Completed',
        readonly=True
    )

    # Medical Record Number (Auto-generated on consultation start)
    mrn = fields.Char(
        string='Medical Record Number (MRN)',
        readonly=True,
        copy=False,
        help='Unique patient medical record identifier'
    )

    # Follow-up Appointment
    followup_appointment_id = fields.Many2one(
        'medical.appointment',
        string='Follow-up Appointment',
        help='Next scheduled follow-up visit'
    )

    # Billing & Commission
    invoice_id = fields.Many2one(
        'account.move',
        string='Patient Invoice',
        readonly=True,
        help='Generated invoice for this appointment'
    )

    appointment_total = fields.Monetary(
        string='Appointment Total',
        currency_field='company_currency_id'
    )

    company_currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        store=True,
        readonly=True
    )

    # Commission Tracking
    commission_rate = fields.Float(
        string='Commission Rate (%)',
        default=5.0,
        help='Commission rate percentage applicable to this appointment'
    )

    commission_amount = fields.Monetary(
        string='Commission Amount',
        compute='_compute_commission_amount',
        store=True,
        currency_field='company_currency_id',
        help='Calculated total commission amount'
    )

    sales_commission_id = fields.Many2one(
        'medical.commission',
        string='Sales Commission',
        help='Commission record for sales representative'
    )

    reception_commission_id = fields.Many2one(
        'medical.commission',
        string='Reception Commission',
        help='Commission record for receptionist'
    )

    nurse_commission_id = fields.Many2one(
        'medical.commission',
        string='Nurse Commission',
        help='Commission record for triage nurse'
    )

    doctor_commission_id = fields.Many2one(
        'medical.commission',
        string='Doctor Commission',
        help='Commission record for doctor'
    )

    @api.depends('appointment_total', 'commission_rate')
    def _compute_commission_amount(self):
        for rec in self:
            rec.commission_amount = (rec.appointment_total or 0.0) * ((rec.commission_rate or 0.0) / 100.0)

    # Metadata
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )

    created_date = fields.Datetime(
        string='Created Date',
        default=fields.Datetime.now,
        readonly=True
    )

    # Documents
    document_ids = fields.One2many(
        'medical.appointment.document',
        'appointment_id',
        string='Documents',
        help='Prescription, lab reports, medical certificates, etc.'
    )

    @api.depends('vital_height', 'vital_weight')
    def _compute_bmi(self):
        for rec in self:
            if rec.vital_height > 0 and rec.vital_weight > 0:
                height_m = rec.vital_height / 100
                rec.vital_bmi = rec.vital_weight / (height_m ** 2)
            else:
                rec.vital_bmi = 0

    SCHEDULING_FIELDS = {
        'patient_id',
        'partner_id',
        'doctor_id',
        'service_id',
        'service_ids',
        'medical_service',
        'appointment_date',
        'appointment_time',
        'start_time',
        'estimated_duration',
        'duration',
        'lead_id',
        'crm_lead_id',
        'source_type',
        'source_platform',
        'marketing_platform',
        'campaign_name',
        'advertisement_name',
    }

    SYSTEM_INTERNAL_FIELDS = {
        'message_ids',
        'message_follower_ids',
        'activity_ids',
        'message_main_attachment_id',
        'access_token',
        'patient_history_ids',
        'patient_history_count',
    }

    @api.depends('status', 'appointment_date', 'appointment_time', 'start_time',
                 'duration', 'estimated_duration', 'appointment_datetime_start',
                 'appointment_datetime_end', 'consultation_started_date')
    def _compute_time_and_status_flags(self):
        now_utc = fields.Datetime.now()
        today = fields.Date.today()
        for apt in self:
            # 1. Started Check:
            # - Doctor has started consultation or appointment is completed
            # - Consultation started date set
            # - Scheduled start datetime is in the past
            # - Scheduled date is in the past
            started = False
            if apt.status in ('in_consultation', 'completed'):
                started = True
            elif apt.consultation_started_date:
                started = True
            elif apt.appointment_datetime_start and apt.appointment_datetime_start <= now_utc:
                started = True
            elif apt.appointment_date and apt.appointment_date < today:
                started = True
            apt.is_started = started

            # 2. Time Passed Check:
            # - Terminal status: completed, cancelled, no_show
            # - Scheduled end datetime is in the past (unless actively in consultation)
            # - Scheduled date is in the past (unless actively in consultation)
            time_passed = False
            if apt.status in ('completed', 'cancelled', 'no_show'):
                time_passed = True
            elif apt.status != 'in_consultation':
                if apt.appointment_datetime_end and apt.appointment_datetime_end <= now_utc:
                    time_passed = True
                elif apt.appointment_date and apt.appointment_date < today:
                    time_passed = True
            apt.is_time_passed = time_passed

    def _search_is_started(self, operator, value):
        now_utc = fields.Datetime.now()
        today = fields.Date.today()
        domain = [
            '|', '|', '|',
            ('status', 'in', ('in_consultation', 'completed')),
            ('consultation_started_date', '!=', False),
            ('appointment_datetime_start', '<=', now_utc),
            ('appointment_date', '<', today),
        ]
        if (operator in ('=', '==') and value) or (operator in ('!=', '<>') and not value):
            return domain
        return ['!'] + domain

    def _search_is_time_passed(self, operator, value):
        now_utc = fields.Datetime.now()
        today = fields.Date.today()
        domain = [
            '|',
            ('status', 'in', ('completed', 'cancelled', 'no_show')),
            '&',
            ('status', '!=', 'in_consultation'),
            '|',
            ('appointment_datetime_end', '<=', now_utc),
            ('appointment_date', '<', today),
        ]
        if (operator in ('=', '==') and value) or (operator in ('!=', '<>') and not value):
            return domain
        return ['!'] + domain

    @api.depends('status', 'appointment_datetime_start')
    def _compute_doctor_action_permissions(self):
        """Check if doctor can start or complete consultation based on time windows"""
        now_utc = fields.Datetime.now()
        for apt in self:
            # Start consultation: within 5 minutes of appointment start (0 to 5 minutes remaining)
            if apt.appointment_datetime_start:
                time_diff = (apt.appointment_datetime_start - now_utc).total_seconds() / 60
                apt.can_doctor_start_consultation = (
                    apt.status == 'ready_for_doctor' and
                    0 <= time_diff <= 5
                )
                # Complete consultation: after appointment time
                apt.can_doctor_complete_consultation = (
                    apt.status == 'in_consultation' and
                    now_utc >= apt.appointment_datetime_start
                )
            else:
                apt.can_doctor_start_consultation = False
                apt.can_doctor_complete_consultation = False

    @api.depends('status', 'appointment_datetime_start', 'appointment_date')
    def _compute_receptionist_action_permissions(self):
        """Check if receptionist can confirm or check in based on time windows"""
        now_utc = fields.Datetime.now()
        today = fields.Date.today()
        for apt in self:
            # Confirm: day before appointment
            if apt.appointment_date:
                days_until = (apt.appointment_date - today).days
                apt.can_receptionist_confirm = (
                    apt.status == 'tentative' and
                    days_until <= 1 and
                    days_until > 0
                )
            else:
                apt.can_receptionist_confirm = False

            # Check in: within 15 minutes before appointment (0 to 15 minutes until)
            if apt.appointment_datetime_start:
                time_diff = (apt.appointment_datetime_start - now_utc).total_seconds() / 60
                apt.can_receptionist_checkin = (
                    apt.status in ('tentative', 'confirmed') and
                    0 <= time_diff <= 15
                )
            else:
                apt.can_receptionist_checkin = False

    @api.depends('status', 'appointment_datetime_start')
    def _compute_nurse_action_permissions(self):
        """Check if nurse can mark ready based on time window"""
        now_utc = fields.Datetime.now()
        for apt in self:
            # Mark ready: within 10 minutes before appointment (0 to 10 minutes remaining)
            if apt.appointment_datetime_start:
                time_diff = (apt.appointment_datetime_start - now_utc).total_seconds() / 60
                apt.can_nurse_mark_ready = (
                    apt.status == 'checked_in' and
                    0 <= time_diff <= 10
                )
            else:
                apt.can_nurse_mark_ready = False

    @api.depends('status', 'is_started', 'is_time_passed')
    def _compute_can_reschedule(self):
        """Check if appointment can be rescheduled"""
        for apt in self:
            apt.can_reschedule = (
                apt.status in ('tentative', 'confirmed') and
                not apt.is_started and
                not apt.is_time_passed
            )

    @api.depends('appointment_datetime_start')
    def _compute_minutes_remaining(self):
        """Calculate minutes until appointment starts"""
        now_utc = fields.Datetime.now()
        for apt in self:
            if apt.appointment_datetime_start:
                time_diff = (apt.appointment_datetime_start - now_utc).total_seconds() / 60
                apt.minutes_remaining = int(time_diff)
            else:
                apt.minutes_remaining = 0

    @api.depends('appointment_datetime_start', 'minutes_remaining', 'status')
    def _compute_appointment_status_display(self):
        """Generate real-time status display with countdown"""
        for apt in self:
            if apt.appointment_datetime_start:
                mins = apt.minutes_remaining
                if mins > 0:
                    apt.appointment_status_display = _("📅 Appointment in %d minutes") % mins
                elif mins == 0:
                    apt.appointment_status_display = _("🔴 Appointment starting now!")
                elif mins > -60:
                    apt.appointment_status_display = _("⏱️ Appointment %d minutes ago") % abs(mins)
                else:
                    apt.appointment_status_display = _("✓ Appointment completed")
            else:
                apt.appointment_status_display = _("⏳ Appointment time not set")

    @api.depends('can_doctor_start_consultation', 'can_doctor_complete_consultation',
                 'can_receptionist_confirm', 'can_receptionist_checkin',
                 'can_nurse_mark_ready', 'appointment_datetime_start', 'can_reschedule',
                 'minutes_remaining')
    def _compute_action_messages(self):
        """Generate message if action is not available"""
        now_utc = fields.Datetime.now()
        for apt in self:
            apt.action_message = ""

            if apt.appointment_datetime_start:
                time_diff = (apt.appointment_datetime_start - now_utc).total_seconds() / 60

                # Receptionist check-in messages (within 15 minutes before)
                if apt.status in ('tentative', 'confirmed'):
                    if 0 <= time_diff <= 15:
                        apt.action_message = _("✓ CHECK-IN AVAILABLE NOW | %d minutes remaining") % apt.minutes_remaining
                    else:
                        apt.action_message = _("⏳ Check-in available in %d minutes (15-minute window)") % apt.minutes_remaining

                # Doctor consultation messages (within 5 minutes)
                elif apt.status == 'ready_for_doctor':
                    if 0 <= time_diff <= 5:
                        apt.action_message = _("✓ START CONSULTATION AVAILABLE NOW | %d minutes remaining") % apt.minutes_remaining
                    else:
                        apt.action_message = _("⏳ Start consultation available in %d minutes (5-minute window)") % apt.minutes_remaining

                # Nurse ready-for-doctor messages (within 10 minutes)
                elif apt.status == 'checked_in':
                    if 0 <= time_diff <= 10:
                        apt.action_message = _("✓ READY FOR DOCTOR AVAILABLE | %d minutes remaining") % apt.minutes_remaining
                    else:
                        apt.action_message = _("⏳ Mark ready available in %d minutes (10-minute window)") % apt.minutes_remaining

                # Reschedule availability
                if apt.status in ('tentative', 'confirmed') and not apt.is_started and not apt.is_time_passed:
                    if apt.action_message:
                        apt.action_message += _("\n📅 Reschedule available - You can reschedule this appointment")
                    else:
                        apt.action_message = _("📅 Reschedule available - You can reschedule this appointment")

    @staticmethod
    def _get_m2m_ids(commands, current_ids):
        ids = set(current_ids)
        if isinstance(commands, (list, tuple)):
            for cmd in commands:
                if isinstance(cmd, (list, tuple)) and len(cmd) >= 2:
                    if cmd[0] == 6 and len(cmd) == 3:
                        return set(cmd[2])
                    elif cmd[0] == 4:
                        ids.add(cmd[1])
                    elif cmd[0] in (3, 2):
                        ids.discard(cmd[1])
                    elif cmd[0] == 5:
                        ids.clear()
        return ids

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('patient_id') and vals.get('partner_id'):
                vals['patient_id'] = vals.pop('partner_id')
            elif vals.get('patient_id') and 'partner_id' in vals:
                vals.pop('partner_id')
            if 'name' not in vals or not vals['name']:
                # Generate appointment name without sequence (sequence had invalid format)
                try:
                    vals['name'] = self.env['ir.sequence'].next_by_code('medical.appointment')
                except Exception:
                    # Fallback: generate name manually if sequence fails
                    from datetime import datetime
                    year = datetime.now().strftime('%Y')
                    # Get next number by counting existing appointments for this year
                    count = self.env['medical.appointment'].search_count([
                        ('name', 'ilike', f'APT/{year}/%')
                    ]) + 1
                    vals['name'] = f'APT/{year}/{count:05d}'

            # Auto-sync sales employee if salesperson / created_by_sales is set
            sales_user = vals.get('salesperson_id') or vals.get('created_by_sales')
            if sales_user and not vals.get('sales_employee_id'):
                emp = self.env['hr.employee'].search([
                    ('user_id', '=', sales_user),
                    ('medical_employee_type', '=', 'sales')
                ], limit=1)
                if not emp:
                    emp = self.env['hr.employee'].search([('user_id', '=', sales_user)], limit=1)
                if emp:
                    vals['sales_employee_id'] = emp.id

            # Auto-sync receptionist if checked_in_by is set
            if vals.get('checked_in_by') and not vals.get('receptionist_id'):
                emp = self.env['hr.employee'].search([
                    ('user_id', '=', vals['checked_in_by']),
                    ('medical_employee_type', '=', 'receptionist')
                ], limit=1)
                if not emp:
                    emp = self.env['hr.employee'].search([('user_id', '=', vals['checked_in_by'])], limit=1)
                if emp:
                    vals['receptionist_id'] = emp.id

            # Auto-sync nurse if vitals_recorded_by is set
            if vals.get('vitals_recorded_by') and not vals.get('nurse_id'):
                emp = self.env['hr.employee'].search([
                    ('user_id', '=', vals['vitals_recorded_by']),
                    ('medical_employee_type', '=', 'nurse')
                ], limit=1)
                if not emp:
                    emp = self.env['hr.employee'].search([('user_id', '=', vals['vitals_recorded_by'])], limit=1)
                if emp:
                    vals['nurse_id'] = emp.id

        records = super(MedicalAppointment, self.with_context(bypass_appointment_lock=True)).create(vals_list)
        return records.with_context(self.env.context)

    def write(self, vals):
        bypass = self.env.context.get('bypass_appointment_lock')

        if not bypass:
            non_system_keys = set(vals.keys()) - self.SYSTEM_INTERNAL_FIELDS
            # Allow status changes and clinical/vitals fields to be updated after appointment starts
            allowed_terminal_keys = {
                'status', 'cancellation_reason',
                # Clinical fields
                'diagnosis', 'prescription', 'treatment_plan', 'doctor_notes',
                # Vitals fields
                'vital_blood_pressure_systolic', 'vital_blood_pressure_diastolic',
                'vital_temperature', 'vital_heart_rate', 'vital_respiratory_rate',
                'vital_oxygen_saturation', 'vital_height', 'vital_weight',
                'vital_blood_sugar', 'nurse_notes',
                # Timestamps and tracking
                'consultation_started_date', 'consultation_completed_date', 'mrn',
                'vitals_recorded_by', 'checked_in_date', 'checked_in_by',
                # Commission and billing
                'appointment_total', 'commission_rate'
            }

            for apt in self:
                # 1. Past time: disable all editing (except terminal status like no-show/cancelled or chatter) - unless admin
                if apt.is_time_passed and not self._is_admin():
                    disallowed = non_system_keys - allowed_terminal_keys
                    if disallowed:
                        raise UserError(_(
                            "This appointment (%s) has passed its scheduled time. Editing is disabled."
                        ) % (apt.name or ''))

                # 2. Started: disable editing booking & schedule fields
                # Exception: Allow assigned doctor to edit during consultation (in_consultation status)
                elif apt.is_started and not self._is_admin():
                    is_in_consultation = apt.status == 'in_consultation'
                    is_assigned_doctor = apt._is_assigned_doctor()

                    # Allow doctor to edit during consultation, but prevent scheduling field changes
                    if is_in_consultation and is_assigned_doctor:
                        # Doctor in consultation can edit, but still cannot change key scheduling fields
                        protected_scheduling = {'patient_id', 'appointment_date', 'appointment_time', 'start_time', 'doctor_id'}
                        for field in protected_scheduling:
                            if field in vals:
                                field_def = self._fields.get(field)
                                field_type = field_def.type if field_def else None
                                current_val = getattr(apt, field)
                                new_val = vals[field]

                                if field_type in ('many2many', 'one2many'):
                                    current_ids = set(current_val.ids)
                                    new_ids = self._get_m2m_ids(new_val, current_ids)
                                    is_changed = current_ids != new_ids
                                elif field_type == 'many2one':
                                    current_id = current_val.id if current_val else False
                                    target_id = new_val if isinstance(new_val, int) else (new_val.id if hasattr(new_val, 'id') else False)
                                    is_changed = current_id != target_id
                                elif field_type == 'date':
                                    is_changed = str(current_val or '') != str(new_val or '')
                                else:
                                    is_changed = current_val != new_val

                                if is_changed:
                                    raise UserError(_(
                                        "Cannot change patient, date/time, or doctor during consultation."
                                    ))
                    else:
                        # Non-doctor or not in consultation: block all scheduling field changes
                        for field in self.SCHEDULING_FIELDS:
                            if field in vals:
                                field_def = self._fields.get(field)
                                field_type = field_def.type if field_def else None
                                current_val = getattr(apt, field)
                                new_val = vals[field]

                                if field_type in ('many2many', 'one2many'):
                                    current_ids = set(current_val.ids)
                                    new_ids = self._get_m2m_ids(new_val, current_ids)
                                    is_changed = current_ids != new_ids
                                elif field_type == 'many2one':
                                    current_id = current_val.id if current_val else False
                                    target_id = new_val if isinstance(new_val, int) else (new_val.id if hasattr(new_val, 'id') else False)
                                    is_changed = current_id != target_id
                                elif field_type == 'date':
                                    is_changed = str(current_val or '') != str(new_val or '')
                                else:
                                    is_changed = current_val != new_val

                                if is_changed:
                                    raise UserError(_(
                                        "Appointment '%s' has already started. Booking details, schedule date/time, doctor, and patient cannot be modified."
                                    ) % (apt.name or ''))

        if 'partner_id' in vals and 'patient_id' not in vals:
            vals['patient_id'] = vals.pop('partner_id')
        elif 'partner_id' in vals and 'patient_id' in vals:
            vals.pop('partner_id')

        return super().write(vals)

    def _is_admin(self):
        """Check if current user is system admin"""
        return self.env.user._is_admin() or self.env.user._is_system()

    def _is_assigned_doctor(self):
        """Check if current user is the doctor assigned to this appointment"""
        self.ensure_one()
        return self.doctor_user_id and self.doctor_user_id.id == self.env.user.id

    def action_confirm_appointment(self):
        """Confirm appointment after day-before confirmation call"""
        self.ensure_one()
        if self.status != 'tentative' and not self._is_admin():
            raise ValidationError(_('Only tentative appointments can be confirmed.'))

        # Time window check: day before appointment (unless admin)
        if not self._is_admin() and self.appointment_date:
            today = fields.Date.today()
            days_until = (self.appointment_date - today).days
            if days_until > 1:
                raise UserError(_('Can only confirm appointments the day before or on appointment day.'))

        self.write({
            'status': 'confirmed',
            'confirmation_call_status': 'confirmed',
        })
        self.message_post(body=_('Appointment confirmed by patient.'))

    def action_check_in(self):
        """Check in patient (receptionist action)

        Strict during time window: must follow sequence
        Flexible after time window passes: can skip from earlier statuses
        """
        self.ensure_one()

        # Determine if we're within the check-in time window (15 min before appointment)
        time_window_active = True
        if self.appointment_datetime_start:
            now_utc = fields.Datetime.now()
            time_diff_minutes = (self.appointment_datetime_start - now_utc).total_seconds() / 60
            # Window is 15 minutes before appointment (after -1 min = too late)
            if time_diff_minutes < -1:
                time_window_active = False

        # During time window: must be in tentative/confirmed
        if time_window_active and self.status not in ('tentative', 'confirmed') and not self._is_admin():
            raise ValidationError(_('During check-in window: can only check in confirmed or tentative appointments.'))

        # After time window: can skip from any earlier status
        if not time_window_active and self.status not in ('tentative', 'confirmed', 'checked_in', 'ready_for_doctor') and not self._is_admin():
            raise ValidationError(_('Appointment has progressed too far to check in now.'))

        # Check timing for check-in notification
        early_checkin_notification = False
        too_early_checkin = False
        if self.appointment_datetime_start:
            now_utc = fields.Datetime.now()
            time_diff_minutes = (self.appointment_datetime_start - now_utc).total_seconds() / 60

            # If more than 15 minutes before appointment, it's too early
            if time_diff_minutes > 15:
                too_early_checkin = True
                minutes_until = int(time_diff_minutes)
            # If within 15 minutes before appointment, notify if early
            elif time_diff_minutes > 0:
                early_checkin_notification = int(time_diff_minutes)

        rec_emp = self.receptionist_id
        if not rec_emp:
            rec_emp = self.env['hr.employee'].search([
                ('user_id', '=', self.env.user.id),
                ('medical_employee_type', '=', 'receptionist')
            ], limit=1)
            if not rec_emp:
                rec_emp = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)

        write_vals = {
            'status': 'checked_in',
            'checked_in_date': fields.Datetime.now(),
            'checked_in_by': self.env.user.id,
            'receptionist_id': rec_emp.id if rec_emp else False,
        }

        self.write(write_vals)

        # Create notification message based on check-in timing
        if too_early_checkin:
            # Warn about too early check-in but still allow it
            self.message_post(
                body=_('<div class="alert alert-info"><b>⚠️ Early Check-in:</b> Patient checked in %d minutes before 15-minute window. Window opens in approximately %d minutes.</div>') % (int(time_diff_minutes * -1), minutes_until - 15),
                subtype_xmlid='mail.mt_comment'
            )
        elif early_checkin_notification:
            # Post message for check-in within the 15-minute window
            self.message_post(
                body=_('<div class="alert alert-warning"><b>⏰ Check-in:</b> Patient checked in %d minutes before appointment start time.</div>') % early_checkin_notification,
                subtype_xmlid='mail.mt_comment'
            )
            # Create activity reminder for early check-ins
            self.env['mail.activity'].create({
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'res_id': self.id,
                'res_model_id': self.env['ir.model']._get_id(self._name),
                'user_id': self.env.user.id,
                'summary': _('Check-in: %d minutes before scheduled time') % early_checkin_notification,
            })
        else:
            # Normal check-in at or after appointment time
            self.message_post(
                body=_('<div class="alert alert-success"><b>✓ Patient checked in.</b></div>'),
                subtype_xmlid='mail.mt_comment'
            )

    def action_ready_for_doctor(self):
        """Mark patient ready for doctor (nurse action)

        Strict during time window: patient must be checked in first
        Flexible after time window: can skip check-in if time passed
        """
        self.ensure_one()

        # Determine if we're within the ready-mark time window (5 min of appointment)
        time_window_active = True
        if self.appointment_datetime_start:
            now_utc = fields.Datetime.now()
            time_diff_minutes = (self.appointment_datetime_start - now_utc).total_seconds() / 60
            # Window is +/- 5 minutes of appointment time
            if abs(time_diff_minutes) > 5:
                time_window_active = False

        # During time window: patient MUST be checked in
        if time_window_active and self.status not in ('checked_in',) and not self._is_admin():
            raise ValidationError(_('During ready-mark window: patient must be checked in first.'))

        # After time window: can skip check-in if not done
        if not time_window_active and self.status not in ('tentative', 'confirmed', 'checked_in', 'ready_for_doctor') and not self._is_admin():
            raise ValidationError(_('Appointment has progressed too far to mark ready now.'))

        # Enforce time window during active period
        if time_window_active and not self._is_admin() and self.appointment_datetime_start:
            now_utc = fields.Datetime.now()
            time_diff_minutes = (self.appointment_datetime_start - now_utc).total_seconds() / 60
            if abs(time_diff_minutes) > 5:
                raise UserError(_('Nurse can mark ready only within 5 minutes of appointment time.'))

        nurse_emp = self.nurse_id
        if not nurse_emp:
            nurse_emp = self.env['hr.employee'].search([
                ('user_id', '=', self.env.user.id),
                ('medical_employee_type', '=', 'nurse')
            ], limit=1)
            if not nurse_emp:
                nurse_emp = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)

        write_vals = {
            'status': 'ready_for_doctor',
            'vitals_recorded_by': self.env.user.id,
            'nurse_id': nurse_emp.id if nurse_emp else False,
        }

        # If skipping check-in (after time window), auto-set it
        if self.status != 'checked_in' and not self.checked_in_date:
            write_vals['checked_in_date'] = fields.Datetime.now()
            write_vals['checked_in_by'] = self.env.user.id

        self.write(write_vals)
        self.message_post(body=_('Patient vitals recorded and marked ready for doctor.'))
        self.activity_schedule(
            'mail.mail_activity_data_todo',
            note=_('Patient %s is ready for consultation.') % self.patient_id.name,
            user_id=self.doctor_user_id.id,
        )

    def action_start_consultation(self):
        """Start consultation (doctor action) - auto-generate MRN if needed

        Strict during time window: patient must be ready for doctor
        Flexible after time window: can skip ready step if time passed
        """
        self.ensure_one()

        # Determine if we're within the start-consultation time window (5 min of appointment)
        time_window_active = True
        if self.appointment_datetime_start:
            now_utc = fields.Datetime.now()
            time_diff_minutes = (self.appointment_datetime_start - now_utc).total_seconds() / 60
            # Window is +/- 5 minutes of appointment time
            if abs(time_diff_minutes) > 5:
                time_window_active = False

        # During time window: patient MUST be ready for doctor
        if time_window_active and self.status not in ('ready_for_doctor',) and not self._is_admin():
            raise ValidationError(_('During consultation start window: patient must be ready for doctor first.'))

        # After time window: can skip ready step
        allowed_statuses = ('confirmed', 'checked_in', 'ready_for_doctor', 'tentative')
        if not time_window_active and self.status not in allowed_statuses and not self._is_admin():
            raise ValidationError(_('Patient must be at least checked in to start consultation.'))

        # Enforce time window during active period
        if time_window_active and not self._is_admin() and self.appointment_datetime_start:
            now_utc = fields.Datetime.now()
            time_diff_minutes = (self.appointment_datetime_start - now_utc).total_seconds() / 60
            if abs(time_diff_minutes) > 5:
                raise UserError(_('Doctor can start consultation only within 5 minutes of appointment time.'))

        # Auto-generate MRN if not present
        if not self.mrn:
            mrn = self.env['ir.sequence'].next_by_code('medical.patient.mrn')
            self.mrn = mrn

        write_vals = {
            'status': 'in_consultation',
            'consultation_started_date': fields.Datetime.now(),
        }

        # If skipping the ready_for_doctor step (after time window), auto-set check-in if needed
        if self.status != 'ready_for_doctor':
            if not self.vitals_recorded_by:
                write_vals['vitals_recorded_by'] = None  # Mark nurse action as skipped
            if not self.checked_in_date:
                write_vals['checked_in_date'] = fields.Datetime.now()
                write_vals['checked_in_by'] = self.env.user.id

        self.write(write_vals)
        self.message_post(body=_('Consultation started. MRN: %s') % self.mrn)

    def action_complete(self):
        """Complete consultation (doctor action)"""
        self.ensure_one()
        if self.status != 'in_consultation' and not self._is_admin():
            raise ValidationError(_('Can only complete consultations that are in progress.'))
        self.write({
            'status': 'completed',
            'consultation_completed_date': fields.Datetime.now(),
        })
        self.message_post(body=_('Consultation completed.'))

    def action_no_show(self):
        """Mark appointment as no-show"""
        self.ensure_one()
        self.write({'status': 'no_show'})
        self.message_post(body=_('Appointment marked as no-show.'))

    def action_cancel(self):
        """Cancel appointment"""
        self.ensure_one()
        self.write({'status': 'cancelled'})
        self.message_post(body=_('Appointment cancelled.'))

    def action_open_reschedule_wizard(self):
        """Open reschedule wizard for appointment"""
        self.ensure_one()
        return {
            'name': _('Reschedule Appointment'),
            'type': 'ir.actions.act_window',
            'res_model': 'appointment.reschedule.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_id': self.id,
                'active_model': self._name,
            }
        }

    @api.depends('appointment_time', 'start_time', 'estimated_duration')
    def _compute_end_time(self):
        for rec in self:
            start = rec.appointment_time or rec.start_time
            if start:
                rec.end_time = start + (rec.estimated_duration or 1.0)
            else:
                rec.end_time = False

    def _get_medical_center_tz(self):
        self.ensure_one()
        tz_name = self.env.user.tz or self.company_id.partner_id.tz or self.env.company.partner_id.tz or 'UTC'
        try:
            return pytz.timezone(tz_name)
        except Exception:
            return pytz.UTC

    @api.depends('appointment_date', 'start_time', 'appointment_time', 'duration', 'estimated_duration', 'company_id')
    def _compute_appointment_datetimes(self):
        for apt in self:
            st = apt.start_time if apt.start_time is not False else apt.appointment_time
            if apt.appointment_date and st is not False and st is not None:
                tz = apt._get_medical_center_tz()
                hours = int(st)
                minutes = int(round((st - hours) * 60))
                if minutes >= 60:
                    hours += 1
                    minutes = 0
                hours = min(max(hours, 0), 23)
                minutes = min(max(minutes, 0), 59)
                local_start_dt = datetime.combine(apt.appointment_date, time(hour=hours, minute=minutes))
                try:
                    localized_start = tz.localize(local_start_dt, is_dst=None)
                except Exception:
                    localized_start = tz.localize(local_start_dt)

                utc_start = localized_start.astimezone(pytz.UTC).replace(tzinfo=None)
                apt.appointment_datetime_start = utc_start
                dur = apt.duration or apt.estimated_duration or 1.0
                apt.appointment_datetime_end = utc_start + timedelta(hours=dur)
            else:
                apt.appointment_datetime_start = False
                apt.appointment_datetime_end = False

    def _inverse_appointment_datetime_start(self):
        for apt in self:
            if apt.appointment_datetime_start:
                tz = apt._get_medical_center_tz()
                utc_start = pytz.UTC.localize(apt.appointment_datetime_start)
                local_start = utc_start.astimezone(tz)
                apt.appointment_date = local_start.date()
                st = local_start.hour + local_start.minute / 60.0
                apt.start_time = st
                apt.appointment_time = st
                if apt.appointment_datetime_end:
                    utc_end = pytz.UTC.localize(apt.appointment_datetime_end)
                    local_end = utc_end.astimezone(tz)
                    dur = (local_end - local_start).total_seconds() / 3600.0
                    apt.duration = max(dur, 0.25)
                    apt.estimated_duration = max(dur, 0.25)

    def _inverse_appointment_datetime_end(self):
        for apt in self:
            if apt.appointment_datetime_start and apt.appointment_datetime_end:
                dur = (apt.appointment_datetime_end - apt.appointment_datetime_start).total_seconds() / 3600.0
                apt.duration = max(dur, 0.25)
                apt.estimated_duration = max(dur, 0.25)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        dt_start_str = self.env.context.get('default_appointment_datetime_start')
        if dt_start_str:
            try:
                dt_start = fields.Datetime.from_string(dt_start_str)
                tz_name = self.env.user.tz or self.env.company.partner_id.tz or 'UTC'
                tz = pytz.timezone(tz_name)
                local_dt = pytz.UTC.localize(dt_start).astimezone(tz)
                if 'appointment_date' in fields_list:
                    res['appointment_date'] = local_dt.date()
                if 'start_time' in fields_list:
                    res['start_time'] = round(local_dt.hour + local_dt.minute / 60.0, 2)
                if 'appointment_time' in fields_list:
                    res['appointment_time'] = round(local_dt.hour + local_dt.minute / 60.0, 2)
            except Exception:
                pass
        return res
