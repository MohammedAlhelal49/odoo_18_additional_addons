import { Component, onMounted, useRef, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

// ساعات التسليم (بدون دقائق): نفس قيم الحقل laundry_expected_hour بالسيرفر
export const EXPECTED_HOURS = Array.from({ length: 24 }, (_, hour) => String(hour).padStart(2, "0"));

export function expectedHourLabel(hour) {
    return hour ? `${hour}:00` : "";
}

// نافذة اختيار التسليم المتوقع: التاريخ + الساعة (اختيارية، بدون دقائق)
export class ExpectedDeliveryPopup extends Component {
    static template = "london_laundry_implementation.ExpectedDeliveryPopup";
    static components = { Dialog };
    static props = {
        title: String,
        startingValue: { type: [String, { value: false }], optional: true },
        startingHour: { type: [String, { value: false }], optional: true },
        getPayload: Function,
        close: Function,
    };

    setup() {
        // قيمة حقل Date بالـ POS بصيغة yyyy-MM-dd، نفس صيغة <input type="date">
        this.state = useState({
            inputValue: this.props.startingValue || "",
            hour: this.props.startingHour || "",
        });
        this.hours = EXPECTED_HOURS.map((hour) => ({ value: hour, label: expectedHourLabel(hour) }));
        this.inputRef = useRef("input");
        onMounted(() => this.inputRef.el.focus());
    }

    confirm() {
        const date = this.state.inputValue || false;
        // ساعة بلا تاريخ ما إلها معنى
        this.props.getPayload({ date, hour: (date && this.state.hour) || false });
        this.props.close();
    }

    clear() {
        this.props.getPayload({ date: false, hour: false });
        this.props.close();
    }
}
