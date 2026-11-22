from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.addons.phone_validation.tools import phone_validation
import logging

_logger = logging.getLogger(__name__)


class CrmLeadMedical(models.Model):
    _inherit = 'crm.lead'

    # Medical Information
    medical_service_ids = fields.Many2many(
        'medical.service',
        'crm_lead_medical_service_rel',
        'lead_id',
        'service_id',
        string='Requested Medical Service',
        help='Types of medical services or consultations requested'
    )

    # Country & Nationality
    country_id = fields.Many2one(
        'res.country',
        string='Country',
        help='Patient or contact country of residence'
    )
    nationality_id = fields.Many2one(
        'res.country',
        string='Nationality',
        help='Patient nationality'
    )

    # Lead Attribution & Source Tracking
    source_type = fields.Selection(
        [('paid', 'Paid'),
         ('organic', 'Organic'),
         ('referral', 'Referral'),
         ('direct', 'Direct'),
         ('offline', 'Offline'),
         ('unknown', 'Unknown')],
        string='Source Type',
        default='unknown',
        help='Type of lead source: Paid advertising, Organic search, Referral, Direct contact, Offline, or Unknown'
    )

    source_platform = fields.Selection(
        [('facebook', 'Facebook'),
         ('instagram', 'Instagram'),
         ('whatsapp', 'WhatsApp'),
         ('website', 'Website'),
         ('google', 'Google'),
         ('offline', 'Offline'),
         ('phone', 'Phone Call'),
         ('email', 'Email'),
         ('referral', 'Referral'),
         ('other', 'Other')],
        string='Source Platform',
        help='Platform where the lead originated'
    )

    source_details = fields.Text(
        string='Source Details',
        help='Additional details about the lead source (e.g., landing page, referral source, etc.)'
    )

    # Lead Received Timestamp
    lead_received_date = fields.Datetime(
        string='Lead Received Date',
        default=fields.Datetime.now,
        help='Date and time when the lead was received'
    )

    # Campaign & Advertisement Links (Many2one relationships created after campaign module is available)
    # These will reference medical_campaign_advertisement module models
    campaign_name = fields.Char(
        string='Campaign Name',
        help='Internal name of the associated campaign (when campaign module is available)'
    )

    advertisement_name = fields.Char(
        string='Advertisement Name',
        help='Internal name of the associated advertisement (when advertisement module is available)'
    )

    # Expected Revenue (already in standard CRM, but explicitly for medical context)
    # expected_revenue field is inherited from crm.lead

    # Follow-up Tracking
    next_followup_date = fields.Date(
        string='Next Follow-up Date',
        help='Scheduled date for next follow-up activity'
    )

    # Internal Notes (mail.thread provides activity history)
    internal_notes = fields.Text(
        string='Internal Notes',
        help='Internal notes and observations about the lead'
    )

    # Duplicate Phone Detection
    potential_duplicate_lead_ids = fields.Many2many(
        'crm.lead',
        'crm_lead_duplicate_rel',
        'lead_id',
        'duplicate_id',
        string='Potential Duplicate Leads',
        compute='_compute_duplicate_phone_warning',
        help='Leads with similar phone numbers that may be duplicates'
    )

    duplicate_phone_warning = fields.Boolean(
        string='Duplicate Phone Warning',
        compute='_compute_duplicate_phone_warning',
        search='_search_duplicate_phone_warning',
        store=False,
        help='True if a potential duplicate phone number is detected'
    )

    # Medical Record Reference (if applicable, with access restrictions)
    medical_record_reference = fields.Char(
        string='Medical Record Reference',
        help='Reference to external medical record system (if authorized)',
        groups='medical_crm_lead_extension.group_medical_staff'
    )

    # Consent & Compliance Fields
    contact_consent = fields.Boolean(
        string='Contact Consent',
        default=False,
        help='Customer has consented to be contacted'
    )

    data_processing_consent = fields.Boolean(
        string='Data Processing Consent',
        default=False,
        help='Customer has consented to data processing and storage'
    )

    # Activity Fields for Medical Context
    last_activity_date = fields.Datetime(
        string='Last Activity Date',
        compute='_compute_last_activity_date',
        store=False,
        help='Date of the most recent activity (call, email, meeting, etc.)'
    )

    @api.depends('activity_ids')
    def _compute_last_activity_date(self):
        """Compute the last activity date based on mail.thread activities"""
        for lead in self:
            activities = lead.activity_ids
            if activities:
                lead.last_activity_date = max(activity.create_date for activity in activities)
            else:
                lead.last_activity_date = lead.create_date

    @api.depends('phone', 'mobile')
    def _compute_duplicate_phone_warning(self):
        """Check for duplicate phone numbers in other leads"""
        for lead in self:
            duplicates = self._find_duplicate_leads(lead)
            lead.duplicate_phone_warning = bool(duplicates)
            lead.potential_duplicate_lead_ids = duplicates

    def _search_duplicate_phone_warning(self, operator, value):
        """Enable search and filter on duplicate_phone_warning"""
        if operator not in ('=', '!='):
            raise NotImplementedError(_('Operation not supported'))
        target_val = bool(value) if operator == '=' else not bool(value)
        self.env.cr.execute("""
            SELECT id FROM crm_lead WHERE (phone IS NOT NULL AND phone != '' AND regexp_replace(phone, '[^0-9]', '', 'g') IN (
                SELECT regexp_replace(phone, '[^0-9]', '', 'g') FROM crm_lead
                WHERE phone IS NOT NULL AND phone != ''
                GROUP BY regexp_replace(phone, '[^0-9]', '', 'g') HAVING count(*) > 1
            )) OR (mobile IS NOT NULL AND mobile != '' AND regexp_replace(mobile, '[^0-9]', '', 'g') IN (
                SELECT regexp_replace(mobile, '[^0-9]', '', 'g') FROM crm_lead
                WHERE mobile IS NOT NULL AND mobile != ''
                GROUP BY regexp_replace(mobile, '[^0-9]', '', 'g') HAVING count(*) > 1
            ))
        """)
        duplicate_ids = [r[0] for r in self.env.cr.fetchall()]
        if target_val:
            return [('id', 'in', duplicate_ids)]
        else:
            return [('id', 'not in', duplicate_ids)]

    def _find_duplicate_leads(self, lead=None):
        """Find leads with similar phone numbers (normalized)"""
        lead = lead or self
        duplicate_leads = self.env['crm.lead']
        lead_id = lead._origin.id if hasattr(lead, '_origin') and lead._origin else (lead.id or 0)

        if lead.phone:
            normalized_phone = self._normalize_phone(lead.phone)
            if normalized_phone:
                self.env.cr.execute("""
                    SELECT id FROM crm_lead
                    WHERE id != %s
                      AND (
                        regexp_replace(phone, '[^0-9]', '', 'g') = %s
                        OR regexp_replace(mobile, '[^0-9]', '', 'g') = %s
                      )
                    LIMIT 10
                """, (lead_id, normalized_phone, normalized_phone))
                dup_ids = [r[0] for r in self.env.cr.fetchall()]
                if dup_ids:
                    duplicate_leads |= self.browse(dup_ids)

        if lead.mobile:
            normalized_mobile = self._normalize_phone(lead.mobile)
            if normalized_mobile:
                self.env.cr.execute("""
                    SELECT id FROM crm_lead
                    WHERE id != %s
                      AND (
                        regexp_replace(phone, '[^0-9]', '', 'g') = %s
                        OR regexp_replace(mobile, '[^0-9]', '', 'g') = %s
                      )
                    LIMIT 10
                """, (lead_id, normalized_mobile, normalized_mobile))
                dup_ids = [r[0] for r in self.env.cr.fetchall()]
                if dup_ids:
                    duplicate_leads |= self.browse(dup_ids)

        return duplicate_leads

    def _normalize_phone(self, phone_str):
        """Normalize phone number for comparison (remove non-numeric characters)"""
        if not phone_str:
            return None
        normalized = ''.join(c for c in phone_str if c.isdigit())
        return normalized if normalized else None

    @api.constrains('date_deadline', 'lead_received_date')
    def _check_date_consistency(self):
        """Ensure date_deadline is after lead_received_date"""
        for lead in self:
            if lead.date_deadline and lead.lead_received_date:
                if lead.date_deadline < lead.lead_received_date.date():
                    raise ValidationError(
                        _('The deadline date cannot be earlier than the lead received date.')
                    )

    @api.constrains('expected_revenue')
    def _check_expected_revenue_non_negative(self):
        """Ensure expected revenue is non-negative"""
        for lead in self:
            if lead.expected_revenue < 0:
                raise ValidationError(
                    _('Expected revenue must be a non-negative value.')
                )

    def action_view_duplicate_leads(self):
        """Open a list view of potential duplicate leads"""
        self.ensure_one()
        duplicates = self._find_duplicate_leads(self)
        return {
            'name': _('Potential Duplicate Leads'),
            'view_mode': 'list,form',
            'res_model': 'crm.lead',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', duplicates.ids)],
            'context': {'default_type': 'lead'},
        }

    def _log_lead_creation(self):
        """Log lead creation details for audit"""
        for lead in self:
            services = ', '.join(lead.medical_service_ids.mapped('name')) if lead.medical_service_ids else 'Not specified'
            message = f"Lead created. Source: {lead.source_platform or 'Unknown'}. Services: {services}"
            lead.message_post(body=message, message_type='comment')

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set default lead_received_date and log creation"""
        for vals in vals_list:
            if 'lead_received_date' not in vals:
                vals['lead_received_date'] = fields.Datetime.now()

        leads = super().create(vals_list)
        leads._log_lead_creation()
        return leads

    @api.constrains('source_type', 'source_platform')
    def _check_source_consistency(self):
        """Validate that source_type and source_platform are consistent"""
        for lead in self:
            # If offline platform is selected, source_type should typically be 'offline'
            if lead.source_platform == 'offline' and lead.source_type not in ('offline', 'unknown'):
                _logger.warning(
                    f"Lead {lead.id}: offline platform selected but source_type is {lead.source_type}"
                )
