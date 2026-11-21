{
    'name': 'Custom Invoice: Secondary Bubble Layout',
    'version': '1.1',
    'category': 'Accounting/Accounting',
    'summary': 'Adds a secondary "Bubble" print option for invoices while keeping the company default layout intact.',
    'description': 'Provides a custom QWeb report action to print invoices using the Enterprise Bubble layout on demand.',
    'depends': ['account'],
    'data': [
        'views/account_move_views.xml',
        'views/report_invoice_custom.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
