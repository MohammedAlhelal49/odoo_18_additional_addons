# -*- coding: utf-8 -*-
import io
from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import format_date, format_datetime

REPORTS = ("daily", "course", "salesperson", "branch", "payment", "source", "remaining")
COMPARISONS = ("none", "previous", "last_year")
NOT_SET = "__none__"
REMAINING_LIMIT = 2000

BIDI_MARKS = {cp: None for cp in (0x200E, 0x200F, 0x061C, 0x202A, 0x202B, 0x202C, 0x202D, 0x202E,
                                   0x2066, 0x2067, 0x2068, 0x2069)}

# Confirmed sales orders (contracts) in scope, with the report filters applied.
ORDERS_CTE = """
    WITH o AS (
        SELECT so.id, so.name, so.partner_id, so.user_id, so.company_id,
               so.amount_total, so.amount_untaxed, so.amount_tax,
               COALESCE(so.remaining_amount, 0) AS remaining_amount,
               COALESCE(so.initial_payment, 0) AS initial_payment,
               so.payment_method, so.enrollment_type, so.source, so.date_order,
               (so.date_order AT TIME ZONE 'UTC' AT TIME ZONE %(tz)s) AS local_dt
          FROM sale_order so
         WHERE so.state = 'sale'
           AND so.company_id = ANY(%(companies)s)
           AND so.date_order >= %(start)s
           AND so.date_order < %(end)s
           AND (%(all_users)s OR so.user_id = ANY(%(users)s))
           AND (%(all_pm)s OR COALESCE(so.payment_method, %(not_set)s) = ANY(%(pms)s))
           AND (%(all_src)s OR COALESCE(so.source, %(not_set)s) = ANY(%(srcs)s))
           AND (%(all_enr)s OR COALESCE(so.enrollment_type, %(not_set)s) = ANY(%(enrs)s))
    )
"""


