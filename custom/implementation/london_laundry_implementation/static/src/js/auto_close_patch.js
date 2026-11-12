import { PosStore } from "@point_of_sale/app/store/pos_store";
import { ClosePosPopup } from "@point_of_sale/app/navbar/closing_popup/closing_popup";
import { patch } from "@web/core/utils/patch";
import { deserializeDateTime } from "@web/core/l10n/dates";

const { DateTime } = luxon;
const CHECK_EVERY_MS = 20000;
// إعدادات الإغلاق بتنقرا من السيرفر كل دقيقة: إذا المدير غيّر الوقت والـ POS مفتوح ما بدها reload
const SETTINGS_EVERY_MS = 60000;
const SETTINGS_FIELDS = ["laundry_auto_close", "laundry_auto_close_time", "laundry_tz"];

// إغلاق آخر اليوم من الشاشة: بالوقت المحدد بإعدادات نقطة البيع (بتوقيت المغسلة) بتنفتح نافذة
// Close Register لحالها وما بتتسكّر (لا Discard ولا Escape) لحتى الكاشير يعدّ ويسكّر الصندوق.
// إذا ما حدا سكّر، السيرفر بيسكّر الجلسة بعد المهلة (pos.session._cron_laundry_auto_close).
patch(PosStore.prototype, {
    async afterProcessServerData() {
        const result = await super.afterProcessServerData(...arguments);
        clearInterval(this._laundryAutoCloseTimer);
        this._laundryAutoCloseTimer = setInterval(() => this.laundryCheckAutoClose(), CHECK_EVERY_MS);
        this.laundryCheckAutoClose();
        return result;
    },

    // آخر وقت إغلاق صار (اليوم إذا وصلناله، وإلا مبارح)
    laundryLastCloseMoment() {
        const hours = this.config.laundry_auto_close_time || 0;
        let hour = Math.floor(hours);
        let minute = Math.round((hours - hour) * 60);
        if (minute === 60) {
            hour += 1;
            minute = 0;
        }
        const now = DateTime.now().setZone(this.config.laundry_tz || "Asia/Dubai");
        let cut = now.set({ hour: Math.min(hour, 23), minute, second: 0, millisecond: 0 });
        if (cut > now) {
            cut = cut.minus({ days: 1 });
        }
        return cut;
    },

    async laundryRefreshAutoCloseSettings() {
        const now = Date.now();
        const waitingOpenTime = this.session?.state === "opened" && !this.session.start_at;
        if (!waitingOpenTime && now - (this._laundrySettingsReadAt || 0) < SETTINGS_EVERY_MS) {
            return;
        }
        this._laundrySettingsReadAt = now;
        try {
            await this.data.read("pos.config", [this.config.id], SETTINGS_FIELDS);
            // السيرفر سكّر الجلسة (بعد المهلة) والصفحة لسا مفتوحة: منرجع نحمّل متل بعد Close Register
            const [session] = await this.data.call("pos.session", "read", [
                [this.session.id],
                ["state", "start_at"],
            ]);
            if (session?.state === "closed") {
                window.location.reload();
                return;
            }
            // الجلسة انفتحت من نفس الصفحة (Open Register): وقت الفتح بيتعبّى بالسيرفر بس
            if (session?.start_at && !this.session.start_at) {
                this.session.start_at = session.start_at;
            }
        } catch {
            // ما في اتصال: منكمّل بالإعدادات اللي معنا
        }
    },

    async laundryCheckAutoClose() {
        await this.laundryRefreshAutoCloseSettings();
        if (
            !this.config.laundry_auto_close ||
            this.laundryForcedClose ||
            this.session?.state !== "opened" ||
            !this.session.start_at
        ) {
            return;
        }
        const openedAt = deserializeDateTime(this.session.start_at);
        if (openedAt >= this.laundryLastCloseMoment()) {
            return;
        }
        this.laundryForcedClose = true;
        try {
            const info = await this.getClosePosInfo();
            if (!info) {
                this.laundryForcedClose = false;
                return;
            }
            this.dialog.add(ClosePosPopup, info, {
                // انسكّرت بلا إغلاق (Escape): بترجع تنفتح بالفحص الجاي
                onClose: () => {
                    this.laundryForcedClose = false;
                },
            });
        } catch {
            this.laundryForcedClose = false; // ما في اتصال: منرجع نجرّب بعد شوي
        }
    },
});

patch(ClosePosPopup.prototype, {
    // نافذة الإغلاق اللي فتحت لحالها آخر اليوم إجبارية: ما في Discard
    canCancel() {
        return !this.pos.laundryForcedClose && super.canCancel(...arguments);
    },
});
