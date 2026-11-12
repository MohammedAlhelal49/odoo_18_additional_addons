# -*- coding: utf-8 -*-
{
    'name': 'Dekad Website',
    'version': '18.0.4.0.0',
    'category': 'Website',
    'summary': (
        'Code-driven Dekad theme built on top of the Website app '
        '(no Drag & Drop / snippets for the core layout)'
    ),
    'description': """
Dekad Website
==================
Corporate financial-services website built as a code-driven theme on
top of Odoo's Website app: QWeb templates inheriting website.layout,
with a refined Dekad design system layered over the existing frontend assets.

The page structure and design are controlled entirely by code (this
module), NOT by dragging/dropping Website Builder snippets. The
Website app is used for what it's genuinely good at - multi-language
routing, RTL, SEO (meta/canonical), menu/session/auth handling, and
the frontend asset pipeline - so none of that has to be rebuilt by
hand.

Pages served:
 - /                 Home
 - /about            About Us
 - /services         Our Services
 - /elements         UI Elements
 - /blog             Blog listing & posts (Odoo's website_blog app)
 - /contact          Contact Us (working contact form)
""",
    'author': 'Dekad',
    'website': 'https://dekad.tech',
    'license': 'LGPL-3',
    'depends': ['website', 'website_blog', 'helpdesk'],
    'data': [
        'security/ir.model.access.csv',
        'views/layout_templates.xml',
        'views/portal_templates.xml',
        'views/pages_home.xml',
        'views/pages_about.xml',
        'views/pages_contact.xml',
        'views/pages_privacy.xml',
        'views/pages_lead_forms.xml',
        'views/success_modal_template.xml',
        'views/ticket_templates.xml',
        'views/blog_theme.xml',
        'views/login_theme.xml',
        'views/contact_submission_views.xml',
        'views/client_backend_views.xml',
        'views/client_import_wizard_views.xml',
        'views/client_templates.xml',
        'views/app_templates.xml',
        'views/industry_templates.xml',
        'views/service_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            # CSS only - safe to include via the standard bundle since
            # only JS gets auto-wrapped in odoo.define().
            'dekad_website/static/src/css/animate.css',
            'dekad_website/static/src/css/bootstrap.min.css',
            'dekad_website/static/src/css/classy-nav.css',
            'dekad_website/static/src/css/credit-icon.css',
            'dekad_website/static/src/css/font-awesome.min.css',
            'dekad_website/static/src/css/owl.carousel.min.css',
            'dekad_website/static/src/css/style.css',
            'dekad_website/static/src/css/custom-override.css',
            'dekad_website/static/src/css/dekad-v4.css',
            # JS deliberately NOT here - loaded as plain <script src>
            # tags directly from layout_templates.xml instead, right
            # after our footer. That way it runs exactly once, in the
            # exact order these old jQuery plugins expect, with zero
            # risk of Odoo's own module-loader wrapping (odoo.define)
            # or of double-initializing anything in web.assets_frontend.
        ],
    },
    'installable': True,
    'application': True,
}