# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


def _is_param_enabled(icp, key, default='False'):
    val = icp.get_param(key, default)
    if isinstance(val, bool):
        return val
    return str(val or '').strip().lower() in ('true', '1')


class CrmLeadAppointment(models.Model):
    _inherit = 'crm.lead'

    doctor_id = fields.Many2one(
        'hr.employee',
        string='Assigned Doctor',
        domain="[('medical_employee_type', '=', 'doctor')]",
        tracking=True,
        help='Doctor assigned to examine or consult with this patient/lead'
    )

    # Medical Staff Salesperson Link & Filter
    medical_staff_id = fields.Many2one(
        'hr.employee',
        string='Medical Staff Salesperson',
        domain="[('medical_employee_type', '!=', False)]",
        tracking=True,
        help='Medical staff member assigned as salesperson for this lead'
    )
    medical_staff_user_ids = fields.Many2many(
        'res.users',
        compute='_compute_medical_staff_user_ids',
        string='Eligible Medical Staff Users'
    )
    user_id = fields.Many2one(
        'res.users',
        string='Salesperson',
        domain="[('share', '=', False)]",
        default=lambda self: self.env.user,
        check_company=True,
        index=True,
        tracking=True
    )

    # Structured Medical Service Link
    medical_service_id = fields.Many2one(
        'medical.service',
        string='Requested Medical Service',
        tracking=True,
        help='Select from medical services catalog to automatically load pricing, duration, and session rules'
    )
    service_standard_price = fields.Monetary(
        string='Service Price',
        related='medical_service_id.price',
        currency_field='company_currency',
        readonly=True
    )
    service_discount = fields.Float(
        string='Service Discount (%)',
        related='medical_service_id.discount',
        readonly=True
    )
    service_final_price = fields.Monetary(
        string='Service Net Price',
        related='medical_service_id.final_price',
        currency_field='company_currency',
        readonly=True
    )
    service_duration = fields.Float(
        string='Service Duration (Hours)',
        related='medical_service_id.duration',
        readonly=True
    )
    service_period_between_sessions = fields.Integer(
        string='Period Between Sessions (Days)',
        related='medical_service_id.period_between_sessions',
        readonly=True
    )

    # Call Logging Relations
    call_log_ids = fields.One2many(
        'crm.lead.call_log',
        'lead_id',
        string='Call History'
    )
    call_log_count = fields.Integer(
        string='Call Count',
        compute='_compute_call_log_count',
        store=True
    )

    # Appointment Relations
    appointment_ids = fields.One2many(
        'medical.appointment',
        'crm_lead_id',
        string='Appointments'
    )
    appointment_count = fields.Integer(
        string='Appointment Count',
        compute='_compute_appointment_count',
        store=True
    )

    # Sales Follow-up & Overdue Tracking
    is_overdue = fields.Boolean(
        string='Overdue Follow-up',
        compute='_compute_is_overdue',
        search='_search_is_overdue',
        help='True if next follow-up date has passed and lead is still open'
    )
    last_call_date = fields.Datetime(
        string='Last Contact Date',
        compute='_compute_call_summary',
        store=True,
        help='Date and time of the most recent phone call attempt'
    )
    last_call_outcome = fields.Selection([
        ('contacted', 'Contacted - Interested'),
        ('no_answer', 'No Answer'),
        ('followup_required', 'Follow-up Required'),
        ('booked', 'Appointment Booked'),
        ('not_interested', 'Not Interested'),
        ('invalid_contact', 'Invalid Phone / Contact'),
    ], string='Last Call Outcome', compute='_compute_call_summary', store=True)

    @api.depends('next_followup_date')
    def _compute_is_overdue(self):
        today = fields.Date.today()
        for lead in self:
            lead.is_overdue = bool(lead.active and lead.probability < 100 and lead.next_followup_date and lead.next_followup_date < today)

    def _search_is_overdue(self, operator, value):
        today = fields.Date.today()
        if (operator == '=' and value) or (operator == '!=' and not value):
            return [('active', '=', True), ('probability', '<', 100), ('next_followup_date', '!=', False), ('next_followup_date', '<', today)]
        else:
            return ['|', ('active', '=', False), '|', ('probability', '=', 100), '|', ('next_followup_date', '=', False), ('next_followup_date', '>=', today)]

    @api.depends('call_log_ids', 'call_log_ids.call_date', 'call_log_ids.outcome')
    def _compute_call_summary(self):
        for lead in self:
            if lead.call_log_ids:
                latest = lead.call_log_ids.sorted('call_date', reverse=True)[0]
                lead.last_call_date = latest.call_date
                lead.last_call_outcome = latest.outcome
            else:
                lead.last_call_date = False
                lead.last_call_outcome = False

    @api.depends_context('uid')
    def _compute_medical_staff_user_ids(self):
        medical_groups = [
            'medical_employee_management.group_medical_sales',
            'medical_employee_management.group_medical_sales_manager',
            'medical_employee_management.group_medical_doctor',
            'medical_employee_management.group_medical_doctor_manager',
            'medical_employee_management.group_medical_receptionist',
            'medical_employee_management.group_medical_receptionist_manager',
            'medical_employee_management.group_medical_nurse',
            'medical_employee_management.group_medical_nurse_manager',
            'medical_employee_management.group_medical_hr_manager',
            'medical_employee_management.group_medical_security_manager',
            'base.group_system',
            'base.group_erp_manager',
        ]
        group_ids = []
        for g_xmlid in medical_groups:
            grp = self.env.ref(g_xmlid, raise_if_not_found=False)
            if grp:
                group_ids.append(grp.id)

        domain = [('share', '=', False)]
        if group_ids:
            domain.append(('groups_id', 'in', group_ids))

        users = self.env['res.users'].search(domain)
        emp_users = self.env['hr.employee'].search([
            ('medical_employee_type', '!=', False),
            ('user_id', '!=', False)
        ]).mapped('user_id').filtered(lambda u: not u.share)

        all_eligible = users | emp_users
        for lead in self:
            lead.medical_staff_user_ids = all_eligible

    @api.onchange('medical_staff_id')
    def _onchange_medical_staff_id(self):
        if self.medical_staff_id and self.medical_staff_id.user_id:
            self.user_id = self.medical_staff_id.user_id

    @api.onchange('user_id')
    def _onchange_user_id_sync_staff(self):
        if self.user_id:
            staff = self.env['hr.employee'].search([
                ('user_id', '=', self.user_id.id),
                ('medical_employee_type', '!=', False)
            ], limit=1)
            if staff:
                self.medical_staff_id = staff

    @api.constrains('user_id')
    def _check_salesperson_medical_staff(self):
        medical_groups = [
            'medical_employee_management.group_medical_sales',
            'medical_employee_management.group_medical_sales_manager',
            'medical_employee_management.group_medical_doctor',
            'medical_employee_management.group_medical_doctor_manager',
            'medical_employee_management.group_medical_receptionist',
            'medical_employee_management.group_medical_receptionist_manager',
            'medical_employee_management.group_medical_nurse',
            'medical_employee_management.group_medical_nurse_manager',
            'medical_employee_management.group_medical_hr_manager',
            'medical_employee_management.group_medical_security_manager',
            'medical_appointment_management.group_medical_appointment_manager',
            'base.group_system',
            'base.group_erp_manager',
        ]
        group_ids = []
        for g_xmlid in medical_groups:
            grp = self.env.ref(g_xmlid, raise_if_not_found=False)
            if grp:
                group_ids.append(grp.id)

        for lead in self:
            if lead.user_id and lead.user_id.id != 1 and not lead.user_id._is_superuser() and not lead.user_id._is_admin():
                has_medical_group = bool(set(lead.user_id.groups_id.ids) & set(group_ids))
                is_medical_emp = bool(self.env['hr.employee'].search_count([
                    ('user_id', '=', lead.user_id.id),
                    ('medical_employee_type', '!=', False)
                ]))
                if not has_medical_group and not is_medical_emp:
                    raise ValidationError(_(
                        "The assigned salesperson '%s' is not part of the Medical Staff. "
                        "Please assign a user with a medical staff role or an active medical employee."
                    ) % lead.user_id.name)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('medical_staff_id') and not vals.get('user_id'):
                staff = self.env['hr.employee'].browse(vals['medical_staff_id'])
                if staff.user_id:
                    vals['user_id'] = staff.user_id.id
            elif vals.get('user_id') and not vals.get('medical_staff_id'):
                staff = self.env['hr.employee'].search([
                    ('user_id', '=', vals['user_id']),
                    ('medical_employee_type', '!=', False)
                ], limit=1)
                if staff:
                    vals['medical_staff_id'] = staff.id
        leads = super().create(vals_list)
        for lead in leads:
            if lead.user_id:
                act_type = self.env.ref('mail.mail_activity_data_call', raise_if_not_found=False)
                if not act_type:
                    act_type = self.env['mail.activity.type'].search([('category', '=', 'phonecall')], limit=1)
                if not act_type:
                    act_type = self.env['mail.activity.type'].search([], limit=1)
                if act_type:
                    existing = lead.activity_ids.filtered(lambda a: a.activity_type_id == act_type and 'Initial' in (a.summary or ''))
                    if not existing:
                        lead.activity_schedule(
                            activity_type_id=act_type.id,
                            summary=_("Initial sales contact call"),
                            note=_("Contact new medical lead %s to discuss services and book appointment.") % (
                                lead.partner_name or lead.contact_name or lead.name
                            ),
                            date_deadline=fields.Date.today(),
                            user_id=lead.user_id.id
                        )
        return leads

    def write(self, vals):
        if 'medical_staff_id' in vals and vals.get('medical_staff_id') and 'user_id' not in vals:
            staff = self.env['hr.employee'].browse(vals['medical_staff_id'])
            if staff.user_id:
                vals['user_id'] = staff.user_id.id
        elif 'user_id' in vals and vals.get('user_id') and 'medical_staff_id' not in vals:
            staff = self.env['hr.employee'].search([
                ('user_id', '=', vals['user_id']),
                ('medical_employee_type', '!=', False)
            ], limit=1)
            if staff:
                vals['medical_staff_id'] = staff.id
        return super().write(vals)

    @api.onchange('medical_service_id')
    def _onchange_medical_service_id(self):
        if self.medical_service_id:
            if self.medical_service_id.final_price and not self.expected_revenue:
                self.expected_revenue = self.medical_service_id.final_price
            if self.medical_service_id.doctor_ids:
                if not self.doctor_id or self.doctor_id not in self.medical_service_id.doctor_ids:
                    self.doctor_id = self.medical_service_id.doctor_ids[0]

    @api.depends('call_log_ids')
    def _compute_call_log_count(self):
        for lead in self:
            lead.call_log_count = len(lead.call_log_ids)

    @api.depends('appointment_ids')
    def _compute_appointment_count(self):
        for lead in self:
            lead.appointment_count = len(lead.appointment_ids)

    def action_log_call(self):
        """Action button on lead form to open quick call logging popup"""
        self.ensure_one()
        return {
            'name': _('Log Sales Call'),
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead.log.call.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_lead_id': self.id,
                'default_next_followup_date': self.next_followup_date,
            }
        }

    def action_book_appointment(self):
        """Action button on lead form to open appointment booking wizard"""
        self.ensure_one()
        # Find or create partner if lead doesn't have one
        partner = self.partner_id
        if not partner:
            partner = self._find_or_create_partner_for_booking()

        return {
            'name': _('Book Medical Appointment'),
            'type': 'ir.actions.act_window',
            'res_model': 'appointment.from.lead.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_lead_id': self.id,
                'default_partner_id': partner.id if partner else False,
                'default_service_id': self.medical_service_id.id if self.medical_service_id else False,
                'default_doctor_id': self.doctor_id.id if self.doctor_id else False,
                'default_salesperson_id': self.user_id.id if self.user_id else False,
                'default_appointment_date': fields.Date.today(),
                'default_notes': self.internal_notes or False,
            }
        }

    def _find_or_create_partner_for_booking(self):
        """Ensure a contact partner exists before booking"""
        self.ensure_one()
        if self.partner_id:
            return self.partner_id
        if self.contact_name or self.partner_name:
            name = self.contact_name or self.partner_name
            partner = self.env['res.partner'].create({
                'name': name,
                'phone': self.phone,
                'mobile': self.mobile,
                'email': self.email_from,
                'country_id': self.country_id.id if self.country_id else False,
            })
            self.partner_id = partner.id
            return partner
        return self.env['res.partner']

    def action_view_appointments(self):
        """Smart button action to view related appointments"""
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('medical_appointment_management.action_medical_appointments')
        action['domain'] = [('crm_lead_id', '=', self.id)]
        action['context'] = {
            'default_crm_lead_id': self.id,
            'default_partner_id': self.partner_id.id if self.partner_id else False,
            'default_service_id': self.medical_service_id.id if self.medical_service_id else False,
        }
        return action

    @api.model
    def _check_medical_crm_access(self):
        """Verify role permissions to access CRM. Shows guidance message for restricted roles."""
        user = self.env.user
        if user._is_admin() or user._is_system() or self.env.su:
            return

        ctx = self.env.context or {}
        # Allow internal/relational queries originating from Medical Appointments, Patients, or Wizards
        if ctx.get('active_model') in ('medical.appointment', 'appointment.from.lead.wizard', 'res.partner') or \
           ctx.get('params', {}).get('model') in ('medical.appointment', 'res.partner') or \
           ctx.get('skip_crm_access_check'):
            return

        icp = self.env['ir.config_parameter'].sudo()

        is_receptionist = user.has_group('medical_employee_management.group_medical_receptionist')
        receptionist_enabled = _is_param_enabled(icp, 'medical_appointment.crm_enable_receptionist', 'True')

        is_sales = user.has_group('medical_employee_management.group_medical_sales')
        sales_enabled = _is_param_enabled(icp, 'medical_appointment.crm_enable_sales', 'True')

        if (is_receptionist and receptionist_enabled) or (is_sales and sales_enabled):
            return

        is_doctor = user.has_group('medical_employee_management.group_medical_doctor')
        doctor_enabled = _is_param_enabled(icp, 'medical_appointment.crm_enable_doctor', 'False')

        is_nurse = user.has_group('medical_employee_management.group_medical_nurse')
        nurse_enabled = _is_param_enabled(icp, 'medical_appointment.crm_enable_nurse', 'False')

        if is_doctor and not doctor_enabled:
            raise UserError(_(
                "Access Restricted: CRM access is disabled for the Doctor role.\n\n"
                "Please use the Medical Appointments app to view your scheduled appointments, "
                "patient queue, and conduct clinical consultations."
            ))

        if is_nurse and not nurse_enabled:
            raise UserError(_(
                "Access Restricted: CRM access is disabled for the Nurse role.\n\n"
                "Please use the Medical Appointments app to record patient vitals and manage "
                "the triage queue."
            ))

        if is_receptionist and not receptionist_enabled:
            raise UserError(_(
                "Access Restricted: CRM access is currently disabled for Receptionists in Medical Settings."
            ))

        if is_sales and not sales_enabled:
            raise UserError(_(
                "Access Restricted: CRM access is currently disabled for Sales staff in Medical Settings."
            ))

    @api.model
    def get_views(self, views, options=None):
        ctx = self.env.context or {}
        if ctx.get('active_model') not in ('medical.appointment', 'appointment.from.lead.wizard', 'res.partner') and \
           ctx.get('params', {}).get('model') not in ('medical.appointment', 'res.partner') and \
           not ctx.get('skip_crm_access_check'):
            self._check_medical_crm_access()
        return super().get_views(views, options=options)

    @api.model
    def web_search_read(self, domain=None, specification=None, offset=0, limit=None, order=None, count_limit=None):
        ctx = self.env.context or {}
        if ctx.get('active_model') not in ('medical.appointment', 'appointment.from.lead.wizard', 'res.partner') and \
           ctx.get('params', {}).get('model') not in ('medical.appointment', 'res.partner') and \
           not ctx.get('skip_crm_access_check'):
            self._check_medical_crm_access()
        return super().web_search_read(domain=domain, specification=specification, offset=offset, limit=limit, order=order, count_limit=count_limit)
