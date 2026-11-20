{
    "name": "best store implementation",
    "version": "18.0.0.10",
    'author': 'Dekad',
    "depends": ["base", "account", 'sale', 'hr', 'mail', 'purchase', 'product', 'point_of_sale', 'web',
                'dekad_pos_sale_enhancement', 'dekad_purchase_enhancement','pos_hr', 'dekad_super_user',
                'sale_purchase_stock_inter_company_rules', 'the_best_store_pos_receipt', 'l10n_gcc_invoice'],
    "data": [
        'data/server_actions.xml',
        'security/groups.xml',
        'report/report_saleorder_image.xml',
        'report/purchase_order_report_image.xml',
        'views/sale_oder_line_view.xml',
        'views/purchase_order_line_view.xml',
        'views/account_move_cost_profit_views.xml',
        'views/account_move_paid_by_views.xml',
        'views/res_partner_views.xml',
        'views/pos_order_collection_views.xml',
        'views/report_invoice_car_info.xml',
        'views/hr_employee_views.xml',
        'views/product_template_views.xml',
'views/stock_pickings_views.xml'

    ],
    'assets': {
        'web.assets_backend': [
            'best_store_implementation/static/src/js/list_vertical_navigation.js',
        ],
        'point_of_sale._assets_pos': [
            'best_store_implementation/static/src/js/pos_price_focus.js',
            'best_store_implementation/static/src/js/partner_car_search.js',
            'best_store_implementation/static/src/js/collection/collection_patch.js',
            'best_store_implementation/static/src/js/collection/collect_payment_popup.js',
            'best_store_implementation/static/src/js/collection/ticket_screen_patch.js',
            'best_store_implementation/static/src/js/collection/order_receipt_patch.js',
            'best_store_implementation/static/src/xml/collection/collect_payment_popup.xml',
            'best_store_implementation/static/src/xml/collection/ticket_screen.xml',
            'best_store_implementation/static/src/xml/collection/receipt.xml',
            'best_store_implementation/static/src/js/receipt_notes.js',
            'best_store_implementation/static/src/xml/receipt_notes.xml',
            'best_store_implementation/static/src/js/ticket_screen_search.js',
            'best_store_implementation/static/src/xml/ticket_screen_phone.xml',

        ],
    },

    "application": False,
    "installable": True,
}
