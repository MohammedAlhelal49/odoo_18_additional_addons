/** @odoo-module */
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";
import { deserializeDateTime, formatDate } from "@web/core/l10n/dates";
import { formatFloat } from "@web/core/utils/numbers";

function plainQty(qty) {
    return Number.isInteger(qty) ? String(qty) : formatFloat(qty, { digits: [69, 2] });
}

// تفاصيل الطلب المدفوع بإيصال التحصيل وإلغائه: من الطلب المحمّل بالـ POS (وقت التحصيل)،
// أو من السيرفر (bs_collected_details) لما ينطبع الإيصال مرة تانية
function collectedOrderDetails(payment, digits) {
    const order = payment.bs_collected_order_id;
    let details = payment.bs_collected_details;
    if (order?.lines?.length) {
        details = {
            date: order.date_order,
            total: order.amount_total,
            lines: order.lines.map((line) => ({
                name: line.full_product_name || line.product_id?.display_name || "",
                qty: line.qty,
                price_unit: line.qty ? line.get_price_with_tax() / line.qty : 0,
                price: line.get_price_with_tax(),
            })),
        };
    }
    if (!details) {
        return null;
    }
    return {
        date: details.date ? formatDate(deserializeDateTime(details.date)) : "",
        total: details.total || 0,
        lines: (details.lines || []).map((line) => ({
            name: line.name,
            qtyPlain: plainQty(line.qty),
            unitPricePlain: formatFloat(line.price_unit, { digits }),
            pricePlain: formatFloat(line.price, { digits }),
        })),
    };
}

// إيصال تحصيل (أو إلغاء تحصيل): الطلبات اللي اندفعت والمتبقي، بالأرقام اللي انحفظت لحظة التحصيل
patch(PosOrder.prototype, {
    export_for_printing(baseUrl, headerData) {
        const result = super.export_for_printing(baseUrl, headerData);
        if (!this.isBsCollection()) {
            return result;
        }
        const digits = [69, this.currency.decimal_places];
        result.is_collection = true;
        result.is_collection_reversal = this.isBsCollectionReversal();
        result.reversed_order_name = this.bs_reversed_order_id?.name || "";
        result.partner_balance = this.bs_partner_balance || 0;
        result.collections = this.bsCollectionLines().map((p) => {
            const paid = -p.get_amount();
            const due = p.bs_collected_due || 0;
            return {
                name: p.bs_collected_order_id?.name || p.bs_collected_order_name || "",
                due,
                paid,
                remaining: Math.max(due - paid, 0),
                details: collectedOrderDetails(p, digits),
            };
        });
        result.collected_total = result.collections.reduce((sum, c) => sum + c.paid, 0);
        // الدفع الفعلي بس (كاش / فيزا / تحويل)، بدون أسطر On Credit المربوطة بالطلبات
        result.collection_payments = this.payment_ids
            .filter((p) => p.payment_method_id?.type !== "pay_later" && !p.is_change)
            .map((p) => ({ name: p.payment_method_id.name, amount: p.get_amount() }));
        result.paymentlines = [];
        return result;
    },
});
