import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { OrderReceipt } from "@point_of_sale/app/screens/receipt_screen/receipt/order_receipt";
import { patch } from "@web/core/utils/patch";

// Patch 1: إضافة بيانات الزبون
patch(PosOrder.prototype, {
    export_for_printing(baseUrl, headerData) {
        const result = super.export_for_printing(baseUrl, headerData);
        const partner = this.get_partner();
        result.partner_name = partner?.name || "";
        result.partner_mobile = partner?.mobile || partner?.phone || "";
        result.invoice_name = this.account_move_name || "";

        // أضف qty + tax + price_inc_vat لكل سطر
        const digits = this.currency?.decimal_places ?? 2;
        const sortedLines = this.getSortedOrderlines();
        result.orderlines = result.orderlines.map((line, index) => {
            const originalLine = sortedLines[index];
            const qty = originalLine ? parseFloat(originalLine.get_quantity().toFixed(2)) : parseFloat(line.qty);
            const taxAmount = originalLine ? originalLine.get_tax() : 0;
            const priceIncVat = originalLine ? originalLine.get_price_with_tax() : 0;
            const unitPrice = originalLine ? originalLine.get_all_prices(1).priceWithoutTax : 0;
            return {
                ...line,
                rawQty: String(qty),
                rawUnitPrice: unitPrice.toFixed(digits),
                rawTax: taxAmount.toFixed(digits),
                rawPriceIncVat: priceIncVat.toFixed(digits),
            };
        });

        return result;
    },
});

// Patch 2: تغيير الـ template مع الاحتفاظ بكل الـ methods (omit, doesAnyOrderlineHaveTaxLabel)
OrderReceipt.template = "the_best_store_pos_receipt.OrderReceipt";
