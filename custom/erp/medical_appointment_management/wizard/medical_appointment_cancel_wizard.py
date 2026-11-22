# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MedicalAppointmentCancelWizard(models.TransientModel):
    _name = 'medical.appointment.cancel.wizard'
    _description = 'Cancel Appointment Wizard'

    appointment_id = fields.Many2one('medical.appointment', string='Appointment', required=True)
    cancellation_reason = fields.Text(string='Reason for Cancellation', required=True)

    def action_confirm_cancellation(self):
        self.ensure_one()
        if not self.cancellation_reason:
            raise ValidationError(_('Please provide a reason for cancelling this appointment.'))

        self.appointment_id.write({
            'status': 'cancelled',
            'cancellation_reason': self.cancellation_reason,
            'cancelled_date': fields.Datetime.now(),
            'cancelled_by_id': self.env.user.id,
        })
        return {'type': 'ir.actions.act_window_close'}
