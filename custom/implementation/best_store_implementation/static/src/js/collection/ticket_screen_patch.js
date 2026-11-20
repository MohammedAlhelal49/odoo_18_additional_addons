/** @odoo-module */
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { makeAwaitable, ask } from "@point_of_sale/app/store/make_awaitable_dialog";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { BsCollectPaymentPopup } from "./collect_payment_popup";

const CREDIT_FILTER = "BS_CREDIT";
const OWED_STATUSES = ["credit_unpaid", "credit_partial"];

function hasPayLater(order) {
    // دفعة سالبة على الحساب = تسديد دين، مو بيع على الحساب
    // أسطر التحصيل وإلغائه مربوطة بطلب: مو بيع على الحساب
    return order.payment_ids.some(
        (p) =>
            p.payment_method_id?.type === "pay_later" &&
            p.get_amount() > 0 &&
            !p.bs_collected_order_id &&
            !p.bs_collected_order_name
    );
}

// طلب على الحساب لسا ما اندفع (كامل أو جزء منه)
function isCreditOwed(order) {
    if (order.bs_collection_status) {
        return OWED_STATUSES.includes(order.bs_collection_status);
    }
    // طلب انعمل هلق بهالجلسة وما رجعت حالته من السيرفر لسا
    return hasPayLater(order);
}

