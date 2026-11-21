{
    'name': 'POS Stock Warning',
    'version': '18.0.1.1.0',
    'category': 'Point of Sale',
    'summary': 'Restrict or warn cashier when product QTY is zero or negative',
    'author': 'Custom',
    'depends': ['point_of_sale', 'stock'],
    'data': [
        'views/pos_config_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_stock_warning/static/src/js/pos_stock_warning.js',
            'pos_stock_warning/static/src/xml/pos_stock_warning.xml',
        ],
    },
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
