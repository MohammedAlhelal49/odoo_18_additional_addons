# -*- coding: utf-8 -*-
from odoo import models
from odoo.osv import expression


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    def _fill_bank_cash_dashboard_data(self, dashboard_data):
        """Extend the core dashboard data with a 'total_balance' key for
        Cash journals, equal to (Balance + Misc. Operations).

        We do NOT touch any existing key in dashboard_data - we only add a
        new one, so the original Balance / Misc. Operations logic (and any
        other module relying on it) is left completely untouched.
        """
        res = super()._fill_bank_cash_dashboard_data(dashboard_data)

        # Always compute Account Total for cash/bank journals, regardless
        # of whether there happen to be any Cash journals in this batch.
        self._fill_gl_account_total(dashboard_data)

        cash_journals = self.filtered(lambda journal: journal.type == 'cash')
        if not cash_journals:
            return res

        # Same "direct bank payments" logic the core uses to build
        # 'account_balance' (see _fill_bank_cash_dashboard_data in
        # account/models/account_journal_dashboard.py)
        direct_payment_balances = cash_journals._get_direct_bank_payments()

        # Same "Misc Entries" domain the core uses to build
        # 'misc_operations_balance'
        misc_domain = []
        for journal in cash_journals:
            date_limit = journal.last_statement_id.date or journal.company_id.fiscalyear_lock_date
            misc_domain.append(
                [('account_id', '=', journal.default_account_id.id), ('date', '>', date_limit)]
                if date_limit else
                [('account_id', '=', journal.default_account_id.id)]
            )
        misc_domain = [
            *self.env['account.move.line']._check_company_domain(self.env.companies),
            ('statement_line_id', '=', False),
            ('parent_state', '=', 'posted'),
            ('payment_id', '=', False),
        ] + expression.OR(misc_domain)

        misc_totals = {
            account: (balance, count_lines, currencies)
            for account, balance, count_lines, currencies in self.env['account.move.line']._read_group(
                domain=misc_domain,
                aggregates=['amount_currency:sum', 'id:count', 'currency_id:recordset'],
                groupby=['account_id'])
        }

        for journal in cash_journals:
            # User may have read access on the journal but not on the company
            currency = journal.currency_id or self.env['res.currency'].browse(
                journal.company_id.sudo().currency_id.id
            )

            nb_direct_payments, direct_payments_balance = direct_payment_balances[journal.id]
            misc_balance, number_misc, misc_currencies = misc_totals.get(
                journal.default_account_id, (0, 0, currency)
            )
            currency_consistent = misc_currencies == currency

            raw_balance = journal.current_statement_balance + direct_payments_balance
            raw_misc = misc_balance if currency_consistent else 0
            raw_total = raw_balance + raw_misc

            dashboard_data[journal.id]['total_balance'] = currency.format(raw_total)

        return res

    def _fill_gl_account_total(self, dashboard_data):
        """Add an 'account_total' key for Cash AND Bank journals, equal to
        the actual General Ledger balance of the journal's underlying
        account (default_account_id): sum(debit - credit) of ALL posted
        entries on that account, with no date/fiscal-year-lock restriction.

        This is intentionally different from 'account_balance' (which is
        based on the bank statement running balance) and from our own
        'total_balance' (statement balance + misc.): this one always
        matches the account's real balance as shown in the General Ledger
        / Trial Balance.
        """
        bank_cash_journals = self.filtered(
            lambda journal: journal.type in ('cash', 'bank') and journal.default_account_id
        )
        if not bank_cash_journals:
            return

        accounts = bank_cash_journals.default_account_id
        domain = [
            *self.env['account.move.line']._check_company_domain(self.env.companies),
            ('account_id', 'in', accounts.ids),
            ('parent_state', '=', 'posted'),
        ]
        account_balances = {
            account: balance
            for account, balance in self.env['account.move.line']._read_group(
                domain=domain,
                aggregates=['balance:sum'],
                groupby=['account_id'],
            )
        }

        for journal in bank_cash_journals:
            # 'balance' on account.move.line is always expressed in the
            # company's currency, so we format using the company currency
            # (not the journal's currency, which may differ for foreign
            # currency bank/cash accounts).
            company_currency = journal.company_id.sudo().currency_id
            raw_account_balance = account_balances.get(journal.default_account_id, 0.0)
            dashboard_data[journal.id]['account_total'] = company_currency.format(raw_account_balance)