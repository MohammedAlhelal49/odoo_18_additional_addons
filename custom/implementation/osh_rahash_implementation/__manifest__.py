{
    'name': 'OSH Rahash POS Receipt',
    'version': '18.0.1.13.0',
    'category': 'Point of Sale',
    'summary': 'Custom POS customer receipt and 38 x 25 mm product barcode labels for OSH Rahash',
    'author': 'Dekad',
    'depends': ['point_of_sale', 'product'],
    'data': [
        'report/paperformat.xml',
        'report/product_label_templates.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'osh_rahash_implementation/static/src/css/receipt.css',
            'osh_rahash_implementation/static/src/js/order_receipt_patch.js',
            'osh_rahash_implementation/static/src/xml/receipt.xml',
        ],
    },
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
