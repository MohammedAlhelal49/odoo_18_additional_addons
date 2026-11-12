/** @odoo-module **/

import { Component, onWillStart, onWillUnmount, useEffect, useRef, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadBundle } from "@web/core/assets";
import { _t } from "@web/core/l10n/translation";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { formatFloat, formatInteger, formatMonetary } from "@web/views/fields/formatters";
import { localization } from "@web/core/l10n/localization";

const MODEL = "alomran.sales.dashboard";

/** Isolate an inserted value so numbers / dates / LTR names keep their place inside RTL text. */
const iso = (value) => `⁨${value}⁩`;
/** Amounts always read left-to-right, even inside the RTL dashboard. */
const ltr = (value) => `⁦${value}⁩`;

const COLORS = {
    main: "#017e84",
    previous: "#adb5bd",
    palette: ["#017e84", "#714b67", "#f0ad4e", "#5bc0de", "#d9534f", "#5cb85c", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f"],
};

// Sales dashboard, same layout and filters as the Bait Al Arab laundry dashboard.
export class SalesDashboard extends Component {
    static template = "alomran_implementation.SalesDashboard";
    static components = { Dropdown, DropdownItem };
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            loading: true,
            filters: { companies: [], users: [], presets: [], can_see_all: false },
            preset: "this_month",
            dateFrom: "",
            dateTo: "",
            companyIds: [],
            userIds: [],
            data: null,
        });
        this.salesChartRef = useRef("salesChart");
        this.paymentChartRef = useRef("paymentChart");
        this.sourceChartRef = useRef("sourceChart");
        this.enrollmentChartRef = useRef("enrollmentChart");
        this.charts = [];

        onWillStart(async () => {
            await loadBundle("web.chartjs_lib");
            this.state.filters = await this.orm.call(MODEL, "get_filters", []);
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
            this.state.data = await this.orm.call(MODEL, "get_data", [], {
                preset: this.state.preset,
                date_from: this.state.dateFrom || false,
                date_to: this.state.dateTo || false,
                company_ids: this.state.companyIds,
                user_ids: this.state.userIds,
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

    toggleCompany(id) {
        const ids = this.state.companyIds;
        this.state.companyIds = ids.includes(id) ? ids.filter((i) => i !== id) : [...ids, id];
        this.load();
    }

    isCompanyActive(id) {
        return !this.state.companyIds.length || this.state.companyIds.includes(id);
    }

    toggleUser(id) {
        const ids = this.state.userIds;
        this.state.userIds = ids.includes(id) ? ids.filter((i) => i !== id) : [...ids, id];
        this.load();
    }

    clearUsers() {
        this.state.userIds = [];
        this.load();
    }

    get userLabel() {
        const ids = this.state.userIds;
        if (!ids.length) {
            return _t("All salespeople");
        }
        if (ids.length === 1) {
            return this.state.filters.users.find((u) => u.id === ids[0])?.name || "";
        }
        return _t("%s salespeople", iso(ids.length));
    }

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

    int(value) {
        return formatInteger(value || 0);
    }

    pct(value) {
        return formatFloat(value || 0, { digits: [16, 1] }) + "%";
    }

    /** {label, cls} comparison of a KPI with the previous period. */
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
            { key: "sales", label: _t("Contracts value"), value: this.money(k.sales), trend: this.trend("sales"),
              sub: _t("excl. VAT %s", iso(this.money(k.sales_untaxed))), onClick: () => this.openOrders() },
            { key: "contracts", label: _t("Contracts"), value: this.int(k.contracts), trend: this.trend("contracts"),
              onClick: () => this.openOrders() },
            { key: "avg", label: _t("Average contract"), value: this.money(k.avg_contract), trend: this.trend("avg_contract") },
            { key: "customers", label: _t("Customers"), value: this.int(k.customers), trend: this.trend("customers"),
              sub: _t("%(new)s new · %(re)s re-enrollment", {
                  new: iso(this.int(k.new_enrollments)), re: iso(this.int(k.re_enrollments)) }) },
        ];
    }

    get followCards() {
        const k = this.state.data.kpis.current;
        return [
            { key: "initial", label: _t("Initial payments"), value: this.money(k.initial_payments),
              trend: this.trend("initial_payments"),
              sub: _t("%s of contracts value", iso(this.pct(k.sales ? (k.initial_payments / k.sales) * 100 : 0))) },
            { key: "remaining", label: _t("Remaining to invoice"), value: this.money(k.remaining),
              valueClass: k.remaining > 0.005 ? "text-warning" : "",
              sub: _t("%s contract(s)", iso(this.int(k.remaining_count))),
              onClick: () => this.openOrders([["remaining_amount", ">", 0.01]], _t("Remaining to invoice")) },
            { key: "quotations", label: _t("Open quotations"), value: this.int(k.quotations),
              sub: this.money(k.quotations_amount),
              onClick: () => this.openQuotations() },
            { key: "pending", label: _t("Pending admin approval"), value: this.int(k.pending_approval),
              valueClass: k.pending_approval ? "text-warning" : "",
              onClick: () => this.openOrders([["admin_approval", "=", "pending"]], _t("Pending admin approval")) },
            { key: "cancelled", label: _t("Cancelled"), value: this.int(k.cancelled),
              trend: this.trend("cancelled", false), valueClass: k.cancelled ? "text-danger" : "",
              onClick: () => this.openCancelled() },
        ];
    }

    get compareLabel() {
        return _t("compared with %s", iso(this.state.data.period.prev_label));
    }

    get timezoneLabel() {
        return _t("Times in %s", iso(this.state.data.timezone.used));
    }

    onCardClick(card) {
        if (card.onClick) {
            card.onClick();
        }
    }

    // ------------------------------------------------------------------ drill-down
    scopeDomain() {
        const d = this.state.data;
        const domain = [["company_id", "in", d.company_ids]];
        if (d.user_ids.length) {
            domain.push(["user_id", "in", d.user_ids]);
        }
        return domain;
    }

    baseDomain(start, end) {
        const p = this.state.data.period;
        return [
            ["state", "=", "sale"],
            ["date_order", ">=", start || p.start],
            ["date_order", "<", end || p.end],
            ...this.scopeDomain(),
        ];
    }

    openSaleOrders(domain, name) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name,
            res_model: "sale.order",
            views: [
                [false, "list"],
                [false, "form"],
            ],
            domain,
            context: { create: false, allowed_company_ids: this.state.data.company_ids },
        });
    }

    openOrders(extraDomain = [], name = _t("Contracts"), start = false, end = false) {
        this.openSaleOrders([...this.baseDomain(start, end), ...extraDomain], name);
    }

    createdDomain() {
        const p = this.state.data.period;
        return [["create_date", ">=", p.start], ["create_date", "<", p.end], ...this.scopeDomain()];
    }

    openQuotations() {
        this.openSaleOrders([["state", "in", ["draft", "sent"]], ...this.createdDomain()], _t("Open quotations"));
    }

    openCancelled() {
        this.openSaleOrders([["state", "=", "cancel"], ...this.createdDomain()], _t("Cancelled"));
    }

    openSelection(field, item) {
        this.openOrders([[field, "=", item.value]], item.name);
    }

    openCourse(course) {
        this.openOrders([["order_line.product_id", "=", course.id]], course.name);
    }

    openSalesperson(person) {
        this.openOrders([["user_id", "=", person.id || false]], person.name);
    }

    openBranch(branch) {
        this.openOrders([["company_id", "=", branch.id]], branch.name);
    }

    openOrder(order) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "sale.order",
            res_id: order.id,
            views: [[false, "form"]],
            context: { allowed_company_ids: this.state.data.company_ids },
        });
    }

    // ------------------------------------------------------------------ charts
    destroyCharts() {
        for (const chart of this.charts) {
            chart.destroy();
        }
        this.charts = [];
    }

    doughnut(ref, items, field) {
        const rows = items.filter((i) => i.amount > 0);
        if (!ref.el || !rows.length) {
            return;
        }
        const rtl = this.isRtl;
        this.charts.push(
            new window.Chart(ref.el, {
                type: "doughnut",
                data: {
                    labels: rows.map((r) => r.name),
                    datasets: [
                        {
                            data: rows.map((r) => r.amount),
                            backgroundColor: rows.map((r, i) => COLORS.palette[i % COLORS.palette.length]),
                        },
                    ],
                },
                options: {
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: "bottom", rtl },
                        tooltip: {
                            callbacks: {
                                label: (ctx) => `${ctx.label}: ${this.money(ctx.raw)} (${this.int(rows[ctx.dataIndex].contracts)})`,
                            },
                        },
                    },
                    onClick: (event, elements) => {
                        if (elements.length) {
                            this.openSelection(field, rows[elements[0].index]);
                        }
                    },
                },
            })
        );
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
                        scales: {
                            y: { beginAtZero: true, position: rtl ? "right" : "left", ticks: { callback: moneyTick } },
                            x: { reverse: rtl },
                        },
                        plugins: {
                            legend: { position: "bottom", rtl },
                            tooltip: {
                                callbacks: {
                                    label: (ctx) =>
                                        ctx.datasetIndex === 0
                                            ? `${ctx.dataset.label}: ${this.money(ctx.raw)} (${this.int(series.contracts[ctx.dataIndex])})`
                                            : `${ctx.dataset.label}: ${this.money(ctx.raw)}`,
                                },
                            },
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

        this.doughnut(this.paymentChartRef, data.payment_methods, "payment_method");
        this.doughnut(this.enrollmentChartRef, data.enrollments, "enrollment_type");

        const sources = data.sources.filter((s) => s.amount > 0);
        if (this.sourceChartRef.el && sources.length) {
            this.charts.push(
                new Chart(this.sourceChartRef.el, {
                    type: "bar",
                    data: {
                        labels: sources.map((s) => s.name),
                        datasets: [
                            {
                                label: _t("Contracts value"),
                                data: sources.map((s) => s.amount),
                                backgroundColor: sources.map((s, i) => COLORS.palette[i % COLORS.palette.length]),
                            },
                        ],
                    },
                    options: {
                        maintainAspectRatio: false,
                        indexAxis: "y",
                        scales: {
                            x: { beginAtZero: true, reverse: rtl, ticks: { callback: moneyTick } },
                            y: { position: rtl ? "right" : "left" },
                        },
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    label: (ctx) => `${this.money(ctx.raw)} (${this.int(sources[ctx.dataIndex].contracts)})`,
                                },
                            },
                        },
                        onClick: (event, elements) => {
                            if (elements.length) {
                                this.openSelection("source", sources[elements[0].index]);
                            }
                        },
                    },
                })
            );
        }
    }
}

registry.category("actions").add("alomran_sales_dashboard", SalesDashboard);
