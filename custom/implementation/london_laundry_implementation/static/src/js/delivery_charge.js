import { PosStore } from "@point_of_sale/app/store/pos_store";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";
import { makeAwaitable, ask } from "@point_of_sale/app/store/make_awaitable_dialog";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { parseFloat } from "@web/views/fields/parsers";
import { roundPrecision } from "@web/core/utils/numbers";

// أجرة التوصيل: لما الكاشير يختار طريقة توصيل بأجرة (Home Delivery) بينضاف سطر "توصيل"
// وبينفتح الـ numpad لسعره (شامل الضريبة، متل الأسعار اللي بيشوفها). بيتشال لما يرجع لـ Store Pickup.
// التوصيل مجاني للطلبات من "Free Delivery From" (50) وطالع، وتحتها الطلب مع التوصيل ما بيتعدّى هالمبلغ.

patch(PosStore.prototype, {
    laundryDeliveryLines(order) {
        const product = this.config.laundry_delivery_product_id;
        return product ? order.lines.filter((line) => line.product_id?.id === product.id) : [];
    },

    // مجموع الأصناف (بدون التوصيل)، شامل الضريبة
    laundryItemsTotal(order) {
        const deliveryLines = new Set(this.laundryDeliveryLines(order));
        return order.lines
            .filter((line) => !deliveryLines.has(line))
            .reduce((sum, line) => sum + line.get_price_with_tax(), 0);
    },

    // أعلى أجرة توصيل مسموحة: 0 = مجاني، null = ما في قاعدة
    laundryDeliveryCap(order) {
        const limit = this.config.laundry_free_delivery_from || 0;
        if (limit <= 0) {
            return null;
        }
        return Math.max(roundPrecision(limit - this.laundryItemsTotal(order), this.currency.rounding), 0);
    },

    // قبل الدفع (والأصناف ممكن تكون تغيّرت): منشيل التوصيل إذا صار مجاني، ومنقلّله إذا تعدّى الحد
    laundryApplyDeliveryRule(order) {
        const lines = this.laundryDeliveryLines(order);
        const cap = this.laundryDeliveryCap(order);
        if (!lines.length || cap === null) {
            return;
        }
        const charge = this.laundryDeliveryCharge(order);
        if (cap <= 0) {
            for (const line of lines) {
                order.removeOrderline(line);
            }
            this.notification.add(_t("Free delivery: the order is %s or more.", this.env.utils.formatCurrency(this.config.laundry_free_delivery_from)), { type: "info" });
        } else if (charge - cap > this.currency.rounding / 2) {
            for (const extra of lines.slice(1)) {
                order.removeOrderline(extra);
            }
            this.laundrySetFinalPrice(lines[0], cap);
            this.notification.add(
                _t("Delivery reduced to %s: the order with delivery cannot exceed %s.",
                    this.env.utils.formatCurrency(cap),
                    this.env.utils.formatCurrency(this.config.laundry_free_delivery_from)),
                { type: "info" }
            );
        }
    },

    async pay() {
        const order = this.get_order();
        if (order && !order.isLaundryCollection()) {
            this.laundryApplyDeliveryRule(order);
        }
        return super.pay(...arguments);
    },

    laundryDeliveryCharge(order) {
        return this.laundryDeliveryLines(order).reduce((sum, line) => sum + line.get_price_with_tax(), 0);
    },

    // السعر اللي بيكتبه الكاشير نهائي (مع الضريبة): منحسب السعر قبل الضريبة اللي بيعطيه بالضبط
    laundrySetFinalPrice(line, total) {
        line.price_type = "manual";
        line.set_unit_price(total);
        const withTax = line.get_all_prices(1).priceWithTax;
        if (!total || !withTax || withTax === total) {
            return;
        }
        const rounding = this.currency.rounding;
        const base = (total * total) / withTax;
        // سعر الوحدة بخانتين: منجرّب الأقرب حتى يطلع المجموع نفس الرقم المكتوب
        for (const candidate of [base, base - rounding, base + rounding]) {
            line.set_unit_price(roundPrecision(candidate, rounding));
            if (roundPrecision(line.get_all_prices(1).priceWithTax, rounding) === roundPrecision(total, rounding)) {
                return;
            }
        }
        line.set_unit_price(roundPrecision(base, rounding));
    },

    async laundrySyncDeliveryCharge(order) {
        const product = this.config.laundry_delivery_product_id;
        if (!product || order.isLaundryCollection()) {
            return;
        }
        const lines = this.laundryDeliveryLines(order);
        if (!order.laundry_delivery_method_id?.laundry_with_charge) {
            for (const line of lines) {
                order.removeOrderline(line);
            }
            return;
        }
        const cap = this.laundryDeliveryCap(order);
        if (cap === 0) {
            // الطلب من 50 وطالع: التوصيل مجاني، ما في سطر ولا سعر
            for (const line of lines) {
                order.removeOrderline(line);
            }
            this.notification.add(
                _t("Free delivery: the order is %s or more.", this.env.utils.formatCurrency(this.config.laundry_free_delivery_from)),
                { type: "info" }
            );
            return;
        }
        const current = lines.length ? this.laundryDeliveryCharge(order) : "";
        const payload = await makeAwaitable(this.dialog, NumberPopup, {
            title: _t("Delivery Price"),
            subtitle:
                cap === null
                    ? _t("VAT included")
                    : _t("VAT included - at most %s (order with delivery up to %s)",
                          this.env.utils.formatCurrency(cap),
                          this.env.utils.formatCurrency(this.config.laundry_free_delivery_from)),
            startingValue: current ? String(current) : "",
            confirmButtonLabel: _t("Apply"),
        });
        if (payload === undefined) {
            return; // إلغاء: منترك السطر متل ما هو (وقت الدفع بيسأل إذا التوصيل مجاني)
        }
        let total = Math.max(parseFloat(payload || "0") || 0, 0);
        if (cap !== null && total - cap > this.currency.rounding / 2) {
            total = cap;
            this.notification.add(
                _t("Delivery reduced to %s: the order with delivery cannot exceed %s.",
                    this.env.utils.formatCurrency(cap),
                    this.env.utils.formatCurrency(this.config.laundry_free_delivery_from)),
                { type: "info" }
            );
        }
        let line = lines[0];
        for (const extra of lines.slice(1)) {
            order.removeOrderline(extra);
        }
        if (!line) {
            line = await this.addLineToOrder({ product_id: product, qty: 1 }, order, {}, false);
        }
        if (line) {
            this.laundrySetFinalPrice(line, total);
        }
    },
});

patch(PaymentScreen.prototype, {
    // طلب توصيل بدون أجرة: الكاشير بيأكّد إنه التوصيل مجاني
    async _isOrderValid(isForceValidate) {
        const order = this.currentOrder;
        const method = order.laundry_delivery_method_id;
        if (
            method?.laundry_with_charge &&
            this.pos.config.laundry_delivery_product_id &&
            !order.isLaundryCollection() &&
            this.pos.laundryDeliveryCharge(order) <= 0 &&
            this.pos.laundryDeliveryCap(order) !== 0
        ) {
            const confirmed = await ask(this.dialog, {
                title: _t("Free delivery?"),
                body: _t(
                    "This order is %(method)s with no delivery charge. Deliver it for free?",
                    { method: method.name }
                ),
                confirmLabel: _t("Yes, free delivery"),
                cancelLabel: _t("No, add the price"),
            });
            if (!confirmed) {
                return false;
            }
        }
        return super._isOrderValid(...arguments);
    },
});
