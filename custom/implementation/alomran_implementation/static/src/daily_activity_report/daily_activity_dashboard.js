/** @odoo-module **/

import { onWillStart, onWillUnmount, useEffect, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { loadBundle } from "@web/core/assets";
import { _t } from "@web/core/l10n/translation";
import { deserializeDate, formatDate } from "@web/core/l10n/dates";
import { DailyActivityReport } from "@alomran_implementation/daily_activity_report/daily_activity_report";

const MODEL = "alomran.daily.activity.report";

// Distinct series colors + meaningful status colors (readable in light and dark mode)
const SERIES_COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ef4444", "#14b8a6", "#ec4899"];
const STATUS_COLORS = { good: "#22c55e", warning: "#f59e0b", danger: "#ef4444" };

// Dashboard (KPI cards + charts) on top of the Daily Activity Report.
// Same filters and same server-side scope: "Own Documents" salespeople
// only get their own figures.
export class DailyActivityDashboard extends DailyActivityReport {
    static template = "alomran_implementation.DailyActivityDashboard";

    setup() {
        super.setup();
        if (!this.props.action?.context?.alomran_options) {
            Object.assign(this.state.options, this.computePreset("this_month"));
        }
        this.charts = [];
        this.validityChart = null;
        this.validityRequest = 0;
        this.state.validity = null;
        this.trendRef = useRef("trend");
        this.tasksRef = useRef("tasks");
        this.pipelineRef = useRef("pipeline");
        this.validityRef = useRef("validity");
        this.employeesRef = useRef("employees");
        onWillStart(() => loadBundle("web.chartjs_lib"));
        useEffect(
            () => {
                this.renderCharts();
            },
            () => [this.state.data]
        );
        useEffect(
            () => {
                this.renderValidityChart();
            },
            () => [this.state.validity]
        );
        onWillUnmount(() => {
            this.destroyCharts();
            this.validityChart?.destroy();
        });
    }

    async load() {
        this.state.loading = true;
        try {
            const data = await this.orm.call(MODEL, "get_dashboard_data", [this.state.options]);
            this.state.data = data;
            this.state.options = { ...data.options, preset: this.state.options.preset };
        } finally {
            this.state.loading = false;
        }
        this.loadValidity();
    }

    // Slowest part (whole chatter history): loaded after the rest of the dashboard
    async loadValidity() {
        const request = ++this.validityRequest;
        this.state.validity = null;
        const validity = await this.orm.call(MODEL, "get_dashboard_validity", [this.state.options]);
        if (request === this.validityRequest) {
            this.state.validity = validity;
        }
    }

    // ------------------------------------------------------------------
    // Cards / lists
    // ------------------------------------------------------------------
    get kpis() {
        const icons = {
            new_customers: "fa-user-plus",
            follow_ups: "fa-comments",
            activities_total: "fa-tasks",
            activities_done: "fa-check-circle",
            activities_overdue: "fa-exclamation-triangle",
            opportunities: "fa-star",
            contracts: "fa-file-text",
            contracts_amount: "fa-money",
        };
        return this.state.data.columns.map((col) => ({
            ...col,
            icon: icons[col.field] || "fa-bar-chart",
            value: this.state.data.totals[col.field],
            danger: col.field === "activities_overdue" && this.state.data.totals[col.field] > 0,
        }));
    }

    get pendingTasks() {
        const t = this.state.data.totals;
        return Math.max(t.activities_total - t.activities_done - t.activities_overdue, 0);
    }

    openDocument(model, resId) {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            res_model: model,
            res_id: resId,
            views: [[false, "form"]],
            target: "current",
            context: { allowed_company_ids: this.state.options.company_ids },
        });
    }

    async openLeads(kind, stageId = false) {
        const action = await this.orm.call(MODEL, "action_open_dashboard_leads", [
            this.state.options,
            kind,
            stageId,
        ]);
        await this.actionService.doAction(action);
    }

    openDetailedReport() {
        this.actionService.doAction("alomran_implementation.alomran_daily_activity_report_client_action", {
            additionalContext: { alomran_options: this.state.options },
        });
    }

    // ------------------------------------------------------------------
    // Charts
    // ------------------------------------------------------------------
    color(index) {
        return SERIES_COLORS[index % SERIES_COLORS.length];
    }

    destroyCharts() {
        for (const chart of this.charts) {
            chart.destroy();
        }
        this.charts = [];
    }

    addChart(ref, config) {
        if (!ref.el) {
            return null;
        }
        config.options = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: "bottom", labels: { boxWidth: 12 } } },
            ...config.options,
        };
        const chart = new Chart(ref.el, config);
        this.charts.push(chart);
        return chart;
    }

    onChartClick(callback) {
        return (ev, elements) => {
            if (elements.length) {
                callback(elements[0].index, elements[0].datasetIndex);
            }
        };
    }

    renderCharts() {
        this.destroyCharts();
        const data = this.state.data;
        if (!data || typeof Chart === "undefined") {
            return;
        }
        const label = (field) => data.columns.find((c) => c.field === field)?.label || field;

        // 1. Daily trend
        const trendFields = ["follow_ups", "activities_done", "opportunities", "contracts"];
        this.addChart(this.trendRef, {
            type: "line",
            data: {
                labels: data.trend.labels.map((d) => formatDate(deserializeDate(d))),
                datasets: trendFields.map((field, i) => ({
                    label: label(field),
                    data: data.trend.series[field],
                    borderColor: this.color(i),
                    backgroundColor: this.color(i),
                    tension: 0.3,
                    pointRadius: data.trend.labels.length > 31 ? 0 : 3,
                })),
            },
            options: {
                interaction: { mode: "index", intersect: false },
                scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
            },
        });

        // 2. Tasks status
        const tasks = [
            ["activities_done", data.totals.activities_done],
            ["activities_total", this.pendingTasks],
            ["activities_overdue", data.totals.activities_overdue],
        ];
        this.addChart(this.tasksRef, {
            type: "doughnut",
            data: {
                labels: [_t("Completed"), _t("Pending"), _t("Overdue")],
                datasets: [
                    {
                        data: tasks.map((t) => t[1]),
                        backgroundColor: [STATUS_COLORS.good, STATUS_COLORS.warning, STATUS_COLORS.danger],
                    },
                ],
            },
            options: {
                onClick: this.onChartClick((index) => {
                    const [field, value] = tasks[index];
                    this.openRecords(field, value);
                }),
            },
        });

        // 3. Pipeline by stage
        this.addChart(this.pipelineRef, {
            type: "bar",
            data: {
                labels: data.pipeline.map((s) => s.name),
                datasets: [
                    {
                        label: _t("Open Opportunities"),
                        data: data.pipeline.map((s) => s.count),
                        backgroundColor: data.pipeline.map((s, i) => this.color(i)),
                    },
                ],
            },
            options: {
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
                onClick: this.onChartClick((index) => this.openLeads("stage", data.pipeline[index].stage_id)),
            },
        });

        // 4. Employees comparison (managers / All Documents only)
        if (data.can_see_all && data.employees.length) {
            const empFields = ["follow_ups", "activities_done", "activities_overdue", "opportunities", "contracts"];
            this.addChart(this.employeesRef, {
                type: "bar",
                data: {
                    labels: data.employees.map((e) => e.name),
                    datasets: empFields.map((field, i) => ({
                        label: label(field),
                        data: data.employees.map((e) => e.values[field]),
                        backgroundColor: this.color(i),
                    })),
                },
                options: {
                    scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
                    onClick: this.onChartClick((index, datasetIndex) => {
                        const employee = data.employees[index];
                        const field = empFields[datasetIndex];
                        this.openRecords(field, employee.values[field], employee.user_id);
                    }),
                },
            });
        }
    }

    renderValidityChart() {
        this.validityChart?.destroy();
        this.validityChart = null;
        const validity = this.state.validity;
        if (!validity || !this.validityRef.el || typeof Chart === "undefined") {
            return;
        }
        const kinds = ["active", "expiring", "expired"];
        this.validityChart = new Chart(this.validityRef.el, {
            type: "doughnut",
            data: {
                labels: [
                    _t("Active"),
                    _t("Expiring in %s days", this.state.data.expiring_days),
                    _t("Expired"),
                ],
                datasets: [
                    {
                        data: kinds.map((k) => validity.counts[k]),
                        backgroundColor: [STATUS_COLORS.good, STATUS_COLORS.warning, STATUS_COLORS.danger],
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: "bottom", labels: { boxWidth: 12 } } },
                onClick: this.onChartClick((index) => this.openLeads(kinds[index])),
            },
        });
    }
}

registry.category("actions").add("alomran_daily_activity_dashboard", DailyActivityDashboard);
