import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { patch } from "@web/core/utils/patch";

// The default customer is put on every new order, and Odoo only sets the customer of the
// refunded order on a refund order without customer: the refund stayed on the default customer.
patch(TicketScreen.prototype, {
    _getEmptyOrder(partner) {
        const defaultPartner = this.pos.config.default_partner_id;
        if (partner && defaultPartner && partner.id !== defaultPartner.id) {
            const empty = this.pos.models["pos.order"].find(
                (order) =>
                    !order.finalized &&
                    !order.get_orderlines().length &&
                    !order.payment_ids.length &&
                    (!order.get_partner() || order.get_partner().id === defaultPartner.id)
            );
            if (empty) {
                return empty;
            }
        }
        return super._getEmptyOrder(...arguments);
    },

    setPartnerToRefundOrder(partner, destinationOrder) {
        const defaultPartner = this.pos.config.default_partner_id;
        if (partner && defaultPartner && destinationOrder.get_partner()?.id === defaultPartner.id) {
            destinationOrder.set_partner(partner);
            return;
        }
        return super.setPartnerToRefundOrder(...arguments);
    },
});
