{
    'name': 'Dekad Default Accounting Customer',
    'version': '1.1',
    'category': 'Accounting/Accounting',
    'summary': 'Set a company-level default customer that auto-fills on new Customer Invoices',
    'description': """
Dekad Default Accounting Customer
==================================
Adds a "Default Customer" setting under Accounting Settings.
When a new Customer Invoice / Credit Note is created and the Customer
field is left empty, it is automatically filled with the configured
default customer.
""",
    'author': 'Dekad',
    'website': '',
    'license': 'LGPL-3',
    'depends': ['account'],
    'data': [
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
