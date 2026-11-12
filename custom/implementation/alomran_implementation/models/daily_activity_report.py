# -*- coding: utf-8 -*-
import json
import re
from datetime import date, timedelta

from odoo import _, api, fields, models, tools
from odoo.exceptions import AccessError, UserError

SALESMAN_GROUP = 'sales_team.group_sale_salesman'
# Sales managers and salespeople with "All Documents" see every employee;
# "Own Documents" salespeople only see their own figures.
ALL_DOCS_GROUP = 'sales_team.group_sale_salesman_all_leads'
EXPIRING_SOON_DAYS = 7
LIST_LIMIT = 10

# kind -> (report column, model opened on drill-down)
KINDS = {
    'customer': 'res.partner',
    'follow_up': 'mail.message',
    'activity_done': 'mail.message',
    'activity_open': 'mail.activity',
    'opportunity': 'crm.lead',
    'contract': 'sale.order',
}

# report column -> kinds (+ optional extra SQL condition)
MEASURES = {
    'new_customers': (['customer'], None),
    'follow_ups': (['follow_up'], None),
    'activities_total': (['activity_open', 'activity_done'], None),
    'activities_done': (['activity_done'], None),
    'activities_overdue': (['activity_open'], 'e.overdue = 1'),
    'activities_open': (['activity_open'], None),
    'opportunities': (['opportunity'], None),
    'contracts': (['contract'], None),
}

# Every event of the report, one row per underlying record. Shared by the
# SQL view (aggregates) and the drill-down (record ids) so both always match.
# Days are computed in each employee's own timezone.
EVENTS_SQL = """
    WITH usr AS (
        SELECT u.id AS user_id,
               u.partner_id,
               u.company_id,
               COALESCE(NULLIF(p.tz, ''), 'UTC') AS tz
          FROM res_users u
          JOIN res_partner p ON p.id = u.partner_id
         WHERE u.share IS NOT TRUE
           AND u.id <> 1
    )
    -- New contacts
    SELECT usr.user_id,
           COALESCE(rp.company_id, usr.company_id) AS company_id,
           (rp.create_date AT TIME ZONE 'UTC' AT TIME ZONE usr.tz)::date AS date,
           'customer'::varchar AS kind, rp.id AS res_id, 0 AS overdue, 0.0 AS amount
      FROM res_partner rp
      JOIN usr ON usr.user_id = rp.create_uid
     WHERE rp.parent_id IS NULL /*pre:rp.create_date*/
       AND NOT EXISTS (SELECT 1 FROM res_users ru WHERE ru.partner_id = rp.id)
       AND NOT EXISTS (SELECT 1 FROM res_company rc WHERE rc.partner_id = rp.id)

    UNION ALL
    -- Follow-ups: notes / messages written by the employee
    -- (system notes posted by code always carry a subject -> excluded)
    SELECT usr.user_id,
           COALESCE(cl.company_id, rp.company_id, so.company_id, usr.company_id),
           (mm.date AT TIME ZONE 'UTC' AT TIME ZONE usr.tz)::date,
           'follow_up', mm.id, 0, 0.0
      FROM mail_message mm
      JOIN usr ON usr.partner_id = mm.author_id
      LEFT JOIN crm_lead cl ON mm.model = 'crm.lead' AND cl.id = mm.res_id
      LEFT JOIN res_partner rp ON mm.model = 'res.partner' AND rp.id = mm.res_id
      LEFT JOIN sale_order so ON mm.model = 'sale.order' AND so.id = mm.res_id
     WHERE mm.model IN ('crm.lead', 'res.partner', 'sale.order') /*pre:mm.date*/
       AND mm.message_type = 'comment'
       AND mm.mail_activity_type_id IS NULL
       AND COALESCE(mm.subject, '') = ''

    UNION ALL
    -- Completed activities
    SELECT usr.user_id,
           COALESCE(cl.company_id, rp.company_id, so.company_id, usr.company_id),
           (mm.date AT TIME ZONE 'UTC' AT TIME ZONE usr.tz)::date,
           'activity_done', mm.id, 0, 0.0
      FROM mail_message mm
      JOIN usr ON usr.partner_id = mm.author_id
      LEFT JOIN crm_lead cl ON mm.model = 'crm.lead' AND cl.id = mm.res_id
      LEFT JOIN res_partner rp ON mm.model = 'res.partner' AND rp.id = mm.res_id
      LEFT JOIN sale_order so ON mm.model = 'sale.order' AND so.id = mm.res_id
     WHERE mm.mail_activity_type_id IS NOT NULL /*pre:mm.date*/

    UNION ALL
    -- Open activities (by deadline) + overdue flag
    SELECT usr.user_id,
           COALESCE(cl.company_id, rp.company_id, so.company_id, usr.company_id),
           ma.date_deadline,
           'activity_open', ma.id,
           CASE WHEN ma.date_deadline < (NOW() AT TIME ZONE usr.tz)::date THEN 1 ELSE 0 END,
           0.0
      FROM mail_activity ma
      JOIN usr ON usr.user_id = ma.user_id
      LEFT JOIN crm_lead cl ON ma.res_model = 'crm.lead' AND cl.id = ma.res_id
      LEFT JOIN res_partner rp ON ma.res_model = 'res.partner' AND rp.id = ma.res_id
      LEFT JOIN sale_order so ON ma.res_model = 'sale.order' AND so.id = ma.res_id
     WHERE ma.active IS TRUE /*pre:ma.date_deadline*/

    UNION ALL
    -- Opportunities created
    SELECT usr.user_id,
           COALESCE(cl.company_id, usr.company_id),
           (cl.create_date AT TIME ZONE 'UTC' AT TIME ZONE usr.tz)::date,
           'opportunity', cl.id, 0, 0.0
      FROM crm_lead cl
      JOIN usr ON usr.user_id = cl.create_uid
     WHERE cl.type = 'opportunity' /*pre:cl.create_date*/

    UNION ALL
    -- Contracts: confirmed sales orders of the salesperson
    SELECT usr.user_id,
           so.company_id,
           (so.date_order AT TIME ZONE 'UTC' AT TIME ZONE usr.tz)::date,
           'contract', so.id, 0, so.amount_total
      FROM sale_order so
      JOIN usr ON usr.user_id = so.user_id
     WHERE so.state = 'sale' /*pre:so.date_order*/
"""

