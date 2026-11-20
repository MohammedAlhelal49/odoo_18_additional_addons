/** @odoo-module */
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

// أرقام الهاتف بدون رموز ومسافات، وبدون مفتاح الدولة أو الصفر بأولها:
// "+971 50 123 4567" و "0501234567" بيصيروا "501234567"
function phoneDigits(value) {
    return String(value || "").replace(/\D/g, "").replace(/^(00971|971|0+)/, "");
}

function partnerPhones(order) {
    const partner = order.get_partner();
    return [partner?.phone, partner?.mobile].filter(Boolean);
}

// البحث بقائمة الطلبات: برقم هاتف الزبون، ولوحة السيارة، وسيريال السيارة
patch(TicketScreen.prototype, {
    _getSearchFields() {
        const fields = super._getSearchFields();
        fields.BS_PHONE = {
            repr: (order) =>
                partnerPhones(order)
                    .flatMap((phone) => [phone, phoneDigits(phone), "0" + phoneDigits(phone)])
                    .join(" "),
            displayName: _t("Customer Phone"),
            // حقل بحث أودو بيتجاهل المسافات والرموز بأرقام الهاتف والموبايل
            modelField: "partner_id.phone_mobile_search",
            formatSearch: (searchTerm) => phoneDigits(searchTerm) || searchTerm,
        };
        fields.BS_CAR_PLATE = {
            repr: (order) => order.get_partner()?.car_plate_number || "",
            displayName: _t("Car Plate Number"),
            modelField: "partner_id.car_plate_number",
        };
        fields.BS_CAR_SERIAL = {
            repr: (order) => order.get_partner()?.car_serial_number || "",
            displayName: _t("Car Serial Number"),
            modelField: "partner_id.car_serial_number",
        };
        return fields;
    },

    bsPartnerPhone(order) {
        return partnerPhones(order)[0] || "";
    },
});
