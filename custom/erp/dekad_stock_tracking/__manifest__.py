{
    'name': 'Dekad Stock Tracking',
    'version': '18.0.1.0.0',
    'category': 'Inventory',
    'summary': 'Add shipment tracking fields on stock picking header and lines',
    'depends': ['stock', 'stock_enterprise', 'sale_stock', 'purchase_stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_picking_views.xml',
        'views/stock_move_views.xml',
        'views/stock_move_line_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
