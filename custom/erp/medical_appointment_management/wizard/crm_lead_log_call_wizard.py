# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CrmLeadLogCallWizard(models.TransientModel):
    _name = 'crm.lead.log.call.wizard'
    _description = 'Quick Log Call Wizard'

    lead_id = fields.Many2one('crm.lead', string='Lead / Opportunity', required=True)
    partner_id = fields.Many2one('res.partner', string='Patient / Contact', related='lead_id.partner_id', readonly=True)
    caller_id = fields.Many2one('res.users', string='Employee / Caller', default=lambda self: self.env.user, required=True)
    call_date = fields.Datetime(string='Call Date & Time', default=fields.Datetime.now, required=True)

    outcome = fields.Selection([
        ('no_answer', 'No Answer'),
        ('contacted', 'Contacted'),
        ('followup_required', 'Follow-up Required'),
        ('interested', 'Interested'),
        ('booked', 'Booked'),
        ('not_interested', 'Not Interested'),
        ('invalid_contact', 'Invalid Contact Information'),
    ], string='Call Outcome', required=True, default='contacted')

    notes = fields.Text(string='Call Notes & Customer Feedback')
    next_followup_date = fields.Date(string='Next Follow-up Date')

    is_followup_required = fields.Boolean(
        string='Follow-up Needed',
        compute='_compute_is_followup_required'
    )

    @api.depends('outcome')
    def _compute_is_followup_required(self):
        for wizard in self:
            wizard.is_followup_required = wizard.outcome in ('no_answer', 'followup_required')

    def action_save_call_log(self):
        self.ensure_one()
        if self.outcome in ('no_answer', 'followup_required') and not self.next_followup_date:
            raise ValidationError(_(
                'Next Follow-up Date is required when call outcome is "No Answer" or "Follow-up Required".'
            ))

        log = self.env['crm.lead.call_log'].create({
            'lead_id': self.lead_id.id,
            'called_by_id': self.caller_id.id,
            'call_date': self.call_date,
            'outcome': self.outcome,
            'notes': self.notes,
            'next_followup_date': self.next_followup_date,
        })

        return {'type': 'ir.actions.act_window_close'}
