# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CrmLeadCallLog(models.Model):
    _name = 'crm.lead.call_log'
    _description = 'Medical CRM Sales Call Log'
    _order = 'call_date desc, id desc'
    _inherit = ['mail.thread']

    lead_id = fields.Many2one(
        'crm.lead',
        string='Lead / Opportunity',
        required=True,
        ondelete='cascade',
        index=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Patient / Contact',
        related='lead_id.partner_id',
        store=True,
        readonly=True
    )
    called_by_id = fields.Many2one(
        'res.users',
        string='Employee / Caller',
        default=lambda self: self.env.user,
        required=True,
        tracking=True
    )
    call_date = fields.Datetime(
        string='Call Date & Time',
        default=fields.Datetime.now,
        required=True,
        tracking=True
    )
    outcome = fields.Selection([
        ('no_answer', 'No Answer'),
        ('contacted', 'Contacted'),
        ('followup_required', 'Follow-up Required'),
        ('interested', 'Interested'),
        ('booked', 'Booked'),
        ('not_interested', 'Not Interested'),
        ('invalid_contact', 'Invalid Contact Information'),
    ], string='Call Outcome', required=True, tracking=True)

    notes = fields.Text(string='Call Notes & Customer Requirements')
    next_followup_date = fields.Date(string='Next Follow-up Date')

    activity_id = fields.Many2one(
        'mail.activity',
        string='Follow-up Activity',
        readonly=True,
        ondelete='set null'
    )

    @api.constrains('call_date')
    def _check_call_date(self):
        for log in self:
            if log.call_date and log.call_date > fields.Datetime.now():
                raise ValidationError(_('Call date cannot be in the future.'))

    @api.constrains('outcome', 'next_followup_date')
    def _check_followup_date_required(self):
        for log in self:
            if log.outcome in ('no_answer', 'followup_required') and not log.next_followup_date:
                raise ValidationError(_(
                    'Next Follow-up Date is required when call outcome is "No Answer" or "Follow-up Required".'
                ))

    @api.model_create_multi
    def create(self, vals_list):
        logs = super().create(vals_list)
        for log in logs:
            log._schedule_followup_activity()
            log._post_lead_chatter_message()
        return logs

    def _schedule_followup_activity(self):
        """Automatically create follow-up activity if outcome requires it"""
        self.ensure_one()
        if self.outcome in ('no_answer', 'followup_required') and self.next_followup_date:
            lead = self.lead_id
            call_type = self.env.ref('mail.mail_activity_data_call', raise_if_not_found=False)
            if not call_type:
                call_type = self.env['mail.activity.type'].search([('category', '=', 'phonecall')], limit=1)

            activity_vals = {
                'res_model_id': self.env['ir.model']._get_id('crm.lead'),
                'res_id': lead.id,
                'activity_type_id': call_type.id if call_type else False,
                'summary': _('Follow-up Call (%s)') % dict(self._fields['outcome'].selection).get(self.outcome),
                'note': self.notes or _('Scheduled follow-up call after: %s') % dict(self._fields['outcome'].selection).get(self.outcome),
                'date_deadline': self.next_followup_date,
                'user_id': lead.user_id.id or self.called_by_id.id,
            }
            activity = self.env['mail.activity'].create(activity_vals)
            self.activity_id = activity.id

            # Update next_followup_date on the lead as well
            lead.write({'next_followup_date': self.next_followup_date})

    def _post_lead_chatter_message(self):
        """Log call summary directly to CRM lead chatter"""
        self.ensure_one()
        outcome_label = dict(self._fields['outcome'].selection).get(self.outcome, self.outcome)
        body = (
            f"<b>📞 Call Logged:</b> {outcome_label}<br/>"
            f"<b>Caller:</b> {self.called_by_id.name}<br/>"
        )
        if self.notes:
            body += f"<b>Notes:</b> {self.notes}<br/>"
        if self.next_followup_date:
            body += f"<b>Next Follow-up:</b> {self.next_followup_date}<br/>"

        self.lead_id.message_post(body=body, message_type='notification')
