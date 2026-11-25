# -*- coding: utf-8 -*-
{
    'name': 'Al Omran Engineering Consultants Website',
    'version': '18.0.1.0.0',
    'category': 'Website',
    'summary': 'Modern bilingual (EN/AR) website for Al Omran International Engineering Consultants',
    'description': """
Al Omran International Engineering Consultants — Website
========================================================
Code-driven corporate website built on top of Odoo's Website app,
tailored to the UAE engineering-consultancy market.

Pages:
 - /                     Home
 - /about                About us & team
 - /services             Services (architecture, structure, MEP, approvals, supervision...)
 - /projects             Portfolio (managed from the backend)
 - /projects/<id>        Project details
 - /contact              Contact & consultation request (creates an inquiry + CRM lead if CRM is installed)

All page texts live in controllers/content.py (English + Arabic side by side).
Portfolio projects are records of `alomran.eng.project` (translatable).
""",
    'author': 'Dekad',
    'website': 'https://alomran-int.ae',
    'license': 'LGPL-3',
    'depends': ['website', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/layout.xml',
        'views/pages_home.xml',
        'views/pages_about.xml',
        'views/pages_services.xml',
        'views/pages_projects.xml',
        'views/pages_contact.xml',
        'views/backend_views.xml',
        'data/project_data.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'alomran_engineering_website/static/src/css/aoe.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
