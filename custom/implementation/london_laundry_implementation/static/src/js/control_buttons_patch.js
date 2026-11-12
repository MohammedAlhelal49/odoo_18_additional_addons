import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { makeAwaitable } from "@point_of_sale/app/store/make_awaitable_dialog";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { deserializeDate, formatDate } from "@web/core/l10n/dates";
import { SelectionPopup } from "@point_of_sale/app/utils/input_popups/selection_popup";
import { ExpectedDeliveryPopup, expectedHourLabel } from "./expected_delivery_popup";
// pay() هون لازم يلفّ pay() تبع أجرة التوصيل: الاختيارات أول، بعدين قاعدة التوصيل المجاني
import "./delivery_charge";

// تعليق أو طي: كيف بترجع الملابس للزبون (نفس قيم laundry_packing بالسيرفر)
export const PACKING_LABELS = {
    hanger: _t("Hanger"),
    fold: _t("Fold"),
};

// اختيارات المغسلة: طريقة التوصيل وتعليق/طي (إجباريين قبل الدفع)، والتسليم المتوقع
patch(PosStore.prototype, {
    // true = انختار، false = لغى الكاشير
    async laundryChooseDeliveryMethod(order) {
        const current = order.laundry_delivery_method_id;
        const list = this.models["london.delivery.method"].getAll().map((method) => ({
            id: method.id,
            label: method.name,
            item: method,
            isSelected: current?.id === method.id,
        }));
        const payload = await makeAwaitable(this.dialog, SelectionPopup, {
            title: _t("Delivery Method"),
            list,
        });
        if (payload === undefined) {
            return false;
        }
        order.update({ laundry_delivery_method_id: payload });
        // توصيل بأجرة: سطر "توصيل" + سعره (واختيار نفس الطريقة مرة تانية بيعدّل السعر)
        await this.laundrySyncDeliveryCharge(order);
        return true;
    },

    async laundryChoosePacking(order) {
        const list = Object.entries(PACKING_LABELS).map(([value, label]) => ({
            id: value,
            label,
            item: value,
            isSelected: order.laundry_packing === value,
        }));
        const payload = await makeAwaitable(this.dialog, SelectionPopup, {
            title: _t("Hanger or Fold"),
            list,
        });
        if (payload === undefined) {
            return false;
        }
        order.laundry_packing = payload;
        return true;
    },

    // قبل الدفع: طلب بيع (مو تحصيل ولا مرتجع) لازم يكون فيه طريقة توصيل وتعليق/طي
    async laundryEnsureOrderChoices(order) {
        if (!order || order.isLaundryCollection() || !order.lines.length || order.get_total_with_tax() < 0) {
            return true;
        }
        if (!order.laundry_delivery_method_id && !(await this.laundryChooseDeliveryMethod(order))) {
            return false;
        }
        if (!order.laundry_packing && !(await this.laundryChoosePacking(order))) {
            return false;
        }
        return true;
    },

    async pay() {
        if (!(await this.laundryEnsureOrderChoices(this.get_order()))) {
            return;
        }
        return super.pay(...arguments);
    },
});

// أزرار Actions: التسليم المتوقع، طريقة التوصيل، تعليق/طي
patch(ControlButtons.prototype, {
    get expectedDeliveryLabel() {
        const order = this.pos.get_order();
        const value = order?.laundry_expected_delivery;
        return value
            ? `${formatDate(deserializeDate(value))} ${expectedHourLabel(order.laundry_expected_hour)}`.trim()
            : "";
    },

    async clickExpectedDelivery() {
        const order = this.pos.get_order();
        if (!order) {
            return;
        }
        const payload = await makeAwaitable(this.dialog, ExpectedDeliveryPopup, {
            title: _t("Expected Delivery"),
            startingValue: order.laundry_expected_delivery || false,
            startingHour: order.laundry_expected_hour || false,
        });
        if (payload !== undefined) {
            order.laundry_expected_delivery = payload.date;
            order.laundry_expected_hour = payload.hour;
        }
    },

    get deliveryMethodLabel() {
        return this.pos.get_order()?.laundry_delivery_method_id?.name || "";
    },

    async clickDeliveryMethod() {
        const order = this.pos.get_order();
        if (order) {
            await this.pos.laundryChooseDeliveryMethod(order);
        }
    },

    get packingLabel() {
        return PACKING_LABELS[this.pos.get_order()?.laundry_packing] || "";
    },

    async clickPacking() {
        const order = this.pos.get_order();
        if (order) {
            await this.pos.laundryChoosePacking(order);
        }
    },
});
