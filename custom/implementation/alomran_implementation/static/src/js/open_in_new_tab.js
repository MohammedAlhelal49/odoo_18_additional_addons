/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";

/**
 * Small "open in new tab" button usable in list / kanban / form views.
 *
 *   <widget name="open_in_new_tab"/>                       -> current record
 *   <widget name="open_in_new_tab" options="{'model_field': 'res_model', 'id_field': 'res_id'}"/>
 *                                                          -> linked document
 *
 * It renders a real <a target="_blank"> link: the browser opens the tab
 * natively (no popup blocker, middle-click / ctrl+click also work). The click
 * is only stopped from bubbling so the list row / kanban card is not opened
 * in the current tab as well.
 */
export class OpenInNewTab extends Component {
    static template = "alomran_implementation.OpenInNewTab";
    static props = {
        ...standardWidgetProps,
        modelField: { type: String, optional: true },
        idField: { type: String, optional: true },
    };

    get target() {
        const record = this.props.record;
        let model = record.resModel;
        let resId = record.resId;
        if (this.props.modelField) {
            model = record.data[this.props.modelField];
        }
        if (this.props.idField) {
            const value = record.data[this.props.idField];
            resId = Array.isArray(value) ? value[0] : value;
        }
        // model names only contain letters, digits, "_" and "."
        if (!model || !/^[\w.]+$/.test(model) || !Number.isInteger(resId) || resId <= 0) {
            return null;
        }
        return { model, resId };
    }

    get url() {
        const target = this.target;
        return target ? `/odoo/${target.model}/${target.resId}` : null;
    }

    onClick(ev) {
        ev.stopPropagation();
    }
}

registry.category("view_widgets").add("open_in_new_tab", {
    component: OpenInNewTab,
    listViewWidth: 40,
    extractProps: ({ options }) => ({
        modelField: options.model_field,
        idField: options.id_field,
    }),
});