def events_sql(prefilter=False):
    """EVENTS_SQL, optionally pre-filtered on the raw dates (a day of margin
    for the timezones) so the report does not scan the whole history.
    The SQL view used by the pivot keeps the full history."""
    def repl(match):
        col = match.group(1)
        return f"AND {col} >= %(ts_from)s AND {col} < %(ts_to)s" if prefilter else ""
    return re.sub(r"/\*pre:([\w.]+)\*/", repl, EVENTS_SQL)


AGGREGATES_SQL = """
    SUM(CASE WHEN e.kind = 'customer' THEN 1 ELSE 0 END)                         AS new_customers,
    SUM(CASE WHEN e.kind = 'follow_up' THEN 1 ELSE 0 END)                        AS follow_ups,
    SUM(CASE WHEN e.kind IN ('activity_open', 'activity_done') THEN 1 ELSE 0 END) AS activities_total,
    SUM(CASE WHEN e.kind = 'activity_open' THEN 1 ELSE 0 END)                    AS activities_open,
    SUM(CASE WHEN e.kind = 'activity_done' THEN 1 ELSE 0 END)                    AS activities_done,
    SUM(CASE WHEN e.kind = 'activity_open' THEN e.overdue ELSE 0 END)            AS activities_overdue,
    SUM(CASE WHEN e.kind = 'opportunity' THEN 1 ELSE 0 END)                      AS opportunities,
    SUM(CASE WHEN e.kind = 'contract' THEN 1 ELSE 0 END)                         AS contracts,
    SUM(e.amount)                                                                AS contracts_amount
"""

