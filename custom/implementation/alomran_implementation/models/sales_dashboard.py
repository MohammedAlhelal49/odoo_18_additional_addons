# -*- coding: utf-8 -*-
import calendar
from datetime import datetime, time, timedelta

import pytz
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.tools.misc import format_date

PRESETS = ("today", "yesterday", "last_7", "this_month", "last_month", "this_year", "custom")
MAX_RANGE_DAYS = 3 * 366
DEFAULT_TZ = "Asia/Dubai"
LIST_LIMIT = 10

# Confirmed sales orders (contracts) of the period, branches and salespeople in scope.
ORDERS_CTE = """
    WITH o AS (
        SELECT so.id, so.partner_id, so.user_id, so.company_id,
               so.amount_total, so.amount_untaxed,
               COALESCE(so.remaining_amount, 0) AS remaining_amount,
               COALESCE(so.initial_payment, 0) AS initial_payment,
               so.payment_method, so.enrollment_type, so.source, so.admin_approval,
               so.date_order,
               (so.date_order AT TIME ZONE 'UTC' AT TIME ZONE %(tz)s) AS local_dt
          FROM sale_order so
         WHERE so.state = 'sale'
           AND so.company_id = ANY(%(companies)s)
           AND so.date_order >= %(start)s
           AND so.date_order < %(end)s
           AND (%(all_users)s OR so.user_id = ANY(%(users)s))
    )
"""