// Odoo بيكتب "Paid" لكل طلب مسكّر، حتى لو انعمل على الحساب (On Credit):
// منعرض حالة التحصيل الحقيقية، ومنضيف فلتر للطلبات اللي لسا عليها مصاري.
patch(TicketScreen.prototype, {
    getStatus(order) {
        const status = super.getStatus(order);
        if (!order.finalized) {
            return status;
        }
        switch (order.bs_collection_status) {
            case "credit_unpaid":
                return _t("Unpaid");
            case "credit_partial":
                return _t("Partially Paid");
            case "credit_paid":
                return _t("Paid");
            case "collection":
                return _t("Collection");
            case "collection_cancelled":
                return _t("Collection - Cancelled");
            case "collection_reversal":
                return _t("Collection Reversal");
            case "paid":
                return status;
        }
        if (order.isBsCollectionReversal()) {
            return _t("Collection Reversal");
        }
        if (order.isBsCollection()) {
            return _t("Collection");
        }
        if (hasPayLater(order)) {
            return _t("Unpaid");
        }
        return status;
    },

    // "Paid" بيعرض كل الطلبات المسكّرة (حتى اللي على الحساب): منسمّيه "Completed"،
    // ومنضيف "Unpaid" (ما اندفعت أو اندفع جزء منها)
    _getFilterOptions() {
        const options = super._getFilterOptions();
        options.set("SYNCED", { text: _t("Completed") });
        options.set(CREDIT_FILTER, { text: _t("Unpaid") });
        return options;
    },

    async onFilterSelected(selectedFilter) {
        if (selectedFilter !== CREDIT_FILTER) {
            return super.onFilterSelected(selectedFilter);
        }
        this.state.filter = selectedFilter;
        this.state.page = 1;
        await this._fetchSyncedOrders();
    },

    async onSearch(search) {
        if (this.state.filter !== CREDIT_FILTER) {
            return super.onSearch(search);
        }
        this.state.search = search;
        this.state.page = 1;
        await this._fetchSyncedOrders();
    },

    // جلب الطلبات من السيرفر: نفس جلب "Completed" بس للطلبات اللي عليها مصاري
    _computeSyncedOrdersDomain() {
        const domain = super._computeSyncedOrdersDomain();
        if (this.state.filter === CREDIT_FILTER) {
            return [...domain, ["bs_collection_status", "in", OWED_STATUSES]];
        }
        return domain;
    },

    getFilteredOrderList() {
        if (this.state.filter !== CREDIT_FILTER) {
            return super.getFilteredOrderList();
        }
        // منعيد استعمال منطق "Completed" (البحث، الترتيب، الصفحات) على الطلبات المسكّرة
        // اللي عليها مصاري بس
        const orderModel = this.pos.models["pos.order"];
        const creditModel = {
            filter: (fn) => orderModel.filter((o) => fn(o) && isCreditOwed(o)),
        };
        const pos = Object.create(this.pos);
        pos.models = new Proxy(this.pos.models, {
            get: (target, key) => (key === "pos.order" ? creditModel : target[key]),
        });
        const view = Object.create(this, {
            pos: { value: pos },
            state: { value: { ...this.state, filter: "SYNCED" } },
        });
        return super.getFilteredOrderList.call(view);
    },

    get isOrderSynced() {
        return (
            super.isOrderSynced ||
            (this.state.filter === CREDIT_FILTER && Boolean(this.getSelectedOrder()?.finalized))
        );
    },

    // زر "Collect Payment": طلب مسكّر على الحساب ولسا عليه مصاري
    canBsCollect(order) {
        return Boolean(order?.finalized && order.get_partner() && isCreditOwed(order));
    },

    async onBsCollect(order) {
        const partner = order.get_partner();
        let result;
        try {
            result = await this.pos.data.call("pos.order", "get_bs_credit_orders", [partner.id]);
        } catch {
            this.dialog.add(AlertDialog, {
                title: _t("Collect Payment"),
                body: _t("A connection to the server is needed to collect a payment."),
            });
            return;
        }
        if (!result.orders.length) {
            this.dialog.add(AlertDialog, {
                title: _t("Collect Payment"),
                body: result.without_invoice
                    ? _t("This customer's unpaid orders have no invoice; they cannot be collected from the POS yet.")
                    : _t("Nothing is due for this customer."),
            });
            return;
        }
        const allocations = await makeAwaitable(this.dialog, BsCollectPaymentPopup, {
            partner,
            orders: result.orders,
            preselectId: order.id,
            withoutInvoice: result.without_invoice,
        });
        if (allocations?.length) {
            await this.pos.bsStartCollection(partner, allocations);
        }
    },

    // الكاشير المختار مدير (pos_hr: Advanced rights أو مدير نقطة بيع)
    get bsCashierIsManager() {
        if (this.pos.config.module_pos_hr) {
            return this.pos.get_cashier()?._role === "manager";
        }
        return true; // بلا pos_hr: السيرفر بيتحقق من صلاحية المستخدم
    },

    // زر "Cancel Collection": تحصيل غلط، بنفس الجلسة المفتوحة وقبل ما يتسكّر، وللمدير بس
    canBsCancelCollection(order) {
        return Boolean(
            this.bsCashierIsManager &&
                order?.finalized &&
                order.bs_collection_status === "collection" &&
                order.session_id?.id === this.pos.session.id
        );
    },

    async onBsCancelCollection(order) {
        let info;
        try {
            info = await this.pos.data.call("pos.order", "get_bs_collection_cancel", [
                order.id,
                this.pos.session.id,
                this.pos.config.module_pos_hr ? this.pos.get_cashier()?.id : null,
            ]);
        } catch {
            this.dialog.add(AlertDialog, {
                title: _t("Cancel Collection"),
                body: _t("A connection to the server is needed to cancel a collection."),
            });
            return;
        }
        if (info.error) {
            this.dialog.add(AlertDialog, { title: _t("Cancel Collection"), body: info.error });
            return;
        }
        const collected = -info.credit_lines.reduce((sum, l) => sum + l.amount, 0);
        const confirmed = await ask(this.dialog, {
            title: _t("Cancel Collection"),
            body: _t(
                "Cancel the collection %(order)s of %(amount)s? The money is given back to the customer " +
                    "and the orders become unpaid again.",
                { order: order.name, amount: this.env.utils.formatCurrency(collected) }
            ),
        });
        if (confirmed) {
            await this.pos.bsStartCollectionReversal(order, info);
        }
    },

    // مرتجع طلب على الحساب انحصّل منه شي: المحاسب لازم يصلّح الدفعة بعدين
    async onDoRefund() {
        const order = this.getSelectedOrder();
        if (
            order?.bs_credit_amount > 0 &&
            ["credit_partial", "credit_paid"].includes(order.bs_collection_status)
        ) {
            const confirmed = await ask(this.dialog, {
                title: _t("Refund a collected order?"),
                body: _t(
                    "Part or all of this On Credit order was already collected. " +
                        "After the refund, the accountant must fix that payment on the invoice. Continue?"
                ),
            });
            if (!confirmed) {
                return;
            }
        }
        return super.onDoRefund(...arguments);
    },
});
