import { Component, onMounted, onWillUnmount, useRef, useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";

const FRAME_WIDTH = 320;
const JPEG_QUALITY = 0.85;

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

export function faceErrorMessage(code) {
    const messages = {
        not_recognized: _t("Face not recognized. Please try again."),
        not_enrolled: _t("Your face is not enrolled yet. Please contact your HR administrator."),
        liveness_failed: _t("Liveness check failed. Follow the instruction on screen and try again."),
        expired: _t("The session expired. Please try again."),
        locked: _t("Too many failed attempts. Please try again later."),
        rate_limited: _t("Too many requests. Please wait a moment and try again."),
        no_face: _t("No face detected. Center your face in the frame."),
        multiple_faces: _t("More than one face detected. Only one person at a time."),
        face_too_small: _t("Please move closer to the camera."),
        bad_input: _t("The captured images were invalid. Please try again."),
        unavailable: _t("Face recognition is not available. Please contact your administrator."),
        disabled: _t("Face recognition is not enabled."),
        no_employee: _t("Your user is not linked to an employee."),
        no_location: _t("Your location is required. Allow location access and try again."),
        outside_geofence: _t("You are not at your work location."),
        camera: _t("The camera is not available. Camera access requires HTTPS and your permission."),
        no_camera: _t("No camera was found on this device."),
        camera_denied: _t("Camera permission was denied. Allow the camera in the browser settings and try again."),
        camera_busy: _t("The camera is already in use by another application."),
    };
    return messages[code] || _t("Something went wrong. Please try again.");
}

/** Map a getUserMedia() error to a faceErrorMessage() code. */
export function cameraErrorCode(error) {
    switch (error && error.name) {
        case "NotFoundError":
        case "OverconstrainedError":
            return "no_camera";
        case "NotAllowedError":
        case "SecurityError":
            return "camera_denied";
        case "NotReadableError":
            return "camera_busy";
        default:
            return "camera";
    }
}

/**
 * Captures frames bound to a server challenge and sends them for server-side
 * recognition. The client never computes or sends any identity information.
 */
export class FaceCapture extends Component {
    static template = "dekad_hr_attendance_face.FaceCapture";
    static props = {
        challengeRoute: String,
        verifyRoute: String,
        params: { type: Object, optional: true },
        withLocation: { type: Boolean, optional: true },
        onSuccess: Function,
        onCancel: Function,
    };
    static defaultProps = { params: {}, withLocation: false };

    setup() {
        this.videoRef = useRef("video");
        this.canvas = document.createElement("canvas");
        this.stream = null;
        this.alive = true;
        this.state = useState({ phase: "starting", challenge: null, error: "" });
        onMounted(() => this.start());
        onWillUnmount(() => {
            this.alive = false;
            this.stopCamera();
        });
    }

    get instruction() {
        switch (this.state.phase) {
            case "starting":
                return _t("Starting the camera…");
            case "frontal":
                return _t("Look straight at the camera");
            case "turn":
                return this.state.challenge === "left"
                    ? _t("Slowly turn your head to your left")
                    : _t("Slowly turn your head to your right");
            case "verifying":
                return _t("Verifying…");
            default:
                return "";
        }
    }

    async start() {
        if (!navigator.mediaDevices?.getUserMedia) {
            return this.showError("camera");
        }
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: "user", width: { ideal: 640 }, height: { ideal: 480 }, frameRate: { ideal: 15, max: 30 } },
                audio: false,
            });
        } catch (error) {
            return this.showError(cameraErrorCode(error));
        }
        if (!this.alive) {
            return this.stopCamera();
        }
        const video = this.videoRef.el;
        video.srcObject = this.stream;
        await video.play();
        await this.run();
    }

    stopCamera() {
        if (this.stream) {
            this.stream.getTracks().forEach((track) => track.stop());
            this.stream = null;
        }
    }

    getLocation() {
        if (!this.props.withLocation || !navigator.geolocation) {
            return Promise.resolve({});
        }
        return new Promise((resolve) => {
            navigator.geolocation.getCurrentPosition(
                ({ coords }) => resolve({ latitude: coords.latitude, longitude: coords.longitude }),
                () => resolve({}),
                { enableHighAccuracy: true, timeout: 10000 }
            );
        });
    }

    grabFrame() {
        const video = this.videoRef.el;
        const width = FRAME_WIDTH;
        const height = Math.round((FRAME_WIDTH * video.videoHeight) / video.videoWidth);
        this.canvas.width = width;
        this.canvas.height = height;
        // Raw (un-mirrored) frame: the preview is mirrored with CSS only.
        this.canvas.getContext("2d").drawImage(video, 0, 0, width, height);
        return this.canvas.toDataURL("image/jpeg", JPEG_QUALITY);
    }

    async run() {
        this.state.error = "";
        this.state.phase = "starting";
        const locationPromise = this.getLocation();
        let challenge;
        try {
            challenge = await rpc(this.props.challengeRoute, { ...this.props.params });
        } catch {
            return this.showError();
        }
        if (!challenge || !challenge.nonce) {
            return this.showError(challenge && challenge.error);
        }
        const total = challenge.frames;
        const frontalCount = Math.max(1, Math.floor(total * 0.4));
        const frames = [];

        this.state.phase = "frontal";
        await sleep(700);
        for (let i = 0; i < frontalCount && this.alive; i++) {
            frames.push(this.grabFrame());
            await sleep(250);
        }
        this.state.challenge = challenge.challenge;
        this.state.phase = "turn";
        await sleep(1300);
        for (let i = frontalCount; i < total && this.alive; i++) {
            frames.push(this.grabFrame());
            await sleep(300);
        }
        if (!this.alive) {
            return;
        }
        this.state.phase = "verifying";
        const location = await locationPromise;
        let result;
        try {
            result = await rpc(this.props.verifyRoute, {
                ...this.props.params,
                nonce: challenge.nonce,
                frames,
                ...location,
            });
        } catch {
            return this.showError();
        }
        if (!this.alive) {
            return;
        }
        if (result && result.attendance) {
            this.stopCamera();
            this.state.phase = "done";
            this.props.onSuccess(result);
        } else {
            this.showError(result && result.error);
        }
    }

    showError(code) {
        this.state.phase = "error";
        this.state.error = faceErrorMessage(code);
    }

    async retry() {
        if (!this.stream) {
            return this.start();
        }
        await this.run();
    }
}
