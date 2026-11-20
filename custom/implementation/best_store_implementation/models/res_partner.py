# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    car_plate_number = fields.Char(string='Car Plate Number')
    car_serial_number = fields.Char(string='Car Serial Number (VIN)')

    @api.model
    def _load_pos_data_fields(self, config_id):
        params = super()._load_pos_data_fields(config_id)
        for field_name in ('car_plate_number', 'car_serial_number'):
            if field_name not in params:
                params = params + [field_name]
        return params
