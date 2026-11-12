import io
import urllib.parse
from datetime import date, timedelta

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import consteq
from odoo.tools.misc import format_date, format_datetime, hmac

BIDI_MARKS = {cp: None for cp in (0x200E, 0x200F, 0x061C, 0x202A, 0x202B, 0x202C, 0x202D, 0x202E,
                                   0x2066, 0x2067, 0x2068, 0x2069)}

REPORTS = ("daily", "category", "collection", "sessions", "cashiers", "customers", "receivables",
           "statement", "monthly_receivables")
# reports on customer debts (POS orders on the customer account): no point of sale / cashier, no comparison
INVOICE_REPORTS = ("statement", "monthly_receivables")
STATEMENT_SCOPE = "london_laundry_implementation.customer_statement"
INVOICE_STATUSES = ("paid", "partial", "not_paid")
SHOW_CHOICES = ("all", "with_balance", "top1", "top10", "top20", "top50")
STATEMENT_MESSAGE_PARAM = "london_laundry_implementation.statement_whatsapp_message"
DEFAULT_STATEMENT_MESSAGE = """مرحباً {{partner_name}}،

كشف حسابكم لدى {{company}} للفترة من {{date_from}} إلى {{date_to}}:
Your statement with {{company}} from {{date_from}} to {{date_to}}:

• رصيد سابق | Previous balance: {{previous_balance}}
• طلبات الفترة | Orders: {{invoiced}} ({{invoice_count}})
• المدفوع | Paid: {{paid}}
• المتبقي | Remaining: {{remaining}}
• إجمالي المستحق | Total due: {{total_due}}

📄 كشف الحساب التفصيلي | Detailed statement:
{{statement_link}}

شكراً لكم / Thank you"""


def format_amount_plain(amount, currency):
    return ("{:,.%sf}" % currency.decimal_places).format(amount)
COMPARISONS = ("none", "previous", "last_year")
CUSTOMERS_LIMIT = 1000


