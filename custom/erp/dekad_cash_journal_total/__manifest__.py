# -*- coding: utf-8 -*-
{
    'name': 'Dekad - Cash Journal Total',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Add a Total (Balance + Misc. Operations) row to Cash journal dashboard cards',
    'description': """
Dekad Cash Journal Total
=========================
Adds a "Total" row to the Cash journal Kanban dashboard card in Accounting,
equal to the sum of the journal's Balance and Misc. Operations amounts.

Only Cash journals are affected. Bank, Sale, Purchase and General journal
cards are left untouched.
    """,
    'author': 'Dekad',
    'depends': ['account'],
    'data': [
        'views/account_journal_dashboard_view.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
