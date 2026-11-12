import { ClosePosPopup } from "@point_of_sale/app/navbar/closing_popup/closing_popup";
import { patch } from "@web/core/utils/patch";

// جرد أعمى: الكاشير (مو مدير) بيعدّ الصندوق وبيكتب اللي لقاه بدون ما يشوف المبلغ المتوقع،
// ولا الفرق، ولا مجاميع الطلبات وطرق الدفع. الفرق بينسجّل وبيوصل للمدير بالإيميل اليومي.
patch(ClosePosPopup.prototype, {
    get laundryBlindCount() {
        // الدور تبع الكاشير المختار (pos_hr)، مو المستخدم اللي فاتح الجهاز
        const cashier = this.pos.get_cashier();
        if (this.pos.config.module_pos_hr) {
            // ما في كاشير مختار (مثلاً الإغلاق فتح لحاله على شاشة القفل) = جرد أعمى
            return cashier?._role !== "manager";
        }
        return !this.props.is_manager;
    },

    // ما في "Payments Difference" ولا "contact your manager": هالرسايل بتكشف إنه العدد غلط،
    // والكاشير بيرجع يغيّر الرقم لحتى تختفي
    async confirm() {
        if (this.laundryBlindCount) {
            return this.closeSession();
        }
        return super.confirm(...arguments);
    },
});
