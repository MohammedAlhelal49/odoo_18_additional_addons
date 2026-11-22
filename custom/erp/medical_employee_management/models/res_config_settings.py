# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResConfigSettingsMedicalEmployee(models.TransientModel):
    _inherit = 'res.config.settings'

    standard_working_hours_per_week = fields.Float(
        string='Standard Weekly Working Hours',
        default=40.0,
        config_parameter='medical_employee.default_working_hours',
        help='Default expected weekly working hours for newly registered medical center staff'
    )
    require_doctor_specialization = fields.Boolean(
        string='Require Doctor Specialization',
        default=True,
        config_parameter='medical_employee.require_specialization',
        help='Prompt for medical specialization when designating an employee as Doctor'
    )
