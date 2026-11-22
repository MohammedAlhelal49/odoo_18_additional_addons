# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MedicalAppointmentRescheduleWizard(models.TransientModel):
    _name = 'appointment.reschedule.wizard'
    _description = 'Reschedule Medical Appointment Wizard'

    appointment_id = fields.Many2one('medical.appointment', string='Appointment', required=True)
    current_doctor_id = fields.Many2one(related='appointment_id.doctor_id', string='Current Doctor', readonly=True)
    current_appointment_date = fields.Date(related='appointment_id.appointment_date', string='Current Date', readonly=True)
    current_start_time = fields.Float(related='appointment_id.start_time', string='Current Start Time', readonly=True)
    current_start_time_display = fields.Char(compute='_compute_current_time_display', string='Current Time (HH:MM)', readonly=True)

    new_doctor_id = fields.Many2one(
        'hr.employee',
        string='New Doctor / Provider',
        required=True,
        domain="[('is_appointment_provider', '=', True)]"
    )
    new_appointment_date = fields.Date(string='New Appointment Date', required=True)
    new_start_time = fields.Float(string='New Start Time', required=True, default=9.0)
    reschedule_reason = fields.Text(string='Reason for Rescheduling', required=True)

    @api.model
    def default_get(self, fields_list):
        """Pre-fill wizard with appointment details"""
        res = super().default_get(fields_list)
        appointment_id = self.env.context.get('active_id')
        if appointment_id:
            apt = self.env['medical.appointment'].browse(appointment_id)
            if apt.exists():
                res['appointment_id'] = apt.id
                if 'new_doctor_id' in fields_list:
                    res['new_doctor_id'] = apt.doctor_id.id
                if 'new_appointment_date' in fields_list:
                    res['new_appointment_date'] = apt.appointment_date
                if 'new_start_time' in fields_list:
                    res['new_start_time'] = apt.start_time
        return res

    @api.depends('current_start_time')
    def _compute_current_time_display(self):
        """Convert Float time to HH:MM format"""
        for wizard in self:
            if wizard.current_start_time:
                hours = int(wizard.current_start_time)
                minutes = round((wizard.current_start_time - hours) * 60)
                wizard.current_start_time_display = f"{hours:02d}:{minutes:02d}"
            else:
                wizard.current_start_time_display = ""

    def action_confirm_reschedule(self):
        self.ensure_one()
        apt = self.appointment_id

        if apt.is_time_passed:
            raise ValidationError(_("This appointment has passed its scheduled time and cannot be rescheduled."))
        if apt.is_started:
            raise ValidationError(_("This appointment has already started and cannot be rescheduled."))

        # Verify conflict on candidate slot
        candidate_end_time = self.new_start_time + (apt.duration or apt.estimated_duration or 1.0)

        # Get all appointments for this doctor on that date
        all_appointments = self.env['medical.appointment'].search([
            ('doctor_id', '=', self.new_doctor_id.id),
            ('appointment_date', '=', self.new_appointment_date),
            ('status', 'not in', ['cancelled', 'no_show']),
            ('id', '!=', apt.id),
        ])

        # Check for time overlaps
        conflicts = []
        for existing_apt in all_appointments:
            # Use appointment_time if available, otherwise start_time
            existing_start = existing_apt.appointment_time or existing_apt.start_time
            existing_end = existing_start + (existing_apt.duration or existing_apt.estimated_duration or 1.0) if existing_start else 0

            # Check for overlap
            if existing_start and existing_end:
                # Overlap if: existing_start < new_end AND existing_end > new_start
                if existing_start < candidate_end_time and existing_end > self.new_start_time:
                    conflicts.append(existing_apt)

        if conflicts and not apt.conflict_override:
            conflict_names = ", ".join([c.name for c in conflicts])
            new_start_hour = int(self.new_start_time)
            new_start_min = int((self.new_start_time % 1) * 60)
            new_end_hour = int(candidate_end_time)
            new_end_min = int((candidate_end_time % 1) * 60)

            raise ValidationError(_(
                "❌ Doctor Schedule Conflict:\n"
                "Doctor %s already has appointment(s) %s during this time slot (%02d:%02d - %02d:%02d).\n"
                "Please choose another time or doctor, or obtain supervisor authorization."
            ) % (
                self.new_doctor_id.name, conflict_names,
                new_start_hour, new_start_min,
                new_end_hour, new_end_min
            ))

        old_date = apt.appointment_date
        old_time = apt.start_time
        old_doctor = apt.doctor_id.name

        apt.write({
            'doctor_id': self.new_doctor_id.id,
            'appointment_date': self.new_appointment_date,
            'start_time': self.new_start_time,
            'status': 'tentative',
            'confirmation_call_status': 'rescheduled',
        })

        apt.message_post(
            body=_(
                "📅 <b>Appointment Rescheduled:</b><br/>"
                "• Previous: %s on %s at %02d:%02d<br/>"
                "• New: %s on %s at %02d:%02d<br/>"
                "• Reason: %s<br/>"
                "• Rescheduled by: %s"
            ) % (
                old_doctor, old_date, int(old_time), int((old_time % 1) * 60),
                self.new_doctor_id.name, self.new_appointment_date,
                int(self.new_start_time), int((self.new_start_time % 1) * 60),
                self.reschedule_reason, self.env.user.name
            )
        )

        return {'type': 'ir.actions.act_window_close'}
