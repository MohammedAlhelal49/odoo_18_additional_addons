# dekad_hr_attendance_face — Deployment handoff

Face recognition for Odoo 18 Attendances:

- **Kiosk (shared tablet):** 1:N identification. Uses the company kiosk URL/token.
- **Personal devices:** 1:1 verification of the logged-in employee from the check-in button in the backend systray. Supports geolocation and a per-work-location geofence.

Detection uses YuNet and recognition uses SFace, both through OpenCV on the CPU.
Everything runs **on the server**. The browser only sends JPEG frames.

Depends only on `hr_attendance`. It never modifies core files: it extends them by
inheritance (`_inherit`, `selection_add`, `@http.route()` overrides, OWL `patch()` /
`t-inherit`).

---

## 1. Install the Python dependencies

These are **optional**. The module installs without them, and the feature then stays
disabled with an explanation in the settings. They are deliberately not declared in
`external_dependencies`, because that would block installation.

Run this with the **same Python environment that runs Odoo** (the venv or system Python
of the Odoo service):

```bash
/path/to/odoo-venv/bin/pip install -r /path/to/addons/dekad_hr_attendance_face/requirements.txt
```

The pinned packages are `opencv-python-headless==4.12.0.88` and `numpy==2.2.6`. Wheels
exist for Python 3.10–3.13 on Linux x86_64 and aarch64. Nothing is compiled, and no
system packages are needed (the *headless* build has no GUI or libGL dependency).

Then check that the installed packages are consistent and that OpenCV has the APIs the
module needs:

```bash
/path/to/odoo-venv/bin/pip check
/path/to/odoo-venv/bin/python -c "import cv2, numpy; print(cv2.__version__, numpy.__version__, hasattr(cv2, 'FaceDetectorYN'))"
```

> If another module on the server pins `numpy<2`, keep that pin and use
> `opencv-python-headless==4.10.0.84`, which supports numpy 1.26.

**Restart Odoo** after installing: the engine is loaded once per worker process.

## 2. Model files

The models are shipped inside the module, in `face_models/`. They are **not** under
`static/`, so Odoo never serves them over HTTP.

| File | Size | SHA-256 | License |
|---|---|---|---|
| `face_detection_yunet_2023mar.onnx` | 232,589 B | `8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4` | MIT |
| `face_recognition_sface_2021dec.onnx` | 38,696,353 B | `0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79` | Apache-2.0 |

To verify them:

```bash
cd /path/to/addons/dekad_hr_attendance_face/face_models && sha256sum -c SHA256SUMS
```

The module also checks these checksums itself when it loads the models. If a file is
missing or modified, the feature is disabled and the settings show the reason.

## 3. Server requirements

1. **HTTPS is mandatory.** Browsers only allow camera access on secure origins (HTTPS or
   `http://localhost`). Over plain HTTP, the kiosk shows "camera not available".

2. **Behind nginx or another reverse proxy, enable `proxy_mode`.** Set
   `proxy_mode = True` in `odoo.conf`. Odoo 18 applies the proxy fix **only when
   `X-Forwarded-Host` is present** (`odoo/http.py`), so the proxy must send all of these
   headers:

   ```nginx
   proxy_set_header X-Forwarded-Host  $host;
   proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
   proxy_set_header X-Forwarded-Proto $scheme;
   proxy_set_header X-Real-IP         $remote_addr;
   client_max_body_size 8m;   # face frames (the route itself refuses > 5 MB)
   ```

   Without these headers, every client appears with the proxy's IP. Per-IP rate
   limiting then becomes one shared counter for everybody.

   The module reads the client IP only from `request.httprequest.remote_addr`, and never
   parses `X-Forwarded-For` itself.