class LaundryReport(models.AbstractModel):
    """Accounting-style reports for the laundry manager.

    Every report is returned in one format, used by the screen, the PDF and the Excel export:
    columns [{key, label, type}], lines [{id, level, label, sublabel, values, children, action}], totals.
    """

    _name = "london.laundry.report"
    _description = "Laundry Reports"

    # ------------------------------------------------------------------ meta
    def _titles(self):
        return {
            "daily": _("Daily Sales"),
            "category": _("Sales by Service and Item"),
            "collection": _("Collection by Payment Method"),
            "sessions": _("Cash Register Sessions"),
            "cashiers": _("Cashier Performance"),
            "customers": _("Customers"),
            "receivables": _("Customer Balances (Receivables)"),
            "statement": _("Customer Statement"),
            "monthly_receivables": _("Monthly Receivables"),
        }

    def _dash(self):
        return self.env["london.laundry.dashboard"]

    @api.model
    def get_filters(self, report_key):
        self._dash()._check_access()
        if report_key not in REPORTS:
            raise UserError(_("Unknown report."))
        dash = self._dash()
        configs = dash._configs(False)
        result = {
            "title": self._titles()[report_key],
            "presets": self._presets(),
            "months": self._month_choices(),
            "years": self._year_choices(),
            "current_month": dash._today().month,
            "current_year": dash._today().year,
            "configs": [{"id": c.id, "name": c.name} for c in configs],
            "comparisons": [
                {"key": "none", "label": _("No comparison")},
                {"key": "previous", "label": _("Previous period")},
                {"key": "last_year", "label": _("Same period last year")},
            ],
            "cashiers": [],
            "categories": [],
            "payment_kinds": [],
            "all_configs_label": _("All points of sale"),
            "all_cashiers_label": _("All cashiers"),
            "all_categories_label": _("All services"),
            "all_payments_label": _("All payment methods"),
        }
        if report_key in ("daily", "category", "cashiers", "customers"):
            result["cashiers"] = self._cashier_choices(configs)
        if report_key == "category":
            result["categories"] = [{"id": c.id, "name": c.name}
                                    for c in self.env["pos.category"].search([], order="sequence, name")]
        if report_key == "collection":
            result["payment_kinds"] = [{"key": "cash", "name": _("Cash")}, {"key": "bank", "name": _("Bank")},
                                       {"key": "other", "name": _("Customer account (pay later)")}]
        # receivables are a snapshot of what is owed today: no period, comparison or branch
        result["has_period"] = report_key != "receivables"
        result["has_comparison"] = report_key not in ("receivables",) + INVOICE_REPORTS
        result["default_preset"] = "this_year" if report_key == "monthly_receivables" else "this_month"
        if report_key in ("receivables",) + INVOICE_REPORTS:
            result["configs"] = []
        result["has_customer_filters"] = report_key in INVOICE_REPORTS
        result["statuses"] = []
        result["companies"] = []
        result["show_choices"] = []
        if report_key in INVOICE_REPORTS:
            labels = self._status_labels()
            result["statuses"] = [{"key": k, "name": labels[k]} for k in INVOICE_STATUSES]
            result["companies"] = [{"id": c.id, "name": c.name} for c in self.env.companies]
            result["all_statuses_label"] = _("All orders")
            result["all_companies_label"] = _("All branches")
        if report_key == "statement":
            result["show_choices"] = [{"key": k, "label": v} for k, v in self._show_labels().items()]
        return result

    def _show_labels(self):
        return {
            "all": _("All customers"),
            "with_balance": _("Customers with a balance"),
            "top1": _("Top debtor"),
            "top10": _("Top 10 debtors"),
            "top20": _("Top 20 debtors"),
            "top50": _("Top 50 debtors"),
        }

    def _presets(self):
        presets = list(self._dash().get_filters()["presets"])
        # a chosen month / year, before "Custom"
        at = next((i for i, p in enumerate(presets) if p["key"] == "custom"), len(presets))
        presets[at:at] = [{"key": "month", "label": _("Specific month")}, {"key": "year", "label": _("Specific year")}]
        return presets

    def _month_choices(self):
        return [{"key": m, "name": format_date(self.env, date(2000, m, 1), date_format="MMMM")} for m in range(1, 13)]

    def _year_choices(self):
        """From the first POS order / invoice to this year, newest first."""
        self.env.cr.execute("""
            SELECT LEAST(
                (SELECT MIN(invoice_date) FROM account_move WHERE state = 'posted' AND company_id = ANY(%(c)s)),
                (SELECT MIN(date_order)::date FROM pos_order WHERE company_id = ANY(%(c)s)))
        """, {"c": self.env.companies.ids})
        first = self.env.cr.fetchone()[0]
        this_year = self._dash()._today().year
        return list(range(this_year, (first.year if first else this_year) - 1, -1))

    def _cashier_choices(self, configs):
        """Everyone who rang up an order at these points of sale (users, and employees with pos_hr)."""
        dash = self._dash()
        employee = "po.employee_id" if dash._has_employee() else "NULL::int"
        self.env.cr.execute(f"""
            SELECT DISTINCT {employee} AS employee_id, po.user_id
              FROM pos_order po JOIN pos_session ps ON ps.id = po.session_id
             WHERE ps.config_id = ANY(%s) AND po.company_id = ANY(%s)
        """, [configs.ids or [0], self.env.companies.ids])
        rows = self.env.cr.dictfetchall()
        choices = {}
        users = self.env["res.users"].browse({r["user_id"] for r in rows if r["user_id"] and not r["employee_id"]})
        for user in users:
            choices["user-%s" % user.id] = user.name
        if dash._has_employee():
            for emp in self.env["hr.employee"].sudo().browse({r["employee_id"] for r in rows if r["employee_id"]}):
                choices["employee-%s" % emp.id] = emp.name
        return sorted(({"key": k, "name": v} for k, v in choices.items()), key=lambda c: c["name"] or "")

    # ------------------------------------------------------------------ options
    def _resolve_options(self, options):
        options = dict(options or {})
        dash = self._dash()
        preset = options.get("preset") or "this_month"
        today = dash._today()
        try:
            year = int(options.get("year") or today.year)
            month = min(max(int(options.get("month") or today.month), 1), 12)
        except (TypeError, ValueError):
            year, month = today.year, today.month
        year = min(max(year, 2000), today.year)
        if preset in ("month", "year"):
            # a chosen calendar month / year = a custom period
            first = date(year, month, 1) if preset == "month" else date(year, 1, 1)
            last = first + (relativedelta(months=1) if preset == "month" else relativedelta(years=1)) - timedelta(days=1)
            start, stop, prev_start, prev_stop = dash._resolve_period(
                "custom", fields.Date.to_string(first), fields.Date.to_string(last))
            if preset == "month":
                # previous period = the month before (not "same number of days")
                prev_start, prev_stop = first - relativedelta(months=1), first - timedelta(days=1)
            else:
                prev_start, prev_stop = first - relativedelta(years=1), first - timedelta(days=1)
        else:
            start, stop, prev_start, prev_stop = dash._resolve_period(preset, options.get("date_from"), options.get("date_to"))
        comparison = options.get("comparison") if options.get("comparison") in COMPARISONS else "none"
        if comparison == "previous":
            cmp_start, cmp_stop = prev_start, prev_stop
        elif comparison == "last_year":
            cmp_start, cmp_stop = start - relativedelta(years=1), stop - relativedelta(years=1)
        else:
            cmp_start = cmp_stop = None
        configs = dash._configs(options.get("config_ids"))
        cashiers = [c for c in (options.get("cashiers") or []) if isinstance(c, str) and "-" in c]
        users = [int(c.split("-")[1]) for c in cashiers if c.startswith("user-")]
        employees = [int(c.split("-")[1]) for c in cashiers if c.startswith("employee-")]
        return {
            "preset": preset,
            "month": month, "year": year,
            "date_from": fields.Date.to_string(start),
            "date_to": fields.Date.to_string(stop),
            "start": start, "stop": stop,
            "comparison": comparison,
            "cmp_start": cmp_start, "cmp_stop": cmp_stop,
            "configs": configs,
            "config_ids": configs.ids,
            "cashiers": cashiers, "users": users, "employees": employees,
            "category_ids": [int(c) for c in (options.get("category_ids") or [])],
            "payment_kinds": [k for k in (options.get("payment_kinds") or []) if k in ("cash", "bank", "other")],
            # customer debt reports
            "partner_search": str(options.get("partner_search") or "").strip()[:100],
            "statuses": [k for k in (options.get("statuses") or []) if k in INVOICE_STATUSES],
            # only branches the user is working in (company switcher)
            "company_ids": [int(c) for c in (options.get("company_ids") or [])
                            if str(c).isdigit() and int(c) in self.env.companies.ids],
            "show": options.get("show") if options.get("show") in SHOW_CHOICES else "all",
            "min_due": self._to_float(options.get("min_due")),
        }

    @staticmethod
    def _to_float(value):
        try:
            return max(float(value), 0.0) if value not in (None, "") else 0.0
        except (TypeError, ValueError):
            return 0.0

    def _matching_partner_ids(self, search):
        """Customers (commercial entities) whose name, reference or phone matches. None = no search."""
        if not search:
            return None
        params = {"like": "%%%s%%" % search, "digits": None, "local": None}
        digits = "".join(ch for ch in search if ch.isdigit())
        if len(digits) >= 3:
            # numbers are stored as '+971 50 123 4567': '0501234567' must still find it
            params["digits"] = "%%%s%%" % digits
            local = digits[2:] if digits.startswith("00") else digits[1:] if digits.startswith("0") else digits
            params["local"] = "%%%s%%" % local if len(local) >= 3 else params["digits"]
        self.env.flush_all()
        self.env.cr.execute("""
            SELECT DISTINCT COALESCE(p.commercial_partner_id, p.id)
              FROM res_partner p
             WHERE p.name ILIKE %(like)s OR p.ref ILIKE %(like)s
                OR (%(digits)s IS NOT NULL AND (
                        regexp_replace(COALESCE(p.phone, ''), '[^0-9]', '', 'g') LIKE %(digits)s
                     OR regexp_replace(COALESCE(p.mobile, ''), '[^0-9]', '', 'g') LIKE %(digits)s
                     OR regexp_replace(COALESCE(p.phone, ''), '[^0-9]', '', 'g') LIKE %(local)s
                     OR regexp_replace(COALESCE(p.mobile, ''), '[^0-9]', '', 'g') LIKE %(local)s))
        """, params)
        return [r[0] for r in self.env.cr.fetchall()] or [0]

    def _for_branches(self, opts):
        """The report restricted to the chosen branches (companies)."""
        return self.with_context(allowed_company_ids=opts["company_ids"]) if opts["company_ids"] else self

    def _params(self, opts, start, stop):
        params = self._dash()._params(start, stop, opts["configs"])
        if opts["cashiers"]:
            params.update(no_cashier=False, users=opts["users"] or [0], employees=opts["employees"] or [0])
        return params

    def _query(self, opts, start, stop, body, extra=None):
        params = self._params(opts, start, stop)
        params.update(extra or {})
        return self._dash()._query(body, params)

    def _period_label(self, start, stop):
        return "%s - %s" % (format_date(self.env, start), format_date(self.env, stop))

    def _order_action(self, opts, name, extra_domain=None, start=None, stop=None):
        dash = self._dash()
        start = start or opts["start"]
        stop = stop or opts["stop"]
        domain = [
            ("date_order", ">=", fields.Datetime.to_string(dash._to_utc(start))),
            ("date_order", "<", fields.Datetime.to_string(dash._to_utc(stop + timedelta(days=1)))),
            ("state", "in", ["paid", "done", "invoiced"]),
            ("session_id.config_id", "in", opts["config_ids"]),
        ]
        if opts["cashiers"]:
            cashier_domain = []
            if opts["users"]:
                user_dom = [("user_id", "in", opts["users"])]
                if dash._has_employee():
                    user_dom = ["&", ("employee_id", "=", False)] + user_dom
                cashier_domain.append(user_dom)
            if opts["employees"]:
                cashier_domain.append([("employee_id", "in", opts["employees"])])
            if len(cashier_domain) == 2:
                domain += ["|"] + cashier_domain[0] + cashier_domain[1]
            else:
                domain += cashier_domain[0]
        return {"res_model": "pos.order", "name": name, "domain": domain + (extra_domain or [])}

    def _local_date(self, utc_dt):
        import pytz
        return pytz.utc.localize(utc_dt).astimezone(self._dash()._tz()).date()

    @staticmethod
    def _delta(current, previous):
        if not previous:
            return None
        return (current - previous) / abs(previous) * 100.0

    def _add_comparison(self, columns, lines, totals, main_key, cmp_values, cmp_total, label):
        """Append "<label> (comparison)" and "Change %" columns, matching lines by id."""
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

    # ------------------------------------------------------------------ reports
    def _discount_sql(self):
        return """CASE WHEN l.product_id = ANY(%(discount_products)s) AND l.price_subtotal_incl < 0
                           THEN -l.price_subtotal_incl
                       WHEN l.discount > 0 AND l.discount < 100
                           THEN l.price_subtotal_incl * l.discount / (100 - l.discount)
                       WHEN l.discount >= 100 THEN l.qty * l.price_unit
                       ELSE 0 END"""

    def _daily_rows(self, opts, start, stop):
        extra = {"discount_products": self._dash()._discount_products(opts["configs"])}
        rows = self._query(opts, start, stop, f"""
            , ord AS (
                SELECT o.local_dt::date AS day, ps.config_id,
                       COUNT(*) FILTER (WHERE o.amount_total >= 0 AND NOT o.is_collection) AS orders,
                       COALESCE(SUM(o.amount_total) FILTER (WHERE o.amount_total >= 0 AND NOT o.is_collection), 0) AS gross,
                       COALESCE(-SUM(o.amount_total) FILTER (WHERE o.amount_total < 0), 0) AS refunds,
                       COALESCE(SUM(o.amount_total), 0) AS net,
                       COALESCE(SUM(o.amount_tax), 0) AS tax
                  FROM o JOIN pos_order po ON po.id = o.id JOIN pos_session ps ON ps.id = po.session_id
                 GROUP BY 1, 2
            ), disc AS (
                SELECT o.local_dt::date AS day, ps.config_id, COALESCE(SUM({self._discount_sql()}), 0) AS discounts
                  FROM pos_order_line l JOIN o ON o.id = l.order_id
                  JOIN pos_order po ON po.id = o.id JOIN pos_session ps ON ps.id = po.session_id
                 WHERE o.amount_total >= 0
                 GROUP BY 1, 2
            )
            SELECT ord.*, COALESCE(disc.discounts, 0) AS discounts
              FROM ord LEFT JOIN disc ON disc.day = ord.day AND disc.config_id = ord.config_id
             ORDER BY ord.day
        """, extra)
        return rows

    def _report_daily(self, opts):
        names = {c.id: c.name for c in opts["configs"]}
        columns = [
            {"key": "orders", "label": _("Orders"), "type": "int"},
            {"key": "gross", "label": _("Sales"), "type": "money"},
            {"key": "discounts", "label": _("Discounts"), "type": "money"},
            {"key": "refunds", "label": _("Refunds"), "type": "money"},
            {"key": "net", "label": _("Net sales"), "type": "money"},
            {"key": "tax", "label": _("VAT"), "type": "money"},
            {"key": "untaxed", "label": _("Net excl. VAT"), "type": "money"},
        ]
        keys = ("orders", "gross", "discounts", "refunds", "net", "tax")
        days = {}
        for r in self._daily_rows(opts, opts["start"], opts["stop"]):
            day = days.setdefault(r["day"], {"values": dict.fromkeys(keys, 0.0), "children": []})
            for k in keys:
                day["values"][k] += r[k]
            day["children"].append((r["config_id"], {k: r[k] for k in keys}))
        lines, totals = [], dict.fromkeys(keys, 0.0)
        show_branches = len(opts["config_ids"]) > 1
        if opts["comparison"] != "none":
            # every day gets a row, so each comparison value has a row to sit on and rows add up to the total
            day = opts["start"]
            while day <= opts["stop"]:
                days.setdefault(day, {"values": dict.fromkeys(keys, 0.0), "children": []})
                day += timedelta(days=1)
        for day in sorted(days):
            entry = days[day]
            entry["values"]["untaxed"] = entry["values"]["net"] - entry["values"]["tax"]
            children = []
            if show_branches:
                for config_id, values in sorted(entry["children"], key=lambda c: names.get(c[0], "")):
                    values["untaxed"] = values["net"] - values["tax"]
                    children.append({
                        "id": "day-%s-%s" % (day, config_id), "level": 1, "label": names.get(config_id, ""),
                        "values": values, "children": [],
                        "action": self._order_action(opts, names.get(config_id, ""),
                                                     [("session_id.config_id", "=", config_id)], day, day),
                    })
            lines.append({
                "id": "day-%s" % day, "level": 0, "label": format_date(self.env, day),
                "sublabel": format_date(self.env, day, date_format="EEEE"),
                "values": entry["values"], "children": children,
                "action": self._order_action(opts, format_date(self.env, day), [], day, day),
            })
            for k in keys:
                totals[k] += entry["values"][k]
        totals["untaxed"] = totals["net"] - totals["tax"]
        if opts["comparison"] != "none":
            # align comparison days by position (1st day with 1st day...)
            cmp_by_day = {}
            for r in self._daily_rows(opts, opts["cmp_start"], opts["cmp_stop"]):
                cmp_by_day[r["day"]] = cmp_by_day.get(r["day"], 0.0) + r["net"]
            cmp_values, offset = {}, 0
            day = opts["start"]
            while day <= opts["stop"]:
                cmp_day = opts["cmp_start"] + timedelta(days=offset)
                cmp_values["day-%s" % day] = cmp_by_day.get(cmp_day, 0.0) if cmp_day <= opts["cmp_stop"] else 0.0
                day += timedelta(days=1)
                offset += 1
            self._add_comparison(columns, lines, totals, "net", cmp_values, sum(cmp_by_day.values()),
                                 self._cmp_label(opts))
        return columns, lines, totals

    def _category_rows(self, opts, start, stop):
        extra = {"discount_products": self._dash()._discount_products(opts["configs"]),
                 "categories": opts["category_ids"] or [0], "all_categories": not opts["category_ids"]}
        return self._query(opts, start, stop, """
            , cl AS (
                SELECT l.product_id, l.qty, l.price_subtotal, l.price_subtotal_incl,
                       (SELECT c.id FROM pos_category_product_template_rel r
                          JOIN pos_category c ON c.id = r.pos_category_id
                         WHERE r.product_template_id = pp.product_tmpl_id
                         ORDER BY c.sequence, c.id LIMIT 1) AS category_id
                  FROM pos_order_line l JOIN o ON o.id = l.order_id
                  JOIN product_product pp ON pp.id = l.product_id
                 WHERE NOT (l.product_id = ANY(%(discount_products)s))
            )
            SELECT category_id, product_id,
                   COALESCE(SUM(qty), 0) AS qty,
                   COALESCE(SUM(price_subtotal), 0) AS untaxed,
                   COALESCE(SUM(price_subtotal_incl), 0) AS amount
              FROM cl
             WHERE %(all_categories)s OR category_id = ANY(%(categories)s)
             GROUP BY category_id, product_id
        """, extra)

    def _report_category(self, opts):
        rows = self._category_rows(opts, opts["start"], opts["stop"])
        columns = [
            {"key": "qty", "label": _("Quantity"), "type": "int"},
            {"key": "untaxed", "label": _("Excl. VAT"), "type": "money"},
            {"key": "amount", "label": _("Amount"), "type": "money"},
            {"key": "share", "label": _("Share %"), "type": "pct"},
        ]
        cats = self.env["pos.category"].browse({r["category_id"] for r in rows if r["category_id"]})
        cat_names = {c.id: c.name for c in cats}
        products = {p.id: p.display_name for p in self.env["product.product"].browse({r["product_id"] for r in rows})}
        total_amount = sum(r["amount"] for r in rows)
        groups = {}
        for r in rows:
            g = groups.setdefault(r["category_id"], {"qty": 0.0, "untaxed": 0.0, "amount": 0.0, "items": []})
            for k in ("qty", "untaxed", "amount"):
                g[k] += r[k]
            g["items"].append(r)
        lines = []
        for cat_id, g in sorted(groups.items(), key=lambda kv: kv[1]["amount"], reverse=True):
            cat_name = cat_names.get(cat_id) or _("Uncategorized")
            cat_dom = [("lines.product_id.pos_categ_ids", "in", [cat_id])] if cat_id else [("lines.product_id.pos_categ_ids", "=", False)]
            children = [{
                "id": "prod-%s" % r["product_id"], "level": 1, "label": products.get(r["product_id"], ""),
                "values": {"qty": r["qty"], "untaxed": r["untaxed"], "amount": r["amount"],
                           "share": r["amount"] / total_amount * 100 if total_amount else 0.0},
                "children": [],
                "action": self._order_action(opts, products.get(r["product_id"], ""), [("lines.product_id", "=", r["product_id"])]),
            } for r in sorted(g["items"], key=lambda r: r["amount"], reverse=True)]
            lines.append({
                "id": "cat-%s" % (cat_id or 0), "level": 0, "label": cat_name,
                "values": {"qty": g["qty"], "untaxed": g["untaxed"], "amount": g["amount"],
                           "share": g["amount"] / total_amount * 100 if total_amount else 0.0},
                "children": children,
                "action": self._order_action(opts, cat_name, cat_dom),
            })
        totals = {"qty": sum(r["qty"] for r in rows), "untaxed": sum(r["untaxed"] for r in rows),
                  "amount": total_amount, "share": 100.0 if total_amount else 0.0}
        if opts["comparison"] != "none":
            cmp_values = {}
            cmp_rows = self._category_rows(opts, opts["cmp_start"], opts["cmp_stop"])
            for r in cmp_rows:
                cmp_values["prod-%s" % r["product_id"]] = cmp_values.get("prod-%s" % r["product_id"], 0.0) + r["amount"]
                key = "cat-%s" % (r["category_id"] or 0)
                cmp_values[key] = cmp_values.get(key, 0.0) + r["amount"]
            self._add_comparison(columns, lines, totals, "amount", cmp_values, sum(r["amount"] for r in cmp_rows),
                                 self._cmp_label(opts))
        return columns, lines, totals

    def _collection_rows(self, opts, start, stop):
        return self._query(opts, start, stop, """
            SELECT pm.id AS method_id,
                   CASE WHEN pm.is_cash_count THEN 'cash'
                        WHEN pm.journal_id IS NULL THEN 'other' ELSE 'bank' END AS kind,
                   COUNT(pp.id) AS payments,
                   COALESCE(SUM(pp.amount), 0) AS amount
              FROM pos_payment pp
              JOIN o ON o.id = pp.pos_order_id AND pp.laundry_collected_order_id IS NULL
              JOIN pos_payment_method pm ON pm.id = pp.payment_method_id
             GROUP BY pm.id, kind
        """)

    def _outside_collection_rows(self, start, stop, by_day=False):
        """Customer money received outside the POS, whatever screen recorded it.

        Any posted receivable line credited by a cash/bank journal entry = money a customer paid
        (accounting payments, bank statement lines reconciled directly with invoices, custom menus...).
        Entries generated by the POS session closing are excluded: those amounts are POS payments,
        already counted from the orders.
        """
        group = "l.date, j.type" if by_day else "j.id, j.type"
        select = "l.date AS day, j.type AS kind" if by_day else "j.id AS journal_id, j.type AS kind"
        self.env.cr.execute(f"""
            SELECT {select},
                   COUNT(DISTINCT l.move_id) AS payments,
                   COALESCE(SUM(l.credit - l.debit), 0) AS amount
              FROM account_move_line l
              JOIN account_journal j ON j.id = l.journal_id
              JOIN account_account acc ON acc.id = l.account_id
             WHERE acc.account_type = 'asset_receivable'
               AND l.parent_state = 'posted'
               AND j.type IN ('cash', 'bank')
               AND l.company_id = ANY(%(companies)s)
               AND l.date >= %(date_from)s AND l.date <= %(date_to)s
               AND NOT EXISTS (SELECT 1 FROM account_payment ap
                                WHERE ap.move_id = l.move_id AND ap.pos_session_id IS NOT NULL)
               AND NOT EXISTS (SELECT 1 FROM account_bank_statement_line sl
                                WHERE sl.move_id = l.move_id AND sl.pos_session_id IS NOT NULL)
             GROUP BY {group}
        """, {"companies": self.env.companies.ids, "date_from": start, "date_to": stop})
        return self.env.cr.dictfetchall()

    def _outside_included(self, opts):
        """Payments outside the POS belong to no branch / cashier: include them only for the whole business."""
        all_configs = self._dash()._configs(False)
        return set(opts["config_ids"]) == set(all_configs.ids) and not opts["cashiers"]

    def _report_collection(self, opts):
        kinds = opts["payment_kinds"] or ["cash", "bank", "other"]
        rows = [r for r in self._collection_rows(opts, opts["start"], opts["stop"]) if r["kind"] in kinds]
        outside = []
        if self._outside_included(opts):
            outside = [r for r in self._outside_collection_rows(opts["start"], opts["stop"]) if r["kind"] in kinds]
        columns = [
            {"key": "payments", "label": _("Payments"), "type": "int"},
            {"key": "amount", "label": _("Amount"), "type": "money"},
            {"key": "share", "label": _("Share %"), "type": "pct"},
        ]
        labels = {"cash": _("Cash"), "bank": _("Bank")}
        methods = {m.id: m.name for m in self.env["pos.payment.method"].browse({r["method_id"] for r in rows})}
        journals = {j.id: j.name for j in self.env["account.journal"].sudo().browse({r["journal_id"] for r in outside})}
        # collected money only: cash + bank (POS and outside); pay-later is a sale, not a collection
        collected = sum(r["amount"] for r in rows if r["kind"] != "other") + sum(r["amount"] for r in outside)
        pay_domain = [("pos_order_id." + d[0], d[1], d[2]) if isinstance(d, tuple) and d[0] != "session_id.config_id"
                      else d for d in self._order_action(opts, "")["domain"]]

        def share(amount):
            return amount / collected * 100 if collected else 0.0

        lines = []
        for kind in ("cash", "bank"):
            pos_items = sorted((r for r in rows if r["kind"] == kind), key=lambda r: r["amount"], reverse=True)
            out_items = sorted((r for r in outside if r["kind"] == kind), key=lambda r: r["amount"], reverse=True)
            if not pos_items and not out_items:
                continue
            children = [{
                "id": "pm-%s" % r["method_id"], "level": 1,
                "label": methods.get(r["method_id"], ""), "sublabel": _("POS"),
                "values": {"payments": r["payments"], "amount": r["amount"], "share": share(r["amount"])},
                "children": [],
                "action": {"res_model": "pos.payment", "name": methods.get(r["method_id"], ""),
                           "domain": pay_domain + [("payment_method_id", "=", r["method_id"])]},
            } for r in pos_items] + [{
                "id": "jr-%s" % r["journal_id"], "level": 1,
                "label": journals.get(r["journal_id"], ""), "sublabel": _("Customer payments"),
                "values": {"payments": r["payments"], "amount": r["amount"], "share": share(r["amount"])},
                "children": [],
                "action": {"res_model": "account.move.line", "name": journals.get(r["journal_id"], ""),
                           "domain": [("journal_id", "=", r["journal_id"]), ("account_type", "=", "asset_receivable"),
                                      ("parent_state", "=", "posted"),
                                      ("date", ">=", fields.Date.to_string(opts["start"])),
                                      ("date", "<=", fields.Date.to_string(opts["stop"]))]},
            } for r in out_items]
            amount = sum(c["values"]["amount"] for c in children)
            lines.append({
                "id": "kind-%s" % kind, "level": 0, "label": labels[kind],
                "values": {"payments": sum(c["values"]["payments"] for c in children), "amount": amount,
                           "share": share(amount)},
                "children": children, "action": False,
            })
        totals = {"payments": sum(l["values"]["payments"] for l in lines), "amount": collected,
                  "share": 100.0 if collected else 0.0}
        later = [r for r in rows if r["kind"] == "other"]
        if later:
            # shown for information, NOT part of the collected total
            lines.append({
                "id": "kind-other", "level": 0, "label": _("Sold on customer account"),
                "sublabel": _("not collected yet"),
                "values": {"payments": sum(r["payments"] for r in later), "amount": sum(r["amount"] for r in later),
                           "share": None},
                "children": [{
                    "id": "pm-%s" % r["method_id"], "level": 1, "label": methods.get(r["method_id"], ""),
                    "values": {"payments": r["payments"], "amount": r["amount"], "share": None}, "children": [],
                    "action": {"res_model": "pos.payment", "name": methods.get(r["method_id"], ""),
                               "domain": pay_domain + [("payment_method_id", "=", r["method_id"])]},
                } for r in later],
                "action": False, "class": "text-muted",
            })
        if opts["comparison"] != "none":
            cmp_rows = [r for r in self._collection_rows(opts, opts["cmp_start"], opts["cmp_stop"]) if r["kind"] in kinds]
            cmp_out = ([r for r in self._outside_collection_rows(opts["cmp_start"], opts["cmp_stop"]) if r["kind"] in kinds]
                       if self._outside_included(opts) else [])
            cmp_values = {}
            for r in cmp_rows:
                cmp_values["pm-%s" % r["method_id"]] = r["amount"]
                cmp_values["kind-%s" % r["kind"]] = cmp_values.get("kind-%s" % r["kind"], 0.0) + r["amount"]
            for r in cmp_out:
                cmp_values["jr-%s" % r["journal_id"]] = r["amount"]
                cmp_values["kind-%s" % r["kind"]] = cmp_values.get("kind-%s" % r["kind"], 0.0) + r["amount"]
            cmp_total = sum(r["amount"] for r in cmp_rows if r["kind"] != "other") + sum(r["amount"] for r in cmp_out)
            self._add_comparison(columns, lines, totals, "amount", cmp_values, cmp_total, self._cmp_label(opts))
        return columns, lines, totals

    # ------------------------------------------------------------------ receivables
    def _receivable_rows(self):
        today = self._dash()._today()
        self.env.flush_all()
        self.env.cr.execute("""
            SELECT l.partner_id,
                   COALESCE(SUM(l.amount_residual), 0) AS total,
                   COALESCE(SUM(l.amount_residual) FILTER (
                       WHERE l.amount_residual > 0 AND COALESCE(l.date_maturity, l.date) >= %(today)s), 0) AS not_due,
                   COALESCE(SUM(l.amount_residual) FILTER (
                       WHERE l.amount_residual > 0 AND %(today)s - COALESCE(l.date_maturity, l.date) BETWEEN 1 AND 30), 0) AS d30,
                   COALESCE(SUM(l.amount_residual) FILTER (
                       WHERE l.amount_residual > 0 AND %(today)s - COALESCE(l.date_maturity, l.date) BETWEEN 31 AND 60), 0) AS d60,
                   COALESCE(SUM(l.amount_residual) FILTER (
                       WHERE l.amount_residual > 0 AND %(today)s - COALESCE(l.date_maturity, l.date) BETWEEN 61 AND 90), 0) AS d90,
                   COALESCE(SUM(l.amount_residual) FILTER (
                       WHERE l.amount_residual > 0 AND %(today)s - COALESCE(l.date_maturity, l.date) > 90), 0) AS older,
                   COALESCE(SUM(l.amount_residual) FILTER (WHERE l.amount_residual < 0), 0) AS credits,
                   MIN(COALESCE(l.date_maturity, l.date)) FILTER (WHERE l.amount_residual > 0) AS oldest_due
              FROM account_move_line l
              JOIN account_account acc ON acc.id = l.account_id
             WHERE acc.account_type = 'asset_receivable'
               AND l.parent_state = 'posted'
               AND NOT l.reconciled
               AND l.amount_residual <> 0
               AND l.company_id = ANY(%(companies)s)
               -- POS intermediary receivable: holds paid / on-credit amounts without customer until the
               -- session is closed (then the real customer debt moves to the customer's receivable)
               AND NOT (l.partner_id IS NULL AND l.account_id = ANY(%(pos_accounts)s))
             GROUP BY l.partner_id
            HAVING ABS(SUM(l.amount_residual)) >= 0.005
             ORDER BY total DESC
        """, {"today": today, "companies": self.env.companies.ids, "pos_accounts": self._pos_receivable_accounts()})
        return self.env.cr.dictfetchall(), today

    def _pos_receivable_accounts(self):
        """Intermediary receivable accounts of the POS (company default + payment methods, archived included)."""
        accounts = self.env.companies.mapped("account_default_pos_receivable_account_id")
        accounts |= self.env["pos.payment.method"].sudo().with_context(active_test=False).search(
            [("company_id", "in", self.env.companies.ids)]).mapped("receivable_account_id")
        return accounts.ids or [0]

    def _report_receivables(self, opts):
        rows, today = self._receivable_rows()
        columns = [
            {"key": "phone", "label": _("Phone"), "type": "text"},
            {"key": "not_due", "label": _("Not due"), "type": "money"},
            {"key": "d30", "label": _("1-30 days"), "type": "money"},
            {"key": "d60", "label": _("31-60 days"), "type": "money"},
            {"key": "d90", "label": _("61-90 days"), "type": "money"},
            {"key": "older", "label": _("Older"), "type": "money"},
            {"key": "credits", "label": _("Unallocated payments"), "type": "money"},
            {"key": "total", "label": _("Balance"), "type": "money"},
            {"key": "oldest_due", "label": _("Oldest due"), "type": "text"},
        ]
        keys = ("not_due", "d30", "d60", "d90", "older", "credits", "total")
        partners = {p.id: p for p in self.env["res.partner"].browse([r["partner_id"] for r in rows if r["partner_id"]])}
        lines, totals = [], dict.fromkeys(keys, 0.0)
        for r in rows:
            partner = partners.get(r["partner_id"])
            # blank zero buckets (like the accounting aged receivable) so the amounts stand out
            values = {k: (r[k] if k == "total" or abs(r[k]) >= 0.005 else None) for k in keys}
            values["phone"] = (partner.mobile or partner.phone or "") if partner else ""
            values["oldest_due"] = format_date(self.env, r["oldest_due"]) if r["oldest_due"] else ""
            domain = [("account_type", "=", "asset_receivable"), ("parent_state", "=", "posted"),
                      ("reconciled", "=", False), ("partner_id", "=", r["partner_id"] or False)]
            lines.append({
                "id": "partner-%s" % (r["partner_id"] or 0), "level": 0,
                "label": partner.display_name if partner else _("Without customer"),
                "values": values, "children": [],
                "class": "text-danger" if (r["d60"] + r["d90"] + r["older"]) > 0.005 else "",
                "action": {"res_model": "account.move.line", "name": partner.display_name if partner else _("Without customer"),
                           "domain": domain},
            })
            for k in keys:
                totals[k] += r[k]
        return columns, lines, totals

    def _report_sessions(self, opts):
        sessions = self._dash()._sessions(opts["start"], opts["stop"], opts["configs"])["list"]
        tz = self._dash()._tz().zone
        columns = [
            {"key": "config", "label": _("Point of Sale"), "type": "text"},
            {"key": "user", "label": _("Opened by"), "type": "text"},
            {"key": "start_at", "label": _("Opened"), "type": "text"},
            {"key": "stop_at", "label": _("Closed"), "type": "text"},
            {"key": "state", "label": _("Status"), "type": "text"},
            {"key": "expected", "label": _("Expected cash"), "type": "money"},
            {"key": "counted", "label": _("Counted cash"), "type": "money"},
            {"key": "difference", "label": _("Difference"), "type": "money"},
        ]

        def dt(value):
            # numeric 24h format: no Arabic letters next to digits (clear, and safe for the PDF engine)
            return format_datetime(self.env, fields.Datetime.to_datetime(value), tz=tz, dt_format="yyyy-MM-dd HH:mm") if value else ""

        lines, totals = [], {"expected": 0.0, "counted": 0.0, "difference": 0.0}
        for s in sessions:
            closed = s["state"] == "closed" and s["cash_control"]
            values = {
                "config": s["config"], "user": s["user"], "start_at": dt(s["start_at"]), "stop_at": dt(s["stop_at"]),
                "state": s["state_label"],
                "expected": s["expected"] if s["cash_control"] else None,
                "counted": s["counted"] if closed else None,
                "difference": s["difference"] if closed else None,
            }
            if closed:
                for k in ("expected", "counted", "difference"):
                    totals[k] += values[k]
            lines.append({"id": "session-%s" % s["id"], "level": 0, "label": s["name"], "values": values,
                          "children": [], "action": {"res_model": "pos.session", "res_id": s["id"], "name": s["name"]},
                          "class": "text-danger" if closed and s["difference"] < -0.005 else ""})
        return columns, lines, totals

    def _report_cashiers(self, opts):
        dash = self._dash()
        rows = self._cashier_rows(opts, opts["start"], opts["stop"])
        columns = [
            {"key": "orders", "label": _("Orders"), "type": "int"},
            {"key": "sales", "label": _("Sales"), "type": "money"},
            {"key": "avg", "label": _("Average order"), "type": "money"},
            {"key": "discounts", "label": _("Discounts"), "type": "money"},
            {"key": "refunds_count", "label": _("Refunds"), "type": "int"},
            {"key": "refunds_amount", "label": _("Refunded amount"), "type": "money"},
        ]
        lines, totals = [], {"orders": 0, "sales": 0.0, "discounts": 0.0, "refunds_count": 0, "refunds_amount": 0.0}
        for c in rows:
            extra = ([("employee_id", "=", c["id"])] if c["kind"] == "employee"
                     else [("user_id", "=", c["id"])] + ([("employee_id", "=", False)] if dash._has_employee() else []))
            values = {k: c[k] for k in totals}
            values["avg"] = c["sales"] / c["orders"] if c["orders"] else 0.0
            lines.append({"id": c["key"], "level": 0, "label": c["name"], "values": values, "children": [],
                          "action": self._order_action(opts, c["name"], extra)})
            for k in totals:
                totals[k] += c[k]
        totals["avg"] = totals["sales"] / totals["orders"] if totals["orders"] else 0.0
        if opts["comparison"] != "none":
            cmp_rows = self._cashier_rows(opts, opts["cmp_start"], opts["cmp_stop"])
            self._add_comparison(columns, lines, totals, "sales", {c["key"]: c["sales"] for c in cmp_rows},
                                 sum(c["sales"] for c in cmp_rows), self._cmp_label(opts))
        return columns, lines, totals

    def _cashier_rows(self, opts, start, stop):
        """Dashboard cashier aggregation, with the report's cashier filter passed explicitly."""
        return self._dash()._cashiers(start, stop, opts["configs"], params=self._params(opts, start, stop))

    def _customer_rows(self, opts, start, stop):
        return self._query(opts, start, stop, """
            SELECT partner_id,
                   COUNT(*) FILTER (WHERE amount_total >= 0 AND NOT is_collection) AS orders,
                   COALESCE(SUM(amount_total), 0) AS amount,
                   MIN(date_order) AS first_order, MAX(date_order) AS last_order
              FROM o
             WHERE NOT is_collection
             GROUP BY partner_id
             ORDER BY amount DESC
        """)

    def _report_customers(self, opts):
        rows = self._customer_rows(opts, opts["start"], opts["stop"])
        named = [r for r in rows if r["partner_id"]][:CUSTOMERS_LIMIT]
        walk_in = next((r for r in rows if not r["partner_id"]), None)
        partners = {p.id: p for p in self.env["res.partner"].browse([r["partner_id"] for r in named])}
        columns = [
            {"key": "phone", "label": _("Phone"), "type": "text"},
            {"key": "orders", "label": _("Orders"), "type": "int"},
            {"key": "amount", "label": _("Spent"), "type": "money"},
            {"key": "avg", "label": _("Average order"), "type": "money"},
            {"key": "last_order", "label": _("Last visit"), "type": "text"},
        ]

        def values(r, phone=""):
            return {"phone": phone, "orders": r["orders"], "amount": r["amount"],
                    "avg": r["amount"] / r["orders"] if r["orders"] else 0.0,
                    "last_order": format_date(self.env, self._local_date(r["last_order"])) if r["last_order"] else ""}

        lines = []
        for r in named:
            p = partners[r["partner_id"]]
            lines.append({"id": "partner-%s" % p.id, "level": 0, "label": p.display_name,
                          "values": values(r, p.mobile or p.phone or ""), "children": [],
                          "action": self._order_action(opts, p.display_name, [("partner_id", "=", p.id)])})
        if walk_in:
            lines.append({"id": "partner-0", "level": 0, "label": _("Walk-in customers (no name)"),
                          "values": values(walk_in), "children": [], "class": "text-muted",
                          "action": self._order_action(opts, _("Walk-in customers"), [("partner_id", "=", False)])})
        totals = {"orders": sum(r["orders"] for r in rows), "amount": sum(r["amount"] for r in rows)}
        totals["avg"] = totals["amount"] / totals["orders"] if totals["orders"] else 0.0
        if opts["comparison"] != "none":
            cmp_rows = self._customer_rows(opts, opts["cmp_start"], opts["cmp_stop"])
            self._add_comparison(columns, lines, totals, "amount",
                                 {"partner-%s" % (r["partner_id"] or 0): r["amount"] for r in cmp_rows},
                                 sum(r["amount"] for r in cmp_rows), self._cmp_label(opts))
        return columns, lines, totals

    # ------------------------------------------------------------------ customer debts (statement)
    # London tracks what a customer owes on the POS order itself (laundry_credit_remaining): it already
    # counts the collections taken at the POS before the session is closed and reconciled, and it is the
    # balance printed on the receipt. The statement uses the same figures.
    def _status_labels(self):
        return {
            "paid": _("Paid"),
            "partial": _("Partially paid"),
            "not_paid": _("Not paid"),
        }

    @staticmethod
    def _order_status(collection_status):
        return {"credit_unpaid": "not_paid", "credit_partial": "partial"}.get(collection_status, "paid")

    def _order_rows(self, start, stop, partner_ids=None, with_walk_in=False):
        """Sales orders dated in the period (local date), with what is still owed on each (as of today).

        Collections (and their reversals) are payments, not sales: left out.
        """
        self.env.flush_all()
        self.env.cr.execute("""
            SELECT o.id, COALESCE(m.name, o.pos_reference, o.name) AS name,
                   (o.date_order AT TIME ZONE 'UTC' AT TIME ZONE %(tz)s)::date AS invoice_date,
                   o.laundry_collection_status AS collection_status,
                   COALESCE(p.commercial_partner_id, p.id) AS partner_id, o.company_id,
                   o.amount_total - o.amount_tax AS untaxed, o.amount_tax AS tax,
                   o.amount_total AS amount, COALESCE(o.laundry_credit_remaining, 0) AS remaining
              FROM pos_order o
              LEFT JOIN res_partner p ON p.id = o.partner_id
              LEFT JOIN account_move m ON m.id = o.account_move AND m.state = 'posted'
             WHERE o.state NOT IN ('draft', 'cancel')
               AND NOT COALESCE(o.laundry_is_collection, FALSE)
               AND o.laundry_reversed_order_id IS NULL
               AND o.company_id = ANY(%(companies)s)
               AND (o.date_order AT TIME ZONE 'UTC' AT TIME ZONE %(tz)s)::date BETWEEN %(start)s AND %(stop)s
               AND (%(with_walk_in)s OR o.partner_id IS NOT NULL)
               AND (%(no_partner_filter)s OR COALESCE(p.commercial_partner_id, p.id) = ANY(%(partners)s))
             ORDER BY o.date_order, o.id
        """, {"tz": self._dash()._tz().zone, "companies": self.env.companies.ids, "start": start, "stop": stop,
              "with_walk_in": with_walk_in, "no_partner_filter": partner_ids is None, "partners": partner_ids or [0]})
        rows = self.env.cr.dictfetchall()
        for r in rows:
            r["paid"] = r["amount"] - r["remaining"]
            r["status"] = self._order_status(r["collection_status"])
        return rows

    def _previous_balances(self, start, partner_ids=None):
        """Per customer: still owed today on On Credit orders dated before the period."""
        self.env.flush_all()
        self.env.cr.execute("""
            SELECT COALESCE(p.commercial_partner_id, p.id) AS partner_id, SUM(o.laundry_credit_remaining) AS previous
              FROM pos_order o
              JOIN res_partner p ON p.id = o.partner_id
             WHERE o.laundry_collection_status IN ('credit_unpaid', 'credit_partial')
               AND o.company_id = ANY(%(companies)s)
               AND (o.date_order AT TIME ZONE 'UTC' AT TIME ZONE %(tz)s)::date < %(start)s
               AND (%(no_partner_filter)s OR COALESCE(p.commercial_partner_id, p.id) = ANY(%(partners)s))
             GROUP BY 1
        """, {"tz": self._dash()._tz().zone, "companies": self.env.companies.ids, "start": start,
              "no_partner_filter": partner_ids is None, "partners": partner_ids or [0]})
        return {r["partner_id"]: r["previous"] or 0.0 for r in self.env.cr.dictfetchall()}

    def _statement_summaries(self, start, stop, partner_ids=None):
        """{partner_id: {invoices, previous, untaxed, tax, invoiced, paid, remaining, total_due}}"""
        result = {}

        def summary(pid):
            return result.setdefault(pid, {"invoices": [], "previous": 0.0, "untaxed": 0.0, "tax": 0.0,
                                           "invoiced": 0.0, "paid": 0.0, "remaining": 0.0})

        for order in self._order_rows(start, stop, partner_ids):
            s = summary(order["partner_id"])
            s["invoices"].append(order)
            s["untaxed"] += order["untaxed"]
            s["tax"] += order["tax"]
            s["invoiced"] += order["amount"]
            s["paid"] += order["paid"]
            s["remaining"] += order["remaining"]
        for pid, previous in self._previous_balances(start, partner_ids).items():
            if abs(previous) >= 0.005:
                summary(pid)["previous"] = previous
        for s in result.values():
            s["total_due"] = s["previous"] + s["remaining"]
        return result

    # public link to one customer's statement PDF (sent by WhatsApp, opened without login)
    def _statement_token(self, partner_id, start, stop, company_ids):
        message = (int(partner_id), fields.Date.to_string(start), fields.Date.to_string(stop),
                   ",".join(str(c) for c in sorted(company_ids)))
        return hmac(self.env(su=True), STATEMENT_SCOPE, message)

    def _statement_url(self, partner_id, start, stop):
        company_ids = self.env.companies.ids
        token = self._statement_token(partner_id, start, stop, company_ids)
        return "%s/london_laundry_implementation/statement/%s?date_from=%s&date_to=%s&companies=%s&token=%s" % (
            self.get_base_url(), partner_id, fields.Date.to_string(start), fields.Date.to_string(stop),
            ",".join(str(c) for c in sorted(company_ids)), token)

    @api.model
    def _check_statement_token(self, partner_id, start, stop, company_ids, token):
        expected = self._statement_token(partner_id, start, stop, company_ids)
        return bool(token) and consteq(expected, token)

    def _whatsapp_phone(self, partner):
        """Partner number as international digits without '+' (wa.me format), or False."""
        raw = partner.mobile or partner.phone
        if not raw:
            return False
        try:
            import phonenumbers
        except ImportError:
            return False
        region = partner.country_id.code or self.env.company.country_id.code or "AE"
        try:
            number = phonenumbers.parse(raw, region)
        except phonenumbers.NumberParseException:
            return False
        if not phonenumbers.is_valid_number(number):
            return False
        return phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164).lstrip("+")

    def _statement_whatsapp_url(self, partner, start, stop, s, message, currency):
        phone = self._whatsapp_phone(partner)
        if not phone or not message:
            return False

        def money(amount):
            return "%s %s" % (format_amount_plain(amount, currency), currency.name)

        values = {
            "partner_name": partner.name or "",
            "company": self.env.company.name or "",
            "date_from": fields.Date.to_string(start),
            "date_to": fields.Date.to_string(stop),
            "previous_balance": money(s["previous"]),
            "invoiced": money(s["invoiced"]),
            "paid": money(s["paid"]),
            "remaining": money(s["remaining"]),
            "total_due": money(s["total_due"]),
            "invoice_count": len(s["invoices"]),
            "open_count": sum(1 for i in s["invoices"] if i["status"] in ("partial", "not_paid")),
            "statement_link": self._statement_url(partner.id, start, stop),
        }
        text = message
        for key, value in values.items():
            text = text.replace("{{%s}}" % key, str(value))
        # safe="" so &, =, ?, # inside the message are encoded and never cut the text
        return "https://wa.me/%s?text=%s" % (phone, urllib.parse.quote(text, safe=""))

    def _statement_message(self):
        return self.env["ir.config_parameter"].sudo().get_param(STATEMENT_MESSAGE_PARAM) or DEFAULT_STATEMENT_MESSAGE

    def _report_statement(self, opts):
        self = self._for_branches(opts)
        start, stop = opts["start"], opts["stop"]
        summaries = self._statement_summaries(start, stop, self._matching_partner_ids(opts["partner_search"]))
        if opts["statuses"]:
            # only these orders: the period columns add up the orders shown,
            # 'Total due' stays the customer's real balance
            for pid in list(summaries):
                s = summaries[pid]
                s["invoices"] = [i for i in s["invoices"] if i["status"] in opts["statuses"]]
                if not s["invoices"]:
                    del summaries[pid]
                    continue
                for key, field in (("untaxed", "untaxed"), ("tax", "tax"), ("invoiced", "amount"),
                                   ("paid", "paid"), ("remaining", "remaining")):
                    s[key] = sum(i[field] for i in s["invoices"])
        if opts["min_due"]:
            summaries = {pid: s for pid, s in summaries.items() if s["total_due"] >= opts["min_due"] - 0.005}
        if opts["show"] != "all":
            summaries = {pid: s for pid, s in summaries.items() if s["total_due"] > 0.005}
        if opts["show"].startswith("top"):
            limit = int(opts["show"][3:])
            ranked = sorted(summaries, key=lambda pid: -summaries[pid]["total_due"])[:limit]
            summaries = {pid: summaries[pid] for pid in ranked}
        columns = [
            {"key": "status", "label": _("Status"), "type": "text"},
            {"key": "previous", "label": _("Previous balance"), "type": "money"},
            {"key": "untaxed", "label": _("Amount excl. VAT"), "type": "money"},
            {"key": "tax", "label": _("VAT"), "type": "money"},
            {"key": "invoiced", "label": _("Amount incl. VAT"), "type": "money"},
            {"key": "paid", "label": _("Paid"), "type": "money"},
            {"key": "remaining", "label": _("Remaining"), "type": "money"},
            {"key": "total_due", "label": _("Total due"), "type": "money"},
        ]
        keys = ("previous", "untaxed", "tax", "invoiced", "paid", "remaining", "total_due")
        partners = self.env["res.partner"].browse(list(summaries)).exists()
        message = self._statement_message()
        currency = self.env.company.currency_id
        labels = self._status_labels()
        status_class = {"paid": "text-success", "partial": "text-warning", "not_paid": "text-danger"}
        lines, totals = [], dict.fromkeys(keys, 0.0)
        for partner in partners.sorted(lambda p: (-summaries[p.id]["total_due"], p.display_name or "")):
            s = summaries[partner.id]
            values = {k: (s[k] if k == "total_due" or abs(s[k]) >= 0.005 else None) for k in keys}
            open_count = sum(1 for i in s["invoices"] if i["status"] in ("partial", "not_paid"))
            values["status"] = _("%(open)s of %(count)s open", open=open_count, count=len(s["invoices"])) if s["invoices"] else ""
            children = []
            for order in s["invoices"]:
                children.append({
                    "id": "order-%s" % order["id"], "level": 1,
                    "label": order["name"], "sublabel": format_date(self.env, order["invoice_date"]),
                    "values": {"status": labels[order["status"]], "untaxed": order["untaxed"], "tax": order["tax"],
                               "invoiced": order["amount"],
                               "paid": order["paid"] if abs(order["paid"]) >= 0.005 else None,
                               "remaining": order["remaining"] if abs(order["remaining"]) >= 0.005 else None},
                    "class": status_class[order["status"]],
                    "action": {"res_model": "pos.order", "res_id": order["id"], "name": order["name"]},
                })
            lines.append({
                "id": "partner-%s" % partner.id, "level": 0,
                "label": partner.display_name, "sublabel": partner.mobile or partner.phone or "",
                "values": values, "children": children,
                "whatsapp_url": self._statement_whatsapp_url(partner, start, stop, s, message, currency),
                "pdf_url": self._statement_url(partner.id, start, stop),
                "class": "text-danger" if s["total_due"] > 0.005 else "",
                "action": {"res_model": "res.partner", "res_id": partner.id, "name": partner.display_name},
            })
            for k in keys:
                totals[k] += s[k]
        return columns, lines, totals

    @api.model
    def get_statement_pdf_values(self, partner, start, stop):
        """Values for the one-customer statement PDF (bilingual, sent to the customer)."""
        s = self._statement_summaries(start, stop, [partner.id]).get(partner.id) or {
            "invoices": [], "previous": 0.0, "untaxed": 0.0, "tax": 0.0, "invoiced": 0.0, "paid": 0.0,
            "remaining": 0.0, "total_due": 0.0}
        # header of the branch that made most of the period's orders (not just the first allowed company)
        counts = {}
        for order in s["invoices"]:
            counts[order["company_id"]] = counts.get(order["company_id"], 0) + 1
        company = (self.env["res.company"].browse(max(counts, key=counts.get)) if counts
                   else partner.company_id or self.env.company)
        return {
            "partner": partner,
            "company": company,
            "date_from": start,
            "date_to": stop,
            "summary": s,
            "invoices": s["invoices"],
            "currency": self.env.company.currency_id,
            "printed_on": format_datetime(self.env, fields.Datetime.now(), tz=self._dash()._tz().zone,
                                          dt_format="yyyy-MM-dd HH:mm"),
        }

    def _report_monthly_receivables(self, opts):
        self = self._for_branches(opts)
        start, stop = opts["start"], opts["stop"]
        partner_ids = self._matching_partner_ids(opts["partner_search"])
        # walk-in sales count in the month totals (always paid), not when searching a customer
        rows = self._order_rows(start, stop, partner_ids, with_walk_in=partner_ids is None)
        if opts["statuses"]:
            rows = [r for r in rows if r["status"] in opts["statuses"]]
        columns = [
            {"key": "count", "label": _("Orders"), "type": "int"},
            {"key": "invoiced", "label": _("Amount incl. VAT"), "type": "money"},
            {"key": "paid", "label": _("Paid"), "type": "money"},
            {"key": "remaining", "label": _("Remaining"), "type": "money"},
            {"key": "open_count", "label": _("Open orders"), "type": "int"},
            {"key": "collected", "label": _("Collected %"), "type": "pct"},
        ]
        keys = ("count", "invoiced", "paid", "remaining", "open_count")

        def empty():
            return dict.fromkeys(keys, 0.0)

        def add(target, order):
            target["count"] += 1
            target["invoiced"] += order["amount"]
            target["paid"] += order["paid"]
            target["remaining"] += order["remaining"]
            if order["status"] in ("partial", "not_paid"):
                target["open_count"] += 1

        def finish(values):
            values = dict(values)
            values["collected"] = values["paid"] / values["invoiced"] * 100.0 if values["invoiced"] else None
            return values

        months = {}
        for order in rows:
            month = order["invoice_date"].replace(day=1)
            m = months.setdefault(month, {"values": empty(), "partners": {}})
            add(m["values"], order)
            if order["partner_id"]:
                add(m["partners"].setdefault(order["partner_id"], empty()), order)

        dash = self._dash()
        partners = {p.id: p for p in self.env["res.partner"].browse(
            list({pid for m in months.values() for pid in m["partners"]})).exists()}
        lines, totals = [], empty()
        for month in sorted(months, reverse=True):
            m = months[month]
            month_end = month + relativedelta(months=1, days=-1)
            first, last = max(month, start), min(month_end, stop)
            month_domain = [("state", "not in", ["draft", "cancel"]), ("laundry_is_collection", "=", False),
                            ("company_id", "in", self.env.companies.ids),
                            ("date_order", ">=", fields.Datetime.to_string(dash._to_utc(first))),
                            ("date_order", "<", fields.Datetime.to_string(dash._to_utc(last + timedelta(days=1))))]
            children = []
            # only customers who still owe something from that month
            owing = [(pid, v) for pid, v in m["partners"].items() if v["remaining"] > 0.005]
            for pid, v in sorted(owing, key=lambda item: -item[1]["remaining"]):
                partner = partners.get(pid)
                name = partner.display_name if partner else _("Without customer")
                children.append({
                    "id": "month-%s-partner-%s" % (month, pid), "level": 1,
                    "label": name, "sublabel": (partner.mobile or partner.phone or "") if partner else "",
                    "values": finish(v),
                    "action": {"res_model": "pos.order", "name": name,
                               "domain": month_domain + [("partner_id", "child_of", pid),
                                                         ("laundry_collection_status", "in",
                                                          ["credit_unpaid", "credit_partial"])]},
                })
            label = format_date(self.env, month, date_format="MMMM y")
            lines.append({
                "id": "month-%s" % month, "level": 0, "label": label,
                "values": finish(m["values"]), "children": children,
                "action": {"res_model": "pos.order", "name": label, "domain": month_domain},
            })
            for k in keys:
                totals[k] += m["values"][k]
        return columns, lines, finish(totals)

    # ------------------------------------------------------------------ public API
    def _filter_pairs(self, opts, report_key):
        pairs = []
        all_configs = self._dash()._configs(False)
        if opts["configs"] and set(opts["config_ids"]) != set(all_configs.ids):
            pairs.append((_("Point of Sale"), ", ".join(opts["configs"].mapped("name"))))
        if opts["cashiers"]:
            names = {c["key"]: c["name"] for c in self._cashier_choices(opts["configs"])}
            pairs.append((_("Cashier"), ", ".join(names.get(c, c) for c in opts["cashiers"])))
        if report_key == "category" and opts["category_ids"]:
            pairs.append((_("Service"), ", ".join(self.env["pos.category"].browse(opts["category_ids"]).mapped("name"))))
        if report_key == "collection" and not self._outside_included(opts):
            pairs.append((_("Note"), _("customer payments made outside the POS are not linked to a branch or cashier, "
                                       "so they are only included when all points of sale are selected")))
        if report_key == "collection" and opts["payment_kinds"]:
            labels = {"cash": _("Cash"), "bank": _("Bank"), "other": _("Customer account (pay later)")}
            pairs.append((_("Payment"), ", ".join(labels[k] for k in opts["payment_kinds"])))
        if report_key in INVOICE_REPORTS:
            if opts["company_ids"]:
                pairs.append((_("Branch"), ", ".join(self.env["res.company"].browse(opts["company_ids"]).mapped("name"))))
            if opts["partner_search"]:
                pairs.append((_("Customer"), opts["partner_search"]))
            if opts["statuses"]:
                labels = self._status_labels()
                pairs.append((_("Orders"), ", ".join(labels[k] for k in opts["statuses"])))
            if report_key == "statement" and opts["show"] != "all":
                pairs.append((_("Show"), self._show_labels()[opts["show"]]))
            if report_key == "statement" and opts["min_due"]:
                pairs.append((_("Minimum due"), "{:,.2f}".format(opts["min_due"])))
        return pairs

    def _notes(self):
        return {
            "statement": _("Customer orders dated in the period. Paid and remaining amounts are as of today "
                           "(collections taken at the POS included). Previous balance: what is still owed "
                           "from before the period."),
            "monthly_receivables": _("Customer orders by month. Paid and remaining amounts are as of today; "
                                     "open a month to see the customers who still owe from it."),
        }

    @api.model
    def get_report(self, report_key, options=None):
        self._dash()._check_access()
        if report_key not in REPORTS:
            raise UserError(_("Unknown report."))
        opts = self._resolve_options(options)
        columns, lines, totals = getattr(self, "_report_%s" % report_key)(opts)
        currency = self.env.company.currency_id
        return {
            "key": report_key,
            "title": self._titles()[report_key],
            "company": self.env.company.name,
            "currency_id": currency.id,
            "period_label": (self._period_label(opts["start"], opts["stop"]) if report_key != "receivables"
                             else _("As of %s", format_date(self.env, self._dash()._today()))),
            "comparison_label": (self._period_label(opts["cmp_start"], opts["cmp_stop"])
                                 if opts["comparison"] != "none" and report_key not in ("receivables",) + INVOICE_REPORTS
                                 else False),
            "note": self._notes().get(report_key, ""),
            "filter_pairs": self._filter_pairs(opts, report_key),
            "filters_summary": ["%s: %s" % pair for pair in self._filter_pairs(opts, report_key)],
            "options": {
                "preset": opts["preset"], "date_from": opts["date_from"], "date_to": opts["date_to"],
                "comparison": opts["comparison"], "config_ids": opts["config_ids"], "cashiers": opts["cashiers"],
                "category_ids": opts["category_ids"], "payment_kinds": opts["payment_kinds"],
                "partner_search": opts["partner_search"], "statuses": opts["statuses"],
                "company_ids": opts["company_ids"], "show": opts["show"], "min_due": opts["min_due"] or "",
                "month": opts["month"], "year": opts["year"],
            },
            "columns": columns,
            "lines": lines,
            "totals": totals,
            "generated": format_datetime(self.env, fields.Datetime.now(), tz=self._dash()._tz().zone, dt_format="yyyy-MM-dd HH:mm"),
        }

    # ------------------------------------------------------------------ Excel
    @api.model
    def get_xlsx(self, report_key, options=None):
        import xlsxwriter

        data = self.get_report(report_key, options)
        currency = self.env["res.currency"].browse(data["currency_id"])
        rtl = (self.env["res.lang"]._get_data(code=self.env.lang or "en_US").direction == "rtl")
        output = io.BytesIO()
        book = xlsxwriter.Workbook(output, {"in_memory": True})
        sheet = book.add_worksheet(data["title"][:31])
        if rtl:
            sheet.right_to_left()
        money_fmt = '#,##0.%s' % ("0" * currency.decimal_places) if currency.decimal_places else "#,##0"
        f = {
            "title": book.add_format({"bold": True, "font_size": 14}),
            "muted": book.add_format({"font_color": "#666666"}),
            "head": book.add_format({"bold": True, "bg_color": "#E9ECEF", "border": 1, "text_wrap": True, "valign": "vcenter"}),
            "head_num": book.add_format({"bold": True, "bg_color": "#E9ECEF", "border": 1, "align": "right", "text_wrap": True, "valign": "vcenter"}),
        }
        for level in (0, 1):
            for kind in ("text", "money", "int", "pct"):
                props = {"bold": level == 0, "indent": level * 2 if kind == "text" else 0}
                if kind == "money":
                    props["num_format"] = money_fmt
                elif kind == "int":
                    props["num_format"] = "#,##0"
                elif kind == "pct":
                    props["num_format"] = '0.0"%"'
                f["%s_%s" % (kind, level)] = book.add_format(props)
        for kind in ("text", "money", "int", "pct"):
            props = {"bold": True, "top": 2, "bg_color": "#F8F9FA"}
            if kind == "money":
                props["num_format"] = money_fmt
            elif kind == "int":
                props["num_format"] = "#,##0"
            elif kind == "pct":
                props["num_format"] = '0.0"%"'
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
            fmt = f["%s_%s" % (kind if kind in ("money", "int", "pct") else "text", min(level, 1))]
            if value is None or value == "":
                sheet.write_blank(r, c, None, fmt)
            elif kind in ("money", "int", "pct"):
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
                    sheet.set_row(row, None, None, {"level": level})  # Excel outline: collapsible groups
                row += 1
                write_lines(line.get("children") or [])

        write_lines(data["lines"])
        sheet.write(row, 0, _("Total"), f["total_text"])
        for i, col in enumerate(columns, start=1):
            value = data["totals"].get(col["key"])
            kind = col["type"] if col["type"] in ("money", "int", "pct") else "text"
            if value is None:
                sheet.write_blank(row, i, None, f["total_%s" % kind])
            elif kind == "text":
                sheet.write_string(row, i, str(value), f["total_text"])
            else:
                sheet.write_number(row, i, float(value), f["total_%s" % kind])
        sheet.set_column(0, 0, 34)
        sheet.set_column(1, len(columns), 16)
        sheet.freeze_panes(header_row + 1, 1)
        sheet.outline_settings(True, False, True, False)
        book.close()
        filename = "%s - %s.xlsx" % (data["title"], data["period_label"].replace("/", "-"))
        return output.getvalue(), filename


