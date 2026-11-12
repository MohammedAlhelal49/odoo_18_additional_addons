from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    website_lead_activity_user_ids = fields.Many2many(
        'res.users',
        string='Website Lead Activity Recipients',
        help='Users who will receive a To-Do activity when a new demo or consultation is requested.'
    )

    crm_reminder_user_ids = fields.Many2many(
        'res.users',
        'crm_inactivity_reminder_users_rel',
        'company_id',
        'user_id',
        string='CRM Inactivity Notification Users'
    )

    crm_inactivity_days = fields.Integer(
        string='Inactivity Period (Days)',
        default=1,
        help="Number of days a lead must be untouched before a reminder is sent."
    )

    enable_deadline_notifications = fields.Boolean(
        string='Enable Deadline Notifications',
        default=False
    )

    deadline_notify_days = fields.Integer(
        string='Notified Before (Days)',
        default=1
    )

    helpdesk_reminder_user_ids = fields.Many2many(
        'res.users',
        'helpdesk_inactivity_reminder_users_rel',
        'company_id',
        'user_id',
        string='Helpdesk Inactivity Notification Users'
    )

    helpdesk_inactivity_days = fields.Integer(
        string='Helpdesk Inactivity Period (Days)',
        default=1,
        help="Number of days a ticket must be untouched before a reminder is sent."
    )
