from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    dekad_signature = fields.Binary(string='User Signature', attachment=True)

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + ['dekad_signature']
