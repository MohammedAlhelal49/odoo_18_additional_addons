from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    website_lead_activity_user_ids = fields.Many2many(
        related='company_id.website_lead_activity_user_ids',
        readonly=False,
        string='Website Lead Activity Recipients'
    )

    crm_reminder_user_ids = fields.Many2many(
        related='company_id.crm_reminder_user_ids',
        readonly=False,
        string='Users to Notify on Inactive Leads'
    )

    crm_inactivity_days = fields.Integer(
        related='company_id.crm_inactivity_days',
        readonly=False,
        string='Inactivity Period (Days)'
    )

    enable_deadline_notifications = fields.Boolean(
        related='company_id.enable_deadline_notifications',
        readonly=False,
        string='Deadline Notifications'
    )

    deadline_notify_days = fields.Integer(
        related='company_id.deadline_notify_days',
        readonly=False,
        string='Notified Before (Days)'
    )

    helpdesk_reminder_user_ids = fields.Many2many(
        related='company_id.helpdesk_reminder_user_ids',
        readonly=False,
        string='Users to Notify on Inactive Tickets'
    )

    helpdesk_inactivity_days = fields.Integer(
        related='company_id.helpdesk_inactivity_days',
        readonly=False,
        string='Helpdesk Inactivity Period (Days)'
    )
