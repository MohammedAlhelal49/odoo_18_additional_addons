import { patch } from "@web/core/utils/patch";
import { PartnerList } from "@point_of_sale/app/screens/partner_list/partner_list";
import { unaccent } from "@web/core/utils/strings";

patch(PartnerList.prototype, {
    getPartners() {
        const query = (this.state.query || "").trim().toLowerCase();
        const partners = this.pos.models["res.partner"].getAll();

        // No query → default list
        if (!query) {
            return partners
                .slice(0, 1000)
                .toSorted((a, b) =>
                    this.props.partner?.id === a.id
                        ? -1
                        : (a.name || "").localeCompare(b.name || "")
                );
        }


        const isNumber = /^\d+$/.test(query);

        if (isNumber) {
            // Numbers are stored in international format (+971 50 123 4567), so also try the
            // typed number without its 00 / 0 prefix: "0501234567" must still find "971501234567".
            const local = query.replace(/^00/, "").replace(/^0/, "");
            const matches = (digits) =>
                digits.includes(query) || (local.length >= 3 && digits.includes(local));
            return partners.filter((p) => {
                const phone = (p.phone || "").replace(/\D/g, "");
                const mobile = (p.mobile || "").replace(/\D/g, "");
                return matches(phone) || matches(mobile);
            });
        }


        const searchWord = unaccent(query, false);

        return partners.filter((p) => {
            const name = unaccent((p.name || "").toLowerCase(), false);
            return name.includes(searchWord); // sequence respected
        });
    },
});