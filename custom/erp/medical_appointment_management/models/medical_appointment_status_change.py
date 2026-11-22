# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class MedicalAppointmentStatusChange(models.Model):
    _name = 'medical.appointment.status_change'
    _description = 'Medical Appointment Status Audit History'
    _order = 'change_date desc, id desc'

    appointment_id = fields.Many2one(
        'medical.appointment',
        string='Appointment',
        required=True,
        ondelete='cascade',
        index=True
    )
    old_status = fields.Char(string='Old Status')
    new_status = fields.Char(string='New Status')
    change_date = fields.Datetime(string='Change Date', default=fields.Datetime.now, required=True)
    changed_by_id = fields.Many2one(
        'res.users',
        string='Changed By',
        default=lambda self: self.env.user,
        required=True
    )
    reason = fields.Text(string='Reason / Notes')