class LaundryReportPdf(models.AbstractModel):
    _name = "report.london_laundry_implementation.report_laundry_document"
    _description = "Laundry Report PDF"

    @staticmethod
    def _clean_bidi(value):
        """Drop invisible direction marks (babel puts them in Arabic dates); the old PDF engine draws them badly."""
        if isinstance(value, str):
            return value.translate(BIDI_MARKS)
        if isinstance(value, dict):
            return {k: LaundryReportPdf._clean_bidi(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return type(value)(LaundryReportPdf._clean_bidi(v) for v in value)
        return value

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        report = self._clean_bidi(
            self.env["london.laundry.report"].get_report(data.get("report_key"), data.get("report_options")))
        return {
            "doc_ids": [],
            "doc_model": "london.laundry.report",
            "docs": [],
            "report": report,
            "currency": self.env["res.currency"].browse(report["currency_id"]),
            "company": self.env.company,
            "rtl": self.env["res.lang"]._get_data(code=self.env.lang or "en_US").direction == "rtl",
            # label / value in separate cells: the PDF engine mis-measures lines mixing Arabic and digits
            "header_rows": [(_("Period"), self._clean_bidi(report["period_label"]))]
                           + ([(_("Compared with"), report["comparison_label"])] if report["comparison_label"] else [])
                           + [tuple(pair) for pair in report["filter_pairs"]],
            "footer_rows": [(_("Currency"), self.env["res.currency"].browse(report["currency_id"]).name),
                            (_("Printed on"), report["generated"])],
        }

class CustomerStatementPdf(models.AbstractModel):
    _name = "report.london_laundry_implementation.report_customer_statement"
    _description = "Customer Statement PDF"

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        report = self.env["london.laundry.report"]
        stop = fields.Date.to_date(data.get("date_to")) or report._dash()._today()
        start = fields.Date.to_date(data.get("date_from")) or stop.replace(day=1)
        partners = self.env["res.partner"].browse(docids).exists()
        return {
            "doc_ids": partners.ids,
            "doc_model": "res.partner",
            "docs": partners,
            "statements": {p.id: report.get_statement_pdf_values(p, start, stop) for p in partners},
        }
