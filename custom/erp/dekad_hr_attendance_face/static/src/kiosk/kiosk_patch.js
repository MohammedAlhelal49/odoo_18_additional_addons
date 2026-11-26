// Extends hr_attendance/static/src/public_kiosk/public_kiosk_app.js
import { onWillStart, useState } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { patch } from "@web/core/utils/patch";
import kioskModule from "@hr_attendance/public_kiosk/public_kiosk_app";
import { FaceCapture } from "@dekad_hr_attendance_face/face_capture/face_capture";

const { kioskAttendanceApp } = kioskModule;

kioskAttendanceApp.components = { ...kioskAttendanceApp.components, FaceCapture };

patch(kioskAttendanceApp.prototype, {
    setup() {
        super.setup(...arguments);
        this.faceState = useState({ enabled: false, faceOnly: false });
        onWillStart(async () => {
            let config = {};
            try {
                config = await rpc("/dekad_face/kiosk/config", { token: this.props.token });
            } catch {
                config = {};
            }
            this.faceState.enabled = Boolean(config.enabled && config.available);
            this.faceState.faceOnly = this.faceState.enabled && Boolean(config.face_only);
            if (this.faceState.faceOnly && this.state.active_display === "manual") {
                this.manualKioskMode = false;
                this.state.active_display = "main";
            }
        });
    },

    switchDisplay(screen) {
        if (screen === "face") {
            this.state.active_display = this.faceState.enabled ? "face" : "main";
            return;
        }
        return super.switchDisplay(...arguments);
    },

    kioskReturn() {
        if (this.faceState.faceOnly && this.state.active_display !== "settings") {
            this.switchDisplay("main");
            return;
        }
        return super.kioskReturn(...arguments);
    },

    onFaceSuccess(result) {
        this.employeeData = result;
        this.switchDisplay("greet");
    },
});
