import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { deserializeDate, deserializeDateTime, formatDate } from "@web/core/l10n/dates";
import { makeAwaitable, ask } from "@point_of_sale/app/store/make_awaitable_dialog";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { CollectPaymentPopup } from "./collect_payment_popup";
import { expectedHourLabel } from "./expected_delivery_popup";
import { SelectionPopup } from "@point_of_sale/app/utils/input_popups/selection_popup";

// الرفوف بالمحل: من 1 لـ 9 (نفس SHELVES بالسيرفر)
const SHELVES = ["1", "2", "3", "4", "5", "6", "7", "8", "9"];

const CREDIT_FILTER = "LAUNDRY_CREDIT";
const OWED_STATUSES = ["credit_unpaid", "credit_partial"];

function hasPayLater(order) {
    // دفعة سالبة على الحساب = تسديد دين (pos_settle_due)، مو بيع على الحساب
    // أسطر التحصيل وإلغائه مربوطة بطلب: مو بيع على الحساب
    return order.payment_ids.some(
        (p) =>
            p.payment_method_id?.type === "pay_later" &&
            p.get_amount() > 0 &&
            !p.laundry_collected_order_id &&
            !p.laundry_collected_order_name
    );
}

// طلب على الحساب لسا ما اندفع (كامل أو جزء منه)
function isCreditOwed(order) {
    if (order.laundry_collection_status) {
        return OWED_STATUSES.includes(order.laundry_collection_status);
    }
    // طلب انعمل هلق بهالجلسة وما رجعت حالته من السيرفر لسا
    return hasPayLater(order);
}

