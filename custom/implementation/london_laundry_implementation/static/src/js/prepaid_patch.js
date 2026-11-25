import { PosStore } from "@point_of_sale/app/store/pos_store";
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";
import { makeAwaitable, ask } from "@point_of_sale/app/store/make_awaitable_dialog";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { parseFloat } from "@web/views/fields/parsers";
import { roundPrecision } from "@web/core/utils/numbers";
// _laundryLineLocked وفحص التحصيل قبل Validate من هون
import "./collection_patch";

// رصيد الغسيل المسبق (شحن مع بونص، والدفع من الرصيد)
// طلب الشحن: بلا أصناف وبلا فاتورة، فيه "Laundry Balance" سالب (الرصيد بيزيد بالمبلغ + البونص)
// و"Prepaid Bonus" موجب بقيمة البونص، والزبون بيدفع المبلغ كاش / فيزا / تحويل من شاشة الدفع.
// الدفع من الرصيد: "Laundry Balance" موجب على أي طلب بيع، لحد الرصيد الموجود.

patch(PosOrder.prototype, {
    laundryPrepaidLines(role) {
        return this.payment_ids.filter((p) => p.payment_method_id?.laundry_prepaid_role === role);
    },

    isLaundryTopup() {
        return (
            Boolean(this.laundry_is_topup) ||
            (!this.lines.length && this.laundryPrepaidLines("balance").some((p) => p.get_amount() < 0))
        );
    },

    // أي حركة على الرصيد بلا أصناف: شحن، إلغاء شحن، استرجاع رصيد
    isLaundryPrepaidMove() {
        return Boolean(this.laundry_is_prepaid_move) || (!this.lines.length && this.laundryPrepaidLines("balance").length > 0);
    },

    isLaundryTopupReversal() {
        return Boolean(this.laundry_reversed_order_id) && this.isLaundryPrepaidMove();
    },

    isLaundryBalanceRefund() {
        return this.isLaundryPrepaidMove() && !this.isLaundryTopup() && !this.laundry_reversed_order_id;
    },

    // Odoo ما بيبعت للسيرفر طلب بلا أصناف إلا إذا فيه On Credit: حركات الرصيد لازم تنبعت كمان
    get hasItemsOrPayLater() {
        return super.hasItemsOrPayLater || this.isLaundryPrepaidMove();
    },

    // المبلغ اللي انزاد عالرصيد (شحن) أو اندفع منه (بيع، موجب)
    laundryPrepaidMoved() {
        return this.laundryPrepaidLines("balance").reduce((sum, p) => sum + p.get_amount(), 0);
    },
});

