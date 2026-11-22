# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AppointmentFromLeadWizard(models.TransientModel):
    _name = 'appointment.from.lead.wizard'
    _description = 'Book Appointment from CRM Lead'

    lead_id = fields.Many2one('crm.lead', string='Related Lead')
    partner_id = fields.Many2one('res.partner', string='Patient / Contact', required=True)
    salesperson_id = fields.Many2one('res.users', string='Assigned Salesperson', readonly=True)
    doctor_id = fields.Many2one(
        'hr.employee',
        string='Doctor / Provider',
        required=True,
        domain="[('is_appointment_provider', '=', True)]"
    )
    service_ids = fields.Many2many(
        'medical.service',
        string='Medical Services',
        domain="[('active', '=', True)]",
        help='Select one or multiple medical services/procedures'
    )
    service_id = fields.Many2one(
        'medical.service',
        string='Primary Service',
        compute='_compute_service_id',
        inverse='_inverse_service_id',
        store=True,
        domain="[('active', '=', True)]"
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='company_id.currency_id'
    )
    total_service_price = fields.Float(
        string='Total Estimated Price',
        compute='_compute_total_service_price'
    )

    appointment_date = fields.Date(string='Appointment Date', required=True, default=fields.Date.today)
    start_time = fields.Float(string='Start Time', required=True, default=9.0, help='E.g. 9.5 for 09:30')
    duration = fields.Float(string='Duration (Hours)', required=True, default=0.5)

    notes = fields.Text(string='Internal Notes')
    special_requirements = fields.Text(string='Special Patient Requirements')

    # Conflict fields in wizard
    has_conflict = fields.Boolean(string='Has Conflict', compute='_compute_conflict')
    conflict_details = fields.Text(string='Conflict Details', compute='_compute_conflict')
    conflict_override = fields.Boolean(string='Override Conflict', default=False)
    conflict_override_reason = fields.Text(string='Override Reason')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('partner_id') and vals.get('lead_id'):
                lead = self.env['crm.lead'].browse(vals['lead_id'])
                if lead.partner_id:
                    vals['partner_id'] = lead.partner_id.id
                else:
                    partner = self.env['res.partner'].create({
                        'name': lead.contact_name or lead.partner_name or lead.name,
                        'phone': lead.phone,
                        'mobile': lead.mobile,
                        'email': lead.email_from,
                    })
                    lead.write({'partner_id': partner.id})
                    vals['partner_id'] = partner.id
        return super().create(vals_list)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_id = self.env.context.get('active_id')
        active_model = self.env.context.get('active_model')

        # If opened from CRM Lead
        lead = False
        if active_model == 'crm.lead' and active_id:
            lead = self.env['crm.lead'].browse(active_id)
        elif self.env.context.get('default_lead_id'):
            lead = self.env['crm.lead'].browse(self.env.context['default_lead_id'])

        if lead and lead.exists():
            if 'lead_id' in fields_list and not res.get('lead_id'):
                res['lead_id'] = lead.id
            if 'partner_id' in fields_list and not res.get('partner_id') and lead.partner_id:
                res['partner_id'] = lead.partner_id.id
            if 'doctor_id' in fields_list and not res.get('doctor_id') and lead.doctor_id:
                res['doctor_id'] = lead.doctor_id.id
            if 'salesperson_id' in fields_list and not res.get('salesperson_id') and lead.user_id:
                res['salesperson_id'] = lead.user_id.id
            if lead.medical_service_id:
                if 'service_ids' in fields_list and not res.get('service_ids'):
                    res['service_ids'] = [(6, 0, [lead.medical_service_id.id])]
                if 'service_id' in fields_list and not res.get('service_id'):
                    res['service_id'] = lead.medical_service_id.id
                if 'duration' in fields_list and lead.medical_service_id.duration:
                    res['duration'] = lead.medical_service_id.duration
            if 'notes' in fields_list and not res.get('notes') and (lead.internal_notes or lead.description):
                res['notes'] = lead.internal_notes or lead.description

        if 'default_doctor_id' in self.env.context and self.env.context['default_doctor_id'] and 'doctor_id' in fields_list and not res.get('doctor_id'):
            res['doctor_id'] = self.env.context['default_doctor_id']

        if 'default_salesperson_id' in self.env.context and self.env.context['default_salesperson_id'] and 'salesperson_id' in fields_list and not res.get('salesperson_id'):
            res['salesperson_id'] = self.env.context['default_salesperson_id']

        # If context passed default_service_ids or default_service_id
        if 'default_service_ids' in self.env.context and 'service_ids' in fields_list:
            res['service_ids'] = self.env.context['default_service_ids']
        elif 'default_service_id' in self.env.context and self.env.context['default_service_id']:
            s_id = self.env.context['default_service_id']
            if 'service_ids' in fields_list and not res.get('service_ids'):
                res['service_ids'] = [(6, 0, [s_id])]
            if 'service_id' in fields_list:
                res['service_id'] = s_id

        return res

    @api.depends('service_ids')
    def _compute_service_id(self):
        for wiz in self:
            wiz.service_id = wiz.service_ids[0] if wiz.service_ids else False

    def _inverse_service_id(self):
        for wiz in self:
            if wiz.service_id and wiz.service_id not in wiz.service_ids:
                wiz.service_ids = [(4, wiz.service_id.id)]

    @api.depends('service_ids', 'service_ids.final_price', 'service_id', 'service_id.final_price')
    def _compute_total_service_price(self):
        for wiz in self:
            if wiz.service_ids:
                wiz.total_service_price = sum(wiz.service_ids.mapped('final_price'))
            elif wiz.service_id:
                wiz.total_service_price = wiz.service_id.final_price
            else:
                wiz.total_service_price = 0.0

    @api.onchange('service_ids')
    def _onchange_service_ids(self):
        if self.service_ids:
            total_duration = sum(self.service_ids.mapped('duration'))
            if total_duration > 0:
                self.duration = total_duration

            qualified_doctors = self.service_ids.mapped('doctor_ids')
            if qualified_doctors:
                if not self.doctor_id or self.doctor_id not in qualified_doctors:
                    self.doctor_id = qualified_doctors[0]

    @api.onchange('service_id')
    def _onchange_service_id(self):
        if self.service_id:
            if self.service_id not in self.service_ids:
                self.service_ids = [(4, self.service_id.id)]
            if not self.duration or self.duration == 0.5:
                self.duration = self.service_id.duration or 0.5
            if self.service_id.doctor_ids:
                if not self.doctor_id or self.doctor_id not in self.service_id.doctor_ids:
                    self.doctor_id = self.service_id.doctor_ids[0]

    @api.depends('doctor_id', 'appointment_date', 'start_time', 'duration')
    def _compute_conflict(self):
        for wizard in self:
            if not wizard.doctor_id or not wizard.appointment_date or not wizard.duration:
                wizard.has_conflict = False
                wizard.conflict_details = ""
                continue

            end_time = wizard.start_time + wizard.duration
            other_apts = self.env['medical.appointment'].search([
                ('doctor_id', '=', wizard.doctor_id.id),
                ('appointment_date', '=', wizard.appointment_date),
                ('status', 'not in', ['cancelled', 'no_show']),
            ])

            conflicts = []
            for other in other_apts:
                if wizard.start_time < other.end_time and other.start_time < end_time:
                    conflicts.append(
                        f"• {other.name} ({other.partner_id.name}) {int(other.start_time):02d}:{int((other.start_time % 1)*60):02d} - {int(other.end_time):02d}:{int((other.end_time % 1)*60):02d}"
                    )

            if conflicts:
                wizard.has_conflict = True
                wizard.conflict_details = _("Doctor is already booked for:\n") + "\n".join(conflicts)
            else:
                wizard.has_conflict = False
                wizard.conflict_details = ""

    def action_create_appointment(self):
        import logging
        logger = logging.getLogger(__name__)

        self.ensure_one()
        lead = self.lead_id

        services = self.service_ids or (self.service_id and [self.service_id]) or []
        primary_service = self.service_ids[0] if self.service_ids else self.service_id

        if not services and not primary_service:
            raise ValidationError(_('Please select at least one medical service for the appointment.'))

        # Validate conflicts
        if self.has_conflict:
            if not self.conflict_override:
                raise ValidationError(_(
                    "❌ Doctor Schedule Conflict:\n\n%s\n\n"
                    "Please choose a different time slot or check 'Override Conflict' with an authorized reason."
                ) % self.conflict_details)
            if not self.conflict_override_reason:
                raise ValidationError(_("A reason is mandatory when overriding a scheduling conflict."))

        # Ensure partner is registered as patient
        if self.partner_id and not self.partner_id.is_patient:
            self.partner_id.is_patient = True

        # Build appointment values preserving lead attribution
        appointment_vals = {
            'lead_id': lead.id if lead else False,
            'crm_lead_id': lead.id if lead else False,
            'patient_id': self.partner_id.id,
            'partner_id': self.partner_id.id,
            'doctor_id': self.doctor_id.id,
            'service_id': primary_service.id if primary_service else False,
            'service_ids': [(6, 0, [s.id for s in services])] if services else False,
            'medical_service': primary_service.name if primary_service else False,
            'appointment_date': self.appointment_date,
            'start_time': self.start_time,
            'appointment_time': self.start_time,
            'duration': self.duration,
            'estimated_duration': self.duration,
            'appointment_total': self.total_service_price or (primary_service.final_price if primary_service else 0.0),
            'notes': self.notes,
            'special_requirements': self.special_requirements,
            'status': 'tentative',
            # Preserved Attribution
            'created_by_sales': (lead.user_id.id if (lead and lead.user_id) else (self.salesperson_id.id if self.salesperson_id else self.env.user.id)),
            'salesperson_id': (lead.user_id.id if (lead and lead.user_id) else (self.salesperson_id.id if self.salesperson_id else self.env.user.id)),
            'sales_employee_id': lead.medical_staff_id.id if lead and lead.medical_staff_id else False,
            'source_type': lead.source_type if lead else 'unknown',
            'source_platform': lead.source_platform if lead else 'other',
            'marketing_platform': lead.source_platform if lead else 'other',
            'campaign_name': lead.campaign_name if lead else False,
            'advertisement_name': lead.advertisement_name if lead else False,
            # Overrides
            'conflict_override': self.conflict_override,
            'conflict_override_reason': self.conflict_override_reason if self.conflict_override else False,
        }

        logger.warning(f"APPOINTMENT CREATE DEBUG: appointment_vals = {appointment_vals}")
        try:
            appointment = self.env['medical.appointment'].create(appointment_vals)
            logger.warning(f"APPOINTMENT CREATE SUCCESS: ID = {appointment.id}, NAME = {appointment.name}")
        except Exception as e:
            logger.error(f"APPOINTMENT CREATE ERROR: {str(e)}", exc_info=True)
            raise

        # Update lead stage to Booked if stage exists
        if lead:
            booked_stage = self.env['crm.stage'].search([('name', 'ilike', 'Booked')], limit=1)
            if booked_stage:
                lead.write({'stage_id': booked_stage.id})

        return {
            'name': _('Medical Appointment'),
            'type': 'ir.actions.act_window',
            'res_model': 'medical.appointment',
            'res_id': appointment.id,
            'view_mode': 'form',
            'target': 'current',
        }