// Odoo بيكتب "Paid" لكل طلب مسكّر، حتى لو انعمل على الحساب (On Credit):
// منعرض حالة التحصيل الحقيقية، ومنضيف فلتر للطلبات اللي لسا عليها مصاري.
// للكاشير بس Paid / Partially Paid / Unpaid (الباك إند بيضل يميّز "On Credit - …" للمحاسب).
patch(TicketScreen.prototype, {
    getStatus(order) {
        const status = super.getStatus(order);
        if (!order.finalized) {
            return status;
        }
        // الطلبات اللي جاية من السيرفر فيها الحالة محسوبة (بتتبع دفع الفاتورة)
        switch (order.laundry_collection_status) {
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
        if (order.isLaundryCollectionReversal()) {
            return _t("Collection Reversal");
        }
        if (order.isLaundryCollection()) {
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
            return [...domain, ["laundry_collection_status", "in", OWED_STATUSES]];
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

    // تلوين السطر متل لائحة الفواتير: أزرق = مسلّم ومدفوع، أخضر = مسلّم ومو مدفوع،
    // أحمر = مو مسلّم ومو مدفوع، أصفر = مدفوع ولسا ما تسلّم. السطر المختار بيضل بلون Odoo.
    getLaundryRowClass(order) {
        const highlighted = this.isHighlighted(order);
        const status = order.laundry_collection_status;
        if (highlighted || !order.finalized || !status || status.startsWith("collection")) {
            return { "highlight bg-primary text-white": highlighted };
        }
        const paid = status === "paid" || status === "credit_paid";
        const delivered = Boolean(order.laundry_delivered);
        return {
            "lry-row-blue": delivered && paid,
            "lry-row-green": delivered && !paid,
            "lry-row-red": !delivered && !paid,
            "lry-row-yellow": !delivered && paid,
        };
    },

    // رقم الزبون بعمود Customer: الموبايل، وإلا الهاتف
    getLaundryPartnerPhone(order) {
        const partner = order.partner_id;
        return partner ? partner.mobile || partner.phone || "" : "";
    },

    // أعمدة المغسلة: الرف والتسليم من الفاتورة، والتسليم المتوقع من الطلب
    getLaundryShelf(order) {
        return order.laundry_shelf || "";
    },

    getLaundryExpectedDelivery(order) {
        return order.laundry_expected_delivery
            ? formatDate(deserializeDate(order.laundry_expected_delivery))
            : "";
    },

    // الساعة بسطر تاني تحت التاريخ (العمود ضيّق)
    getLaundryExpectedHour(order) {
        return order.laundry_expected_delivery ? expectedHourLabel(order.laundry_expected_hour) : "";
    },

    // التاريخ بس (الوقت موجود على الفاتورة بالباك إند)
    getLaundryDeliveryDate(order) {
        return order.laundry_delivery_datetime
            ? formatDate(deserializeDateTime(order.laundry_delivery_datetime))
            : "";
    },

    get isOrderSynced() {
        return (
            super.isOrderSynced ||
            (this.state.filter === CREDIT_FILTER && Boolean(this.getSelectedOrder()?.finalized))
        );
    },

    // زر "Collect Payment": طلب مسكّر على الحساب ولسا عليه مصاري
    canLaundryCollect(order) {
        return Boolean(order?.finalized && order.get_partner() && isCreditOwed(order));
    },

    async onLaundryCollect(order) {
        const partner = order.get_partner();
        let result;
        try {
            result = await this.pos.data.call("pos.order", "get_laundry_credit_orders", [partner.id]);
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
        const allocations = await makeAwaitable(this.dialog, CollectPaymentPopup, {
            partner,
            orders: result.orders,
            preselectId: order.id,
            withoutInvoice: result.without_invoice,
        });
        if (allocations?.length) {
            await this.pos.laundryStartCollection(partner, allocations);
        }
    },

    // طلب بيع مسكّر وإله فاتورة (account.move مو محمّل بالـ POS: رقم الفاتورة بـ raw متل Reprint Invoice)
    laundryIsInvoicedSale(order) {
        return Boolean(order?.finalized && order.raw?.account_move && !order.isLaundryCollection());
    },

    laundryAlert(title, body) {
        this.dialog.add(AlertDialog, { title, body });
    },

    // زر "WhatsApp Ready": رسالة "الطلب جاهز" للزبون (واتساب ويب بنافذة جديدة)
    canLaundryWhatsappReady(order) {
        return Boolean(order?.finalized && order.partner_id && !order.isLaundryCollection());
    },

    async onLaundryWhatsappReady(order) {
        // النافذة بتنفتح فوراً (قبل الانتظار) حتى المتصفح ما يمنعها كـ popup
        const win = window.open("", "_blank");
        let result;
        try {
            result = await this.pos.data.call("pos.order", "get_laundry_ready_whatsapp", [order.id]);
        } catch {
            win?.close();
            return this.laundryAlert(_t("WhatsApp"), _t("A connection to the server is needed to send the message."));
        }
        if (result.error) {
            win?.close();
            return this.laundryAlert(_t("WhatsApp"), result.error);
        }
        if (win) {
            win.location.href = result.url;
        } else {
            window.open(result.url, "_blank");
        }
    },

    // زر "Shelf": رقم الرف من 1 لـ 9 (بينحفظ على الفاتورة)
    canLaundrySetShelf(order) {
        return this.laundryIsInvoicedSale(order);
    },

    async onLaundrySetShelf(order) {
        const current = order.laundry_shelf || "";
        const list = [...SHELVES.map((shelf) => ({ id: shelf, label: shelf, item: shelf, isSelected: shelf === current })),
            { id: "clear", label: _t("No shelf"), item: "", isSelected: !current }];
        const shelf = await makeAwaitable(this.dialog, SelectionPopup, { title: _t("Shelf"), list });
        if (shelf === undefined) {
            return;
        }
        let result;
        try {
            result = await this.pos.data.call("pos.order", "set_laundry_shelf", [order.id, shelf || false]);
        } catch {
            return this.laundryAlert(_t("Shelf"), _t("A connection to the server is needed to save the shelf."));
        }
        if (result.error) {
            return this.laundryAlert(_t("Shelf"), result.error);
        }
        await this.pos.data.read("pos.order", [order.id]);
    },

    // زر "Delivered": الطلب تسلّم، والكاشير اللي ضغط الزر هو اللي سلّمه
    canLaundryMarkDelivered(order) {
        return this.laundryIsInvoicedSale(order) && !order.laundry_delivered;
    },

    async onLaundryMarkDelivered(order) {
        const cashier = this.pos.get_cashier();
        // نفس تنبيه الباك إند: الطلب لسا عليه مصاري (التسليم مسموح)
        const due = order.laundry_credit_remaining || 0;
        const body = due > this.pos.currency.rounding / 2
            ? _t("%(order)s still has %(due)s to pay. Collect the payment before handing over the clothes. Deliver anyway?",
                  { order: order.name, due: this.env.utils.formatCurrency(due) })
            : _t("Mark %(order)s as delivered by %(cashier)s?", { order: order.name, cashier: cashier?.name || "" });
        const confirmed = await ask(this.dialog, {
            title: due > this.pos.currency.rounding / 2 ? _t("Unpaid order") : _t("Delivered"),
            body,
            confirmLabel: _t("Delivered"),
        });
        if (!confirmed) {
            return;
        }
        let result;
        try {
            result = await this.pos.data.call("pos.order", "set_laundry_delivered", [
                order.id,
                this.pos.config.module_pos_hr ? cashier?.id || null : null,
            ]);
        } catch {
            return this.laundryAlert(_t("Delivered"), _t("A connection to the server is needed to save the delivery."));
        }
        if (result.error) {
            return this.laundryAlert(_t("Delivered"), result.error);
        }
        await this.pos.data.read("pos.order", [order.id]);
    },

    // الكاشير المختار مدير (pos_hr: Advanced rights أو مدير نقطة بيع)
    get laundryCashierIsManager() {
        if (this.pos.config.module_pos_hr) {
            return this.pos.get_cashier()?._role === "manager";
        }
        return true; // بلا pos_hr: السيرفر بيتحقق من صلاحية المستخدم
    },

    // زر "Cancel Collection": تحصيل غلط، بنفس الجلسة المفتوحة وقبل ما يتسكّر، وللمدير بس
    canLaundryCancelCollection(order) {
        return Boolean(
            this.laundryCashierIsManager &&
                order?.finalized &&
                order.laundry_collection_status === "collection" &&
                order.session_id?.id === this.pos.session.id
        );
    },

    async onLaundryCancelCollection(order) {
        let info;
        try {
            info = await this.pos.data.call("pos.order", "get_laundry_collection_cancel", [
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
            await this.pos.laundryStartCollectionReversal(order, info);
        }
    },

    // مرتجع طلب على الحساب انحصّل منه شي: المحاسب لازم يصلّح الدفعة بعدين
    async onDoRefund() {
        const order = this.getSelectedOrder();
        if (
            order?.laundry_credit_amount > 0 &&
            ["credit_partial", "credit_paid"].includes(order.laundry_collection_status)
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