class AlomranSalesReport(models.AbstractModel):
    """Tabular sales reports (same layout as the Bait Al Arab reports).

    Every report is returned in one format, used by the screen, the PDF and the Excel export:
    columns [{key, label, type}], lines [{id, level, label, sublabel, values, children, action}], totals.
    """
    _name = "alomran.sales.report"
    _description = "Sales Reports"

    # ------------------------------------------------------------------ meta
    def _titles(self):
        return {
            "daily": _("Daily Sales"),
            "course": _("Sales by Course"),
            "salesperson": _("Salesperson Performance"),
            "branch": _("Sales by Branch"),
            "payment": _("Sales by Payment Method"),
            "source": _("Sales by Customer Source"),
            "remaining": _("Remaining to Invoice"),
        }

    def _dash(self):
        return self.env["alomran.sales.dashboard"]

    def _selection_choices(self, field_name):
        field = self.env["sale.order"]._fields[field_name]
        return ([{"key": k, "name": v} for k, v in field._description_selection(self.env)]
                + [{"key": NOT_SET, "name": _("Not set")}])

    @api.model
    def get_filters(self, report_key):
        dash = self._dash()
        dash._check_access()
        if report_key not in REPORTS:
            raise UserError(_("Unknown report."))
        dash_filters = dash.get_filters()
        return {
            "title": self._titles()[report_key],
            "presets": dash_filters["presets"],
            "companies": dash_filters["companies"],
            "users": dash_filters["users"],
            "can_see_all": dash_filters["can_see_all"],
            "comparisons": [
                {"key": "none", "label": _("No comparison")},
                {"key": "previous", "label": _("Previous period")},
                {"key": "last_year", "label": _("Same period last year")},
            ] if report_key != "remaining" else [],
            "payment_methods": self._selection_choices("payment_method"),
            "sources": self._selection_choices("source"),
            "enrollments": self._selection_choices("enrollment_type"),
            "all_companies_label": _("All branches"),
            "all_users_label": _("All salespeople"),
            "all_payments_label": _("All payment methods"),
            "all_sources_label": _("All sources"),
            "all_enrollments_label": _("New and re-enrollment"),
        }

    # ------------------------------------------------------------------ options
    def _clean_keys(self, values, field_name):
        allowed = {c["key"] for c in self._selection_choices(field_name)}
        return [v for v in (values or []) if v in allowed]

    def _resolve_options(self, options, report_key):
        options = dict(options or {})
        dash = self._dash()
        preset = options.get("preset") or "this_month"
        start, stop, prev_start, prev_stop = dash._resolve_period(preset, options.get("date_from"), options.get("date_to"))
        comparison = options.get("comparison") if options.get("comparison") in COMPARISONS else "none"
        if report_key == "remaining":
            comparison = "none"
        if comparison == "previous":
            cmp_start, cmp_stop = prev_start, prev_stop
        elif comparison == "last_year":
            cmp_start, cmp_stop = start - relativedelta(years=1), stop - relativedelta(years=1)
        else:
            cmp_start = cmp_stop = None
        companies, users = dash._scope(options.get("company_ids"), options.get("user_ids"))
        return {
            "preset": preset,
            "date_from": fields.Date.to_string(start),
            "date_to": fields.Date.to_string(stop),
            "start": start, "stop": stop,
            "comparison": comparison,
            "cmp_start": cmp_start, "cmp_stop": cmp_stop,
            "companies": companies, "users": users,
            "payment_methods": self._clean_keys(options.get("payment_methods"), "payment_method"),
            "sources": self._clean_keys(options.get("sources"), "source"),
            "enrollments": self._clean_keys(options.get("enrollments"), "enrollment_type"),
        }

    def _params(self, opts, start, stop):
        params = self._dash()._params(start, stop, opts["companies"], opts["users"])
        params.update({
            "not_set": NOT_SET,
            "all_pm": not opts["payment_methods"], "pms": opts["payment_methods"] or [""],
            "all_src": not opts["sources"], "srcs": opts["sources"] or [""],
            "all_enr": not opts["enrollments"], "enrs": opts["enrollments"] or [""],
        })
        return params

    def _query(self, opts, start, stop, body, extra=None):
        params = self._params(opts, start, stop)
        params.update(extra or {})
        self.env["sale.order"].flush_model()
        self.env.cr.execute(ORDERS_CTE + body, params)
        return self.env.cr.dictfetchall()

    def _period_label(self, start, stop):
        return "%s - %s" % (format_date(self.env, start), format_date(self.env, stop))

    def _selection_domain(self, field_name, keys):
        if not keys:
            return []
        values = [k for k in keys if k != NOT_SET]
        if NOT_SET in keys:
            return ["|", (field_name, "in", values), (field_name, "=", False)] if values else [(field_name, "=", False)]
        return [(field_name, "in", values)]

    def _order_action(self, opts, name, extra_domain=None, start=None, stop=None):
        dash = self._dash()
        start = start or opts["start"]
        stop = stop or opts["stop"]
        domain = [
            ("state", "=", "sale"),
            ("date_order", ">=", fields.Datetime.to_string(dash._to_utc(start))),
            ("date_order", "<", fields.Datetime.to_string(dash._to_utc(stop + timedelta(days=1)))),
            ("company_id", "in", opts["companies"].ids),
        ]
        if opts["users"]:
            domain.append(("user_id", "in", opts["users"].ids))
        domain += self._selection_domain("payment_method", opts["payment_methods"])
        domain += self._selection_domain("source", opts["sources"])
        domain += self._selection_domain("enrollment_type", opts["enrollments"])
        return {"res_model": "sale.order", "name": name, "domain": domain + (extra_domain or []),
                "company_ids": opts["companies"].ids}

    @staticmethod
    def _delta(current, previous):
        if not previous:
            return None
        return (current - previous) / abs(previous) * 100.0

    def _add_comparison(self, columns, lines, totals, main_key, cmp_values, cmp_total, label):
        """Append "<label>" and "Change %" columns, matching lines by id."""
        columns += [
            {"key": "cmp", "label": label, "type": "money"},
            {"key": "delta", "label": _("Change %"), "type": "pct"},
        ]

        def walk(items):
            for line in items:
                prev = cmp_values.get(line["id"], 0.0)
                line["values"]["cmp"] = prev
                line["values"]["delta"] = self._delta(line["values"].get(main_key) or 0.0, prev)
                walk(line.get("children") or [])

        walk(lines)
        totals["cmp"] = cmp_total
        totals["delta"] = self._delta(totals.get(main_key) or 0.0, cmp_total)

    def _cmp_label(self, opts):
        return _("Comparison (%s)", self._period_label(opts["cmp_start"], opts["cmp_stop"]))

    def _names(self, model, ids):
        return {r.id: r.display_name for r in self.env[model].sudo().browse([i for i in ids if i])}

    @staticmethod
    def _share(values, key, total):
        values["share"] = values[key] / total * 100.0 if total else 0.0

    # ------------------------------------------------------------------ grouped reports
    def _grouped(self, opts, start, stop, group_sql, sub_sql=None, extra_select="", extra=None):
        """Rows grouped by ``group_sql`` (and ``sub_sql`` for the children)."""
        sub = f", {sub_sql} AS sub" if sub_sql else ", NULL::int AS sub"
        rows = self._query(opts, start, stop, f"""
            SELECT {group_sql} AS grp {sub},
                   COUNT(*) AS contracts,
                   COALESCE(SUM(amount_total), 0) AS amount,
                   COALESCE(SUM(amount_untaxed), 0) AS untaxed,
                   COALESCE(SUM(amount_tax), 0) AS tax,
                   COALESCE(SUM(initial_payment), 0) AS initial,
                   COALESCE(SUM(remaining_amount) FILTER (WHERE remaining_amount > 0.01), 0) AS remaining,
                   COUNT(*) FILTER (WHERE enrollment_type = 'new') AS new_enrollments,
                   COUNT(*) FILTER (WHERE enrollment_type = 're_enrollment') AS re_enrollments
                   {extra_select}
              FROM o GROUP BY 1, 2
        """, extra)
        return rows

    def _build_grouped(self, opts, rows, keys, label_of, action_of, sub_label_of=None, sub_action_of=None,
                       sort_key="amount"):
        groups = {}
        for r in rows:
            g = groups.setdefault(r["grp"], {"values": dict.fromkeys(keys, 0.0), "children": []})
            for k in keys:
                g["values"][k] += r[k] or 0.0
            if r["sub"] is not None and sub_label_of:
                g["children"].append((r["sub"], {k: r[k] or 0.0 for k in keys}))
        lines, totals = [], dict.fromkeys(keys, 0.0)
        for grp, entry in sorted(groups.items(), key=lambda item: -(item[1]["values"].get(sort_key) or 0.0)):
            children = []
            if len(entry["children"]) > 1:
                for sub, values in sorted(entry["children"], key=lambda c: -(c[1].get(sort_key) or 0.0)):
                    children.append({
                        "id": "g-%s-%s" % (grp, sub), "level": 1, "label": sub_label_of(sub),
                        "values": values, "children": [], "action": sub_action_of(grp, sub),
                    })
            lines.append({
                "id": "g-%s" % (grp,), "level": 0, "label": label_of(grp),
                "values": entry["values"], "children": children, "action": action_of(grp),
            })
            for k in keys:
                totals[k] += entry["values"][k]
        return lines, totals

    def _finish_grouped(self, opts, columns, lines, totals, cmp_rows_fn):
        for line in lines:
            values = line["values"]
            if "avg" in [c["key"] for c in columns]:
                values["avg"] = values["amount"] / values["contracts"] if values["contracts"] else 0.0
                for child in line["children"]:
                    child["values"]["avg"] = (child["values"]["amount"] / child["values"]["contracts"]
                                              if child["values"]["contracts"] else 0.0)
            if "share" in [c["key"] for c in columns]:
                self._share(values, "amount", totals["amount"])
                for child in line["children"]:
                    self._share(child["values"], "amount", totals["amount"])
        if "avg" in [c["key"] for c in columns]:
            totals["avg"] = totals["amount"] / totals["contracts"] if totals["contracts"] else 0.0
        if "share" in [c["key"] for c in columns]:
            totals["share"] = 100.0 if totals["amount"] else 0.0
        if opts["comparison"] != "none":
            cmp_values, cmp_total = {}, 0.0
            for r in cmp_rows_fn(opts["cmp_start"], opts["cmp_stop"]):
                cmp_values["g-%s" % (r["grp"],)] = cmp_values.get("g-%s" % (r["grp"],), 0.0) + r["amount"]
                if r["sub"] is not None:
                    key = "g-%s-%s" % (r["grp"], r["sub"])
                    cmp_values[key] = cmp_values.get(key, 0.0) + r["amount"]
                cmp_total += r["amount"]
            self._add_comparison(columns, lines, totals, "amount", cmp_values, cmp_total, self._cmp_label(opts))
        return columns, lines, totals

    # ------------------------------------------------------------------ reports
    def _report_daily(self, opts):
        companies = self._names("res.company", opts["companies"].ids)
        columns = [
            {"key": "contracts", "label": _("Contracts"), "type": "int"},
            {"key": "amount", "label": _("Contracts value"), "type": "money"},
            {"key": "untaxed", "label": _("Excl. VAT"), "type": "money"},
            {"key": "tax", "label": _("VAT"), "type": "money"},
            {"key": "initial", "label": _("Initial payments"), "type": "money"},
            {"key": "remaining", "label": _("Remaining to invoice"), "type": "money"},
        ]
        keys = [c["key"] for c in columns]

        def rows(start, stop):
            return self._grouped(opts, start, stop, "local_dt::date", "company_id")

        days = {}
        for r in rows(opts["start"], opts["stop"]):
            day = days.setdefault(r["grp"], {"values": dict.fromkeys(keys, 0.0), "children": []})
            for k in keys:
                day["values"][k] += r[k] or 0.0
            day["children"].append((r["sub"], {k: r[k] or 0.0 for k in keys}))
        if opts["comparison"] != "none":
            day = opts["start"]
            while day <= opts["stop"]:
                days.setdefault(day, {"values": dict.fromkeys(keys, 0.0), "children": []})
                day += timedelta(days=1)
        show_branches = len(opts["companies"]) > 1
        lines, totals = [], dict.fromkeys(keys, 0.0)
        for day in sorted(days):
            entry = days[day]
            children = []
            if show_branches:
                for company_id, values in sorted(entry["children"], key=lambda c: companies.get(c[0], "")):
                    children.append({
                        "id": "day-%s-%s" % (day, company_id), "level": 1, "label": companies.get(company_id, ""),
                        "values": values, "children": [],
                        "action": self._order_action(opts, companies.get(company_id, ""),
                                                     [("company_id", "=", company_id)], day, day),
                    })
            lines.append({
                "id": "day-%s" % day, "level": 0, "label": format_date(self.env, day),
                "sublabel": format_date(self.env, day, date_format="EEEE"),
                "values": entry["values"], "children": children,
                "action": self._order_action(opts, format_date(self.env, day), [], day, day),
            })
            for k in keys:
                totals[k] += entry["values"][k]
        if opts["comparison"] != "none":
            cmp_by_day = {}
            for r in rows(opts["cmp_start"], opts["cmp_stop"]):
                cmp_by_day[r["grp"]] = cmp_by_day.get(r["grp"], 0.0) + r["amount"]
            cmp_values, offset = {}, 0
            day = opts["start"]
            while day <= opts["stop"]:
                cmp_day = opts["cmp_start"] + timedelta(days=offset)
                cmp_values["day-%s" % day] = cmp_by_day.get(cmp_day, 0.0) if cmp_day <= opts["cmp_stop"] else 0.0
                day += timedelta(days=1)
                offset += 1
            self._add_comparison(columns, lines, totals, "amount", cmp_values, sum(cmp_by_day.values()),
                                 self._cmp_label(opts))
        return columns, lines, totals

    def _report_course(self, opts):
        columns = [
            {"key": "contracts", "label": _("Contracts"), "type": "int"},
            {"key": "qty", "label": _("Quantity"), "type": "int"},
            {"key": "amount", "label": _("Amount"), "type": "money"},
            {"key": "share", "label": _("Share %"), "type": "pct"},
        ]
        keys = ["contracts", "qty", "amount"]

        def rows(start, stop):
            return self._query(opts, start, stop, """
                SELECT l.product_id AS grp, o.company_id AS sub,
                       COUNT(DISTINCT l.order_id) AS contracts,
                       COALESCE(SUM(l.product_uom_qty), 0) AS qty,
                       COALESCE(SUM(l.price_total), 0) AS amount
                  FROM sale_order_line l JOIN o ON o.id = l.order_id
                 WHERE l.product_id IS NOT NULL AND l.display_type IS NULL
                 GROUP BY 1, 2
            """)

        current = rows(opts["start"], opts["stop"])
        products = self._names("product.product", {r["grp"] for r in current})
        companies = self._names("res.company", opts["companies"].ids)
        lines, totals = self._build_grouped(
            opts, current, keys,
            label_of=lambda pid: products.get(pid, _("Unknown")),
            action_of=lambda pid: self._order_action(opts, products.get(pid, ""), [("order_line.product_id", "=", pid)]),
            sub_label_of=(lambda cid: companies.get(cid, "")) if len(opts["companies"]) > 1 else None,
            sub_action_of=lambda pid, cid: self._order_action(
                opts, companies.get(cid, ""), [("order_line.product_id", "=", pid), ("company_id", "=", cid)]),
        )
        return self._finish_grouped(opts, columns, lines, totals, rows)

    def _report_salesperson(self, opts):
        columns = [
            {"key": "contracts", "label": _("Contracts"), "type": "int"},
            {"key": "new_enrollments", "label": _("New"), "type": "int"},
            {"key": "re_enrollments", "label": _("Re-enrollment"), "type": "int"},
            {"key": "amount", "label": _("Contracts value"), "type": "money"},
            {"key": "avg", "label": _("Average contract"), "type": "money"},
            {"key": "initial", "label": _("Initial payments"), "type": "money"},
            {"key": "remaining", "label": _("Remaining to invoice"), "type": "money"},
        ]
        keys = ["contracts", "new_enrollments", "re_enrollments", "amount", "initial", "remaining"]

        def rows(start, stop):
            return self._grouped(opts, start, stop, "user_id", "company_id")

        current = rows(opts["start"], opts["stop"])
        users = self._names("res.users", {r["grp"] for r in current})
        companies = self._names("res.company", opts["companies"].ids)
        lines, totals = self._build_grouped(
            opts, current, keys,
            label_of=lambda uid: users.get(uid) or _("Unassigned"),
            action_of=lambda uid: self._order_action(opts, users.get(uid) or _("Unassigned"), [("user_id", "=", uid or False)]),
            sub_label_of=(lambda cid: companies.get(cid, "")) if len(opts["companies"]) > 1 else None,
            sub_action_of=lambda uid, cid: self._order_action(
                opts, companies.get(cid, ""), [("user_id", "=", uid or False), ("company_id", "=", cid)]),
        )
        return self._finish_grouped(opts, columns, lines, totals, rows)

    def _report_branch(self, opts):
        columns = [
            {"key": "contracts", "label": _("Contracts"), "type": "int"},
            {"key": "amount", "label": _("Contracts value"), "type": "money"},
            {"key": "avg", "label": _("Average contract"), "type": "money"},
            {"key": "share", "label": _("Share %"), "type": "pct"},
            {"key": "initial", "label": _("Initial payments"), "type": "money"},
            {"key": "remaining", "label": _("Remaining to invoice"), "type": "money"},
        ]
        keys = ["contracts", "amount", "initial", "remaining"]

        def rows(start, stop):
            return self._grouped(opts, start, stop, "company_id", "user_id")

        current = rows(opts["start"], opts["stop"])
        companies = self._names("res.company", {r["grp"] for r in current})
        users = self._names("res.users", {r["sub"] for r in current})
        lines, totals = self._build_grouped(
            opts, current, keys,
            label_of=lambda cid: companies.get(cid, ""),
            action_of=lambda cid: self._order_action(opts, companies.get(cid, ""), [("company_id", "=", cid)]),
            sub_label_of=(lambda uid: users.get(uid) or _("Unassigned")) if self._dash()._can_see_all() else None,
            sub_action_of=lambda cid, uid: self._order_action(
                opts, users.get(uid) or _("Unassigned"), [("company_id", "=", cid), ("user_id", "=", uid or False)]),
        )
        return self._finish_grouped(opts, columns, lines, totals, rows)

    def _report_by_selection(self, opts, field_name, with_new=False):
        columns = [
            {"key": "contracts", "label": _("Contracts"), "type": "int"},
            {"key": "amount", "label": _("Contracts value"), "type": "money"},
            {"key": "share", "label": _("Share %"), "type": "pct"},
            {"key": "avg", "label": _("Average contract"), "type": "money"},
        ]
        if with_new:
            columns.insert(1, {"key": "new_enrollments", "label": _("New"), "type": "int"})
        else:
            columns.append({"key": "initial", "label": _("Initial payments"), "type": "money"})
        keys = ["contracts", "amount", "initial", "new_enrollments"]
        labels = {c["key"]: c["name"] for c in self._selection_choices(field_name)}

        def rows(start, stop):
            return self._grouped(opts, start, stop, f"COALESCE({field_name}, '{NOT_SET}')")

        current = rows(opts["start"], opts["stop"])
        lines, totals = self._build_grouped(
            opts, current, keys,
            label_of=lambda key: labels.get(key, key),
            action_of=lambda key: self._order_action(opts, labels.get(key, key), self._selection_domain(field_name, [key])),
        )
        return self._finish_grouped(opts, columns, lines, totals, rows)

    def _report_payment(self, opts):
        return self._report_by_selection(opts, "payment_method")

    def _report_source(self, opts):
        return self._report_by_selection(opts, "source", with_new=True)

    def _report_remaining(self, opts):
        columns = [
            {"key": "date", "label": _("Date"), "type": "text"},
            {"key": "salesperson", "label": _("Salesperson"), "type": "text"},
            {"key": "branch", "label": _("Branch"), "type": "text"},
            {"key": "amount", "label": _("Contract value"), "type": "money"},
            {"key": "invoiced", "label": _("Invoiced"), "type": "money"},
            {"key": "remaining", "label": _("Remaining"), "type": "money"},
        ]
        rows = self._query(opts, opts["start"], opts["stop"], """
            SELECT id, amount_total, remaining_amount FROM o
             WHERE remaining_amount > 0.01
             ORDER BY remaining_amount DESC LIMIT %(limit)s
        """, {"limit": REMAINING_LIMIT})
        orders = {so.id: so for so in self.env["sale.order"].sudo().browse([r["id"] for r in rows])}
        lines, totals = [], {"amount": 0.0, "invoiced": 0.0, "remaining": 0.0}
        for r in rows:
            so = orders[r["id"]]
            values = {
                "date": format_date(self.env, so.date_order),
                "salesperson": so.user_id.name or "",
                "branch": so.company_id.name or "",
                "amount": r["amount_total"],
                "invoiced": r["amount_total"] - r["remaining_amount"],
                "remaining": r["remaining_amount"],
            }
            for k in totals:
                totals[k] += values[k]
            lines.append({
                "id": "so-%s" % so.id, "level": 0, "label": so.name,
                "sublabel": " · ".join(filter(None, [so.partner_id.name, so.partner_id.mobile or so.partner_id.phone])),
                "values": values, "children": [],
                "action": {"res_model": "sale.order", "res_id": so.id, "name": so.name,
                           "company_ids": opts["companies"].ids},
            })
        return columns, lines, totals

    # ------------------------------------------------------------------ public API
    def _filter_pairs(self, opts):
        pairs = []
        if set(opts["companies"].ids) != set(self.env.companies.ids) or len(opts["companies"]) > 1:
            pairs.append((_("Branch"), ", ".join(opts["companies"].mapped("name"))))
        if opts["users"]:
            pairs.append((_("Salesperson"), ", ".join(opts["users"].mapped("name"))))
        for key, field_name, label in (("payment_methods", "payment_method", _("Payment method")),
                                       ("sources", "source", _("Source")),
                                       ("enrollments", "enrollment_type", _("Enrollment"))):
            if opts[key]:
                names = {c["key"]: c["name"] for c in self._selection_choices(field_name)}
                pairs.append((label, ", ".join(names[k] for k in opts[key])))
        return pairs

    @api.model
    def get_report(self, report_key, options=None):
        dash = self._dash()
        dash._check_access()
        if report_key not in REPORTS:
            raise UserError(_("Unknown report."))
        opts = self._resolve_options(options, report_key)
        columns, lines, totals = getattr(self, "_report_%s" % report_key)(opts)
        pairs = self._filter_pairs(opts)
        return {
            "key": report_key,
            "title": self._titles()[report_key],
            "company": self.env.company.name,
            "currency_id": self.env.company.currency_id.id,
            "can_see_all": dash._can_see_all(),
            "period_label": self._period_label(opts["start"], opts["stop"]),
            "comparison_label": (self._period_label(opts["cmp_start"], opts["cmp_stop"])
                                 if opts["comparison"] != "none" else False),
            "filter_pairs": pairs,
            "filters_summary": ["%s: %s" % pair for pair in pairs],
            "options": {
                "preset": opts["preset"], "date_from": opts["date_from"], "date_to": opts["date_to"],
                "comparison": opts["comparison"], "company_ids": opts["companies"].ids,
                "user_ids": opts["users"].ids, "payment_methods": opts["payment_methods"],
                "sources": opts["sources"], "enrollments": opts["enrollments"],
            },
            "columns": columns,
            "lines": lines,
            "totals": totals,
            "generated": format_datetime(self.env, fields.Datetime.now(), tz=dash._tz().zone,
                                         dt_format="yyyy-MM-dd HH:mm"),
        }

    # ------------------------------------------------------------------ Excel
    @api.model
    def get_xlsx(self, report_key, options=None):
        import xlsxwriter

        data = self.get_report(report_key, options)
        currency = self.env["res.currency"].browse(data["currency_id"])
        rtl = self.env["res.lang"]._get_data(code=self.env.lang or "en_US").direction == "rtl"
        output = io.BytesIO()
        book = xlsxwriter.Workbook(output, {"in_memory": True})
        sheet = book.add_worksheet(data["title"][:31])
        if rtl:
            sheet.right_to_left()
        money_fmt = "#,##0.%s" % ("0" * currency.decimal_places) if currency.decimal_places else "#,##0"
        number_formats = {"money": money_fmt, "int": "#,##0", "pct": '0.0"%"'}
        f = {
            "title": book.add_format({"bold": True, "font_size": 14}),
            "muted": book.add_format({"font_color": "#666666"}),
            "head": book.add_format({"bold": True, "bg_color": "#E9ECEF", "border": 1, "text_wrap": True, "valign": "vcenter"}),
            "head_num": book.add_format({"bold": True, "bg_color": "#E9ECEF", "border": 1, "align": "right",
                                         "text_wrap": True, "valign": "vcenter"}),
        }
        for level in (0, 1):
            for kind in ("text", "money", "int", "pct"):
                props = {"bold": level == 0, "indent": level * 2 if kind == "text" else 0}
                if kind in number_formats:
                    props["num_format"] = number_formats[kind]
                f["%s_%s" % (kind, level)] = book.add_format(props)
        for kind in ("text", "money", "int", "pct"):
            props = {"bold": True, "top": 2, "bg_color": "#F8F9FA"}
            if kind in number_formats:
                props["num_format"] = number_formats[kind]
            f["total_%s" % kind] = book.add_format(props)

        row = 0
        sheet.write(row, 0, data["title"], f["title"]); row += 1
        sheet.write(row, 0, data["company"], f["muted"]); row += 1
        sheet.write(row, 0, _("Period: %s", data["period_label"]), f["muted"]); row += 1
        if data["comparison_label"]:
            sheet.write(row, 0, _("Compared with: %s", data["comparison_label"]), f["muted"]); row += 1
        for part in data["filters_summary"]:
            sheet.write(row, 0, part, f["muted"]); row += 1
        sheet.write(row, 0, _("Currency: %s", currency.name), f["muted"]); row += 2

        columns = data["columns"]
        header_row = row
        sheet.write(row, 0, "", f["head"])
        for i, col in enumerate(columns, start=1):
            sheet.write(row, i, col["label"], f["head_num"] if col["type"] != "text" else f["head"])
        sheet.set_row(row, 30)
        row += 1

        def cell(r, c, value, kind, level):
            fmt = f["%s_%s" % (kind if kind in number_formats else "text", min(level, 1))]
            if value is None or value == "":
                sheet.write_blank(r, c, None, fmt)
            elif kind in number_formats:
                sheet.write_number(r, c, float(value), fmt)
            else:
                sheet.write_string(r, c, str(value), fmt)

        def write_lines(lines):
            nonlocal row
            for line in lines:
                level = line["level"]
                label = line["label"] + (" (%s)" % line["sublabel"] if line.get("sublabel") else "")
                cell(row, 0, label, "text", level)
                for i, col in enumerate(columns, start=1):
                    cell(row, i, line["values"].get(col["key"]), col["type"], level)
                if level:
                    sheet.set_row(row, None, None, {"level": level})
                row += 1
                write_lines(line.get("children") or [])

        write_lines(data["lines"])
        sheet.write(row, 0, _("Total"), f["total_text"])
        for i, col in enumerate(columns, start=1):
            value = data["totals"].get(col["key"])
            kind = col["type"] if col["type"] in number_formats else "text"
            if value is None:
                sheet.write_blank(row, i, None, f["total_%s" % kind])
            elif kind == "text":
                sheet.write_string(row, i, str(value), f["total_text"])
            else:
                sheet.write_number(row, i, float(value), f["total_%s" % kind])
        sheet.set_column(0, 0, 36)
        sheet.set_column(1, len(columns), 16)
        sheet.freeze_panes(header_row + 1, 1)
        sheet.outline_settings(True, False, True, False)
        book.close()
        filename = "%s - %s.xlsx" % (data["title"], data["period_label"].replace("/", "-"))
        return output.getvalue(), filename


