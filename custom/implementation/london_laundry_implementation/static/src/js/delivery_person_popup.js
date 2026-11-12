import { Component, onMounted, useRef, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

// مين وصّل الطلب: كتابة حرّة مع اقتراحات الأسماء اللي انكتبت قبل (الاسم الجديد بينضاف لحاله)
export class DeliveryPersonPopup extends Component {
    static template = "london_laundry_implementation.DeliveryPersonPopup";
    static components = { Dialog };
    static props = {
        title: String,
        names: Array,
        startingValue: { type: String, optional: true },
        getPayload: Function,
        close: Function,
    };

    setup() {
        this.state = useState({ name: this.props.startingValue || "" });
        this.inputRef = useRef("input");
        onMounted(() => this.inputRef.el.focus());
    }

    // اقتراحات حسب اللي عم ينكتب (بالـ datalist ما بتطلع منيح على شاشات اللمس)
    get suggestions() {
        const typed = this.state.name.trim().toLowerCase();
        return this.props.names
            .filter((name) => !typed || (name.toLowerCase().includes(typed) && name.toLowerCase() !== typed))
            .slice(0, 8);
    }

    pick(name) {
        this.state.name = name;
        this.confirm();
    }

    confirm() {
        this.props.getPayload(this.state.name.trim());
        this.props.close();
    }

    clear() {
        this.props.getPayload("");
        this.props.close();
    }
}
