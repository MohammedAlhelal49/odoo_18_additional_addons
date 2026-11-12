from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    api_token = fields.Char(
        string="API Token",
        help="Bearer token used to authorize requests to the Orchida API.",
    )
    orchida_base_url = fields.Char(
        string="Orchida Base URL",
        help="Base API URL (must start with http:// or https://).",
    )
    companyid = fields.Char(
        string="Orchida Company ID",
        help="Company identifier sent in request header Company-id.",
    )
    orchida_auto_submit_einvoice = fields.Boolean(
        string='Send Automatically on Posting',
        default=True,
        help='Submit eligible invoices immediately when posted. Disable to send them manually later.',
    )
    last_ap_sync_date = fields.Datetime(string="Last AP Sync Date")
    last_ar_sync_date = fields.Datetime(string="Last AR Sync Date")


class ResConfigSettingsApiToken(models.TransientModel):
    _inherit = 'res.config.settings'

    URL_Orchida = fields.Char(
        related='company_id.orchida_base_url',
        string="Base URL",
        readonly=False,
        help="Base API URL (must start with http:// or https://).",
    )
    api_token = fields.Char(
        related='company_id.api_token',
        string="API Token",
        readonly=False,
        help="Bearer token used to authorize requests to the Orchida API.",
    )
    companyid = fields.Char(
        related='company_id.companyid',
        string="Orchida Company ID",
        readonly=False,
        help="Company identifier sent in request header Company-id.",
    )
    orchida_auto_submit_einvoice = fields.Boolean(
        related='company_id.orchida_auto_submit_einvoice',
        string='Send Automatically on Posting',
        readonly=False,
    )
    orchida_connector_enabled = fields.Boolean(
        related='company_id.orchida_connector_enabled',
        readonly=False,
    )
