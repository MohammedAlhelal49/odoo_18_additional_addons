import { Component, onWillStart, onWillUnmount, useEffect, useRef, useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { cameraErrorCode, faceErrorMessage } from "@dekad_hr_attendance_face/face_capture/face_capture";

const MAX_SAMPLES = 10;
const MIN_SAMPLES = 3;
const CAPTURE_WIDTH = 640;
const MAX_UPLOAD_BYTES = 6 * 1024 * 1024;
const ALLOWED_TYPES = ["image/jpeg", "image/png"];

/**
 * Administrator-only enrollment screen. Photos stay in the browser until they
 * are submitted; the server keeps only the computed templates.
 */
export class FaceEnrollment extends Component {
    static template = "dekad_hr_attendance_face.FaceEnrollment";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.videoRef = useRef("video");
        // params are lost on page reload; the router keeps the employee as active_id.
        const params = this.props.action.params || {};
        const router = this.env.services.router;
        this.employeeId =
            params.employee_id ||
            this.props.action.context?.active_id ||
            (router && router.current && router.current.active_id);
        this.employeeName = params.employee_name || "";
        onWillStart(async () => {
            if (this.employeeId && !this.employeeName) {
                const [employee] = await this.orm.read("hr.employee", [this.employeeId], ["name"]);
                this.employeeName = employee ? employee.name : "";
            }
        });
        this.minSamples = MIN_SAMPLES;
        this.maxSamples = MAX_SAMPLES;
        this.stream = null;
        this.state = useState({ consent: false, images: [], cameraOn: false, videoReady: false, busy: false, rejected: [] });
        // Attach the stream once OWL has actually rendered the <video> element.
        useEffect(
            (video) => {
                if (video && this.stream && video.srcObject !== this.stream) {
                    video.srcObject = this.stream;
                    // MediaStream events can fire before a listener is attached: rely on play() instead.
                    video
                        .play()
                        .then(() => (this.state.videoReady = video.videoWidth > 0 || video.readyState >= 2))
                        .catch(() => {});
                }
            },
            () => [this.videoRef.el]
        );
        onWillUnmount(() => this.stopCamera());
    }

    async startCamera() {
        if (!navigator.mediaDevices?.getUserMedia) {
            this.notification.add(_t("The camera is not available. Camera access requires HTTPS."), { type: "danger" });
            return;
        }
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                // 640x480 is all we keep (CAPTURE_WIDTH); higher modes only cost USB bandwidth and CPU.
                video: { facingMode: "user", width: { ideal: 640 }, height: { ideal: 480 }, frameRate: { ideal: 15, max: 30 } },
                audio: false,
            });
        } catch (error) {
            this.notification.add(faceErrorMessage(cameraErrorCode(error)), { type: "danger" });
            return;
        }
        this.state.cameraOn = true;
    }

    stopCamera() {
        if (this.stream) {
            this.stream.getTracks().forEach((track) => track.stop());
            this.stream = null;
        }
        this.state.cameraOn = false;
        this.state.videoReady = false;
    }

    capture() {
        if (this.state.images.length >= MAX_SAMPLES) {
            return;
        }
        const video = this.videoRef.el;
        if (!video || !video.videoWidth) {
            return; // camera not ready yet
        }
        const canvas = document.createElement("canvas");
        canvas.width = CAPTURE_WIDTH;
        canvas.height = Math.round((CAPTURE_WIDTH * video.videoHeight) / video.videoWidth);
        canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
        this.state.images.push(canvas.toDataURL("image/jpeg", 0.92));
    }

    onUpload(ev) {
        for (const file of ev.target.files) {
            if (this.state.images.length >= MAX_SAMPLES) {
                break;
            }
            if (!ALLOWED_TYPES.includes(file.type) || file.size > MAX_UPLOAD_BYTES) {
                this.notification.add(_t("%s: only JPEG or PNG images up to 6 MB.", file.name), {
                    type: "warning",
                });
                continue;
            }
            const reader = new FileReader();
            reader.onload = () => this.state.images.push(reader.result);
            reader.readAsDataURL(file);
        }
        ev.target.value = "";
    }

    removeImage(index) {
        this.state.images.splice(index, 1);
    }

    get canSubmit() {
        return this.state.consent && this.state.images.length >= MIN_SAMPLES && !this.state.busy;
    }

    async submit() {
        if (!this.canSubmit) {
            return;
        }
        this.state.busy = true;
        try {
            const result = await this.orm.call("hr.face.profile", "enroll_samples", [
                this.employeeId,
                [...this.state.images],
                this.state.consent,
            ]);
            this.state.images = [];
            this.state.rejected = result.rejected || [];
            this.stopCamera();
            this.notification.add(_t("%s face samples enrolled.", result.accepted), { type: "success" });
            if (this.state.rejected.length) {
                this.notification.add(this.state.rejected.join("\n"), {
                    type: "warning",
                    title: _t("Some photos were rejected"),
                });
            }
            await this.back();
        } finally {
            this.state.busy = false;
        }
    }

    async back() {
        this.stopCamera();
        await this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "hr.employee",
            res_id: this.employeeId,
            views: [[false, "form"]],
        }, { clearBreadcrumbs: false });
    }
}

registry.category("actions").add("dekad_face_enrollment", FaceEnrollment);