class AlomranSalesDashboard(models.AbstractModel):
    """Sales dashboard (same layout and filters as the Bait Al Arab reports).

    Scope:
      * branches: the companies selected in the company switcher,
      * salespeople: everybody for Sales Managers / "All Documents" users,
        only the current user for "Own Documents" salespeople (enforced here).
    """
    _name = "alomran.sales.dashboard"
    _description = "Sales Dashboard"

    # ------------------------------------------------------------------ helpers
    def _check_access(self):
        if not self.env.user.has_group("sales_team.group_sale_salesman"):
            raise AccessError(_("Only salespeople can open the sales dashboard."))

    def _can_see_all(self):
        return self.env.user.has_group("sales_team.group_sale_salesman_all_leads")

    def _tz(self):
        for name in (self.env.user.tz, self.env.context.get("sd_browser_tz"), DEFAULT_TZ):
            if name:
                try:
                    return pytz.timezone(name)
                except pytz.UnknownTimeZoneError:
                    continue
        return pytz.utc

    def _to_utc(self, day):
        local = self._tz().localize(datetime.combine(day, time.min))
        return local.astimezone(pytz.utc).replace(tzinfo=None)

    def _today(self):
        return datetime.now(self._tz()).date()

    def _resolve_period(self, preset, date_from, date_to):
        today = self._today()
        if preset == "today":
            start = stop = today
        elif preset == "yesterday":
            start = stop = today - timedelta(days=1)
        elif preset == "last_7":
            start, stop = today - timedelta(days=6), today
        elif preset == "this_month":
            start, stop = today.replace(day=1), today
        elif preset == "last_month":
            stop = today.replace(day=1) - timedelta(days=1)
            start = stop.replace(day=1)
        elif preset == "this_year":
            start, stop = today.replace(month=1, day=1), today
        elif preset == "custom":
            try:
                start, stop = fields.Date.to_date(date_from), fields.Date.to_date(date_to)
            except (TypeError, ValueError):
                start = stop = None
            if not start or not stop:
                raise UserError(_("Please choose both dates."))
            if start > stop:
                raise UserError(_("The start date must be before the end date."))
            if (stop - start).days > MAX_RANGE_DAYS:
                raise UserError(_("Please choose a period of 3 years or less."))
        else:
            raise UserError(_("Unknown period."))
        days = (stop - start).days + 1
        prev_stop = start - timedelta(days=1)
        prev_start = prev_stop - timedelta(days=days - 1)
        return start, stop, prev_start, prev_stop

    def _scope(self, company_ids, user_ids):
        """Branches (within the active companies) and salespeople the user may see."""
        companies = self.env.companies
        if company_ids:
            companies = companies.filtered(lambda c: c.id in [int(i) for i in company_ids]) or self.env.companies
        if not self._can_see_all():
            users = self.env.user
        elif user_ids:
            users = self.env["res.users"].browse([int(i) for i in user_ids]).exists()
        else:
            users = self.env["res.users"]
        return companies, users

    def _params(self, start, stop, companies, users):
        return {
            "tz": self._tz().zone,
            "companies": companies.ids or [0],
            "start": self._to_utc(start),
            "end": self._to_utc(stop + timedelta(days=1)),
            "all_users": not users,
            "users": users.ids or [0],
        }

    def _query(self, body, params):
        self.env["sale.order"].flush_model()
        self.env.cr.execute(ORDERS_CTE + body, params)
        return self.env.cr.dictfetchall()

    def _selection_label(self, field_name, value):
        if not value:
            return _("Not set")
        field = self.env["sale.order"]._fields[field_name]
        return dict(field._description_selection(self.env)).get(value, value)

    # ------------------------------------------------------------------ blocks
    def _kpis(self, start, stop, companies, users):
        params = self._params(start, stop, companies, users)
        row = self._query("""
            SELECT COUNT(*)                                                    AS contracts,
                   COALESCE(SUM(amount_total), 0)                              AS sales,
                   COALESCE(SUM(amount_untaxed), 0)                            AS sales_untaxed,
                   COUNT(DISTINCT partner_id)                                  AS customers,
                   COUNT(*) FILTER (WHERE enrollment_type = 'new')             AS new_enrollments,
                   COUNT(*) FILTER (WHERE enrollment_type = 're_enrollment')   AS re_enrollments,
                   COALESCE(SUM(initial_payment), 0)                           AS initial_payments,
                   COALESCE(SUM(remaining_amount) FILTER (WHERE remaining_amount > 0.01), 0) AS remaining,
                   COUNT(*) FILTER (WHERE remaining_amount > 0.01)             AS remaining_count,
                   COUNT(*) FILTER (WHERE admin_approval = 'pending')          AS pending_approval
              FROM o
        """, params)[0]
        # Quotations created in the period and still not confirmed / cancelled orders
        self.env.cr.execute("""
            SELECT COUNT(*) FILTER (WHERE so.state IN ('draft', 'sent'))                         AS quotations,
                   COALESCE(SUM(so.amount_total) FILTER (WHERE so.state IN ('draft', 'sent')), 0) AS quotations_amount,
                   COUNT(*) FILTER (WHERE so.state = 'cancel')                                    AS cancelled
              FROM sale_order so
             WHERE so.company_id = ANY(%(companies)s)
               AND so.create_date >= %(start)s AND so.create_date < %(end)s
               AND (%(all_users)s OR so.user_id = ANY(%(users)s))
        """, params)
        row.update(self.env.cr.dictfetchone())
        row["avg_contract"] = row["sales"] / row["contracts"] if row["contracts"] else 0.0
        return row

    def _buckets(self, start, stop, granularity):
        buckets = []
        if granularity == "day":
            day = start
            while day <= stop:
                buckets.append((day, day))
                day += timedelta(days=1)
        else:
            month = start.replace(day=1)
            while month <= stop:
                last = month.replace(day=calendar.monthrange(month.year, month.month)[1])
                buckets.append((max(month, start), min(last, stop)))
                month += relativedelta(months=1)
        return buckets

    def _series_values(self, start, stop, companies, users, granularity):
        params = self._params(start, stop, companies, users)
        params["gran"] = granularity
        rows = self._query("""
            SELECT date_trunc(%(gran)s, local_dt)::date AS bucket,
                   COALESCE(SUM(amount_total), 0) AS sales,
                   COUNT(*) AS contracts
              FROM o GROUP BY 1
        """, params)
        return {r["bucket"]: r for r in rows}

    def _series(self, start, stop, prev_start, prev_stop, companies, users):
        granularity = "day" if (stop - start).days <= 62 else "month"
        buckets = self._buckets(start, stop, granularity)
        prev_buckets = self._buckets(prev_start, prev_stop, granularity)
        current = self._series_values(start, stop, companies, users, granularity)
        previous = self._series_values(prev_start, prev_stop, companies, users, granularity)

        def key(day):
            return day if granularity == "day" else day.replace(day=1)

        empty = {"sales": 0.0, "contracts": 0}
        fmt = "d MMM" if granularity == "day" else "MMM yyyy"
        series = {"granularity": granularity, "labels": [], "buckets": [],
                  "sales": [], "contracts": [], "prev_sales": []}
        for index, (b_start, b_stop) in enumerate(buckets):
            row = current.get(key(b_start), empty)
            series["labels"].append(format_date(self.env, b_start, date_format=fmt))
            series["buckets"].append({
                "start": fields.Datetime.to_string(self._to_utc(b_start)),
                "end": fields.Datetime.to_string(self._to_utc(b_stop + timedelta(days=1))),
            })
            series["sales"].append(row["sales"])
            series["contracts"].append(row["contracts"])
            prev = previous.get(key(prev_buckets[index][0]), empty) if index < len(prev_buckets) else empty
            series["prev_sales"].append(prev["sales"])
        return series

    def _group_by_selection(self, field_name, params):
        rows = self._query(f"""
            SELECT {field_name} AS value, COUNT(*) AS contracts, COALESCE(SUM(amount_total), 0) AS amount
              FROM o GROUP BY 1 ORDER BY 3 DESC
        """, params)
        return [{"value": r["value"] or False, "name": self._selection_label(field_name, r["value"]),
                 "contracts": r["contracts"], "amount": r["amount"]} for r in rows]

    def _courses(self, params):
        rows = self._query("""
            SELECT l.product_id AS id, COUNT(DISTINCT l.order_id) AS contracts,
                   COALESCE(SUM(l.product_uom_qty), 0) AS qty, COALESCE(SUM(l.price_total), 0) AS amount
              FROM sale_order_line l JOIN o ON o.id = l.order_id
             WHERE l.product_id IS NOT NULL AND l.display_type IS NULL
             GROUP BY 1 ORDER BY 4 DESC LIMIT %(limit)s
        """, dict(params, limit=LIST_LIMIT))
        products = {p.id: p.display_name for p in self.env["product.product"].sudo().browse([r["id"] for r in rows])}
        return [dict(r, name=products.get(r["id"], "")) for r in rows]

    def _salespeople(self, params):
        rows = self._query("""
            SELECT user_id AS id, COUNT(*) AS contracts, COALESCE(SUM(amount_total), 0) AS amount,
                   COUNT(*) FILTER (WHERE enrollment_type = 'new') AS new_enrollments,
                   COALESCE(SUM(remaining_amount) FILTER (WHERE remaining_amount > 0.01), 0) AS remaining
              FROM o GROUP BY 1 ORDER BY 3 DESC
        """, params)
        names = {u.id: u.name for u in self.env["res.users"].sudo().browse([r["id"] for r in rows if r["id"]])}
        return [dict(r, name=names.get(r["id"]) or _("Unassigned"),
                     avg=r["amount"] / r["contracts"] if r["contracts"] else 0.0) for r in rows]

    def _branches(self, params):
        rows = self._query("""
            SELECT company_id AS id, COUNT(*) AS contracts, COALESCE(SUM(amount_total), 0) AS amount,
                   COALESCE(SUM(remaining_amount) FILTER (WHERE remaining_amount > 0.01), 0) AS remaining
              FROM o GROUP BY 1 ORDER BY 3 DESC
        """, params)
        names = {c.id: c.name for c in self.env["res.company"].sudo().browse([r["id"] for r in rows if r["id"]])}
        return [dict(r, name=names.get(r["id"], "")) for r in rows]

    def _top_remaining(self, params):
        rows = self._query("""
            SELECT id, remaining_amount FROM o
             WHERE remaining_amount > 0.01 ORDER BY remaining_amount DESC LIMIT %(limit)s
        """, dict(params, limit=LIST_LIMIT))
        orders = {so.id: so for so in self.env["sale.order"].sudo().browse([r["id"] for r in rows])}
        result = []
        for r in rows:
            so = orders[r["id"]]
            result.append({
                "id": so.id, "name": so.name, "customer": so.partner_id.name or "",
                "phone": so.partner_id.mobile or so.partner_id.phone or "",
                "user": so.user_id.name or "", "date": format_date(self.env, so.date_order),
                "total": so.amount_total, "remaining": r["remaining_amount"],
            })
        return result

    # ------------------------------------------------------------------ API
    @api.model
    def get_filters(self):
        self._check_access()
        can_see_all = self._can_see_all()
        users = self.env["res.users"]
        if can_see_all:
            users = self.env["res.users"].search([
                ("share", "=", False), ("id", "!=", 1),
                ("groups_id", "in", self.env.ref("sales_team.group_sale_salesman").id),
            ], order="name")
        return {
            "companies": [{"id": c.id, "name": c.name} for c in self.env.companies],
            "users": [{"id": u.id, "name": u.name} for u in users],
            "can_see_all": can_see_all,
            "presets": [
                {"key": "today", "label": _("Today")},
                {"key": "yesterday", "label": _("Yesterday")},
                {"key": "last_7", "label": _("Last 7 days")},
                {"key": "this_month", "label": _("This month")},
                {"key": "last_month", "label": _("Last month")},
                {"key": "this_year", "label": _("This year")},
                {"key": "custom", "label": _("Custom")},
            ],
        }

    @api.model
    def get_data(self, preset="this_month", date_from=False, date_to=False, company_ids=None, user_ids=None,
                 browser_tz=False):
        self._check_access()
        if browser_tz:
            self = self.with_context(sd_browser_tz=browser_tz)
        if preset not in PRESETS:
            raise UserError(_("Unknown period."))
        companies, users = self._scope(company_ids, user_ids)
        start, stop, prev_start, prev_stop = self._resolve_period(preset, date_from, date_to)
        params = self._params(start, stop, companies, users)
        return {
            "currency_id": self.env.company.currency_id.id,
            "can_see_all": self._can_see_all(),
            "company_ids": companies.ids,
            "user_ids": users.ids,
            "period": {
                "preset": preset,
                "date_from": fields.Date.to_string(start),
                "date_to": fields.Date.to_string(stop),
                "label": "%s - %s" % (format_date(self.env, start), format_date(self.env, stop)),
                "prev_label": "%s - %s" % (format_date(self.env, prev_start), format_date(self.env, prev_stop)),
                "start": fields.Datetime.to_string(params["start"]),
                "end": fields.Datetime.to_string(params["end"]),
            },
            "kpis": {
                "current": self._kpis(start, stop, companies, users),
                "previous": self._kpis(prev_start, prev_stop, companies, users),
            },
            "series": self._series(start, stop, prev_start, prev_stop, companies, users),
            "payment_methods": self._group_by_selection("payment_method", params),
            "sources": self._group_by_selection("source", params),
            "enrollments": self._group_by_selection("enrollment_type", params),
            "courses": self._courses(params),
            "salespeople": self._salespeople(params) if self._can_see_all() else [],
            "branches": self._branches(params) if len(companies) > 1 else [],
            "top_remaining": self._top_remaining(params),
            "timezone": {"used": self._tz().zone, "user": self.env.user.tz or False,
                         "browser": browser_tz or False},
        }
