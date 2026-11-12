# -*- coding: utf-8 -*-
{
    'name': 'Dekad Company',
    'version': '18.0.4.0.0',
    'summary': 'All features for Dekad Company.',
    'description': """
        This module implements internal features for Dekad.
        Key Features:
        - CRM lead inactivity reminders with filters and group by.
        - Helpdesk tickets inactivity reminders with filters and group by.
        - Convert a helpdesk ticket to CRM lead.
        - Create a project from CRM lead.
        - Project and task reminder.
        - Technical proposals and contracts.
        - Transaltion wizard.
    """,
    'author': 'Dekad (Mofeed Dozkanji)',
    'website': 'https://www.dekad.tech',
    'depends': [
      'web',
        'base',
        'crm',
        'project',
        'helpdesk',
        'sale',
        'mail',
        'sale',
        'sale_management'
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'views/res_config_settings_views.xml',
        'views/crm_lead_views.xml',
        'views/helpdesk_ticket_views.xml',
        'views/translation_wizard_views.xml',
        'views/sale_order_views.xml',
        'reports/proposal_report.xml',
        'reports/proposal_report_arabic.xml',
        'reports/daem_contract_report_arabic.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
