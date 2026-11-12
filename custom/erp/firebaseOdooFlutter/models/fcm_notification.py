from odoo import fields, models, api
import json
import logging
from datetime import timedelta

_logger = logging.getLogger(__name__)

class FcmNotification(models.Model):
    _name = 'fcm.notification'
    _description = 'FCM Notification Log'
    _order = 'create_date desc'

    partner_id = fields.Many2one('res.partner', string='Recipient', required=True, ondelete='cascade', index=True)
    device_id = fields.Many2one('fcm.device', string='Device', ondelete='cascade')
    title = fields.Char(string='Title')
    body = fields.Text(string='Body')
    
    # Detailed Data fields
    res_model = fields.Char(string='Model', index=True)
    res_id = fields.Integer(string='Resource ID', index=True)
    record_name = fields.Char(string='Record Name')
    notification_type = fields.Char(string='Notification Type', index=True)
    click_url = fields.Char(string='Click URL')
    
    fcm_data = fields.Text(string='FCM Data (JSON)', help='Raw data payload sent to FCM')
    server_url = fields.Char(string='Server URL', help='Odoo server base URL')
    dbname = fields.Char(string='Database Name', help='Odoo database name')
    status = fields.Selection([
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ], string='Status', default='pending')
    error_message = fields.Text(string='Error Message')

    is_read = fields.Selection([
        ('read', 'Read'),
        ('notread', 'Not Read'),
    ], string='Is Read', default='notread', required=True, index=True)

    expiration_date = fields.Datetime(
        string='Expiration Date',
        index=True,
        help='Date after which this notification will be automatically deleted.'
    )

    @api.model_create_multi
    def create(self, vals_list):
        params = self.env['ir.config_parameter'].sudo()
        retention_days_str = params.get_param('firebaseOdooFlutter.retention_days', '30')
        try:
            retention_days = int(retention_days_str)
        except (ValueError, TypeError):
            retention_days = 30

        now = fields.Datetime.now()
        for vals in vals_list:
            if not vals.get('expiration_date'):
                create_date = fields.Datetime.to_datetime(vals.get('create_date')) if vals.get('create_date') else now
                vals['expiration_date'] = create_date + timedelta(days=retention_days)
            if not vals.get('is_read'):
                vals['is_read'] = 'notread'

        return super().create(vals_list)

    def action_mark_as_read(self):
        self.write({'is_read': 'read'})

    def action_mark_as_not_read(self):
        self.write({'is_read': 'notread'})

    @api.model
    def _gc_expired_notifications(self):
        """Delete notifications that have reached their expiration date."""
        now = fields.Datetime.now()
        expired_notifications = self.sudo().search([('expiration_date', '<=', now)])
        count = len(expired_notifications)
        if count:
            _logger.info("FCM GC: Deleting %s expired notification(s).", count)
            expired_notifications.unlink()
        return True

    @api.model
    def get_notifications_by_user_id(self, user_id, start_date=None, end_date=None, limit=50):
        """Fetch notifications for a specific user ID with optional start_date and end_date filtering."""
        user = self.env['res.users'].sudo().browse(int(user_id))
        if not user.exists():
            return []
            
        domain = [('partner_id', '=', user.partner_id.id)]

        if start_date:
            s_date = str(start_date).strip()
            if len(s_date) == 10:  # YYYY-MM-DD
                s_date = f"{s_date} 00:00:00"
            domain.append(('create_date', '>=', s_date))

        if end_date:
            e_date = str(end_date).strip()
            if len(e_date) == 10:  # YYYY-MM-DD
                e_date = f"{e_date} 23:59:59"
            domain.append(('create_date', '<=', e_date))

        search_limit = limit if limit else None

        notifications = self.search(domain, limit=search_limit)
        return [{
            'id': n.id,
            'title': n.title,
            'body': n.body,
            'res_model': n.res_model,
            'res_id': n.res_id,
            'record_name': n.record_name,
            'type': n.notification_type,
            'url': n.click_url,
            'fcm_data': n.fcm_data,
            'status': n.status,
            'create_date': fields.Datetime.to_string(n.create_date) if n.create_date else False,
            'is_read': n.is_read or 'notread',
            'expiration_date': fields.Datetime.to_string(n.expiration_date) if n.expiration_date else False,
        } for n in notifications]
