# -*- coding: utf-8 -*-
"""
Analytic share for the General Ledger and the Trial Balance
===========================================================

When an analytic filter or an analytic group is applied, every journal item
must count only for the share of its analytic distribution that belongs to
the selected analytic accounts (no double counting when a line is split).

Mechanism (same idea as Odoo's analytic columns, see account_reports
account_analytic_report.py): the table account_move_line is shadowed, for the
SQL queries of the report, by a temporary table holding the same journal items
(same ids, so links, audit and joins on the id keep working) whose amounts are
multiplied by the share of the selected analytic accounts:

    share = SUM(percentages of the distribution keys containing one of the
                selected accounts) / 100

A key "dubai,sales" (one line tagged in two analytic plans) is counted once,
so selecting accounts of several plans never counts a line twice.

The scope is carried by options['dekad_analytic_scope'] (sorted tuple of
analytic account ids). Without it nothing changes: the reports keep their
standard behaviour.
"""
import hashlib

from odoo import _, api, models
from odoo.tools.sql import SQL


def _scope_table_name(scope):
    key = ','.join(str(i) for i in scope)
    return 'dekad_analytic_share_' + hashlib.md5(key.encode()).hexdigest()[:16]


class AccountReport(models.Model):
    _inherit = 'account.report'

    def _get_report_query(self, options, date_scope, domain=None):
        scope = options.get('dekad_analytic_scope')
        if scope:
            # The context is read by account.move.line._where_calc below.
            self = self.with_context(dekad_analytic_scope=tuple(scope))
        return super(AccountReport, self)._get_report_query(options, date_scope, domain=domain)

    @api.model
    def _dekad_prepare_analytic_share_table(self, scope):
        """Create (once per transaction) the shadow table for this analytic scope."""
        table = _scope_table_name(scope)
        self.env.cr.execute("SELECT to_regclass(%s)", [table])
        if self.env.cr.fetchone()[0]:
            return table

        share = SQL(
            """COALESCE((
                SELECT SUM(dk_e.value::numeric)
                  FROM jsonb_each_text(account_move_line.analytic_distribution) dk_e
                 WHERE string_to_array(dk_e.key, ',')::int[] && %s::int[]
            ), 0) / 100.0""",
            list(scope),
        )
        debit = SQL("ROUND(account_move_line.debit * %s, dk_cc.decimal_places)", share)
        credit = SQL("ROUND(account_move_line.credit * %s, dk_cc.decimal_places)", share)
        change_equivalence_dict = {
            'debit': debit,
            'credit': credit,
            'balance': SQL("(%s) - (%s)", debit, credit),
            'amount_currency': SQL(
                "ROUND(account_move_line.amount_currency * %s, COALESCE(dk_lc.decimal_places, 2))", share),
        }
        for fname, field in self.env['account.move.line']._fields.items():
            if field.store and field.column_type and fname not in change_equivalence_dict:
                change_equivalence_dict[fname] = SQL('account_move_line.%s', SQL.identifier(fname))
        stored_fields, fields_to_insert = self.env['account.move.line']._prepare_aml_shadowing_for_report(
            change_equivalence_dict)

        self.env.cr.execute(SQL(
            """
            CREATE TEMPORARY TABLE %(table)s () INHERITS (account_move_line) ON COMMIT DROP;
            ALTER TABLE %(table)s NO INHERIT account_move_line;
            ALTER TABLE %(table)s DROP CONSTRAINT IF EXISTS account_move_line_check_amount_currency_balance_sign;

            INSERT INTO %(table)s (%(stored_fields)s)
            SELECT %(fields_to_insert)s
              FROM account_move_line
              JOIN res_company dk_company ON dk_company.id = account_move_line.company_id
              JOIN res_currency dk_cc ON dk_cc.id = dk_company.currency_id
              LEFT JOIN res_currency dk_lc ON dk_lc.id = account_move_line.currency_id
             WHERE account_move_line.analytic_distribution IS NOT NULL
               AND %(share)s > 0;

            CREATE INDEX ON %(table)s (account_id, date, company_id);
            ANALYZE %(table)s;
            """,
            table=SQL.identifier(table),
            stored_fields=stored_fields,
            fields_to_insert=fields_to_insert,
            share=share,
        ))
        return table

    # ------------------------------------------------------------------
    # Excel export: describe the analytic filter / grouping under the table
    # (the PDF shows them in its header, see get_report_information).
    # ------------------------------------------------------------------
    def _inject_report_into_xlsx_sheet(self, options, workbook, sheet):
        result = super()._inject_report_into_xlsx_sheet(options, workbook, sheet)
        labels = self._dekad_analytic_labels(options)
        if labels:
            row = sheet.dim_rowmax + 2 if sheet.dim_rowmax is not None else 0
            style = workbook.add_format({'font_name': 'Arial', 'italic': True, 'font_color': '#666666'})
            for label in labels:
                sheet.write(row, 0, label, style)
                row += 1
        return result

    def _dekad_analytic_labels(self, options):
        labels = []
        analytic_ids = [int(a) for a in options.get('analytic_accounts') or [] if isinstance(a, (int, str))]
        if analytic_ids:
            names = self.env['account.analytic.account'].sudo().browse(analytic_ids).exists().mapped('name')
            if names:
                labels.append(_('Analytic Accounts: %s', ', '.join(names)))
        if options.get('group_by_analytic'):
            labels.append(_('Grouped by: Analytic Account'))
        return labels


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def _where_calc(self, domain, active_test=True):
        query = super()._where_calc(domain, active_test)
        scope = self.env.context.get('dekad_analytic_scope')
        if scope and not self.env.context.get('account_report_analytic_groupby'):
            table = self.env['account.report']._dekad_prepare_analytic_share_table(tuple(scope))
            query._tables['account_move_line'] = SQL.identifier(table)
        return query
