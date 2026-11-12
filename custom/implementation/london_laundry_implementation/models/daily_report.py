import logging
from collections import defaultdict
from datetime import datetime, time, timedelta

import pytz

from odoo import api, fields, models
from odoo.tools.misc import format_date, formatLang

from .dashboard import VALID_STATES

_logger = logging.getLogger(__name__)

REPORT_LANG = "ar_001"
DEFAULT_TZ = "Asia/Dubai"
# the previous day is sent once the local time passes this hour/minute
SEND_AFTER = time(0, 30)
LIST_LIMIT = 50


class LaundryDailyReport(models.AbstractModel):
    _name = "london.laundry.daily.report"
    _description = "Laundry Daily E-mail Report"

    # ------------------------------------------------------------------ helpers
    def _config_tz(self, config):
        name = config.company_id.partner_id.tz or DEFAULT_TZ
        try:
            return pytz.timezone(name)
        except pytz.UnknownTimeZoneError:
            return pytz.timezone(DEFAULT_TZ)

    def _report_day(self, config):
        """Yesterday in the local time of the point of sale."""
        return datetime.now(self._config_tz(config)).date() - timedelta(days=1)

    def _dashboard(self, config):
        return (self.env["london.laundry.dashboard"].sudo()
                .with_company(config.company_id)
                .with_context(ld_force_tz=self._config_tz(config).zone, lang=REPORT_LANG))

    @staticmethod
    def _change(current, previous):
        if not previous:
            return None
        return (current - previous) / abs(previous) * 100.0

    def _payment_methods(self, dash, day, config):
        rows = dash._query("""
            SELECT pp.payment_method_id AS method_id,
                   COUNT(DISTINCT pp.pos_order_id) AS orders,
                   COALESCE(SUM(pp.amount), 0) AS amount
              FROM pos_payment pp JOIN o ON o.id = pp.pos_order_id AND pp.laundry_collected_order_id IS NULL
             GROUP BY 1 ORDER BY amount DESC
        """, dash._params(day, day, config))
        methods = {m.id: m for m in dash.env["pos.payment.method"].browse([r["method_id"] for r in rows])}
        result = []
        for r in rows:
            method = methods[r["method_id"]]
            kind = "cash" if method.is_cash_count else ("credit" if not method.journal_id else "bank")
            result.append({"name": method.name, "kind": kind, "orders": r["orders"], "amount": r["amount"]})
        return result

    def _collections(self, dash, day, config, local_time):
        """تحصيلات ديون On Credit بهاليوم (قسم لحاله): الطلبات اللي اندفعت وطريقة الدفع."""
        rows = dash._query("SELECT id FROM o WHERE is_collection ORDER BY date_order, id",
                           dash._params(day, day, config))
        orders = dash.env["pos.order"].browse([r["id"] for r in rows])
        has_employee = dash._has_employee()
        lines, by_method = [], {}
        for order in orders:
            credit = order.payment_ids.filtered("laundry_collected_order_id")
            paid = order.payment_ids.filtered(lambda p: p.payment_method_id.type != "pay_later")
            methods = {}
            for payment in paid:
                methods[payment.payment_method_id.name] = methods.get(payment.payment_method_id.name, 0.0) + payment.amount
            for name, amount in methods.items():
                by_method[name] = by_method.get(name, 0.0) + amount
            cashier = order.employee_id if has_employee and order.employee_id else order.user_id
            lines.append({
                "time": local_time(order.date_order),
                "cashier": cashier.name or "",
                "customer": order.partner_id.display_name or "",
                "orders": ", ".join(credit.mapped("laundry_collected_order_id.name")) + (
                    " (إلغاء %s)" % order.laundry_reversed_order_id.name if order.laundry_reversed_order_id else ""),
                "methods": " + ".join(name for name, amount in methods.items() if amount),
                "amount": -sum(credit.mapped("amount")),
            })
        return {
            "list": lines,
            "total": sum(line["amount"] for line in lines),
            "by_method": sorted(((name, amount) for name, amount in by_method.items()
                                 if not config.currency_id.is_zero(amount)), key=lambda item: -item[1]),
        }

    def _deliveries(self, config, today):
        """Orders expected today or earlier that are not delivered yet (delivery is ticked on the invoice)."""
        self.env.flush_all()
        self.env.cr.execute("""
            SELECT po.id, COALESCE(po.pos_reference, po.name) AS ref, po.partner_id,
                   po.amount_total, po.laundry_expected_delivery AS expected, po.laundry_expected_hour AS hour,
                   am.laundry_shelf AS shelf
              FROM pos_order po
              JOIN pos_session ps ON ps.id = po.session_id
              LEFT JOIN account_move am ON am.id = po.account_move
             WHERE ps.config_id = %(config)s
               AND po.state IN %(states)s
               AND po.amount_total >= 0
               AND po.laundry_expected_delivery IS NOT NULL
               AND po.laundry_expected_delivery <= %(today)s
               AND NOT COALESCE(am.laundry_delivered, FALSE)
             ORDER BY po.laundry_expected_delivery, po.laundry_expected_hour NULLS LAST, po.id
        """, {"config": config.id, "states": VALID_STATES, "today": today})
        rows = self.env.cr.dictfetchall()
        partners = {p.id: p for p in self.env["res.partner"].sudo().browse({r["partner_id"] for r in rows if r["partner_id"]})}
        due_today, overdue = [], []
        for r in rows:
            partner = partners.get(r["partner_id"])
            line = {
                "ref": r["ref"],
                "customer": partner.display_name if partner else "",
                "mobile": (partner.mobile or partner.phone or "") if partner else "",
                "shelf": r["shelf"] or "",
                "amount": r["amount_total"],
                "expected": r["expected"],
                "hour": "%s:00" % r["hour"] if r["hour"] else "",
                "days_late": (today - r["expected"]).days,
            }
            (due_today if r["expected"] == today else overdue).append(line)
        return due_today, overdue

    # ------------------------------------------------------------------ data
    def _get_report_values(self, config, day):
        """Values of one point of sale (one section of the e-mail)."""
        dash = self._dashboard(config)
        env = dash.env
        tz = self._config_tz(config)
        currency = config.currency_id or config.company_id.currency_id
        kpis = dash._kpis(day, day, config)
        last_week = dash._kpis(day - timedelta(days=7), day - timedelta(days=7), config)
        sessions = dash._sessions(day, day, config, active_in_period=True)
        due_today, overdue = self._deliveries(config, day + timedelta(days=1))

        def money(amount):
            return formatLang(env, amount or 0.0, currency_obj=currency)

        def local_time(value):
            if not value:
                return ""
            utc = pytz.utc.localize(fields.Datetime.to_datetime(value))
            return utc.astimezone(tz).strftime("%H:%M")

        def short_date(value):
            return format_date(env, value, date_format="d MMM") if value else ""

        collected = kpis["cash"] + kpis["bank"]
        last_week_collected = last_week["cash"] + last_week["bank"]
        return {
            "config": config,
            "company": config.company_id,
            "currency": currency,
            "day_label": format_date(env, day, date_format="EEEE d MMMM y"),
            "today_label": format_date(env, day + timedelta(days=1), date_format="EEEE d MMMM"),
            "kpis": kpis,
            "collected": collected,
            "last_week": {"sales": last_week["sales"], "orders": last_week["orders"], "collected": last_week_collected},
            "changes": {
                "sales": self._change(kpis["sales"], last_week["sales"]),
                "orders": self._change(kpis["orders"], last_week["orders"]),
                "collected": self._change(collected, last_week_collected),
            },
            "last_week_label": format_date(env, day - timedelta(days=7), date_format="EEEE d MMM"),
            "methods": self._payment_methods(dash, day, config),
            "collections": self._collections(dash, day, config, local_time),
            "cashiers": dash._cashiers(day, day, config),
            "sessions": sessions,
            "open_sessions": len([x for x in sessions["list"] if x["state"] != "closed"]),
            "due_today": due_today[:LIST_LIMIT],
            "due_today_count": len(due_today),
            "overdue": overdue[:LIST_LIMIT],
            "overdue_count": len(overdue),
            "money": money,
            "local_time": local_time,
            "short_date": short_date,
        }

    @staticmethod
    def _title(names):
        if len(names) <= 3:
            return " و ".join(names)
        return "%s نقاط بيع" % len(names)

    def _get_email_values(self, sections):
        """Whole e-mail: one or several point-of-sale sections, plus a comparison table when several."""
        first = sections[0]
        dash = self._dashboard(first["config"])
        totals = {"sales": 0.0, "collected": 0.0, "remaining": 0.0, "orders": 0,
                  "last_sales": 0.0, "last_collected": 0.0, "last_orders": 0}
        alerts = []
        for sec in sections:
            totals["sales"] += sec["kpis"]["sales"]
            totals["collected"] += sec["collected"]
            totals["remaining"] += sec["kpis"]["on_account"]
            totals["orders"] += sec["kpis"]["orders"]
            totals["last_sales"] += sec["last_week"]["sales"]
            totals["last_collected"] += sec["last_week"]["collected"]
            totals["last_orders"] += sec["last_week"]["orders"]
            name = sec["config"].name
            if sec["open_sessions"]:
                alerts.append("في %s جلسة صندوق لسا مفتوحة بنقطة %s." % (sec["open_sessions"], name))
            if sec["sessions"]["with_difference"]:
                alerts.append("في %s جلسة فيها فرق بالصندوق بنقطة %s، المجموع %s." % (
                    sec["sessions"]["with_difference"], name, sec["money"](sec["sessions"]["total_difference"])))
            auto_closed = [s for s in sec["sessions"]["list"] if s.get("auto_closed")]
            if auto_closed:
                alerts.append("انسكّرت %s جلسة تلقائياً بدون جرد للكاش بنقطة %s (%s): الكاش ما انعدّ، وأي نقص بيبيّن وقت فتح الصندوق." % (
                    len(auto_closed), name, "، ".join("%s - %s" % (s["name"], s["user"]) for s in auto_closed)))
            if sec["overdue_count"]:
                alerts.append("في %s طلب فات موعد تسليمه وما تسلّم بنقطة %s." % (sec["overdue_count"], name))
        totals["changes"] = {
            "sales": self._change(totals["sales"], totals["last_sales"]),
            "collected": self._change(totals["collected"], totals["last_collected"]),
            "orders": self._change(totals["orders"], totals["last_orders"]),
        }
        return {
            "sections": sections,
            "multi": len(sections) > 1,
            "title": self._title([sec["config"].name for sec in sections]),
            "company": first["company"],
            "day_label": first["day_label"],
            "today_label": first["today_label"],
            "last_week_label": first["last_week_label"],
            "alerts": alerts,
            "totals": totals,
            "receivables": dash._receivables_summary(),
            "money": first["money"],
        }

    def _render_html(self, configs, day, cache=None):
        cache = {} if cache is None else cache
        sections = []
        for config in configs:
            if config.id not in cache:
                cache[config.id] = self._get_report_values(config, day)
            sections.append(cache[config.id])
        return self.env["ir.qweb"].with_context(lang=REPORT_LANG)._render(
            "london_laundry_implementation.daily_report_email", self._get_email_values(sections))

    # ------------------------------------------------------------------ sending
    def _send_report(self, configs, day, emails, cache=None):
        """One e-mail covering `configs` (sorted by name) to `emails`."""
        configs = configs.sorted("name")
        names = configs.mapped("name")
        title = self._title(names)
        mail = self.env["mail.mail"].sudo().create({
            "subject": "التقرير اليومي - %s - %s" % (title, day.strftime("%d/%m/%Y")),
            "body_html": self._render_html(configs, day, cache),
            "email_to": ", ".join(emails),
            "email_from": configs[0].company_id.email_formatted or self.env.user.email_formatted or False,
            "auto_delete": False,
        })
        mail.send(raise_exception=False)
        if mail.state == "exception":
            _logger.warning("Laundry daily report for %s (%s) failed: %s", ", ".join(names), day, mail.failure_reason)
        return mail

    def _send_config_report(self, config, day):
        """Settings button: this point of sale only, to its own addresses."""
        return self._send_report(config, day, config._laundry_report_email_list())

    @api.model
    def _cron_send_daily_reports(self):
        """Group the points of sale by recipient: each address gets ONE e-mail with all its points of sale.

        Recipients that follow exactly the same points of sale share the same e-mail.
        """
        due = defaultdict(lambda: self.env["pos.config"])  # day -> configs whose report is due
        for config in self.env["pos.config"].sudo().search([("laundry_report_emails", "!=", False)]):
            if not config._laundry_report_email_list():
                continue
            local_now = datetime.now(self._config_tz(config))
            if local_now.time() < SEND_AFTER:
                continue
            day = local_now.date() - timedelta(days=1)
            if config.laundry_report_last_date and config.laundry_report_last_date >= day:
                continue
            due[day] |= config

        for day, configs in due.items():
            configs_by_email = defaultdict(lambda: self.env["pos.config"])
            for config in configs:
                for email in config._laundry_report_email_list():
                    configs_by_email[email.lower()] |= config
            emails_by_configs = defaultdict(list)
            for email, email_configs in configs_by_email.items():
                emails_by_configs[frozenset(email_configs.ids)].append(email)
            cache = {}
            for config_ids, emails in emails_by_configs.items():
                group = self.env["pos.config"].sudo().browse(sorted(config_ids))
                try:
                    self._send_report(group, day, sorted(emails), cache)
                except Exception:
                    _logger.exception("Laundry daily report for %s (%s) could not be built",
                                      ", ".join(group.mapped("name")), day)
            # marked even when sending failed: a failed mail stays in Settings > Emails to retry,
            # instead of building new ones every run
            configs.write({"laundry_report_last_date": day})
            self.env.cr.commit()
