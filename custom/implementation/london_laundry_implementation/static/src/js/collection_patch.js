import { PosStore } from "@point_of_sale/app/store/pos_store";
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

// تحصيل دين على طلب (On Credit): طلب فاضي بدون أصناف وبدون فاتورة، فيه سطر On Credit سالب
// لكل طلب عم يندفع (مربوط فيه) + الدفع الفعلي (كاش / فيزا / تحويل) من شاشة الدفع العادية.
// عند إغلاق الجلسة كل سطر بيتطابق مع فاتورة طلبه (pos.session بالسيرفر).
// إلغاء تحصيل (بنفس الجلسة): طلب معاكس، On Credit موجب لكل طلب + المصاري بترجع بنفس الطريقة.

patch(PosOrder.prototype, {
    isLaundryCollection() {
        return (
            Boolean(this.laundry_is_collection) ||
            this.payment_ids.some((p) => p.laundry_collected_order_id || p.laundry_collected_order_name)
        );
    },

    isLaundryCollectionReversal() {
        return Boolean(this.laundry_reversed_order_id);
    },

    laundryCollectionLines() {
        return this.payment_ids.filter(
            (p) => p.laundry_collected_order_id || p.laundry_collected_order_name
        );
    },
});

patch(PosStore.prototype, {
    // allocations: [{ id: طلب On Credit, amount: المبلغ المحصّل, due: المتبقي قبل التحصيل }]
    async laundryStartCollection(partner, allocations) {
        const creditMethod = this.config.payment_method_ids.find((m) => m.type === "pay_later");
        if (!creditMethod) {
            this.dialog.add(AlertDialog, {
                title: _t("Collect Payment"),
                body: _t("This point of sale has no customer account (On Credit) payment method."),
            });
            return;
        }
        // الطلبات الأصلية لازم تكون محمّلة بالـ POS حتى ينربط فيها سطر الدفع
        await this.data.read("pos.order", allocations.map((a) => a.id));
        const order = this.add_new_order();
        order.set_partner(partner);
        order.set_to_invoice(false);
        for (const allocation of allocations) {
            const line = this.models["pos.payment"].create({
                pos_order_id: order,
                payment_method_id: creditMethod,
                laundry_collected_order_id: this.models["pos.order"].get(allocation.id),
                laundry_collected_due: allocation.due,
            });
            line.set_amount(-allocation.amount);
        }
        this.showScreen("PaymentScreen", { orderUuid: order.uuid });
    },

    // info: نتيجة get_laundry_collection_cancel (الدفعات اللي لازم تنعكس)
    async laundryStartCollectionReversal(original, info) {
        await this.data.read("pos.order", [...new Set(info.credit_lines.map((l) => l.target_id))]);
        const order = this.add_new_order();
        order.set_partner(original.get_partner());
        order.set_to_invoice(false);
        order.update({ laundry_reversed_order_id: original });
        for (const credit of info.credit_lines) {
            const line = this.models["pos.payment"].create({
                pos_order_id: order,
                payment_method_id: this.models["pos.payment.method"].get(credit.method_id),
                laundry_collected_order_id: this.models["pos.order"].get(credit.target_id),
                laundry_collected_due: credit.due,
                laundry_reversed_payment_id: this.models["pos.payment"].get(credit.id),
            });
            line.set_amount(-credit.amount);
        }
        for (const payment of info.payments) {
            const line = this.models["pos.payment"].create({
                pos_order_id: order,
                payment_method_id: this.models["pos.payment.method"].get(payment.method_id),
            });
            line.set_amount(-payment.amount);
        }
        this.showScreen("PaymentScreen", { orderUuid: order.uuid });
    },

    // طلب التحصيل ما بيقبل أصناف
    async addLineToOrder(vals, order, opts = {}, configure = true) {
        if (order?.isLaundryCollection()) {
            this.notification.add(_t("A collection cannot contain products. Start a new order."), {
                type: "warning",
            });
            return;
        }
        return super.addLineToOrder(...arguments);
    },
});

