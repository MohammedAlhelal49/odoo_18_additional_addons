/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { ResPartner } from "@point_of_sale/app/models/res_partner";
import { PartnerList } from "@point_of_sale/app/screens/partner_list/partner_list";

const CAR_FIELDS = ["car_plate_number", "car_serial_number"];

function normalize(value) {
    return String(value || "").replace(/\s+/g, "").toLowerCase();
}

patch(ResPartner.prototype, {
    // Local search (customers already loaded in the POS): name, phone, mobile, ...
    // plus car plate and car serial number.
    get searchString() {
        const carValues = CAR_FIELDS.map((field) => this[field] || "").filter(Boolean);
        return [super.searchString, ...carValues].filter(Boolean).join(" ");
    },

    // An exact plate / serial number shows only that customer.
    exactMatch(searchWord) {
        const word = normalize(searchWord);
        if (word && CAR_FIELDS.some((field) => this[field] && normalize(this[field]) === word)) {
            return true;
        }
        return super.exactMatch(searchWord);
    },
});

patch(PartnerList.prototype, {
    // Server search ("Search more"): name, phone/mobile, car plate, car serial number.
    async getNewPartners() {
        if (!this.state.query) {
            return super.getNewPartners();
        }
        const query = this.state.query.trim();
        const search_fields = [
            "name",
            "parent_name",
            "phone_mobile_search",
            "email",
            "barcode",
            ...CAR_FIELDS,
        ];
        const domain = [
            ...Array(search_fields.length - 1).fill("|"),
            ...search_fields.map((field) => [field, "ilike", query]),
        ];
        return await this.pos.data.searchRead("res.partner", domain, [], {
            limit: 30,
            offset: this.state.currentOffset,
        });
    },
});