COLUMNS = [
    'new_customers', 'follow_ups', 'activities_total', 'activities_done',
    'activities_overdue', 'opportunities', 'contracts', 'contracts_amount',
]


class AlomranDailyActivityReport(models.Model):
    """Daily activity per salesperson / branch / day (SQL view).

      * New Contacts     : contacts created by the employee
      * Follow-ups       : notes / messages written by the employee on
                           opportunities, contacts and quotations/orders
      * Activities       : open activities due that day + activities completed that day
      * Completed Tasks  : activities marked as done by the employee
      * Overdue Tasks    : still-open activities whose deadline has passed
      * Opportunities    : opportunities created by the employee
      * Contracts        : confirmed sales orders of the salesperson (by order date)
    """
    _name = 'alomran.daily.activity.report'
    _description = 'Daily Activity Report'
    _auto = False
    _order = 'date desc, user_id'
    _rec_name = 'user_id'

    date = fields.Date(string="Date", readonly=True)
    user_id = fields.Many2one('res.users', string="Employee", readonly=True)
    company_id = fields.Many2one('res.company', string="Branch", readonly=True)
    new_customers = fields.Integer(string="New Contacts", readonly=True)
    follow_ups = fields.Integer(string="Follow-ups", readonly=True)
    activities_total = fields.Integer(string="Activities", readonly=True)
    activities_open = fields.Integer(string="Pending Activities", readonly=True)
    activities_done = fields.Integer(string="Completed Tasks", readonly=True)
    activities_overdue = fields.Integer(string="Overdue Tasks", readonly=True)
    opportunities = fields.Integer(string="Opportunities", readonly=True)
    contracts = fields.Integer(string="Contracts", readonly=True)
    contracts_amount = fields.Float(string="Contracts Amount", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                SELECT ROW_NUMBER() OVER (ORDER BY e.date, e.user_id, e.company_id) AS id,
                       e.date, e.user_id, e.company_id,
                       {AGGREGATES_SQL}
                  FROM ({EVENTS_SQL}) e
                 WHERE e.date IS NOT NULL
                 GROUP BY e.date, e.user_id, e.company_id
            )
        """)

    # ------------------------------------------------------------------
    # Interactive report (client action / PDF / Excel)
    # ------------------------------------------------------------------
    @api.model
    def _check_report_access(self):
        if not self.env.user.has_group(SALESMAN_GROUP):
            raise AccessError(_("Only salespeople can access the Daily Activity Report."))

    @api.model
    def _can_see_all(self):
        return self.env.user.has_group(ALL_DOCS_GROUP)

    @api.model
    def _sanitize_options(self, options):
        """Validate everything coming from the client (dates, ids)."""
        options = dict(options or {})
        today = fields.Date.context_today(self)
        try:
            date_from = fields.Date.to_date(options.get('date_from')) or today
            date_to = fields.Date.to_date(options.get('date_to')) or date_from
        except (TypeError, ValueError):
            raise UserError(_("Invalid date."))
        if date_to < date_from:
            date_from, date_to = date_to, date_from
        if (date_to - date_from).days > 366:
            raise UserError(_("The period cannot exceed one year."))

        # Only the branches currently selected in the company switcher
        allowed_companies = self.env.companies
        company_ids = [int(c) for c in options.get('company_ids') or [] if str(c).isdigit()]
        companies = allowed_companies.filtered(lambda c: c.id in company_ids) if company_ids \
            else self.env.companies
        user_ids = [int(u) for u in options.get('user_ids') or [] if str(u).isdigit()]
        if not self._can_see_all():
            # Own Documents: always restricted to the current user, whatever the client sends
            user_ids = [self.env.uid]
        return {
            'date_from': fields.Date.to_string(date_from),
            'date_to': fields.Date.to_string(date_to),
            'company_ids': companies.ids,
            'user_ids': user_ids,
            'preset': options.get('preset') or 'custom',
        }

    @api.model
    def _events_where(self, opts, alias='e'):
        where = [f"{alias}.date BETWEEN %(date_from)s AND %(date_to)s",
                 f"{alias}.company_id = ANY(%(company_ids)s)"]
        params = {
            'date_from': opts['date_from'],
            'date_to': opts['date_to'],
            'ts_from': fields.Date.to_string(fields.Date.to_date(opts['date_from']) - timedelta(days=1)),
            'ts_to': fields.Date.to_string(fields.Date.to_date(opts['date_to']) + timedelta(days=2)),
            'company_ids': opts['company_ids'] or [0],
        }
        if opts['user_ids']:
            where.append(f"{alias}.user_id = ANY(%(user_ids)s)")
            params['user_ids'] = opts['user_ids']
        return " AND ".join(where), params

    @api.model
    def _flush_sources(self):
        for model in ('res.partner', 'mail.message', 'mail.activity', 'crm.lead', 'sale.order'):
            self.env[model].flush_model()

    @api.model
    def get_report_data(self, options=None):
        self._check_report_access()
        opts = self._sanitize_options(options)
        self._flush_sources()
        where, params = self._events_where(opts)
        self.env.cr.execute(f"""
            SELECT e.user_id, e.date, {AGGREGATES_SQL}
              FROM ({events_sql(prefilter=True)}) e
             WHERE {where}
             GROUP BY e.user_id, e.date
             ORDER BY e.user_id, e.date
        """, params)
        rows = self.env.cr.dictfetchall()

        users = self.env['res.users'].sudo().browse({r['user_id'] for r in rows})
        names = {u.id: u.name for u in users}
        lines_by_user = {}
        totals = dict.fromkeys(COLUMNS, 0)
        for r in rows:
            values = {c: r[c] or 0 for c in COLUMNS}
            line = lines_by_user.setdefault(r['user_id'], {
                'user_id': r['user_id'],
                'name': names.get(r['user_id'], ''),
                'values': dict.fromkeys(COLUMNS, 0),
                'days': [],
            })
            line['days'].append({'date': fields.Date.to_string(r['date']), 'values': values})
            for c in COLUMNS:
                line['values'][c] += values[c]
                totals[c] += values[c]
        lines = sorted(lines_by_user.values(), key=lambda l: l['name'].lower())

        # filter choices
        company_choices = [{'id': c.id, 'name': c.name} for c in self.env.companies]
        if self._can_see_all():
            sales_users = self.env['res.users'].search([
                ('share', '=', False),
                ('id', '!=', 1),
                ('groups_id', 'in', self.env.ref('sales_team.group_sale_salesman').id),
            ], order='name')
        else:
            sales_users = self.env.user
        return {
            'options': opts,
            'lines': lines,
            'totals': totals,
            'columns': self._get_columns(),
            'filters': {
                'companies': company_choices,
                'users': [{'id': u.id, 'name': u.name} for u in sales_users],
            },
            'currency_symbol': self.env.company.currency_id.symbol or '',
            'can_see_all': self._can_see_all(),
        }

    @api.model
    def _get_columns(self):
        labels = {f: self._fields[f].get_description(self.env)['string'] for f in COLUMNS}
        return [{'field': f, 'label': labels[f]} for f in COLUMNS]

    @api.model
    def action_open_records(self, options, measure, user_id=None, day=None):
        """Drill-down: open the exact records behind a number of the report."""
        self._check_report_access()
        if measure not in MEASURES:
            raise UserError(_("Unknown measure."))
        opts = self._sanitize_options(options)
        if day:
            opts['date_from'] = opts['date_to'] = fields.Date.to_string(fields.Date.to_date(day))
        if user_id:
            if not self._can_see_all() and int(user_id) != self.env.uid:
                raise AccessError(_("You can only open your own records."))
            opts['user_ids'] = [int(user_id)]
        kinds, extra = MEASURES[measure]
        self._flush_sources()
        where, params = self._events_where(opts)
        params['kinds'] = kinds
        if extra:
            where += f" AND {extra}"
        self.env.cr.execute(f"""
            SELECT e.kind, e.res_id FROM ({events_sql(prefilter=True)}) e
             WHERE {where} AND e.kind = ANY(%(kinds)s)
        """, params)
        ids_by_model = {}
        for kind, res_id in self.env.cr.fetchall():
            ids_by_model.setdefault(KINDS[kind], []).append(res_id)
        if not ids_by_model:
            raise UserError(_("No records."))
        if len(ids_by_model) > 1:
            # "Activities" mixes open activities and completed ones: show open ones
            model = 'mail.activity'
        else:
            model = next(iter(ids_by_model))
        ids = ids_by_model[model]
        label = dict((c['field'], c['label']) for c in self._get_columns())[measure]
        action = {
            'type': 'ir.actions.act_window',
            'name': label,
            'res_model': model,
            'views': [[False, 'list'], [False, 'form']],
            'domain': [('id', 'in', ids)],
            # Open the records with the branches selected in the report, not only
            # the ones selected in the company switcher (otherwise the list is
            # empty for employees of other branches). Already limited to the
            # user's allowed companies by _sanitize_options.
            'context': {'create': False, 'active_test': False,
                        'allowed_company_ids': opts['company_ids']},
            'target': 'current',
        }
        if model == 'mail.message':
            action['views'] = [[self.env.ref('alomran_implementation.mail_message_view_list_daily_report').id, 'list'],
                               [False, 'form']]
            search_view = self.env.ref('alomran_implementation.mail_message_view_search_daily_report')
            action['search_view_id'] = [search_view.id, 'search']
        return action

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------
    @api.model
    def _dashboard_lead_domain(self, opts, open_only=True):
        domain = [('type', '=', 'opportunity'),
                  ('company_id', 'in', opts['company_ids'] + [False])]
        if opts['user_ids']:
            domain.append(('user_id', 'in', opts['user_ids']))
        if open_only:
            domain.append(('stage_id.is_won', '=', False))
        return domain

    @api.model
    def _dashboard_validity(self, opts):
        """Validity of the opportunities in scope (won ones included):
        {'active': ids, 'expiring': [(lead_id, remaining_days)], 'expired': ids}"""
        tools = self.env['alomran.validity.tools']
        # won opportunities included: they must be followed up too
        lead_ids = set(self.env['crm.lead'].sudo().search(
            self._dashboard_lead_domain(opts, open_only=False)).ids)
        result = {'active': [], 'expiring': [], 'expired': []}
        if not lead_ids:
            return result
        # Computing every lead then filtering is faster than passing tens of
        # thousands of ids to the query.
        rows = tools._get_lead_validity_rows(lead_ids if len(lead_ids) < 5000 else None)
        for lead_id, last_update, status in rows:
            if lead_id not in lead_ids:
                continue
            if status == 'expired':
                result['expired'].append(lead_id)
            elif status == 'active':
                remaining = tools._get_validity_info(last_update)[0]
                if remaining <= EXPIRING_SOON_DAYS:
                    result['expiring'].append((lead_id, remaining))
                else:
                    result['active'].append(lead_id)
        result['expiring'].sort(key=lambda r: r[1])
        return result

    @api.model
    def get_dashboard_data(self, options=None):
        data = self.get_report_data(options)
        opts = data['options']
        Lead = self.env['crm.lead'].sudo()

        # Daily trend (every day of the period, zeros included)
        by_day = {}
        for line in data['lines']:
            for day in line['days']:
                values = by_day.setdefault(day['date'], dict.fromkeys(COLUMNS, 0))
                for c in COLUMNS:
                    values[c] += day['values'][c]
        start = fields.Date.to_date(opts['date_from'])
        end = fields.Date.to_date(opts['date_to'])
        days = [fields.Date.to_string(start + timedelta(days=i)) for i in range((end - start).days + 1)]
        trend = {'labels': days, 'series': {c: [by_day.get(d, {}).get(c, 0) for d in days] for c in COLUMNS}}

        # Employees comparison (top 15 by work done)
        employees = sorted(
            data['lines'],
            key=lambda l: -(l['values']['follow_ups'] + l['values']['activities_done'] + l['values']['opportunities']),
        )[:15]
        employees = [{'user_id': l['user_id'], 'name': l['name'], 'values': l['values']} for l in employees]

        # Pipeline of the open opportunities by stage
        groups = Lead._read_group(self._dashboard_lead_domain(opts), ['stage_id'],
                                  ['__count', 'expected_revenue:sum'])
        pipeline = sorted(
            ({'stage_id': stage.id, 'name': stage.name or _("No Stage"), 'sequence': stage.sequence or 0,
              'count': count, 'revenue': revenue or 0.0} for stage, count, revenue in groups),
            key=lambda r: (r['sequence'], r['stage_id'] or 0),
        )

        # Oldest overdue tasks on opportunities
        today = fields.Date.context_today(self)
        # Branch + user filters in the query itself (not after a LIMIT), so the
        # list is never empty because older overdue tasks belong to other branches.
        self.env['mail.activity'].flush_model()
        self.env.cr.execute("""
            SELECT a.id FROM mail_activity a
              JOIN crm_lead l ON l.id = a.res_id
             WHERE a.res_model = 'crm.lead' AND a.active IS TRUE AND a.date_deadline < %(today)s
               AND (l.company_id IS NULL OR l.company_id = ANY(%(companies)s))
               AND (%(all_users)s OR a.user_id = ANY(%(users)s))
             ORDER BY a.date_deadline, a.id
             LIMIT %(limit)s
        """, {'today': today, 'companies': opts['company_ids'] or [0], 'all_users': not opts['user_ids'],
              'users': opts['user_ids'] or [0], 'limit': LIST_LIMIT})
        activities = self.env['mail.activity'].sudo().browse([r[0] for r in self.env.cr.fetchall()])
        overdue = []
        for act in activities:
            overdue.append({
                'id': act.id, 'res_model': act.res_model, 'res_id': act.res_id,
                'name': act.res_name or '', 'summary': act.summary or act.activity_type_id.name or '',
                'user': act.user_id.name or '', 'deadline': fields.Date.to_string(act.date_deadline),
                'late': (today - act.date_deadline).days,
            })

        data.update({
            'trend': trend,
            'employees': employees,
            'pipeline': pipeline,
            'overdue': overdue,
            'expiring_days': EXPIRING_SOON_DAYS,
        })
        return data

    @api.model
    def get_dashboard_validity(self, options=None):
        """Lead validity chart + leads expiring soon. Loaded separately by the
        dashboard because it is the slowest part (whole chatter history)."""
        self._check_report_access()
        opts = self._sanitize_options(options)
        validity = self._dashboard_validity(opts)
        remaining_by_id = dict(validity['expiring'][:LIST_LIMIT])
        expiring = [{
            'id': lead.id, 'name': lead.name, 'customer': lead.partner_id.name or lead.contact_name or '',
            'user': lead.user_id.name or '', 'remaining': remaining_by_id[lead.id],
        } for lead in self.env['crm.lead'].sudo().browse(list(remaining_by_id))]
        expiring.sort(key=lambda r: r['remaining'])
        return {
            'counts': {k: len(v) for k, v in validity.items()},
            'expiring': expiring,
        }

    @api.model
    def action_open_dashboard_leads(self, options, kind, stage_id=None):
        """Opportunities behind a dashboard chart / card (pipeline stage or validity)."""
        self._check_report_access()
        opts = self._sanitize_options(options)
        if kind == 'stage':
            domain = self._dashboard_lead_domain(opts) + [('stage_id', '=', int(stage_id) if stage_id else False)]
            ids = self.env['crm.lead'].sudo().search(domain).ids
        elif kind in ('active', 'expiring', 'expired'):
            rows = self._dashboard_validity(opts)[kind]
            ids = [r[0] for r in rows] if kind == 'expiring' else rows
        else:
            raise UserError(_("Unknown selection."))
        return {
            'type': 'ir.actions.act_window',
            'name': _("Opportunities"),
            'res_model': 'crm.lead',
            'views': [[False, 'list'], [False, 'form']],
            'domain': [('id', 'in', ids)],
            'context': {'create': False, 'allowed_company_ids': opts['company_ids']},
            'target': 'current',
        }

    @api.model
    def action_print_pdf(self, options=None):
        self._check_report_access()
        opts = self._sanitize_options(options)
        return self.env.ref('alomran_implementation.action_report_daily_activity').report_action(
            None, data={'options': opts})

    @api.model
    def _get_xlsx_content(self, options):
        import io
        import xlsxwriter
        data = self.get_report_data(options)
        opts = data['options']
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet(_("Daily Activity"))
        if (self.env.user.lang or '').startswith('ar'):
            sheet.right_to_left()
        title = workbook.add_format({'bold': True, 'font_size': 14})
        head = workbook.add_format({'bold': True, 'bg_color': '#D9E1F2', 'border': 1, 'align': 'center'})
        user_f = workbook.add_format({'bold': True, 'border': 1})
        day_f = workbook.add_format({'border': 1, 'indent': 1, 'font_color': '#555555'})
        num_f = workbook.add_format({'border': 1})
        num_bold = workbook.add_format({'border': 1, 'bold': True})
        amount_f = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})
        amount_bold = workbook.add_format({'border': 1, 'bold': True, 'num_format': '#,##0.00'})
        total_f = workbook.add_format({'bold': True, 'border': 1, 'bg_color': '#F2F2F2'})

        sheet.write(0, 0, _("Daily Activity Report"), title)
        sheet.write(1, 0, _("Period: %(start)s → %(end)s", start=opts['date_from'], end=opts['date_to']))
        companies = self.env['res.company'].browse(opts['company_ids'])
        sheet.write(2, 0, _("Branches: %s", ", ".join(companies.mapped('name'))))

        row = 4
        sheet.write(row, 0, _("Employee / Day"), head)
        for col, c in enumerate(data['columns'], start=1):
            sheet.write(row, col, c['label'], head)
        sheet.set_column(0, 0, 32)
        sheet.set_column(1, len(data['columns']), 15)

        def write_values(r, values, bold):
            for col, c in enumerate(data['columns'], start=1):
                if c['field'] == 'contracts_amount':
                    sheet.write_number(r, col, values[c['field']], amount_bold if bold else amount_f)
                else:
                    sheet.write_number(r, col, values[c['field']], num_bold if bold else num_f)

        for line in data['lines']:
            row += 1
            sheet.write(row, 0, line['name'], user_f)
            write_values(row, line['values'], True)
            for d in line['days']:
                row += 1
                sheet.write(row, 0, d['date'], day_f)
                write_values(row, d['values'], False)
        row += 1
        sheet.write(row, 0, _("Total"), total_f)
        write_values(row, data['totals'], True)
        workbook.close()
        return output.getvalue()


class ReportDailyActivityPdf(models.AbstractModel):
    _name = 'report.alomran_implementation.report_daily_activity'
    _description = 'Daily Activity Report (PDF)'

    @api.model
    def _get_report_values(self, docids, data=None):
        Report = self.env['alomran.daily.activity.report']
        options = (data or {}).get('options') or {}
        if isinstance(options, str):
            options = json.loads(options)
        report = Report.get_report_data(options)
        return {
            'doc_ids': docids,
            'doc_model': Report._name,
            'docs': Report,
            'report': report,
            'companies': self.env['res.company'].browse(report['options']['company_ids']),
            'company': self.env.company,
            'print_date': fields.Datetime.context_timestamp(self, fields.Datetime.now()),
        }
