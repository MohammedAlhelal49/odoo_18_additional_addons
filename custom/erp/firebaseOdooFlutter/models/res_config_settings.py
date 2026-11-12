from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    fcm_api_type = fields.Selection([
        ('legacy', 'Legacy HTTP API'),
        ('v1', 'HTTP v1 API (Service Account)')
    ], string='FCM API Type', default='legacy', config_parameter='firebaseOdooFlutter.api_type')
    fcm_server_key = fields.Char(string='FCM Server Key (Legacy)', config_parameter='firebaseOdooFlutter.server_key')
    fcm_sender_id = fields.Char(string='FCM Sender ID', config_parameter='firebaseOdooFlutter.sender_id')
    fcm_retention_days = fields.Integer(
        string='Notification Store Duration (Days)',
        default=30,
        config_parameter='firebaseOdooFlutter.retention_days',
        help='Number of days to store notifications in database before deleting them. Default is 30 days.'
    )
    
    # Manual sync for Text fields to avoid Odoo 18 settings limitations with config_parameter
    fcm_service_account = fields.Text(string='Service Account JSON (v1)')
    fcm_custom_data = fields.Text(string='Custom Data (JSON)', 
                                help="Additional JSON data to send with every notification. E.g. {'key': 'value'}")
    fcm_app_config = fields.Text(string='App Configuration (JSON)',
                                help="Additional JSON configuration for the Flutter mobile application.")

    # App Version & Configuration settings
    fcm_app_version = fields.Char(string='Latest App Version', default='1.0.0', config_parameter='firebaseOdooFlutter.app_version')
    fcm_min_app_version = fields.Char(string='Minimum Required App Version', default='1.0.0', config_parameter='firebaseOdooFlutter.min_app_version')
    fcm_force_update = fields.Boolean(string='Force App Update', default=False, config_parameter='firebaseOdooFlutter.force_update')
    fcm_app_url_android = fields.Char(string='Android Store URL', config_parameter='firebaseOdooFlutter.app_url_android')
    fcm_app_url_ios = fields.Char(string='iOS Store URL', config_parameter='firebaseOdooFlutter.app_url_ios')

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        retention = params.get_param('firebaseOdooFlutter.retention_days', default=30)
        res.update(
            fcm_service_account=params.get_param('firebaseOdooFlutter.service_account'),
            fcm_custom_data=params.get_param('firebaseOdooFlutter.custom_data'),
            fcm_app_config=params.get_param('firebaseOdooFlutter.app_config'),
            fcm_retention_days=int(retention) if str(retention).isdigit() else 30,
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('firebaseOdooFlutter.service_account', self.fcm_service_account)
        params.set_param('firebaseOdooFlutter.custom_data', self.fcm_custom_data)
        params.set_param('firebaseOdooFlutter.app_config', self.fcm_app_config)
        params.set_param('firebaseOdooFlutter.retention_days', str(self.fcm_retention_days or 30))

