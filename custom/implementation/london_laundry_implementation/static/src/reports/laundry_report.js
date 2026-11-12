/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { download } from "@web/core/network/download";
import { localization } from "@web/core/l10n/localization";
import { formatFloat, formatInteger, formatMonetary } from "@web/views/fields/formatters";

/** Amounts / numbers always read left-to-right, even inside an RTL page. */
const ltr = (value) => `\u2066${value}\u2069`;

export class LaundryReport extends Component {
    static template = "london_laundry_implementation.Report";
    static components = { Dropdown, DropdownItem };
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.ui = useService("ui");
        this.reportKey = this.props.action.params?.report || "daily";
        this.state = useState({
            filters: null,
            data: null,
            loading: false,
            unfolded: {},
            options: {
                preset: "this_month",
                month: 0,
                year: 0,
                date_from: "",
                date_to: "",
                comparison: "none",
                config_ids: [],
                cashiers: [],
                category_ids: [],
                payment_kinds: [],
                partner_search: "",
                statuses: [],
                company_ids: [],
                show: "all",
                min_due: "",
            },
        });
        onWillStart(async () => {
            this.state.filters = await this.orm.call("london.laundry.report", "get_filters", [this.reportKey]);
            this.state.options.preset = this.state.filters.default_preset || "this_month";
            this.state.options.month = this.state.filters.current_month;
            this.state.options.year = this.state.filters.current_year;
            await this.load();
        });
    }

    get isRtl() {
        return localization.direction === "rtl";
    }

    // ------------------------------------------------------------------ data
    async load() {
        const o = this.state.options;
        if (o.preset === "custom" && (!o.date_from || !o.date_to)) {
            return;
        }
        this.state.loading = true;
        try {
            this.state.data = await this.orm.call("london.laundry.report", "get_report", [this.reportKey, { ...o }]);
            if (o.preset !== "custom") {
                o.date_from = this.state.data.options.date_from;
                o.date_to = this.state.data.options.date_to;
            }
        } finally {
            this.state.loading = false;
        }
    }

    setOption(name, value) {
        this.state.options[name] = value;
        if (name !== "preset" || value !== "custom") {
            this.load();
        }
    }

    toggleInList(name, value) {
        const list = this.state.options[name];
        this.state.options[name] = list.includes(value) ? list.filter((v) => v !== value) : [...list, value];
        this.load();
    }

    clearList(name) {
        this.state.options[name] = [];
        this.load();
    }

    onSelectChange(name, ev) {
        this.setOption(name, parseInt(ev.target.value));
    }

    onTextChange(name, ev) {
        const value = ev.target.value.trim();
        if (value !== this.state.options[name]) {
            this.setOption(name, value);
        }
    }

    get showLabel() {
        const choice = this.state.filters.show_choices.find((c) => c.key === this.state.options.show);
        return choice ? choice.label : "";
    }

    onDateChange(name, ev) {
        this.state.options[name] = ev.target.value;
        if (this.state.options.preset === "custom") {
            this.load();
        }
    }

    // ------------------------------------------------------------------ labels
    get presetLabel() {
        const preset = this.state.filters.presets.find((p) => p.key === this.state.options.preset);
        return preset ? preset.label : "";
    }

    get comparisonLabel() {
        const c = this.state.filters.comparisons.find((c) => c.key === this.state.options.comparison);
        return c ? c.label : "";
    }

    listLabel(name, items, idKey, allLabel) {
        const selected = this.state.options[name];
        if (!selected.length) {
            return allLabel;
        }
        if (selected.length === 1) {
            const item = items.find((i) => i[idKey] === selected[0]);
            return item ? item.name : allLabel;
        }
        return _t("%s selected", selected.length);
    }

    // ------------------------------------------------------------------ table
    isUnfolded(line) {
        return !!this.state.unfolded[line.id];
    }

    toggleLine(line) {
        if (line.children?.length) {
            this.state.unfolded[line.id] = !this.state.unfolded[line.id];
        }
    }

    get hasChildren() {
        return this.state.data.lines.some((l) => l.children?.length);
    }

    unfoldAll(value) {
        const unfolded = {};
        if (value) {
            for (const line of this.state.data.lines) {
                if (line.children?.length) {
                    unfolded[line.id] = true;
                }
            }
        }
        this.state.unfolded = unfolded;
    }

    get visibleLines() {
        const result = [];
        for (const line of this.state.data.lines) {
            result.push(line);
            if (this.isUnfolded(line)) {
                result.push(...line.children);
            }
        }
        return result;
    }

    format(value, type) {
        if (value === null || value === undefined || value === "") {
            return "";
        }
        if (type === "money") {
            return ltr(formatMonetary(value, { currencyId: this.state.data.currency_id }));
        }
        if (type === "int") {
            return ltr(formatInteger(value));
        }
        if (type === "pct") {
            return ltr(formatFloat(value, { digits: [16, 1] }) + "%");
        }
        return String(value);
    }

    deltaClass(col, value) {
        if (col.key !== "delta" || value === null || value === undefined) {
            return "";
        }
        return value > 0.05 ? "text-success" : value < -0.05 ? "text-danger" : "text-muted";
    }

    openLine(line) {
        const a = line.action;
        if (!a) {
            return;
        }
        if (a.res_id) {
            this.action.doAction({
                type: "ir.actions.act_window",
                name: a.name,
                res_model: a.res_model,
                res_id: a.res_id,
                views: [[false, "form"]],
            });
            return;
        }
        this.action.doAction({
            type: "ir.actions.act_window",
            name: a.name,
            res_model: a.res_model,
            views: [
                [false, "list"],
                [false, "form"],
            ],
            domain: a.domain,
            context: { create: false },
        });
    }

    openUrl(url) {
        // direct user click: never blocked by the browser
        window.open(url, "_blank");
    }

    openWhatsapp(url) {
        // direct user click: never blocked by the browser
        window.open(url, "_blank");
    }

    // ------------------------------------------------------------------ exports
    get exportOptions() {
        return { ...this.state.options };
    }

    async printPdf() {
        await this.action.doAction({
            type: "ir.actions.report",
            report_type: "qweb-pdf",
            report_name: "london_laundry_implementation.report_laundry_document",
            report_file: "london_laundry_implementation.report_laundry_document",
            data: { report_key: this.reportKey, report_options: this.exportOptions },
        });
    }

    async exportXlsx() {
        this.ui.block();
        try {
            await download({
                url: "/london_laundry_implementation/report/xlsx",
                data: { report_key: this.reportKey, options: JSON.stringify(this.exportOptions) },
            });
        } finally {
            this.ui.unblock();
        }
    }
}

registry.category("actions").add("london_laundry_report", LaundryReport);
