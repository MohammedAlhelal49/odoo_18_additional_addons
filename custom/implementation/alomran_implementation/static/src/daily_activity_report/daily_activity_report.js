/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { download } from "@web/core/network/download";
import { formatFloat } from "@web/core/utils/numbers";
import { deserializeDate, formatDate, serializeDate } from "@web/core/l10n/dates";
import { user } from "@web/core/user";

const { DateTime } = luxon;

const MODEL = "alomran.daily.activity.report";

export class DailyActivityReport extends Component {
    static template = "alomran_implementation.DailyActivityReport";
    static components = { Dropdown, DropdownItem };
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.ui = useService("ui");
        this.presets = [
            { key: "today", label: _t("Today") },
            { key: "yesterday", label: _t("Yesterday") },
            { key: "this_week", label: _t("This Week") },
            { key: "last_7", label: _t("Last 7 Days") },
            { key: "this_month", label: _t("This Month") },
            { key: "last_month", label: _t("Last Month") },
        ];
        const saved = this.props.action?.context?.alomran_options;
        this.state = useState({
            options: saved || { ...this.computePreset("today"), user_ids: [], company_ids: [] },
            data: null,
            expanded: {},
            loading: false,
        });
        onWillStart(() => this.load());
    }

    // ------------------------------------------------------------------
    // Data
    // ------------------------------------------------------------------
    async load() {
        this.state.loading = true;
        try {
            const data = await this.orm.call(MODEL, "get_report_data", [this.state.options]);
            this.state.data = data;
            // keep sanitized values (dates swapped, companies resolved...)
            this.state.options = { ...data.options, preset: this.state.options.preset };
        } finally {
            this.state.loading = false;
        }
    }

    computePreset(key) {
        const today = DateTime.local().startOf("day");
        let from = today;
        let to = today;
        switch (key) {
            case "yesterday":
                from = to = today.minus({ days: 1 });
                break;
            case "this_week":
                from = today.startOf("week");
                break;
            case "last_7":
                from = today.minus({ days: 6 });
                break;
            case "this_month":
                from = today.startOf("month");
                break;
            case "last_month":
                from = today.minus({ months: 1 }).startOf("month");
                to = today.minus({ months: 1 }).endOf("month").startOf("day");
                break;
        }
        return { preset: key, date_from: serializeDate(from), date_to: serializeDate(to) };
    }

    // ------------------------------------------------------------------
    // Filters
    // ------------------------------------------------------------------
    get presetLabel() {
        const preset = this.presets.find((p) => p.key === this.state.options.preset);
        return preset ? preset.label : _t("Custom");
    }

    async selectPreset(key) {
        Object.assign(this.state.options, this.computePreset(key));
        await this.load();
    }

    async onDateChange(field, ev) {
        if (!ev.target.value) {
            return;
        }
        this.state.options[field] = ev.target.value;
        this.state.options.preset = "custom";
        await this.load();
    }

    isSelected(field, id) {
        return this.state.options[field].includes(id);
    }

    async toggleFilter(field, id) {
        const values = new Set(this.state.options[field]);
        values.has(id) ? values.delete(id) : values.add(id);
        this.state.options[field] = [...values];
        await this.load();
    }

    async clearFilter(field) {
        this.state.options[field] = [];
        await this.load();
    }

    filterLabel(field, choices, emptyLabel) {
        const ids = this.state.options[field];
        if (!ids.length) {
            return emptyLabel;
        }
        if (ids.length === 1) {
            return choices.find((c) => c.id === ids[0])?.name || emptyLabel;
        }
        return _t("%s selected", ids.length);
    }

    get userLabel() {
        return this.filterLabel("user_ids", this.state.data.filters.users, _t("All Employees"));
    }

    get companyLabel() {
        const companies = this.state.data.filters.companies;
        const ids = this.state.options.company_ids;
        if (!ids.length || ids.length === companies.length) {
            return _t("All Branches");
        }
        return this.filterLabel("company_ids", companies, _t("All Branches"));
    }

    // ------------------------------------------------------------------
    // Table helpers
    // ------------------------------------------------------------------
    toggleLine(userId) {
        this.state.expanded[userId] = !this.state.expanded[userId];
    }

    get allExpanded() {
        const lines = this.state.data?.lines || [];
        return lines.length && lines.every((l) => this.state.expanded[l.user_id]);
    }

    toggleAll() {
        const expand = !this.allExpanded;
        for (const line of this.state.data.lines) {
            this.state.expanded[line.user_id] = expand;
        }
    }

    formatValue(field, value) {
        if (field === "contracts_amount") {
            return formatFloat(value || 0, { digits: [16, 2] });
        }
        return value || 0;
    }

    formatDay(value) {
        const date = deserializeDate(value);
        return `${date.toFormat("ccc")} ${formatDate(date)}`;
    }

    cellClass(field, value) {
        const classes = ["text-center"];
        if (field === "activities_overdue" && value) {
            classes.push("text-danger fw-bold");
        }
        if (value && field !== "contracts_amount") {
            classes.push("o_alomran_dar_clickable");
        }
        return classes.join(" ");
    }

    get periodLabel() {
        const { date_from, date_to } = this.state.options;
        const from = formatDate(deserializeDate(date_from));
        const to = formatDate(deserializeDate(date_to));
        return date_from === date_to ? from : `${from} → ${to}`;
    }

    // ------------------------------------------------------------------
    // Actions
    // ------------------------------------------------------------------
    async openRecords(field, value, userId = false, day = false) {
        if (!value || field === "contracts_amount") {
            return;
        }
        const action = await this.orm.call(MODEL, "action_open_records", [
            this.state.options,
            field,
            userId,
            day,
        ]);
        await this.actionService.doAction(action);
    }

    async printPdf() {
        const action = await this.orm.call(MODEL, "action_print_pdf", [this.state.options]);
        await this.actionService.doAction(action);
    }

    async exportXlsx() {
        this.ui.block();
        try {
            await download({
                url: "/alomran/daily_activity_report/xlsx",
                data: { options: JSON.stringify(this.state.options) },
            });
        } finally {
            this.ui.unblock();
        }
    }

    openAnalysis() {
        this.actionService.doAction("alomran_implementation.alomran_daily_activity_report_action");
    }

    get isRtl() {
        return (user.lang || "").startsWith("ar");
    }
}

registry.category("actions").add("alomran_daily_activity_report", DailyActivityReport);
