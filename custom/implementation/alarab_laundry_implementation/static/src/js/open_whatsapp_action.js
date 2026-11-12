/** @odoo-module **/

import { registry } from "@web/core/registry";
import { browser } from "@web/core/browser/browser";
import { _t } from "@web/core/l10n/translation";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

function isBlocked(win) {
    return !win || win.closed || typeof win.closed === "undefined";
}

/**
 * Opens a WhatsApp Web link, then continues with params.next (e.g. the invoice form).
 * If the browser blocks the popup, asks the user to click (a real click is never blocked).
 */
async function alarabOpenWhatsapp(env, action) {
    const { url, next } = action.params || {};
    if (!url) {
        return next;
    }
    if (!isBlocked(browser.open(url, "_blank"))) {
        return next;
    }
    return new Promise((resolve) => {
        env.services.dialog.add(
            ConfirmationDialog,
            {
                title: _t("WhatsApp"),
                body: _t("Your browser blocked the WhatsApp window. Click the button to open it."),
                confirmLabel: _t("Open WhatsApp"),
                confirm: () => {
                    browser.open(url, "_blank");
                    resolve(next);
                },
                cancelLabel: _t("Skip"),
                cancel: () => resolve(next),
            },
            { onClose: () => resolve(next) }
        );
    });
}

registry.category("actions").add("alarab_open_whatsapp", alarabOpenWhatsapp);
