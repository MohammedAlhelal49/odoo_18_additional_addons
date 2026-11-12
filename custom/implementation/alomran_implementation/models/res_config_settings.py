from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    duplicate_contact_policy = fields.Selection([
        ('warning', 'Warning Only'),
        ('block', 'Prevent Duplicates'),
    ], default='warning')



class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    enable_auto_transfer = fields.Boolean(string="Enable Opportunity Transfer after Inactivity")
    auto_transfer_duration_days = fields.Integer(string="Transfer Duration (Days)")
    lead_validity_days = fields.Integer(
        string="Lead Validity (Days)",
        default=31,
        config_parameter='alomran_implementation.lead_validity_days',
        help="Number of FULL days without any update on an opportunity after which it "
             "expires; a customer can be taken over once all its opportunities (won ones included) are expired.",
    )
    # Stored explicitly as 'True'/'False' (see get/set_values): ON by default,
    # and a plain config_parameter boolean cannot remember an unchecked value.
    manual_transfer_enabled = fields.Boolean(
        string="Allow Manual Transfer (Take Over)",
        help="When disabled, nobody can take over an expired customer/lead; "
             "the validity status is still displayed.",
    )
    duplicate_contact_policy = fields.Selection(
        related='company_id.duplicate_contact_policy',
        readonly=False
    )


    def set_values(self):
        super().set_values()
        self.env['ir.config_parameter'].sudo().set_param('alomran_implementation.enable_auto_transfer', self.enable_auto_transfer)
        self.env['ir.config_parameter'].sudo().set_param('alomran_implementation.auto_transfer_duration_days', self.auto_transfer_duration_days)
        self.env['ir.config_parameter'].sudo().set_param(
            'alomran_implementation.manual_transfer_enabled', str(bool(self.manual_transfer_enabled)))

    def get_values(self):
        res = super().get_values()
        res.update({
            'enable_auto_transfer': self.env['ir.config_parameter'].sudo().get_param('alomran_implementation.enable_auto_transfer') == 'True',
            'auto_transfer_duration_days': int(self.env['ir.config_parameter'].sudo().get_param('alomran_implementation.auto_transfer_duration_days', default=10)),
            'manual_transfer_enabled': self.env['alomran.validity.tools']._is_manual_transfer_enabled(),
        })
        return res
