from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    dekad_trade_license = fields.Char(
        string='Trade Licence No.',
        help='Commercial registration / trade licence number printed in the implementation contract.')

    def ct_address(self):
        """One-line address: street, street 2, city, state, country (empty parts skipped)."""
        self.ensure_one()
        parts = [self.street, self.street2, self.city, self.state_id.name, self.country_id.name]
        return ', '.join(part.strip() for part in parts if part and part.strip())
