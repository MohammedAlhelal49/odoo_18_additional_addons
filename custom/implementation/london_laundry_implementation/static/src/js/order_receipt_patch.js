import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { OrderReceipt } from "@point_of_sale/app/screens/receipt_screen/receipt/order_receipt";
import { patch } from "@web/core/utils/patch";
import { deserializeDate, deserializeDateTime, formatDate } from "@web/core/l10n/dates";
import { formatFloat } from "@web/core/utils/numbers";
import { expectedHourLabel } from "./expected_delivery_popup";

// تفاصيل الطلب المدفوع بإيصال التحصيل وإلغائه: من الطلب المحمّل بالـ POS (وقت التحصيل)،
// أو من السيرفر (laundry_collected_details) لما ينطبع الإيصال مرة تانية
function collectedOrderDetails(payment, digits) {
    const order = payment.laundry_collected_order_id;
    let details = payment.laundry_collected_details;
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

function plainQty(qty) {
    return Number.isInteger(qty) ? String(qty) : formatFloat(qty, { digits: [69, 2] });
}

// Patch 1: بيانات الزبون والتسليم المتوقع ومجموع الكميات، وأسعار الأصناف بدون رمز العملة
patch(PosOrder.prototype, {
    export_for_printing(baseUrl, headerData) {
        const result = super.export_for_printing(baseUrl, headerData);
        const partner = this.get_partner();
        result.partner_name = partner?.name || "";
        result.partner_mobile = partner?.mobile || partner?.phone || "";
        result.expected_delivery = this.laundry_expected_delivery
            ? `${formatDate(deserializeDate(this.laundry_expected_delivery))} ${expectedHourLabel(
                  this.laundry_expected_hour
              )}`.trim()
            : "";
        // نفس ترتيب orderlines بالإيصال (getSortedOrderlines)
        const lines = this.getSortedOrderlines();
        const digits = [69, this.currency.decimal_places];
        result.orderlines = result.orderlines.map((data, index) => {
            const line = lines[index];
            return line
                ? {
                      ...data,
                      qtyPlain: plainQty(line.get_quantity()),
                      unitPricePlain: formatFloat(line.get_unit_display_price(), { digits }),
                      pricePlain: formatFloat(line.get_display_price(), { digits }),
                  }
                : data;
        });
        // الدفع على الحساب (On Credit) مو مصاري واصلة: منفصله عن المبلغ المدفوع فعلياً
        const credit = this.payment_ids
            .filter((p) => p.payment_method_id?.type === "pay_later" && !p.laundry_collected_order_id)
            .reduce((sum, p) => sum + p.get_amount(), 0);
        // سالب = تسديد دين أو إيداع (pos_settle_due): المبلغ المدفوع هو الدفعات الفعلية
        result.credit_amount = Math.max(credit, 0);
        result.paid_real = result.total_paid - credit;
        // إيصال تحصيل: الطلبات اللي اندفعت والمتبقي (بالأرقام اللي انحفظت لحظة التحصيل)
        if (this.isLaundryCollection()) {
            result.is_collection = true;
            // إلغاء تحصيل: المبالغ بترجع للزبون (منعرضها موجبة مع عنوان الإلغاء)
            result.is_collection_reversal = this.isLaundryCollectionReversal();
            result.reversed_order_name = this.laundry_reversed_order_id?.name || "";
            result.partner_balance = this.laundry_partner_balance || 0;
            result.collections = this.laundryCollectionLines().map((p) => {
                const paid = -p.get_amount();
                const due = p.laundry_collected_due || 0;
                return {
                    name: p.laundry_collected_order_id?.name || p.laundry_collected_order_name || "",
                    due,
                    paid,
                    remaining: Math.max(due - paid, 0),
                    details: collectedOrderDetails(p, [69, this.currency.decimal_places]),
                };
            });
            result.collected_total = result.collections.reduce((sum, c) => sum + c.paid, 0);
            result.collection_payments = this.payment_ids
                .filter((p) => p.payment_method_id?.type !== "pay_later" && !p.is_change)
                .map((p) => ({ name: p.payment_method_id.name, amount: p.get_amount() }));
        }
        // مجموع الكميات الفعلية (مو عدد السطور)
        // تعليق أو طي (بدل كلمة FOLD الثابتة)
        result.packing = this.laundry_packing || "";
        // (سطر أجرة التوصيل مو قطعة ملابس)
        const deliveryProduct = this.config.laundry_delivery_product_id;
        result.total_qty = plainQty(
            this.lines
                .filter((line) => !deliveryProduct || line.product_id?.id !== deliveryProduct.id)
                .reduce((sum, line) => sum + (line.get_quantity() || 0), 0)
        );
        return result;
    },
});

// Patch 2: تغيير الـ template
OrderReceipt.template = "london_laundry_implementation.OrderReceipt";
