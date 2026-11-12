import calendar
from datetime import date, datetime, time, timedelta

import pytz
from babel.dates import get_day_names
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.tools.misc import babel_locale_parse, format_date

VALID_STATES = ("paid", "done", "invoiced")
PRESETS = ("today", "yesterday", "last_7", "this_month", "last_month", "this_year", "custom")
MAX_RANGE_DAYS = 3 * 366

# Valid POS orders of the selected points of sale and period, with their local date-time.
ORDERS_CTE = """
    o AS (
        SELECT po.id, po.partner_id, po.user_id, {employee} AS employee_id,
               po.amount_total, po.amount_tax, po.date_order,
               (po.date_order AT TIME ZONE 'UTC' AT TIME ZONE %(tz)s) AS local_dt
          FROM pos_order po
          JOIN pos_session ps ON ps.id = po.session_id
         WHERE po.state IN %(states)s
           AND ps.config_id = ANY(%(configs)s)
           AND po.company_id = ANY(%(companies)s)
           AND po.date_order >= %(start)s
           AND po.date_order < %(end)s
           AND (%(no_cashier)s
                OR ({employee} IS NULL AND po.user_id = ANY(%(users)s))
                OR {employee} = ANY(%(employees)s))
    )
"""


class LaundryDashboard(models.AbstractModel):
    _name = "alarab.laundry.dashboard"
    _description = "Laundry Manager Dashboard"

    # ------------------------------------------------------------------ helpers
    def _check_access(self):
        if not self.env.user.has_group("alarab_laundry_dashboard.group_laundry_dashboard"):
            raise AccessError(_("You are not allowed to open the laundry dashboard."))

    def _tz(self):
        """User timezone; if the user has none, the device timezone sent by the browser."""
        for name in (self.env.user.tz, self.env.context.get("ld_browser_tz")):
            if name:
                try:
                    return pytz.timezone(name)
                except pytz.UnknownTimeZoneError:
                    continue
        return pytz.utc

    def _to_utc(self, day):
        """Local midnight of `day` -> naive UTC datetime (how Odoo stores datetimes)."""
        local = self._tz().localize(datetime.combine(day, time.min))
        return local.astimezone(pytz.utc).replace(tzinfo=None)

    def _today(self):
        return datetime.now(self._tz()).date()

    def _resolve_period(self, preset, date_from, date_to):
        today = self._today()
        if preset == "today":
            start, stop = today, today
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

    def _configs(self, config_ids):
        domain = [("company_id", "in", self.env.companies.ids)]
        if config_ids:
            domain.append(("id", "in", [int(c) for c in config_ids]))
        return self.env["pos.config"].search(domain)

    def _has_employee(self):
        return "employee_id" in self.env["pos.order"]._fields

    def _params(self, start, stop, configs):
        return {
            "tz": self._tz().zone,
            "states": VALID_STATES,
            "configs": configs.ids or [0],
            "companies": self.env.companies.ids,
            "start": self._to_utc(start),
            "end": self._to_utc(stop + timedelta(days=1)),
            # optional cashier filter (used by the reports): "user-<id>" / "employee-<id>" keys
            "no_cashier": True,
            "users": [],
            "employees": [],
        }

    def _query(self, body, params):
        employee = "po.employee_id" if self._has_employee() else "NULL::int"
        cte = ORDERS_CTE.replace("{employee}", employee)
        self.env.cr.execute("WITH " + cte + body, params)
        return self.env.cr.dictfetchall()

    def _discount_products(self, configs):
        if "discount_product_id" in self.env["pos.config"]._fields:
            return configs.mapped("discount_product_id").ids or [0]
        return [0]

    # ------------------------------------------------------------------ blocks
    def _kpis(self, start, stop, configs):
        params = self._params(start, stop, configs)
        params["discount_products"] = self._discount_products(configs)
        orders = self._query("""
            SELECT COUNT(*) FILTER (WHERE amount_total >= 0)                         AS orders,
                   COALESCE(SUM(amount_total), 0)                                    AS sales,
                   COALESCE(SUM(amount_total - amount_tax), 0)                       AS sales_untaxed,
                   COALESCE(SUM(amount_total) FILTER (WHERE amount_total >= 0), 0)  AS gross_sales,
                   COUNT(*) FILTER (WHERE amount_total < 0)                          AS refunds_count,
                   COALESCE(-SUM(amount_total) FILTER (WHERE amount_total < 0), 0)   AS refunds_amount,
                   COUNT(DISTINCT partner_id) FILTER (WHERE amount_total >= 0)       AS customers
              FROM o
        """, params)[0]
        discounts = self._query("""
            SELECT COALESCE(SUM(
                     CASE WHEN l.product_id = ANY(%(discount_products)s) AND l.price_subtotal_incl < 0
                              THEN -l.price_subtotal_incl
                          WHEN l.discount > 0 AND l.discount < 100
                              THEN l.price_subtotal_incl * l.discount / (100 - l.discount)
                          WHEN l.discount >= 100 THEN l.qty * l.price_unit
                          ELSE 0 END), 0) AS discounts
              FROM pos_order_line l JOIN o ON o.id = l.order_id
             WHERE o.amount_total >= 0
        """, params)[0]["discounts"]
        payments = {"cash": 0.0, "bank": 0.0, "other": 0.0}
        for row in self._query("""
            SELECT CASE WHEN pm.is_cash_count THEN 'cash'
                        WHEN pm.journal_id IS NULL THEN 'other'
                        ELSE 'bank' END AS kind,
                   COALESCE(SUM(pp.amount), 0) AS amount
              FROM pos_payment pp
              JOIN o ON o.id = pp.pos_order_id
              JOIN pos_payment_method pm ON pm.id = pp.payment_method_id
             GROUP BY 1
        """, params):
            payments[row["kind"]] = row["amount"]
        outside = {"cash": 0.0, "bank": 0.0}
        if self._whole_business(configs):
            for row in self.env["alarab.laundry.report"]._outside_collection_rows(start, stop):
                outside[row["kind"]] += row["amount"]
        new_customers = self._new_customers(start, stop, configs)
        gross_orders = orders["orders"]
        return {
            "sales": orders["sales"],
            "sales_untaxed": orders["sales_untaxed"],
            "orders": gross_orders,
            "avg_order": orders["gross_sales"] / gross_orders if gross_orders else 0.0,
            "refunds_count": orders["refunds_count"],
            "refunds_amount": orders["refunds_amount"],
            "discounts": discounts,
            # collected = POS cash/bank payments + customer payments recorded outside the POS
            "cash": payments["cash"] + outside["cash"],
            "bank": payments["bank"] + outside["bank"],
            "outside": outside["cash"] + outside["bank"],
            "outside_cash": outside["cash"],
            "outside_bank": outside["bank"],
            "on_account": payments["other"],
            "other": payments["other"],
            "customers": orders["customers"],
            "new_customers": new_customers,
            "returning_customers": max(orders["customers"] - new_customers, 0),
        }

    def _new_customers(self, start, stop, configs):
        """Customers whose very first order (at the selected points of sale) falls in the period."""
        params = self._params(start, stop, configs)
        self.env.cr.execute("""
            SELECT COUNT(*) FROM (
                SELECT po.partner_id, MIN(po.date_order) AS first_order
                  FROM pos_order po JOIN pos_session ps ON ps.id = po.session_id
                 WHERE po.partner_id IS NOT NULL
                   AND po.state IN %(states)s
                   AND po.amount_total >= 0
                   AND ps.config_id = ANY(%(configs)s)
                   AND po.company_id = ANY(%(companies)s)
                 GROUP BY po.partner_id
            ) f
             WHERE f.first_order >= %(start)s AND f.first_order < %(end)s
        """, params)
        return self.env.cr.fetchone()[0]

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

    def _series_values(self, start, stop, configs, granularity):
        params = self._params(start, stop, configs)
        params["gran"] = granularity
        rows = self._query("""
            , p AS (
                SELECT pp.pos_order_id,
                       SUM(pp.amount) FILTER (WHERE pm.is_cash_count) AS cash,
                       SUM(pp.amount) FILTER (WHERE NOT pm.is_cash_count AND pm.journal_id IS NOT NULL) AS bank,
                       SUM(pp.amount) FILTER (WHERE pm.journal_id IS NULL) AS other
                  FROM pos_payment pp JOIN pos_payment_method pm ON pm.id = pp.payment_method_id
                 WHERE pp.pos_order_id IN (SELECT id FROM o)
                 GROUP BY pp.pos_order_id
            )
            SELECT date_trunc(%(gran)s, o.local_dt)::date AS bucket,
                   COALESCE(SUM(o.amount_total), 0) AS sales,
                   COUNT(*) FILTER (WHERE o.amount_total >= 0) AS orders,
                   COALESCE(SUM(p.cash), 0) AS cash,
                   COALESCE(SUM(p.bank), 0) AS bank,
                   COALESCE(SUM(p.other), 0) AS other
              FROM o LEFT JOIN p ON p.pos_order_id = o.id
             GROUP BY 1
        """, params)
        return {r["bucket"]: r for r in rows}

    def _whole_business(self, configs):
        """Payments outside the POS have no branch: only count them when every point of sale is shown."""
        return set(configs.ids) == set(self._configs(False).ids)

    def _add_outside_series(self, values, start, stop, configs, granularity):
        if not self._whole_business(configs):
            return values
        empty = {"sales": 0.0, "orders": 0, "cash": 0.0, "bank": 0.0, "other": 0.0}
        for row in self.env["alarab.laundry.report"]._outside_collection_rows(start, stop, by_day=True):
            key = row["day"] if granularity == "day" else row["day"].replace(day=1)
            bucket = values.setdefault(key, dict(empty))
            bucket = values[key] = dict(bucket)
            bucket[row["kind"]] += row["amount"]
        return values

    def _series(self, start, stop, prev_start, prev_stop, configs):
        granularity = "day" if (stop - start).days <= 62 else "month"
        buckets = self._buckets(start, stop, granularity)
        prev_buckets = self._buckets(prev_start, prev_stop, granularity)
        current = self._add_outside_series(self._series_values(start, stop, configs, granularity),
                                           start, stop, configs, granularity)
        previous = self._series_values(prev_start, prev_stop, configs, granularity)

        def key(day):
            return day if granularity == "day" else day.replace(day=1)

        empty = {"sales": 0.0, "orders": 0, "cash": 0.0, "bank": 0.0, "other": 0.0}
        fmt = "d MMM" if granularity == "day" else "MMM yyyy"
        series = {"granularity": granularity, "labels": [], "buckets": [],
                  "sales": [], "orders": [], "cash": [], "bank": [], "other": [], "prev_sales": []}
        for index, (b_start, b_stop) in enumerate(buckets):
            row = current.get(key(b_start), empty)
            series["labels"].append(format_date(self.env, b_start, date_format=fmt))
            series["buckets"].append({
                "start": fields.Datetime.to_string(self._to_utc(b_start)),
                "end": fields.Datetime.to_string(self._to_utc(b_stop + timedelta(days=1))),
            })
            for name in ("sales", "orders", "cash", "bank", "other"):
                series[name].append(row[name])
            prev = previous.get(key(prev_buckets[index][0]), empty) if index < len(prev_buckets) else empty
            series["prev_sales"].append(prev["sales"])
        return series

    def _heatmap(self, start, stop, configs):
        matrix = [[0] * 24 for _ in range(7)]
        for row in self._query("""
            SELECT (EXTRACT(ISODOW FROM local_dt)::int - 1) AS dow,
                   EXTRACT(HOUR FROM local_dt)::int AS hour,
                   COUNT(*) AS orders
              FROM o WHERE amount_total >= 0
             GROUP BY 1, 2
        """, self._params(start, stop, configs)):
            matrix[row["dow"]][row["hour"]] = row["orders"]
        locale = babel_locale_parse(self.env.lang or "en_US")
        names = get_day_names("abbreviated", locale=locale)  # 0 = Monday
        return {"days": [names[i] for i in range(7)], "matrix": matrix,
                "max": max(max(r) for r in matrix)}

    def _categories(self, start, stop, configs):
        params = self._params(start, stop, configs)
        params["discount_products"] = self._discount_products(configs)
        rows = self._query("""
            SELECT cat.id AS category_id,
                   COALESCE(SUM(l.price_subtotal_incl), 0) AS amount,
                   COALESCE(SUM(l.qty), 0) AS qty
              FROM pos_order_line l
              JOIN o ON o.id = l.order_id
              JOIN product_product pp ON pp.id = l.product_id
              LEFT JOIN LATERAL (
                    SELECT c.id FROM pos_category_product_template_rel r
                      JOIN pos_category c ON c.id = r.pos_category_id
                     WHERE r.product_template_id = pp.product_tmpl_id
                     ORDER BY c.sequence, c.id LIMIT 1) cat ON TRUE
             WHERE NOT (l.product_id = ANY(%(discount_products)s))
             GROUP BY cat.id
             ORDER BY amount DESC
        """, params)
        cats = self.env["pos.category"].browse([r["category_id"] for r in rows if r["category_id"]])
        names = {c.id: c.name for c in cats}
        return [{"id": r["category_id"], "name": names.get(r["category_id"]) or _("Uncategorized"),
                 "amount": r["amount"], "qty": r["qty"]} for r in rows]

    def _products(self, start, stop, configs, limit=10):
        params = self._params(start, stop, configs)
        params.update(discount_products=self._discount_products(configs), limit=limit)
        rows = self._query("""
            SELECT l.product_id, COALESCE(SUM(l.qty), 0) AS qty,
                   COALESCE(SUM(l.price_subtotal_incl), 0) AS amount
              FROM pos_order_line l JOIN o ON o.id = l.order_id
             WHERE NOT (l.product_id = ANY(%(discount_products)s))
             GROUP BY l.product_id
             ORDER BY amount DESC
             LIMIT %(limit)s
        """, params)
        products = self.env["product.product"].browse([r["product_id"] for r in rows])
        names = {p.id: p.display_name for p in products}
        return [{"id": r["product_id"], "name": names.get(r["product_id"], ""),
                 "qty": r["qty"], "amount": r["amount"]} for r in rows]

    def _cashiers(self, start, stop, configs, params=None):
        params = dict(params) if params else self._params(start, stop, configs)
        orders = self._query("""
            SELECT employee_id, user_id,
                   COUNT(*) FILTER (WHERE amount_total >= 0) AS orders,
                   COALESCE(SUM(amount_total) FILTER (WHERE amount_total >= 0), 0) AS sales,
                   COUNT(*) FILTER (WHERE amount_total < 0) AS refunds_count,
                   COALESCE(-SUM(amount_total) FILTER (WHERE amount_total < 0), 0) AS refunds_amount
              FROM o GROUP BY employee_id, user_id
        """, params)
        params["discount_products"] = self._discount_products(configs)
        discounts = {
            (r["employee_id"], r["user_id"]): r["discounts"]
            for r in self._query("""
                SELECT o.employee_id, o.user_id, COALESCE(SUM(
                         CASE WHEN l.product_id = ANY(%(discount_products)s) AND l.price_subtotal_incl < 0
                                  THEN -l.price_subtotal_incl
                              WHEN l.discount > 0 AND l.discount < 100
                                  THEN l.price_subtotal_incl * l.discount / (100 - l.discount)
                              WHEN l.discount >= 100 THEN l.qty * l.price_unit
                              ELSE 0 END), 0) AS discounts
                  FROM pos_order_line l JOIN o ON o.id = l.order_id
                 WHERE o.amount_total >= 0
                 GROUP BY o.employee_id, o.user_id
            """, params)
        }
        users = {u.id: u.name for u in self.env["res.users"].browse({r["user_id"] for r in orders if r["user_id"]})}
        employees = {}
        if self._has_employee():
            employees = {e.id: e.name for e in self.env["hr.employee"].sudo().browse(
                {r["employee_id"] for r in orders if r["employee_id"]})}
        merged = {}
        for r in orders:
            # with pos_hr the employee is the cashier; otherwise the user
            ident = ("employee", r["employee_id"]) if r["employee_id"] else ("user", r["user_id"])
            name = employees.get(r["employee_id"]) if r["employee_id"] else users.get(r["user_id"])
            entry = merged.setdefault(ident, {
                "key": "%s-%s" % ident, "kind": ident[0], "id": ident[1], "name": name or _("Unknown"),
                "orders": 0, "sales": 0.0, "refunds_count": 0, "refunds_amount": 0.0, "discounts": 0.0})
            for name_ in ("orders", "sales", "refunds_count", "refunds_amount"):
                entry[name_] += r[name_]
            entry["discounts"] += discounts.get((r["employee_id"], r["user_id"]), 0.0)
        return sorted(merged.values(), key=lambda e: e["sales"], reverse=True)

    def _sessions(self, start, stop, configs):
        params = self._params(start, stop, configs)
        sessions = self.env["pos.session"].search([
            ("config_id", "in", configs.ids),
            "|", ("state", "!=", "closed"),
            "&", ("stop_at", ">=", params["start"]), ("stop_at", "<", params["end"]),
        ], order="start_at desc")
        result, total_difference, with_difference = [], 0.0, 0
        for session in sessions:
            closed = session.state == "closed"
            difference = session.cash_register_difference if (closed and session.cash_control) else 0.0
            if closed and abs(difference) >= 0.01:
                total_difference += difference
                with_difference += 1
            result.append({
                "id": session.id,
                "name": session.name,
                "config": session.config_id.name,
                "user": session.user_id.name,
                "state": session.state,
                "state_label": dict(session._fields["state"]._description_selection(self.env)).get(session.state),
                "start_at": fields.Datetime.to_string(session.start_at) if session.start_at else False,
                "stop_at": fields.Datetime.to_string(session.stop_at) if session.stop_at else False,
                "cash_control": session.cash_control,
                "expected": session.cash_register_balance_end if session.cash_control else 0.0,
                "counted": session.cash_register_balance_end_real if closed else 0.0,
                "difference": difference,
            })
        return {
            "list": result,
            "open_count": len([s for s in result if s["state"] != "closed"]),
            "total_difference": total_difference,
            "with_difference": with_difference,
        }

    def _top_customers(self, start, stop, configs, limit=10):
        params = self._params(start, stop, configs)
        params["limit"] = limit
        rows = self._query("""
            SELECT partner_id, COUNT(*) AS orders, COALESCE(SUM(amount_total), 0) AS amount
              FROM o WHERE partner_id IS NOT NULL AND amount_total >= 0
             GROUP BY partner_id ORDER BY amount DESC LIMIT %(limit)s
        """, params)
        partners = {p.id: p for p in self.env["res.partner"].browse([r["partner_id"] for r in rows])}
        return [{"id": r["partner_id"], "name": partners[r["partner_id"]].display_name,
                 "phone": partners[r["partner_id"]].mobile or partners[r["partner_id"]].phone or "",
                 "orders": r["orders"], "amount": r["amount"]} for r in rows]

    def _lapsed_customers(self, configs, lapse_days, limit=30):
        """Regular customers (2+ orders) who have not come back for `lapse_days` (within a year)."""
        now = fields.Datetime.now()
        self.env.cr.execute("""
            SELECT po.partner_id, COUNT(*) AS orders, COALESCE(SUM(po.amount_total), 0) AS amount,
                   MAX(po.date_order) AS last_order
              FROM pos_order po JOIN pos_session ps ON ps.id = po.session_id
             WHERE po.partner_id IS NOT NULL
               AND po.state IN %(states)s
               AND po.amount_total >= 0
               AND ps.config_id = ANY(%(configs)s)
               AND po.company_id = ANY(%(companies)s)
             GROUP BY po.partner_id
            HAVING COUNT(*) >= 2
               AND MAX(po.date_order) < %(lapse_start)s
               AND MAX(po.date_order) >= %(floor)s
             ORDER BY amount DESC
             LIMIT %(limit)s
        """, {
            "states": VALID_STATES, "configs": configs.ids or [0], "companies": self.env.companies.ids,
            "lapse_start": now - timedelta(days=lapse_days), "floor": now - timedelta(days=365),
            "limit": limit,
        })
        rows = self.env.cr.dictfetchall()
        partners = {p.id: p for p in self.env["res.partner"].browse([r["partner_id"] for r in rows])}
        link = self.env["alarab.whatsapp.link"]
        template = self.env.ref("alarab_laundry_dashboard.whatsapp_winback_template", raise_if_not_found=False)
        result = []
        for r in rows:
            partner = partners[r["partner_id"]]
            url = False
            phone = link.normalize_phone(partner)
            if phone and template:
                text = self.env["whatsapp.template"].render_template(template.message, partner)
                url = link.build_url(phone, text)
            result.append({
                "id": partner.id, "name": partner.display_name,
                "phone": partner.mobile or partner.phone or "",
                "orders": r["orders"], "amount": r["amount"],
                "last_order": format_date(self.env, r["last_order"]),
                "days": (now - r["last_order"]).days,
                "whatsapp_url": url,
            })
        return result

    def _receivables_summary(self):
        rows, _today = self.env["alarab.laundry.report"]._receivable_rows()
        return {
            "total": sum(r["total"] for r in rows),
            "overdue": sum(r["d30"] + r["d60"] + r["d90"] + r["older"] for r in rows),
            "customers": len([r for r in rows if r["total"] > 0.005]),
        }

    # ------------------------------------------------------------------ API
    @api.model
    def get_filters(self):
        self._check_access()
        configs = self._configs(False)
        return {
            "configs": [{"id": c.id, "name": c.name} for c in configs],
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
    def get_data(self, preset="this_month", date_from=False, date_to=False, config_ids=None, lapse_days=45,
                 browser_tz=False):
        self._check_access()
        if browser_tz:
            self = self.with_context(ld_browser_tz=browser_tz)
        if preset not in PRESETS:
            raise UserError(_("Unknown period."))
        lapse_days = min(max(int(lapse_days or 45), 7), 365)
        configs = self._configs(config_ids)
        start, stop, prev_start, prev_stop = self._resolve_period(preset, date_from, date_to)
        currency = self.env.company.currency_id
        params = self._params(start, stop, configs)
        return {
            "currency_id": currency.id,
            "config_ids": configs.ids,
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
                "current": self._kpis(start, stop, configs),
                "previous": self._kpis(prev_start, prev_stop, configs),
            },
            "series": self._series(start, stop, prev_start, prev_stop, configs),
            "receivables": self._receivables_summary(),
            "heatmap": self._heatmap(start, stop, configs),
            "categories": self._categories(start, stop, configs),
            "products": self._products(start, stop, configs),
            "cashiers": self._cashiers(start, stop, configs),
            "sessions": self._sessions(start, stop, configs),
            "customers": {
                "top": self._top_customers(start, stop, configs),
                "lapsed": self._lapsed_customers(configs, lapse_days),
                "lapse_days": lapse_days,
            },
            "timezone": {
                "used": self._tz().zone,
                "user": self.env.user.tz or False,
                "browser": browser_tz or False,
            },
            "states": list(VALID_STATES),
            "has_employee": self._has_employee(),
        }