3. **Upgrade:** `odoo-bin -u dekad_hr_attendance_face`. Three cron jobs are created
   (hourly cleanup, daily photo purge, daily purge of archived employees' data). They need
   the cron thread (`max_cron_threads >= 1`).

## 4. Configuration after installation

Open **Attendances › Configuration › Settings › Face Recognition**:

1. Check that the engine line says *"The face recognition engine is ready."*
2. Enable **Face Recognition in Kiosk** and/or **Face Recognition on Personal Devices**.
3. Optionally enable **Face Only**. With it, the server rejects badge scans, manual
   selection and the employee list in the kiosk, and the plain check-in button on personal
   devices (for each channel where face is enabled). It is disabled by default, so the
   standard Odoo behaviour stays unchanged.
4. Matching policy defaults:

   | Setting | Default |
   |---|---|
   | Similarity threshold | 0.40 (cosine) |
   | Margin over the second-best employee | 0.06 |
   | Frames per attempt | 5 |
   | Challenge validity | 60 s |

   Raise the threshold to reduce false accepts. Lower it only if real employees are
   rejected too often.
5. Rate limits, all counted in a 15-minute window, with a 15-minute lockout when a limit
   is reached:

   | Counter | Default |
   |---|---|
   | Failures per IP | 20 |
   | Failures per kiosk | 60 |
   | Failures per user | 5 |
   | Challenges per IP | 30 |

6. Optional: **Store check-in photo**, with a retention period (default 30 days). Expired
   photos are purged by a daily cron.
7. **Personal devices:** set latitude, longitude and a radius on each **Work Location**
   (Employees › Configuration › Work Locations). The geofence applies to employees
   assigned to that location.
8. **Enrollment:** only Attendance *Administrators* can enroll.
   - Open the employee and click the **Face** button.
   - Tick the consent box, then capture or upload 3–10 clear frontal photos.
   - Photos are processed in memory and are not stored. Only 128-number templates are kept.
   - Enrollment is refused if the face is too similar to another enrolled employee.
9. **Audit:** Attendances › Face Attempts. The audit stores result, reason, IP, browser,
   score and employee. It never stores images or templates. The server log gets one line
   per attempt, also without images or templates.

## 5. Expected CPU and memory impact

Measured on an Intel i7-8850H with one thread per worker (`cv2.setNumThreads(1)`).

| Operation | Time |
|---|---|
| Face detection (YuNet, 320 px frame) | ~12 ms per frame |
| Embedding (SFace) | ~34 ms per face |
| 1:N matching over 5,000 templates | ~5 ms |
| **Full kiosk attempt** (5 frames, 2–3 embeddings, decoding) | **≈ 150–200 ms CPU on one core** |
| Enrollment | ~50 ms per photo |

Memory: **about +110 MB RSS per worker**, loaded lazily the first time that worker handles
a face request. With `workers = 3`, plan for up to ~330 MB extra in total. The default
`limit_memory_soft` (2 GB) is unaffected.

Database: one small row per attempt in `hr_face_attempt`, plus short-lived rows for
challenges and rate-limit counters, which are cleaned every hour. Photos, if enabled, are
about 10–20 KB each, stored as attachments.

## 6. Threat model

**Mitigated:**

- **Client-side spoofing of identity.** The client sends only frames. Detection,
  embeddings and matching happen on the server. Any `employee_id`, `embedding`, `score`,
  `match`, etc. sent by the client causes the attempt to be rejected and audited as
  `tampered`.
- **Replay of captured requests.** The server issues a single-use nonce with a 60 s
  expiry, bound to the company, the channel (kiosk or mobile) and the user. It is burnt
  atomically (`UPDATE … WHERE state='issued'`) before any processing. Identical frames
  are rejected. Only the nonce hash is stored.
- **Printed photo or static screen.** The random head-turn challenge (left or right)
  requires a frontal frame followed by a turn in the requested direction, with the same
  identity across frames.
- **Brute force and enumeration.**
  - DB-based counters per IP, per kiosk and per user, with lockout. They work across
    multiple workers.
  - An invalid kiosk token gets `{}`, exactly like the core routes.
  - Errors are generic: "not recognized" does not reveal whether the face was below the
    threshold or ambiguous.
- **Misidentification between similar people.** Matching requires both the threshold and
  a margin over the second-best employee, and rejects ambiguous matches. Enrollment
  refuses near-duplicate faces.
- **Cross-company leakage.** The company comes from the token. Only active, consented
  employees of that company are matched, filtered on the employee's current company.
  Multi-company record rules apply too.
- **Biometric data exposure.**
  - Templates live in `hr.face.sample`, readable only by Attendance Administrators, by
    ACL, record rule and field group. They are not on `hr.employee` and are never sent to
    the browser.
  - Data is deleted when the employee is archived or deleted (plus a daily safety-net
    cron).
  - Consent is mandatory and recorded with the date and the user who recorded it.
- **Malformed input.**
  - JPEG and PNG only, checked by magic bytes and against the declared type.
  - Size and dimension limits are checked from the header before decoding, plus a 5 MB
    limit per request and 3–8 frames per attempt.
  - Any decoding failure returns a clean error.
- **Missing dependencies.** The module still installs. The feature stays off, and the
  rest of Odoo is unaffected.

**Residual risks** (not mitigated):

- **Recorded video or live deepfake.** A video of the employee that happens to turn the
  right way, or a real-time deepfake, can pass the head-turn check. The liveness check is
  pluggable (`lib/liveness.py`, `register()` plus `selection_add` on
  `face_liveness_method`), so an anti-spoofing model can be added later.
- **Twins and look-alikes.** These remain a recognition-accuracy limitation. Tune the
  threshold and margin.
- **The kiosk token is a bearer secret.** Anyone with the kiosk URL can request challenges
  (rate-limited). Regenerate the URL from the settings if it leaks.
- **Personal devices: GPS can be spoofed** on a rooted or developer-mode phone. Treat the
  geofence as a deterrent.
- **Database dumps contain the templates.** Templates are not reversible to a photo, but
  they are biometric data. Protect backups accordingly.
- **Without Face Only,** the standard methods (manual selection without PIN, badge)
  remain as weak as in core Odoo.
- **Rate-limit side effect.** Several kiosks behind one NAT share the per-IP counter.
  Adjust the limits if needed.
- **Training data.** The SFace weights are Apache-2.0, but they were trained on academic
  face datasets that have their own terms. Have legal review this before a commercial
  rollout.

---

## Developer notes

**Run the tests** (local database only):

```bash
odoo-bin -c odoo.conf -d <test_db> -u dekad_hr_attendance_face --test-tags /dekad_hr_attendance_face --stop-after-init --http-port 8079
```

They cover:

- kiosk token validation
- nonce replay, expiry and binding
- rate limiting and lockout
- rejection of client-sent IDs
- access rights on templates
- threshold and margin logic
- company isolation
- the 1:1 mobile flow and geofence
- Face Only
- input hardening
- a real-model test that shows a static photo is rejected

**Testing the camera from a phone on the LAN.** `http://localhost` works on the laptop
itself. A phone needs HTTPS. Two simple options:

- **Caddy with a local certificate.** Install `caddy`, then run:

  ```bash
  caddy reverse-proxy --from https://<laptop-LAN-IP>:8443 --to localhost:8069 --internal-certs
  ```

  Then open `https://<laptop-LAN-IP>:8443` on the phone and accept the certificate. To
  avoid the warning, install Caddy's root CA (`caddy trust` prints its location) on the
  phone. Set `proxy_mode = True` locally too, and make sure `X-Forwarded-Host` is passed.
  Caddy sends it by default.
- **Chrome flag, testing only.** On the phone, open
  `chrome://flags/#unsafely-treat-insecure-origin-as-secure`, add
  `http://<laptop-LAN-IP>:8069` and relaunch Chrome.

Code layout:

| Path | Contents |
|---|---|
| `lib/engine.py` | lazy OpenCV, safe decoding |
| `lib/liveness.py` | pluggable checkers |
| `lib/matching.py` | policy |
| `controllers/main.py` | routes, extends `hr_attendance/controllers/main.py` |
| `static/src/kiosk/` | patch of `public_kiosk_app` |
| `static/src/systray/` | patch of `attendance_menu` |
