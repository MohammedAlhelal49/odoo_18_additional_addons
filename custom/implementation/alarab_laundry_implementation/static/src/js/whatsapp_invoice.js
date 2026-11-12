/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { InvoiceButton } from "@point_of_sale/app/screens/ticket_screen/invoice_button/invoice_button";

patch(PosStore.prototype, {
    /** Open a WhatsApp Web link; if the browser blocks it, ask for a click. */
    alarabOpenWhatsapp(url) {
        if (!url) {
            return;
        }
        const win = window.open(url, "_blank");
        if (!win || win.closed || typeof win.closed === "undefined") {
            this.dialog.add(ConfirmationDialog, {
                title: _t("WhatsApp"),
                body: _t("Your browser blocked the WhatsApp window. Click the button to open it."),
                confirmLabel: _t("Open WhatsApp"),
                confirm: () => window.open(url, "_blank"),
                cancelLabel: _t("Skip"),
                cancel: () => {},
            });
        }
    },
    async alarabOpenWhatsappInvoice(orderId) {
        if (typeof orderId !== "number") {
            return;
        }
        let url = false;
        try {
            url = await this.data.call("pos.order", "get_whatsapp_invoice_url", [[orderId]]);
        } catch (error) {
            console.warn("WhatsApp: could not get the invoice link", error);
            return;
        }
        this.alarabOpenWhatsapp(url);
    },
});

// Invoice made at payment: the link comes back with the order sync (no extra request).
patch(PaymentScreen.prototype, {
    async afterOrderValidation() {
        const order = this.currentOrder;
        const url = order?.is_to_invoice() && order.raw?.alarab_wa_invoice_url;
        if (url) {
            this.pos.alarabOpenWhatsapp(url);
        }
        return await super.afterOrderValidation(...arguments);
    },
});

// Invoice made later from the ticket screen (not on "Reprint Invoice").
patch(InvoiceButton.prototype, {
    async _invoiceOrder() {
        const wasInvoiced = this.isAlreadyInvoiced;
        const orderId = this.props.order?.id;
        await super._invoiceOrder(...arguments);
        if (!wasInvoiced && orderId) {
            await this.pos.alarabOpenWhatsappInvoice(orderId);
        }
    },
});