class AlomranSalesReportPdf(models.AbstractModel):
    _name = "report.alomran_implementation.report_sales_document"
    _description = "Sales Report PDF"

    @staticmethod
    def _clean_bidi(value):
        """Drop invisible direction marks (babel puts them in Arabic dates); the PDF engine draws them badly."""
        if isinstance(value, str):
            return value.translate(BIDI_MARKS)
        if isinstance(value, dict):
            return {k: AlomranSalesReportPdf._clean_bidi(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return type(value)(AlomranSalesReportPdf._clean_bidi(v) for v in value)
        return value

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        report = self._clean_bidi(
            self.env["alomran.sales.report"].get_report(data.get("report_key"), data.get("report_options")))
        currency = self.env["res.currency"].browse(report["currency_id"])
        return {
            "doc_ids": [],
            "doc_model": "alomran.sales.report",
            "docs": [],
            "report": report,
            "currency": currency,
            "company": self.env.company,
            "rtl": self.env["res.lang"]._get_data(code=self.env.lang or "en_US").direction == "rtl",
            "header_rows": [(_("Period"), report["period_label"])]
                           + ([(_("Compared with"), report["comparison_label"])] if report["comparison_label"] else [])
                           + [tuple(pair) for pair in report["filter_pairs"]],
            "footer_rows": [(_("Currency"), currency.name), (_("Printed on"), report["generated"])],
        }
