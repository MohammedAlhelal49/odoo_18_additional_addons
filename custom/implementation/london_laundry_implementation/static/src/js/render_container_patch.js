import { RenderContainer } from "@point_of_sale/app/printer/render_service";
import { onRendered, useRef } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";

// طباعة الإيصال: Odoo بيرسم الإيصال مخفي وبيستنى 100ms ثابتة وبعدين بياخده. الإيصال بينحط بالصفحة
// مع رسمة الشاشة الجاية، ومع "طباعة تلقائية + تخطّي شاشة الإيصال" الـ POS بيرسم شاشة المنتجات بنفس
// اللحظة، فبتاخد أكتر من 100ms وبيطلع "Cannot read properties of null (reading 'cloneNode')".
// هون منستنى لحتى الإيصال يصير فعلاً بالصفحة (لحد 2 ثانية).
const MAX_WAIT_MS = 2000;
const STEP_MS = 50;

patch(RenderContainer.prototype, {
    setup() {
        this.ref = useRef("ref");
        onRendered(async () => {
            await new Promise((r) => setTimeout(r, 100));
            let el = this.ref?.el?.firstElementChild;
            for (let waited = 0; !el && this.props.comp.component && waited < MAX_WAIT_MS; waited += STEP_MS) {
                await new Promise((r) => setTimeout(r, STEP_MS));
                el = this.ref?.el?.firstElementChild;
            }
            // خط الإيصال (Tajawal) لازم يكون محمّل قبل الطباعة، وإلا أول إيصال بيطلع بخط تاني
            if (el && document.fonts?.ready) {
                await Promise.race([document.fonts.ready, new Promise((r) => setTimeout(r, MAX_WAIT_MS))]);
            }
            this.props.onRendered(el);
        });
    },
});

// تحميل خط الإيصال من أول ما ينفتح الـ POS (العادي والعريض، عربي وإنكليزي)
if (document.fonts?.load) {
    for (const weight of ["400", "700"]) {
        document.fonts.load(`${weight} 12px Tajawal`, "إيصال Receipt 0123").catch(() => {});
    }
}

