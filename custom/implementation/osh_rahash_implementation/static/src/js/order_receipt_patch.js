import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { OrderReceipt } from "@point_of_sale/app/screens/receipt_screen/receipt/order_receipt";
import { parseUTCString } from "@point_of_sale/utils";
import { patch } from "@web/core/utils/patch";

const ARABIC = /[؀-ۿ]/;

// "English / عربي" -> { en: "English", ar: "عربي" }.
// الاسم بينقسم على "/" بس إذا فيه فعلاً جزء عربي وجزء غير عربي، فأسماء متل "1/2 kg" بتضل متل ما هي.
function splitName(name) {
    name = (name || "").trim();
    const parts = name.split("/").map((part) => part.trim()).filter(Boolean);
    const ar = parts.filter((part) => ARABIC.test(part));
    const en = parts.filter((part) => !ARABIC.test(part));
    if (ar.length && en.length) {
        return { en: en.join(" / "), ar: ar.join(" / ") };
    }
    return ARABIC.test(name) ? { en: "", ar: name } : { en: name, ar: "" };
}

// Patch 1: بيانات الإيصال (اسم المنتج عربي/إنجليزي، أرقام بدون عملة، التاريخ والوقت منفصلين)
patch(PosOrder.prototype, {
    export_for_printing(baseUrl, headerData) {
        const result = super.export_for_printing(baseUrl, headerData);
        const digits = this.currency?.decimal_places ?? 2;
        const partner = this.get_partner();
        result.partner_name = partner?.name || "";
        result.partner_mobile = partner?.mobile || partner?.phone || "";

        const company = headerData?.company;
        result.osh_address = [company?.street, company?.city].filter(Boolean).join(" - ");

        // date_order is UTC: convert to local time (like formatDateTime does).
        // Latin digits and AM/PM even when the POS is in Arabic
        const orderDate = parseUTCString(this.date_order)
            .setZone("default")
            .reconfigure({ locale: "en-US", numberingSystem: "latn" });
        result.osh_date = orderDate.toFormat("dd/MM/yyyy");
        result.osh_time = orderDate.toFormat("hh:mm a");

        // نفس ترتيب سطور الإيصال الأصلي (getSortedOrderlines)
        const sortedLines = this.getSortedOrderlines();
        result.orderlines = result.orderlines.map((line, index) => {
            const orderline = sortedLines[index];
            // English + Arabic names loaded from the server (osh_name_en / osh_name_ar),
            // so the receipt is bilingual even when the cashier works in Arabic
            const product = orderline?.product_id;
            const names =
                product && (product.osh_name_en || product.osh_name_ar)
                    ? { en: product.osh_name_en || "", ar: product.osh_name_ar || "" }
                    : splitName(line.productName);
            return {
                ...line,
                nameEn: names.en,
                nameAr: names.ar,
                rawUnitPrice: orderline ? orderline.get_unit_display_price().toFixed(digits) : "",
                rawTotal: orderline ? orderline.get_display_price().toFixed(digits) : "",
            };
        });

        // مجموع الكميات الفعلية (مو عدد السطور)
        const totalQty = this.lines.reduce((sum, line) => sum + (line.get_quantity() || 0), 0);
        result.total_qty = Number.isInteger(totalQty) ? String(totalQty) : totalQty.toFixed(2);
        // الصافي = الإجمالي + التقريب (إذا في تقريب نقدي)
        result.osh_net = result.taxTotals.order_total + (result.show_rounding ? result.order_rounding : 0);
        result.osh_payment_names = result.paymentlines.map((p) => p.name).join(" + ");
        return result;
    },
});

// Patch 2: تغيير الـ template
OrderReceipt.template = "osh_rahash_implementation.OrderReceipt";
