import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)

class MailActivity(models.Model):
    _inherit = 'mail.activity'

    @api.model_create_multi
    def create(self, vals_list):
        skip_fcm = self.env.context.get('skip_fcm_notification')
        activities = super(MailActivity, self.with_context(skip_fcm_notification=True)).create(vals_list)
        if not skip_fcm:
            for activity in activities:
                if activity.user_id:
                    try:
                        # Notify the assigned user
                        activity.with_context(skip_fcm_notification=False).env['mail.thread'].sudo()._send_fcm_activity_notification(activity)
                    except Exception as e:
                        _logger.error(f"Failed to send FCM notification on activity create: {e}")
        return activities

    def write(self, vals):
        skip_fcm = self.env.context.get('skip_fcm_notification')
        res = super(MailActivity, self.with_context(skip_fcm_notification=True)).write(vals)
        if not skip_fcm and 'user_id' in vals:
            for activity in self:
                if activity.user_id:
                    try:
                        # Notify the newly assigned user
                        activity.with_context(skip_fcm_notification=False).env['mail.thread'].sudo()._send_fcm_activity_notification(activity)
                    except Exception as e:
                        _logger.error(f"Failed to send FCM notification on activity write: {e}")
        return res
