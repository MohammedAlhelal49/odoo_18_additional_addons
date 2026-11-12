import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

// حقل نصي بينكتب مباشرة من لائحة غير قابلة للتعديل (متل boolean_toggle)،
// بدون ما تنفتح الفاتورة، وبينحفظ لحاله عند الخروج من الخانة أو Enter
export class InlineCharField extends Component {
    static template = "london_laundry_implementation.InlineCharField";
    static props = { ...standardFieldProps };

    get value() {
        return this.props.record.data[this.props.name] || "";
    }

    onClick(ev) {
        // منع اللائحة من فتح السجل
        ev.target.special_click = true;
    }

    onKeydown(ev) {
        ev.stopPropagation();
        if (ev.key === "Enter") {
            ev.target.blur();
        } else if (ev.key === "Escape") {
            ev.target.value = this.value;
            ev.target.blur();
        }
    }

    async onChange(ev) {
        const newValue = ev.target.value.trim() || false;
        if (newValue !== (this.props.record.data[this.props.name] || false)) {
            await this.props.record.update({ [this.props.name]: newValue }, { save: true });
        }
    }
}

export const inlineCharField = {
    component: InlineCharField,
    displayName: _t("Inline Char"),
    supportedTypes: ["char"],
    // نفس boolean_toggle: الـ readonly حسب الـ view بس، مو حسب وضع التعديل
    extractProps(fieldInfo, dynamicInfo) {
        return { readonly: dynamicInfo.readonly };
    },
};

registry.category("fields").add("laundry_inline_char", inlineCharField);
