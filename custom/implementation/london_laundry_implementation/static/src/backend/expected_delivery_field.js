import { Component, xml } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { formatDate } from "@web/core/l10n/dates";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

// التسليم المتوقع بعمود واحد بلائحة الفواتير: التاريخ + الساعة ("30/10/2026 15:00").
// الحقلين بيضلّوا منفصلين بالداتابيز (الترتيب والفلاتر على التاريخ)، العرض بس موحّد.
export class ExpectedDeliveryListField extends Component {
    static template = xml`<span class="text-nowrap" t-esc="text"/>`;
    static props = { ...standardFieldProps };

    get text() {
        const date = this.props.record.data[this.props.name];
        if (!date) {
            return "";
        }
        const hour = this.props.record.data.laundry_expected_hour;
        return hour ? `${formatDate(date)} ${hour}:00` : formatDate(date);
    }
}

registry.category("fields").add("laundry_expected_delivery", {
    component: ExpectedDeliveryListField,
    supportedTypes: ["date"],
    fieldDependencies: [{ name: "laundry_expected_hour", type: "selection" }],
});
