/** @odoo-module */
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";

// الملاحظة الداخلية (Internal Note) على سطر الطلب بتنطبع بإيصال الزبون تحت المنتج
// (Odoo بيشيلها من الإيصال افتراضياً)
patch(PosOrder.prototype, {
    export_for_printing(baseUrl, headerData) {
        const result = super.export_for_printing(baseUrl, headerData);
        // نفس ترتيب orderlines بالإيصال (getSortedOrderlines)
        const lines = this.getSortedOrderlines();
        result.orderlines = result.orderlines.map((data, index) => ({
            ...data,
            bsNote: (lines[index]?.getNote?.() || lines[index]?.note || "").trim(),
        }));
        // بيانات الزبون تحت اسمه بالإيصال: الهاتف، لوحة السيارة، سيريال السيارة
        const partner = this.get_partner();
        result.bsPartnerPhone = partner?.mobile || partner?.phone || "";
        result.bsCarPlate = partner?.car_plate_number || "";
        result.bsCarSerial = partner?.car_serial_number || "";
        return result;
    },
});
