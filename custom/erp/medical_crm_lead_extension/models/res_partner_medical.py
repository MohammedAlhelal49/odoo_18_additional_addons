from odoo import fields, models


class ResPartnerMedical(models.Model):
    _inherit = 'res.partner'

    # Medical-specific partner fields
    nationality_id = fields.Many2one(
        'res.country',
        string='Nationality',
        help='Customer/patient nationality'
    )

    medical_record_reference = fields.Char(
        string='Medical Record Reference',
        help='Reference to external medical system (if authorized)',
        groups='medical_crm_lead_extension.group_medical_staff'
    )

    contact_consent = fields.Boolean(
        string='Contact Consent',
        default=False,
        help='Customer has consented to be contacted'
    )

    data_processing_consent = fields.Boolean(
        string='Data Processing Consent',
        default=False,
        help='Customer has consented to data processing'
    )

    preferred_service = fields.Char(
        string='Preferred Medical Service',
        help='Customer\'s preferred medical service or treatment'
    )

    # Link to related CRM leads
    crm_lead_ids = fields.One2many(
        'crm.lead',
        'partner_id',
        string='Related CRM Leads',
        help='CRM leads associated with this contact'
    )