patch(PaymentScreen.prototype, {
    get laundryIsCollection() {
        return Boolean(this.currentOrder?.isLaundryCollection());
    },

    get laundryIsReversal() {
        return Boolean(this.currentOrder?.isLaundryCollectionReversal());
    },

    // إلغاء التحصيل: كل الأسطر ثابتة (نفس مبالغ التحصيل الأصلي بالعكس)
    _laundryLineLocked(line) {
        return Boolean(line?.laundry_collected_order_id || (line && this.laundryIsReversal));
    },

    _laundryLockedNotice() {
        this.notification.add(
            _t("Collection lines are fixed. Discard this order and start the collection again to change them."),
            { type: "warning" }
        );
    },

    async addNewPaymentLine(paymentMethod) {
        if (this.laundryIsReversal) {
            this._laundryLockedNotice();
            return false;
        }
        if (this.laundryIsCollection && paymentMethod.type === "pay_later") {
            this.notification.add(_t("A collection must be paid with cash, card or transfer."), {
                type: "warning",
            });
            return false;
        }
        return super.addNewPaymentLine(...arguments);
    },

    updateSelectedPaymentline(amount = false) {
        if (this.laundryIsReversal || this._laundryLineLocked(this.selectedPaymentLine)) {
            this.numberBuffer.reset();
            this._laundryLockedNotice();
            return;
        }
        return super.updateSelectedPaymentline(...arguments);
    },

    deletePaymentLine(uuid) {
        const line = this.paymentLines.find((l) => l.uuid === uuid);
        if (this._laundryLineLocked(line)) {
            this._laundryLockedNotice();
            return;
        }
        return super.deletePaymentLine(...arguments);
    },

    async _isOrderValid(isForceValidate) {
        if (this.laundryIsCollection && !(await this._laundryCheckCollection())) {
            return false;
        }
        return super._isOrderValid(...arguments);
    },

    // قبل Validate: المتبقي من السيرفر هلق (ممكن كاشير تاني حصّل نفس الطلب بهالوقت)
    async _laundryCheckCollection() {
        const order = this.currentOrder;
        const alert = (body) => {
            this.dialog.add(AlertDialog, { title: _t("Collect Payment"), body });
            return false;
        };
        if (order.lines.length) {
            return alert(_t("A collection cannot contain products."));
        }
        order.set_to_invoice(false);
        const lines = order.laundryCollectionLines();
        let result;
        try {
            if (order.isLaundryCollectionReversal()) {
                const check = await this.pos.data.call("pos.order", "get_laundry_collection_cancel", [
                    order.laundry_reversed_order_id.id,
                    this.pos.session.id,
                    this.pos.config.module_pos_hr ? this.pos.get_cashier()?.id : null,
                ]);
                if (check.error) {
                    return alert(check.error);
                }
            }
            result = await this.pos.data.call(
                "pos.order",
                "get_laundry_credit_orders",
                [order.partner_id.id],
                { order_ids: lines.map((l) => l.laundry_collected_order_id.id) }
            );
        } catch {
            return alert(_t("A connection to the server is needed to check the remaining amounts."));
        }
        const remaining = new Map(result.orders.map((o) => [o.id, o.remaining]));
        const rounding = this.pos.currency.rounding;
        for (const line of lines) {
            if (line.get_amount() > 0) {
                continue; // إلغاء تحصيل: الدين بيرجع، ما في حد أعلى
            }
            const target = line.laundry_collected_order_id;
            const due = remaining.get(target.id) || 0;
            if (-line.get_amount() - due > rounding / 2) {
                return alert(
                    _t("%(order)s: only %(due)s is still due. Discard this order and start the collection again.", {
                        order: target.name,
                        due: this.env.utils.formatCurrency(due),
                    })
                );
            }
            line.laundry_collected_due = due;
        }
        // رصيد الزبون بعد هالعملية (كل طلباته)، بينحفظ على الطلب للإيصال
        const moved = lines.reduce((sum, l) => sum + l.get_amount(), 0);
        order.laundry_partner_balance = Math.max((result.total_due || 0) + moved, 0);
        return true;
    },
});
