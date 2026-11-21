{
    'name': 'The Best Store POS Receipt',
    'version': '18.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Custom POS receipt for The Best Store',
    'author': 'Dekad',
    'depends': ['point_of_sale'],
    'assets': {
        'point_of_sale._assets_pos': [
            'the_best_store_pos_receipt/static/src/css/receipt.css',
            'the_best_store_pos_receipt/static/src/js/order_receipt_patch.js',
            'the_best_store_pos_receipt/static/src/xml/receipt.xml',
        ],
    },
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
