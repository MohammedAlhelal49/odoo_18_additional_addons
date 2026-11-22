{
    'name': 'Medical CRM Lead Extension',
    'version': '18.0.1.0',
    'category': 'Sales/CRM',
    'sequence': 14,
    'summary': 'Extend CRM leads with medical fields, attribution tracking, and duplicate detection',
    'description': """
Medical CRM Lead Extension
==========================

Extends the standard Odoo CRM Lead model with:
* Medical service tracking and consultation requests
* Lead attribution and external platform tracking (Facebook, Instagram, WhatsApp, etc.)
* Lead source categorization (Paid, Organic, Referral, Direct, Offline)
* Phone number duplicate detection with warnings
* Campaign and advertisement linking
* Activity history and follow-up tracking for medical context

Compatible with medical_campaign_advertisement, medical_lead_attribution, and medical_social_integration modules.
    """,
    'author': 'Medical Center',
    'website': 'https://www.medical-center.example.com',
    'images': ['static/description/icon.png'],
    'depends': [
        'crm',
        'sales_team',
        'contacts',
        'utm',
        'mail',
        'phone_validation',
    ],
    'data': [
        'security/lead_security_rules.xml',
        'security/ir.model.access.csv',
        'data/crm_lead_stage_data.xml',
        'views/crm_lead_views.xml',
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
