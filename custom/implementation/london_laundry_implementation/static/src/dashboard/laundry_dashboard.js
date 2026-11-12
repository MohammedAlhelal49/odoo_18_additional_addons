/** @odoo-module **/

import { Component, onWillStart, onWillUnmount, useEffect, useRef, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadBundle } from "@web/core/assets";
import { _t } from "@web/core/l10n/translation";
import { formatFloat, formatInteger, formatMonetary } from "@web/views/fields/formatters";
import { deserializeDateTime, formatDateTime } from "@web/core/l10n/dates";
import { localization } from "@web/core/l10n/localization";

/** Isolate an inserted value so numbers / dates / LTR names keep their place inside RTL text. */
const iso = (value) => `\u2068${value}\u2069`;
/** Amounts always read left-to-right ("$ -11.50"), even inside the RTL dashboard. */
const ltr = (value) => `\u2066${value}\u2069`;

const COLORS = {
    main: "#017e84",
    previous: "#adb5bd",
    cash: "#28a745",
    bank: "#1f77b4",
    other: "#ff9f40",
    palette: ["#017e84", "#714b67", "#f0ad4e", "#5bc0de", "#d9534f", "#5cb85c", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f"],
};

export class LaundryDashboard extends Component {
    static template = "london_laundry_implementation.Dashboard";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.state = useState({
            loading: true,
            filters: { configs: [], presets: [] },
            preset: "this_month",
            dateFrom: "",
            dateTo: "",
            configIds: [],
            lapseDays: 45,
            data: null,
        });
        this.salesChartRef = useRef("salesChart");
        this.paymentsChartRef = useRef("paymentsChart");
        this.categoryChartRef = useRef("categoryChart");
        this.charts = [];

        onWillStart(async () => {
            await loadBundle("web.chartjs_lib");
            this.state.filters = await this.orm.call("london.laundry.dashboard", "get_filters", []);
            await this.load();
        });
        useEffect(
            () => {
                this.renderCharts();
            },
            () => [this.state.data]
        );
        onWillUnmount(() => this.destroyCharts());
    }

    // ------------------------------------------------------------------ data
    async load() {
        if (this.state.preset === "custom" && (!this.state.dateFrom || !this.state.dateTo)) {
            return;
        }
        this.state.loading = true;
        try {
            this.state.data = await this.orm.call("london.laundry.dashboard", "get_data", [], {
                preset: this.state.preset,
                date_from: this.state.dateFrom || false,
                date_to: this.state.dateTo || false,
                config_ids: this.state.configIds,
                lapse_days: this.state.lapseDays,
                browser_tz: Intl.DateTimeFormat().resolvedOptions().timeZone || false,
            });
            if (this.state.preset !== "custom") {
                this.state.dateFrom = this.state.data.period.date_from;
                this.state.dateTo = this.state.data.period.date_to;
            }
        } finally {
            this.state.loading = false;
        }
    }

    selectPreset(key) {
        this.state.preset = key;
        if (key !== "custom") {
            this.load();
        }
    }

    onDateChange(field, ev) {
        this.state[field] = ev.target.value;
        if (this.state.preset === "custom") {
            this.load();
        }
    }

    toggleConfig(id) {
        const ids = this.state.configIds;
        this.state.configIds = ids.includes(id) ? ids.filter((i) => i !== id) : [...ids, id];
        this.load();
    }

    isConfigActive(id) {
        return !this.state.configIds.length || this.state.configIds.includes(id);
    }

    onLapseChange(ev) {
        this.state.lapseDays = parseInt(ev.target.value);
        this.load();
    }

    /** Odoo mirrors the CSS for RTL languages but keeps the text direction LTR; the template sets
     *  dir="rtl" itself so Arabic sentences with numbers read in the right order. */
    get isRtl() {
        return localization.direction === "rtl";
    }

    // ------------------------------------------------------------------ formatting
    get currencyId() {
        return this.state.data?.currency_id;
    }

    money(value) {
        return ltr(formatMonetary(value || 0, { currencyId: this.currencyId, digits: [16, 0] }));
    }

    money2(value) {
        return ltr(formatMonetary(value || 0, { currencyId: this.currencyId }));
    }

    int(value) {
        return formatInteger(value || 0);
    }

    pct(value) {
        return formatFloat(value || 0, { digits: [16, 1] }) + "%";
    }

    dateTime(value) {
        return value ? formatDateTime(deserializeDateTime(value)) : "";
    }

    /** {pct, up, good} comparison of a KPI with the previous period. */
    trend(name, higherIsBetter = true) {
        const current = this.state.data.kpis.current[name] || 0;
        const previous = this.state.data.kpis.previous[name] || 0;
        if (!previous) {
            return current ? { label: _t("New"), cls: "text-muted" } : { label: "-", cls: "text-muted" };
        }
        const change = ((current - previous) / Math.abs(previous)) * 100;
        const up = change >= 0;
        const good = up === higherIsBetter;
        return {
            label: `${up ? "▲" : "▼"} ${formatFloat(Math.abs(change), { digits: [16, 1] })}%`,
            cls: Math.abs(change) < 0.05 ? "text-muted" : good ? "text-success" : "text-danger",
        };
    }

    get salesCards() {
        const k = this.state.data.kpis.current;
        return [
            { key: "sales", label: _t("Sales"), value: this.money(k.sales), trend: this.trend("sales"),
              sub: _t("excl. VAT %s", iso(this.money(k.sales_untaxed))), onClick: () => this.openOrders() },
            { key: "orders", label: _t("Orders"), value: this.int(k.orders), trend: this.trend("orders"),
              onClick: () => this.openOrders([["amount_total", ">=", 0]]) },
            { key: "avg", label: _t("Average order"), value: this.money2(k.avg_order), trend: this.trend("avg_order") },
            { key: "customers", label: _t("Customers"), value: this.int(k.customers), trend: this.trend("customers"),
              sub: _t("%(new)s new · %(returning)s returning", {
                  new: iso(this.int(k.new_customers)), returning: iso(this.int(k.returning_customers)) }) },
        ];
    }

    get collectionCards() {
        const k = this.state.data.kpis.current;
        const s = this.state.data.sessions;
        const r = this.state.data.receivables;
        const diff = s.total_difference;
        return [
            { key: "cash", label: _t("Cash collected"), value: this.money(k.cash), trend: this.trend("cash"),
              sub: [_t("%s of collected", iso(this.pct(this.cashShare))),
                    k.outside_cash ? _t("incl. %s paid outside the POS", this.money(k.outside_cash)) : ""]
                    .filter(Boolean).join(" · "),
              onClick: () => this.openReport("collection") },
            { key: "bank", label: _t("Bank collected"), value: this.money(k.bank), trend: this.trend("bank"),
              sub: k.outside_bank ? _t("incl. %s paid outside the POS", this.money(k.outside_bank)) : "",
              onClick: () => this.openReport("collection") },
            { key: "on_account", label: _t("Sold on account"), value: this.money(k.on_account),
              trend: this.trend("on_account", false), sub: _t("to be collected later"),
              onClick: () => this.openReport("collection") },
            { key: "receivables", label: _t("Customer balances"), value: this.money(r.total),
              valueClass: r.overdue > 0.005 ? "text-danger" : "",
              sub: _t("%(overdue)s overdue · %(count)s customers", { overdue: iso(this.money(r.overdue)), count: iso(this.int(r.customers)) }),
              onClick: () => this.openReport("receivables") },
            { key: "diff", label: _t("Cash difference"), value: this.money2(diff),
              valueClass: diff < -0.005 ? "text-danger" : diff > 0.005 ? "text-warning" : "",
              sub: _t("%s session(s) with a difference", iso(this.int(s.with_difference))) },
            { key: "refunds", label: _t("Refunds"), value: this.money(k.refunds_amount),
              trend: this.trend("refunds_amount", false), sub: _t("%s refund(s)", iso(this.int(k.refunds_count))),
              onClick: () => this.openRefunds() },
            { key: "discounts", label: _t("Discounts given"), value: this.money(k.discounts),
              trend: this.trend("discounts", false) },
        ];
    }

    get timezoneWarning() {
        const tz = this.state.data.timezone;
        if (tz.user && tz.browser && tz.user !== tz.browser) {
            return _t(
                "Times are shown in your user timezone (%(user)s), which differs from this device (%(device)s). You can change it in your preferences.",
                { user: iso(tz.user), device: iso(tz.browser) }
            );
        }
        return false;
    }

    get timezoneLabel() {
        return _t("Times in %s", iso(this.state.data.timezone.used));
    }

    get compareLabel() {
        return _t("compared with %s", iso(this.state.data.period.prev_label));
    }

    lapseLabel(days) {
        return _t("No visit for %s+ days", iso(days));
    }

    daysAgo(days) {
        return _t("%s days", iso(this.int(days)));
    }

    get openSessionsLabel() {
        return _t("%s open", iso(this.int(this.state.data.sessions.open_count)));
    }

    onCardClick(card) {
        if (card.onClick) {
            card.onClick();
        }
    }

    get cashShare() {
        const k = this.state.data.kpis.current;
        const total = (k.cash || 0) + (k.bank || 0);
        return total ? ((k.cash || 0) / total) * 100 : 0;
    }

    heatColor(value) {
        const max = this.state.data.heatmap.max || 1;
        const alpha = value ? 0.12 + (0.88 * value) / max : 0;
        return `background-color: rgba(1, 126, 132, ${alpha.toFixed(2)}); color: ${alpha > 0.55 ? "#fff" : "inherit"};`;
    }

    get hours() {
        return [...Array(24).keys()];
    }

    // ------------------------------------------------------------------ drill-down
    baseDomain(start, end) {
        const p = this.state.data.period;
        return [
            ["date_order", ">=", start || p.start],
            ["date_order", "<", end || p.end],
            ["state", "in", this.state.data.states],
            ["session_id.config_id", "in", this.state.data.config_ids],
        ];
    }

    openOrders(extraDomain = [], name = _t("Orders"), start = false, end = false) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name,
            res_model: "pos.order",
            views: [
                [false, "list"],
                [false, "form"],
            ],
            domain: [...this.baseDomain(start, end), ...extraDomain],
            context: { create: false },
        });
    }

    openRefunds() {
        this.openOrders([["amount_total", "<", 0]], _t("Refunds"));
    }

    openCustomerOrders(customer) {
        this.openOrders([["partner_id", "=", customer.id]], customer.name);
    }

    openCashierOrders(cashier) {
        const field = cashier.kind === "employee" ? "employee_id" : "user_id";
        const extra = [[field, "=", cashier.id]];
        if (cashier.kind === "user" && this.state.data.has_employee) {
            extra.push(["employee_id", "=", false]);
        }
        this.openOrders(extra, cashier.name);
    }

    openProduct(product) {
        this.openOrders([["lines.product_id", "=", product.id]], product.name);
    }

    openCategory(category) {
        const extra = category.id
            ? [["lines.product_id.pos_categ_ids", "in", [category.id]]]
            : [["lines.product_id.pos_categ_ids", "=", false]];
        this.openOrders(extra, category.name);
    }

    openPayments(kind) {
        const p = this.state.data.period;
        const domain = [
            ["pos_order_id.date_order", ">=", p.start],
            ["pos_order_id.date_order", "<", p.end],
            ["pos_order_id.state", "in", this.state.data.states],
            ["session_id.config_id", "in", this.state.data.config_ids],
        ];
        if (kind === "cash") {
            domain.push(["payment_method_id.is_cash_count", "=", true]);
        } else if (kind === "bank") {
            domain.push(["payment_method_id.is_cash_count", "=", false], ["payment_method_id.journal_id", "!=", false]);
        }
        this.action.doAction({
            type: "ir.actions.act_window",
            name: _t("Payments"),
            res_model: "pos.payment",
            views: [[false, "list"]],
            domain,
            context: { create: false },
        });
    }

    openReport(key) {
        this.action.doAction(`london_laundry_implementation.action_report_${key}`);
    }

    openSession(session) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "pos.session",
            res_id: session.id,
            views: [[false, "form"]],
        });
    }

    openPartner(customer) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "res.partner",
            res_id: customer.id,
            views: [[false, "form"]],
        });
    }

    openHeatCell(dayIndex, hour) {
        this.notification.add(
            _t("%(day)s %(hour)s:00 — %(count)s orders", {
                day: this.state.data.heatmap.days[dayIndex],
                hour: iso(hour),
                count: iso(this.state.data.heatmap.matrix[dayIndex][hour]),
            }),
            { type: "info" }
        );
    }

    // ------------------------------------------------------------------ charts
    destroyCharts() {
        for (const chart of this.charts) {
            chart.destroy();
        }
        this.charts = [];
    }

    renderCharts() {
        this.destroyCharts();
        const data = this.state.data;
        if (!data || !window.Chart) {
            return;
        }
        const Chart = window.Chart;
        const series = data.series;
        const moneyTick = (value) => formatFloat(value, { digits: [16, 0] });
        const rtl = this.isRtl;

        if (this.salesChartRef.el) {
            this.charts.push(
                new Chart(this.salesChartRef.el, {
                    type: "line",
                    data: {
                        labels: series.labels,
                        datasets: [
                            {
                                label: _t("This period"),
                                data: series.sales,
                                borderColor: COLORS.main,
                                backgroundColor: "rgba(1, 126, 132, 0.12)",
                                fill: true,
                                tension: 0.3,
                                pointRadius: 3,
                            },
                            {
                                label: _t("Previous period"),
                                data: series.prev_sales,
                                borderColor: COLORS.previous,
                                borderDash: [6, 4],
                                fill: false,
                                tension: 0.3,
                                pointRadius: 0,
                            },
                        ],
                    },
                    options: {
                        maintainAspectRatio: false,
                        interaction: { mode: "index", intersect: false },
                        layout: { padding: { left: 18, right: 18 } },
                        scales: { y: { beginAtZero: true, position: rtl ? "right" : "left", ticks: { callback: moneyTick } }, x: { reverse: rtl } },
                        plugins: {
                            legend: { position: "bottom", rtl },
                            tooltip: { callbacks: { label: (ctx) => `${ctx.dataset.label}: ${this.money2(ctx.raw)}` } },
                        },
                        onClick: (event, elements) => {
                            if (elements.length) {
                                const bucket = series.buckets[elements[0].index];
                                this.openOrders([], series.labels[elements[0].index], bucket.start, bucket.end);
                            }
                        },
                    },
                })
            );
        }

        if (this.paymentsChartRef.el) {
            const datasets = [
                { label: _t("Cash"), data: series.cash, backgroundColor: COLORS.cash, stack: "p" },
                { label: _t("Bank"), data: series.bank, backgroundColor: COLORS.bank, stack: "p" },
            ];
            if (series.other.some((v) => v)) {
                datasets.push({ label: _t("Other"), data: series.other, backgroundColor: COLORS.other, stack: "p" });
            }
            this.charts.push(
                new Chart(this.paymentsChartRef.el, {
                    type: "bar",
                    data: { labels: series.labels, datasets },
                    options: {
                        maintainAspectRatio: false,
                        layout: { padding: { left: 18, right: 18 } },
                        scales: {
                            x: { stacked: true, reverse: rtl },
                            y: { stacked: true, beginAtZero: true, position: rtl ? "right" : "left", ticks: { callback: moneyTick } },
                        },
                        plugins: {
                            legend: { position: "bottom", rtl },
                            tooltip: { callbacks: { label: (ctx) => `${ctx.dataset.label}: ${this.money2(ctx.raw)}` } },
                        },
                        onClick: (event, elements) => {
                            if (elements.length) {
                                const bucket = series.buckets[elements[0].index];
                                this.openOrders([], series.labels[elements[0].index], bucket.start, bucket.end);
                            }
                        },
                    },
                })
            );
        }

        const categories = data.categories.filter((c) => c.amount > 0);
        if (this.categoryChartRef.el && categories.length) {
            this.charts.push(
                new Chart(this.categoryChartRef.el, {
                    type: "doughnut",
                    data: {
                        labels: categories.map((c) => c.name),
                        datasets: [
                            {
                                data: categories.map((c) => c.amount),
                                backgroundColor: categories.map((c, i) => COLORS.palette[i % COLORS.palette.length]),
                            },
                        ],
                    },
                    options: {
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { position: "bottom", rtl },
                            tooltip: { callbacks: { label: (ctx) => `${ctx.label}: ${this.money2(ctx.raw)}` } },
                        },
                        onClick: (event, elements) => {
                            if (elements.length) {
                                this.openCategory(categories[elements[0].index]);
                            }
                        },
                    },
                })
            );
        }
    }
}

registry.category("actions").add("london_laundry_dashboard", LaundryDashboard);
