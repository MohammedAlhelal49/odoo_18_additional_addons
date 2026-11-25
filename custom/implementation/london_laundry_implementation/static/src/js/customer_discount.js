import { PosStore } from "@point_of_sale/app/store/pos_store";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";
import { makeAwaitable } from "@point_of_sale/app/store/make_awaitable_dialog";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { parseFloat } from "@web/views/fields/parsers";
import { roundPrecision } from "@web/core/utils/numbers";
// laundrySetFinalPrice / laundryItemsTotal (التوصيل) و laundryPrepaidInfo (الرصيد المسبق)
import "./delivery_charge";
import "./prepaid_patch";

// خصم الزبون التلقائي: سطر "خصم الزبون" سالب على الطلب، نسبة من الملابس أو مبلغ ثابت على كل طلب.
// - الملابس بس (مش التوصيل)، وما بيتعدّى قيمة الملابس.
// - ما بينطبق على زبون إله قائمة أسعار خاصة، ولا على زبون إله رصيد مسبق (اشتراك).
// - المدير بس بيقدر يعدّله أو يشيله على طلب معيّن (Actions > Customer Discount).
// - المرتجع بيرجّع حصّة القطع المرتجعة من الخصم لحاله (بالنسبة): الزبون ما بياخد أكتر من اللي دفعه.

patch(PosStore.prototype, {
    laundryDiscountLines(order) {
        const product = this.config.laundry_customer_discount_product_id;
        return product ? order.lines.filter((line) => line.product_id?.id === product.id) : [];
    },

    // حد التوصيل المجاني بينحسب على الملابس قبل الخصم
    laundryItemsTotal(order) {
        const discount = this.laundryDiscountLines(order).reduce((sum, l) => sum + l.get_price_with_tax(), 0);
        return super.laundryItemsTotal(order) - discount;
    },

    // الرصيد المسبق لكل زبون (آخر قيمة من السيرفر): الزبون المشترك ما إله خصم
    laundryPrepaidCache(partner) {
        this._laundryPrepaid = this._laundryPrepaid || {};
        return this._laundryPrepaid[partner.id];
    },

    async laundryRefreshPrepaid(partner) {
        if (!partner?.laundry_discount_type || !this.laundryPrepaidMethod("balance")) {
            return;
        }
        const info = await this.laundryPrepaidInfo(partner);
        if (!info.error) {
            this._laundryPrepaid = this._laundryPrepaid || {};
            this._laundryPrepaid[partner.id] = info.balance;
        }
    },

    // مبلغ الخصم (شامل الضريبة) حسب بطاقة الزبون، أو 0
    laundryCustomerDiscountAmount(order) {
        const partner = order.get_partner();
        const value = partner?.laundry_discount_value || 0;
        if (!partner?.laundry_discount_type || value <= 0 || !order.lines.length) {
            return 0;
        }
        if (order.isLaundryCollection() || order.isLaundryPrepaidMove()) {
            return 0;
        }
        // زبون بأسعار خاصة: الخصم للأسعار العادية بس
        if (this.config.pricelist_id && order.pricelist_id && order.pricelist_id.id !== this.config.pricelist_id.id) {
            return 0;
        }
        if ((this.laundryPrepaidCache(partner) || 0) > this.currency.rounding / 2) {
            return 0;
        }
        const base = this.laundryItemsTotal(order);
        if (base <= 0) {
            return 0;
        }
        const amount =
            partner.laundry_discount_type === "percent" ? (base * Math.min(value, 100)) / 100 : Math.min(value, base);
        return roundPrecision(amount, this.currency.rounding);
    },

    async laundrySetCustomerDiscount(order, amount) {
        const product = this.config.laundry_customer_discount_product_id;
        if (!product) {
            return;
        }
        const lines = this.laundryDiscountLines(order);
        if (amount <= this.currency.rounding / 2) {
            for (const line of lines) {
                order.removeOrderline(line);
            }
            return;
        }
        for (const extra of lines.slice(1)) {
            order.removeOrderline(extra);
        }
        let line = lines[0];
        if (!line) {
            this._laundryAddingDiscount = true;
            try {
                line = await this.addLineToOrder({ product_id: product, qty: 1 }, order, {}, false);
            } finally {
                this._laundryAddingDiscount = false;
            }
        }
        if (line) {
            this.laundrySetFinalPrice(line, -amount);
        }
    },

    async laundryApplyCustomerDiscount(order) {
        if (!order || order.finalized || order.laundry_discount_override || order.get_total_with_tax() < 0) {
            return;
        }
        const amount = this.laundryCustomerDiscountAmount(order);
        const current = -this.laundryDiscountLines(order).reduce((sum, l) => sum + l.get_price_with_tax(), 0);
        if (Math.abs(amount - current) > this.currency.rounding / 2) {
            await this.laundrySetCustomerDiscount(order, amount);
        }
    },

    // المرتجع: حصّة الخصم من كل طلب أصلي = خصمه × (الملابس المرتجعة ÷ ملابسه)، بسطر "خصم الزبون" موجب
    async laundryApplyRefundDiscount(order) {
        const product = this.config.laundry_customer_discount_product_id;
        if (!product || !order) {
            return;
        }
        const delivery = this.config.laundry_delivery_product_id;
        const isDiscount = (line) => line.product_id?.id === product.id;
        const isClothes = (line) => !isDiscount(line) && (!delivery || line.product_id?.id !== delivery.id);
        // سطر الحصّة اللي حطّيناه قبل (مش مرتجع سطر خصم): منعيد حسابه
        for (const line of order.lines.filter((l) => isDiscount(l) && !l.refunded_orderline_id)) {
            order.removeOrderline(line);
        }
        const byOrder = new Map();
        for (const line of order.lines) {
            const original = line.refunded_orderline_id?.order_id;
            if (original) {
                byOrder.set(original, [...(byOrder.get(original) || []), line]);
            }
        }
        let share = 0;
        for (const [original, refundLines] of byOrder) {
            // الكاشير اختار سطر الخصم بنفسه: ما منزيد حصّة لهالطلب
            if (refundLines.some(isDiscount)) {
                continue;
            }
            const discount = -original.lines.filter(isDiscount).reduce((sum, l) => sum + l.get_price_with_tax(), 0);
            const clothes = original.lines.filter(isClothes).reduce((sum, l) => sum + l.get_price_with_tax(), 0);
            const refunded = -refundLines.filter(isClothes).reduce((sum, l) => sum + l.get_price_with_tax(), 0);
            if (discount > 0 && clothes > 0 && refunded > 0) {
                share += (discount * Math.min(refunded, clothes)) / clothes;
            }
        }
        share = roundPrecision(share, this.currency.rounding);
        if (share <= this.currency.rounding / 2) {
            return;
        }
        this._laundryAddingDiscount = true;
        let line;
        try {
            line = await this.addLineToOrder({ product_id: product, qty: 1 }, order, {}, false);
        } finally {
            this._laundryAddingDiscount = false;
        }
        if (line) {
            this.laundrySetFinalPrice(line, share);
        }
    },

    async addLineToOrder(vals, order, opts = {}, configure = true) {
        const line = await super.addLineToOrder(...arguments);
        if (!this._laundryAddingDiscount && line) {
            await this.laundryApplyCustomerDiscount(order || this.get_order());
        }
        return line;
    },

    async selectPartner() {
        const result = await super.selectPartner(...arguments);
        const order = this.get_order();
        if (order?.get_partner()) {
            await this.laundryRefreshPrepaid(order.get_partner());
        }
        await this.laundryApplyCustomerDiscount(order);
        return result;
    },

    // قبل الدفع: الأصناف ممكن تكون تغيّرت، والرصيد المسبق من السيرفر هلق
    async pay() {
        const order = this.get_order();
        if (order?.get_partner()) {
            await this.laundryRefreshPrepaid(order.get_partner());
        }
        await this.laundryApplyCustomerDiscount(order);
        // مرتجع: الكميات ممكن تكون تغيّرت بعد ما انعمل
        if (order?.lines.some((l) => l.refunded_orderline_id)) {
            await this.laundryApplyRefundDiscount(order);
        }
        return super.pay(...arguments);
    },
});

