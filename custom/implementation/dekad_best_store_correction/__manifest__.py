{
    'name': 'Dekad Best Store Correction Center',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'One screen to check and fix every problem found in the Best Store database',
    'description': """
Best Store correction center (Accounting > Accounting > Best Store Correction Center).

Every check runs live on the database of the chosen company and shows its status, records and amount:

Automatic fixes
    * Stock accounting: vendor bills of stored products on a wrong account, stock revaluation, sold part,
      Stock Output, valuation movements without entry, customer payments matching (correction screen with preview).
    * POS receivable account: cancelled / re-issued / edited POS invoices (correction screen with preview).
    * Account types of the fixed asset, depreciation and Stock Input / Output accounts.
    * Product categories not on Average Cost (AVCO).
    * POS categories of products in stock that are not allowed in the Points of Sale.

Fixes after a decision of the accountant
    * Stock Input balance left on products (entry against a chosen account).
    * Fixed asset purchases without an asset (draft assets from a chosen model).
    * POS cash differences booked on a wrong account (keep, or move to the loss / profit account).
    * POS orders with a duplicate invoice (cancel the duplicate with its POS entries).
    * Customer payments not matched with an invoice.

Review lists for the branch
    * Deliveries / receipts not done, inter-company transit, negative stock, zero sales prices, products without
      POS category, duplicate barcodes, duplicate customers, sales to the default customer, cash differences,
      sales without tax, payments not matched with a bank statement, inter-company balances, customer debts.

Replaces the modules dekad_stock_accounting_correction and dekad_pos_receivable_correction.
""",
    'author': 'Dekad',
    'depends': ['account', 'stock_account', 'point_of_sale', 'account_asset'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/stock_accounting_correction_views.xml',
        'wizard/pos_receivable_correction_views.xml',
        'wizard/correction_center_views.xml',
        'views/account_move_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