patch(PosStore.prototype, {
    laundryPrepaidMethod(role) {
        return this.config.payment_method_ids.find((m) => m.laundry_prepaid_role === role);
    },

    // رصيد الزبون (والبونص على المبلغ إذا انبعت) من السيرفر
    async laundryPrepaidInfo(partner, amount) {
        try {
            return await this.data.call(
                "pos.order",
                "get_laundry_prepaid_info",
                [partner.id, this.config.id],
                amount === undefined ? {} : { amount }
            );
        } catch {
            return { error: _t("A connection to the server is needed to read the prepaid balance.") };
        }
    },

    laundryPrepaidAlert(body) {
        this.dialog.add(AlertDialog, { title: _t("Prepaid Balance"), body });
    },

    async laundryStartTopup() {
        const current = this.get_order();
        const partner = current?.get_partner();
        if (!partner) {
            return this.laundryPrepaidAlert(_t("Select the customer first, then top up their balance."));
        }
        const balanceMethod = this.laundryPrepaidMethod("balance");
        const bonusMethod = this.laundryPrepaidMethod("bonus");
        if (!balanceMethod || !bonusMethod) {
            return this.laundryPrepaidAlert(
                _t("The prepaid balance payment methods are not added to this point of sale.")
            );
        }
        const info = await this.laundryPrepaidInfo(partner);
        if (info.error) {
            return this.laundryPrepaidAlert(info.error);
        }
        const fmt = (amount) => this.env.utils.formatCurrency(amount);
        const payload = await makeAwaitable(this.dialog, NumberPopup, {
            title: _t("Top Up Balance"),
            subtitle: _t("%(name)s - balance %(balance)s - %(percent)s bonus from %(min)s", {
                name: partner.name,
                balance: fmt(info.balance),
                percent: `${info.bonus_percent}%`,
                min: fmt(info.bonus_min),
            }),
            confirmButtonLabel: _t("Next"),
        });
        if (payload === undefined) {
            return;
        }
        const amount = roundPrecision(parseFloat(payload || "0") || 0, this.currency.rounding);
        if (amount <= 0) {
            return;
        }
        const check = await this.laundryPrepaidInfo(partner, amount);
        if (check.error) {
            return this.laundryPrepaidAlert(check.error);
        }
        const bonus = check.bonus || 0;
        const credited = amount + bonus;
        const confirmed = await ask(this.dialog, {
            title: _t("Top Up Balance"),
            body: bonus
                ? _t("%(name)s pays %(amount)s and gets %(bonus)s bonus: %(credited)s added to the balance. New balance: %(after)s.", {
                      name: partner.name,
                      amount: fmt(amount),
                      bonus: fmt(bonus),
                      credited: fmt(credited),
                      after: fmt(check.balance + credited),
                  })
                : _t("%(name)s pays %(amount)s (no bonus below %(min)s). New balance: %(after)s.", {
                      name: partner.name,
                      amount: fmt(amount),
                      min: fmt(check.bonus_min),
                      after: fmt(check.balance + credited),
                  }),
            confirmLabel: _t("Continue to payment"),
        });
        if (!confirmed) {
            return;
        }
        // طلب جديد للشحن (الطلب الحالي بيضل متل ما هو)
        const order = current.lines.length || current.payment_ids.length ? this.add_new_order() : current;
        order.set_partner(partner);
        order.set_to_invoice(false);
        this.models["pos.payment"]
            .create({ pos_order_id: order, payment_method_id: balanceMethod })
            .set_amount(-credited);
        if (bonus) {
            this.models["pos.payment"]
                .create({ pos_order_id: order, payment_method_id: bonusMethod })
                .set_amount(bonus);
        }
        order.laundry_prepaid_balance = check.balance + credited;
        this.showScreen("PaymentScreen", { orderUuid: order.uuid });
    },

    // info: نتيجة get_laundry_topup_cancel (الدفعات اللي لازم تنعكس، صافي لكل طريقة)
    async laundryStartTopupReversal(original, info) {
        const order = this.add_new_order();
        order.set_partner(original.get_partner());
        order.set_to_invoice(false);
        order.update({ laundry_reversed_order_id: original });
        for (const payment of info.payments) {
            this.models["pos.payment"]
                .create({ pos_order_id: order, payment_method_id: this.models["pos.payment.method"].get(payment.method_id) })
                .set_amount(-payment.amount);
        }
        this.showScreen("PaymentScreen", { orderUuid: order.uuid });
    },

    // استرجاع الرصيد (للمدير): الزبون بياخد الباقي من المصاري اللي دفعها، والبونص بيروح
    async laundryStartBalanceRefund() {
        const current = this.get_order();
        const partner = current?.get_partner();
        if (!partner) {
            return this.laundryPrepaidAlert(_t("Select the customer first."));
        }
        if (this.config.module_pos_hr && this.get_cashier()?._role !== "manager") {
            return this.laundryPrepaidAlert(_t("Only a manager can refund a prepaid balance."));
        }
        let info;
        try {
            info = await this.data.call("pos.order", "get_laundry_prepaid_refund", [
                partner.id,
                this.config.id,
                this.config.module_pos_hr ? this.get_cashier()?.id : null,
            ]);
        } catch {
            info = { error: _t("A connection to the server is needed to read the prepaid balance.") };
        }
        if (info.error) {
            return this.laundryPrepaidAlert(info.error);
        }
        const fmt = (amount) => this.env.utils.formatCurrency(amount);
        const confirmed = await ask(this.dialog, {
            title: _t("Refund Balance"),
            body: _t(
                "%(name)s has %(balance)s, of which %(bonus)s is bonus. The bonus is not refunded: give back %(refund)s. The balance becomes 0.",
                { name: partner.name, balance: fmt(info.balance), bonus: fmt(info.bonus_left), refund: fmt(info.refundable) }
            ),
            confirmLabel: _t("Continue to payment"),
        });
        if (!confirmed) {
            return;
        }
        const order = current.lines.length || current.payment_ids.length ? this.add_new_order() : current;
        order.set_partner(partner);
        order.set_to_invoice(false);
        this.models["pos.payment"]
            .create({ pos_order_id: order, payment_method_id: this.laundryPrepaidMethod("balance") })
            .set_amount(info.balance);
        if (info.bonus_left) {
            this.models["pos.payment"]
                .create({ pos_order_id: order, payment_method_id: this.laundryPrepaidMethod("bonus") })
                .set_amount(-info.bonus_left);
        }
        this.showScreen("PaymentScreen", { orderUuid: order.uuid });
    },

    // حركات الرصيد ما بتقبل أصناف
    async addLineToOrder(vals, order, opts = {}, configure = true) {
        if (order?.isLaundryPrepaidMove()) {
            this.notification.add(_t("A prepaid balance operation cannot contain products. Start a new order."), {
                type: "warning",
            });
            return;
        }
        return super.addLineToOrder(...arguments);
    },
});

