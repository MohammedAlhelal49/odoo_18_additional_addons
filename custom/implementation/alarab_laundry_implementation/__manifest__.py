# custom_pos_receipt/__manifest__.py
{
    'name': 'alarab_laundry_implementation',
    'version': '18.0.1.6',
    'category': 'Point of Sale',
    'summary': 'Add customer details to POS receipt',
    'depends': ['base','sale','account','point_of_sale','contacts' , 'dekad_additional_features', 'l10n_ae',
                'dekad_pos_sale_enhancement'],
    'data': [
        'data/quotation_order.xml',
        'views/pos_invoice_menu.xml',
        "views/report_invoice.xml",
        "views/pos_order_views.xml",

    ],
    'assets': {
        'web.assets_backend': [
            '/alarab_laundry_implementation/static/src/js/open_whatsapp_action.js',
        ],
        'point_of_sale._assets_pos': [
            '/alarab_laundry_implementation/static/src/js/pos_receipt.js',
            '/alarab_laundry_implementation/static/src/js/partner_list_patch.js',
            '/alarab_laundry_implementation/static/src/js/whatsapp_invoice.js',
            '/alarab_laundry_implementation/static/src/xml/pos_receipt_template.xml',
            '/alarab_laundry_implementation/static/src/scss/receipt.css',
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
}