patch(TicketScreen.prototype, {
    postRefund(destinationOrder) {
        super.postRefund(...arguments);
        this.pos.laundryApplyRefundDiscount(destinationOrder);
    },
});

patch(ControlButtons.prototype, {
    get laundryDiscountLabel() {
        const order = this.pos.get_order();
        if (!order) {
            return "";
        }
        const amount = -this.pos.laundryDiscountLines(order).reduce((sum, l) => sum + l.get_price_with_tax(), 0);
        return amount > 0 ? this.env.utils.formatCurrency(amount) : "";
    },

    // المدير بس: يعدّل خصم الزبون على هالطلب أو يشيله (0)
    async clickLaundryCustomerDiscount() {
        const order = this.pos.get_order();
        if (!order) {
            return;
        }
        if (this.pos.config.module_pos_hr && this.pos.get_cashier()?._role !== "manager") {
            this.dialog.add(AlertDialog, {
                title: _t("Customer Discount"),
                body: _t("Only a manager can change the customer discount of an order."),
            });
            return;
        }
        const current = -this.pos.laundryDiscountLines(order).reduce((sum, l) => sum + l.get_price_with_tax(), 0);
        const payload = await makeAwaitable(this.dialog, NumberPopup, {
            title: _t("Customer Discount"),
            subtitle: _t("Amount VAT included, on the clothes only. 0 = no discount."),
            startingValue: current > 0 ? String(current) : "",
            confirmButtonLabel: _t("Apply"),
        });
        if (payload === undefined) {
            return;
        }
        const base = this.pos.laundryItemsTotal(order);
        const amount = Math.min(Math.max(parseFloat(payload || "0") || 0, 0), Math.max(base, 0));
        order.laundry_discount_override = true;
        await this.pos.laundrySetCustomerDiscount(order, roundPrecision(amount, this.pos.currency.rounding));
    },
});