patch(ControlButtons.prototype, {
    async clickLaundryTopup() {
        await this.pos.laundryStartTopup();
    },

    async clickLaundryRefundBalance() {
        await this.pos.laundryStartBalanceRefund();
    },
});

patch(PaymentScreen.prototype, {
    setup() {
        super.setup(...arguments);
        // البونص بينحط لحاله على طلب الشحن، ما بيختاره الكاشير
        this.payment_methods_from_config = this.payment_methods_from_config.filter(
            (m) => m.laundry_prepaid_role !== "bonus"
        );
    },

    get laundryIsPrepaidMove() {
        return Boolean(this.currentOrder?.isLaundryPrepaidMove());
    },

    _laundryLineLocked(line) {
        return Boolean(
            super._laundryLineLocked(line) ||
                (line?.payment_method_id?.laundry_prepaid_role && this.laundryIsPrepaidMove)
        );
    },

    async addNewPaymentLine(paymentMethod) {
        const order = this.currentOrder;
        const role = paymentMethod.laundry_prepaid_role;
        if (this.laundryIsPrepaidMove && (role || paymentMethod.type === "pay_later")) {
            this.notification.add(_t("Use cash, card or transfer for the money of a prepaid balance operation."), {
                type: "warning",
            });
            return false;
        }
        if (role !== "balance") {
            return super.addNewPaymentLine(...arguments);
        }
        if (order.isLaundryCollection()) {
            this.notification.add(_t("A collection cannot be paid from the prepaid balance."), {
                type: "warning",
            });
            return false;
        }
        const partner = order.get_partner();
        if (!partner) {
            this.notification.add(_t("Select the customer to pay from their prepaid balance."), {
                type: "warning",
            });
            return false;
        }
        const info = await this.pos.laundryPrepaidInfo(partner);
        if (info.error) {
            this.pos.laundryPrepaidAlert(info.error);
            return false;
        }
        const rounding = this.pos.currency.rounding;
        const available = roundPrecision(info.balance - order.laundryPrepaidMoved(), rounding);
        if (available <= rounding / 2) {
            this.notification.add(
                _t("%(name)s has no prepaid balance left (%(balance)s).", {
                    name: partner.name,
                    balance: this.env.utils.formatCurrency(info.balance),
                }),
                { type: "warning" }
            );
            return false;
        }
        const due = order.get_due();
        const result = await super.addNewPaymentLine(...arguments);
        if (result && due > available) {
            this.selectedPaymentLine?.set_amount(available);
            this.notification.add(
                _t("Only %s in the balance: pay the rest with another method.", this.env.utils.formatCurrency(available)),
                { type: "info" }
            );
        }
        return result;
    },

    async _isOrderValid(isForceValidate) {
        const order = this.currentOrder;
        const usesBalance = order.laundryPrepaidLines("balance").length > 0;
        if (usesBalance && !(await this._laundryCheckPrepaid())) {
            return false;
        }
        return super._isOrderValid(...arguments);
    },

    // قبل Validate: الرصيد من السيرفر هلق (ممكن انصرف من جهاز تاني)، ورصيد الزبون بعد الطلب للإيصال
    async _laundryCheckPrepaid() {
        const order = this.currentOrder;
        const alert = (body) => {
            this.pos.laundryPrepaidAlert(body);
            return false;
        };
        const partner = order.get_partner();
        if (!partner) {
            return alert(_t("Select the customer to pay from their prepaid balance."));
        }
        if (order.isLaundryPrepaidMove()) {
            if (order.lines.length) {
                return alert(_t("A prepaid balance operation cannot contain products."));
            }
            order.set_to_invoice(false);
        }
        const info = await this.pos.laundryPrepaidInfo(partner);
        if (info.error) {
            return alert(info.error);
        }
        const moved = order.laundryPrepaidMoved();
        const rounding = this.pos.currency.rounding;
        // استرجاع: كل الرصيد بيطلع، والبونص اللي ضمنه بينخصم (إذا تغيّر الرصيد من جهاز تاني منعيد)
        if (order.isLaundryBalanceRefund()) {
            const bonus = -order.laundryPrepaidLines("bonus").reduce((sum, p) => sum + p.get_amount(), 0);
            if (Math.abs(moved - info.balance) > rounding / 2 || Math.abs(bonus - info.bonus_left) > rounding / 2) {
                return alert(_t("The customer's balance changed. Discard this order and start the refund again."));
            }
        }
        if (moved - info.balance > rounding / 2) {
            return alert(
                _t("%(name)s has only %(balance)s in the prepaid balance.", {
                    name: partner.name,
                    balance: this.env.utils.formatCurrency(info.balance),
                })
            );
        }
        order.laundry_prepaid_balance = roundPrecision(info.balance - moved, rounding);
        return true;
    },
});
