import { Component, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { _t } from "@web/core/l10n/translation";
import { formatDateTime } from "@web/core/l10n/dates";
import { parseUTCString } from "@point_of_sale/utils";
import { roundPrecision } from "@web/core/utils/numbers";

// نافذة "Collect Payment": طلبات الزبون اللي عليها مصاري، الكاشير بيعلّم شو بدو يحصّل
// والمبلغ لكل طلب (افتراضياً المتبقي، وفيه ينقّصه: الدفع الجزئي مسموح)
export class CollectPaymentPopup extends Component {
    static template = "london_laundry_implementation.CollectPaymentPopup";
    static components = { Dialog };
    static props = {
        partner: Object,
        orders: Array,
        preselectId: { type: Number, optional: true },
        withoutInvoice: { type: Number, optional: true },
        getPayload: Function,
        close: Function,
    };

    setup() {
        this.pos = usePos();
        this.state = useState({
            error: "",
            rows: this.props.orders.map((order) => ({
                ...order,
                selected: order.id === this.props.preselectId,
                amount: order.remaining,
            })),
        });
    }

    formatCurrency(amount) {
        return this.env.utils.formatCurrency(amount);
    }

    formatDate(value) {
        return formatDateTime(parseUTCString(value));
    }

    round(amount) {
        return roundPrecision(Number(amount) || 0, this.pos.currency.rounding);
    }

    get selectedRows() {
        return this.state.rows.filter((row) => row.selected);
    }

    get total() {
        return this.selectedRows.reduce((sum, row) => sum + this.round(row.amount), 0);
    }

    toggleAll(ev) {
        for (const row of this.state.rows) {
            row.selected = ev.target.checked;
        }
    }

    confirm() {
        const rows = this.selectedRows;
        if (!rows.length) {
            this.state.error = _t("Select at least one order.");
            return;
        }
        for (const row of rows) {
            const amount = this.round(row.amount);
            if (amount <= 0) {
                this.state.error = _t("Enter an amount for %s.", row.name);
                return;
            }
            if (amount - row.remaining > this.pos.currency.rounding / 2) {
                this.state.error = _t("%(order)s: the amount is more than the remaining %(due)s.", {
                    order: row.name,
                    due: this.formatCurrency(row.remaining),
                });
                return;
            }
        }
        this.props.getPayload(
            rows.map((row) => ({ id: row.id, amount: this.round(row.amount), due: row.remaining }))
        );
        this.props.close();
    }
}
