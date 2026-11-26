// Extends hr_attendance/static/src/components/attendance_menu/attendance_menu.js
import { Component } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { ActivityMenu } from "@hr_attendance/components/attendance_menu/attendance_menu";
import { FaceCapture } from "@dekad_hr_attendance_face/face_capture/face_capture";

export class FaceCaptureDialog extends Component {
    static template = "dekad_hr_attendance_face.FaceCaptureDialog";
    static components = { Dialog, FaceCapture };
    static props = {
        close: Function,
        onSuccess: { type: Function, optional: true },
    };

    setup() {
        this.notification = useService("notification");
    }

    onSuccess(result) {
        const checkedIn = result.attendance && !result.attendance.check_out;
        this.notification.add(checkedIn ? _t("Checked in") : _t("Checked out"), { type: "success" });
        this.props.onSuccess?.(result);
        this.props.close();
    }
}

patch(ActivityMenu.prototype, {
    setup() {
        super.setup(...arguments);
        this.dialog = useService("dialog");
        this.faceConfig = {};
    },

    async searchReadEmployee() {
        await super.searchReadEmployee(...arguments);
        if (!this.employee || !this.employee.id) {
            return;
        }
        try {
            this.faceConfig = (await rpc("/dekad_face/my/config")) || {};
        } catch {
            this.faceConfig = {};
        }
    },

    async signInOut() {
        if (!this.faceConfig.enabled) {
            return super.signInOut(...arguments);
        }
        this.dropdown.close();
        this.dialog.add(FaceCaptureDialog, {
            onSuccess: () => this.searchReadEmployee(),
        });
    },
});
