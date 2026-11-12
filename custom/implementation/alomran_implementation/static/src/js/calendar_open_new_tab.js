/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { CalendarCommonRenderer } from "@web/views/calendar/calendar_common/calendar_common_renderer";

const isMac = /Mac|iPhone|iPad/.test(navigator.platform);
// Only Firefox honours a synthetic Ctrl+click: Chrome / Edge ignore the
// modifier of untrusted events (pop-under protection), so there a script
// cannot open a background tab at all.
const isFirefox = /Firefox\//.test(navigator.userAgent);

// Open ``url`` in a new tab WITHOUT switching to it: window.open() always
// focuses the new tab, while a Ctrl+click (Cmd+click on macOS) on a link
// opens it in the background, like the browser does for the user.
function openInBackgroundTab(url) {
    const link = document.createElement("a");
    link.href = url;
    link.target = "_blank";
    link.rel = "noopener";
    link.dispatchEvent(
        new MouseEvent("click", {
            bubbles: true,
            cancelable: true,
            view: window,
            ctrlKey: !isMac,
            metaKey: isMac,
        })
    );
}

// Each opportunity of the CRM calendar is a real link to its form, so the
// browser itself handles it like any link (all browsers):
//   * middle click / Ctrl+click: opens it in a background tab,
//   * right click: browser menu with "Open link in new tab"
//     (Firefox: right click opens the background tab directly).
// A plain left click keeps opening the calendar popover as before.
patch(CalendarCommonRenderer.prototype, {
    onEventDidMount(info) {
        super.onEventDidMount(info);
        if (this.props.model.resModel !== "crm.lead") {
            return;
        }
        const record = this.props.model.records[info.event.id];
        if (!record) {
            return;
        }
        const url = `/odoo/crm.lead/${record.id}`;
        const el = info.el;
        el.setAttribute("href", url);
        // no native link drag: the calendar's own drag & drop must keep working
        el.setAttribute("draggable", "false");
        el.addEventListener("click", (ev) => {
            if (ev.ctrlKey || ev.metaKey || ev.shiftKey) {
                // let the browser open the link, without the calendar popover
                ev.stopPropagation();
            } else {
                // plain click: popover only, no navigation of the current page
                ev.preventDefault();
            }
        });
        if (isFirefox) {
            el.addEventListener("contextmenu", (ev) => {
                ev.preventDefault();
                ev.stopPropagation();
                openInBackgroundTab(url);
            });
        }
    },
});
