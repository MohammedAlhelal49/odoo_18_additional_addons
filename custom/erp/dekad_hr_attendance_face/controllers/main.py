"""Face-recognition routes for the attendance kiosk and personal devices.

Extends hr_attendance/controllers/main.py (HrAttendance): the company is
resolved from the kiosk token with the core ``_get_company`` and the
check-in/out goes through the core ``_attendance_action_change``.

Rules enforced here:
* the client only sends raw frames; detection, embeddings and matching are
  server-side, and identity-related parameters from the client are rejected;
* a single-use nonce bound to company, channel and user, with a liveness
  challenge;
* rate limiting / lockout in PostgreSQL, written on a separate cursor so it
  survives the rollback of a failed request;
* sudo() is used only for the specific reads/writes listed below.
"""
import logging
import math
from contextlib import contextmanager

from odoo import SUPERUSER_ID, api, http
from odoo.http import request

from odoo.addons.hr_attendance.controllers.main import HrAttendance

from ..lib import engine, liveness, matching

_logger = logging.getLogger(__name__)

MIN_FRAMES = 3
MAX_FRAMES = 8
MAX_REQUEST_BYTES = 5 * 1024 * 1024

# Anything identifying a person or a match result must come from the server.
FORBIDDEN_PARAMS = frozenset({
    'employee_id', 'employee', 'employee_ids', 'user_id', 'company_id', 'embedding', 'embeddings',
    'descriptor', 'match', 'matched', 'score', 'result', 'barcode', 'pin_code',
})

# Internal reason -> code returned to the client (no oracle on why a match failed).
PUBLIC_ERRORS = {
    'invalid_nonce': 'expired',
    'expired_nonce': 'expired',
    'nonce_mismatch': 'expired',
    'below_threshold': 'not_recognized',
    'ambiguous': 'not_recognized',
    'no_gallery': 'not_recognized',
    'too_fast': 'liveness_failed',
    'no_frontal': 'liveness_failed',
    'challenge_failed': 'liveness_failed',
    'identity_changed': 'liveness_failed',
    'tampered': 'error',
    'attendance_error': 'error',
    'engine_unavailable': 'unavailable',
}
# Failures that do not count towards the lockout (not caused by the person in front of the camera).
NOT_COUNTED = frozenset({'engine_unavailable', 'attendance_error', 'error', 'locked',
                         'no_location', 'outside_geofence'})


class FaceAttendanceController(HrAttendance):

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _face_company(self, token):
        if not isinstance(token, str) or not token:
            return request.env['res.company']
        return self._get_company(token)

    @contextmanager
    def _face_side_env(self):
        """Superuser env on a separate, committed cursor.

        Used only for nonces, rate-limit counters and failure audits, which
        must persist even though the request itself returns an error.
        """
        with request.env.registry.cursor() as cr:
            yield api.Environment(cr, SUPERUSER_ID, {})

    def _face_ctx(self, company, channel, user=None, employee=None):
        httprequest = request.httprequest
        return {
            'company': company,
            'channel': channel,
            'user': user,
            'employee': employee,
            # Odoo resolves the client address from X-Forwarded-* only when proxy_mode is on.
            'ip': httprequest.remote_addr or 'unknown',
            'browser': (httprequest.user_agent.browser or '')[:64],
        }

    def _face_fail_keys(self, ctx):
        company = ctx['company']
        keys = [(f"fail:ip:{ctx['ip']}", company.face_max_failures_ip)]
        if ctx['channel'] == 'kiosk':
            keys.append((f"fail:kiosk:{company.id}", company.face_max_failures_kiosk))
        else:
            keys.append((f"fail:user:{ctx['user'].id}", company.face_max_failures_user))
        return keys

    def _face_challenge_keys(self, ctx):
        company = ctx['company']
        keys = [(f"chal:ip:{ctx['ip']}", company.face_max_challenges)]
        if ctx['channel'] == 'kiosk':
            keys.append((f"chal:kiosk:{company.id}", company.face_max_challenges * 5))
        else:
            keys.append((f"chal:user:{ctx['user'].id}", company.face_max_challenges))
        return keys

    def _face_audit(self, env, ctx, stage, result, reason, employee=None, score=0.0, second_score=0.0,
                    attendance=None):
        env['hr.face.attempt'].create({
            'company_id': ctx['company'].id,
            'channel': ctx['channel'],
            'stage': stage,
            'result': result,
            'reason': reason,
            'employee_id': (employee or ctx['employee'] or env['hr.employee']).id,
            'user_id': ctx['user'].id if ctx['user'] else False,
            'score': score if math.isfinite(score) else 0.0,
            'second_score': second_score if math.isfinite(second_score) else 0.0,
            'attendance_id': attendance.id if attendance else False,
            'ip_address': ctx['ip'],
            'browser': ctx['browser'],
        })
        _logger.info("Face attendance %s: company=%s channel=%s result=%s reason=%s ip=%s",
                     stage, ctx['company'].id, ctx['channel'], result, reason, ctx['ip'])

    def _face_public_error(self, reason, channel):
        if channel == 'mobile' and reason == 'no_gallery':
            return 'not_enrolled'
        return PUBLIC_ERRORS.get(reason, reason)

    def _face_fail(self, ctx, stage, reason, **audit):
        result = 'locked' if reason in ('locked', 'rate_limited') else 'failure'
        with self._face_side_env() as env:
            if reason not in NOT_COUNTED:
                Throttle = env['hr.face.throttle']
                for key, limit in self._face_fail_keys(ctx):
                    Throttle._hit(key, limit, ctx['company'].face_rate_window, ctx['company'].face_lockout_minutes)
            self._face_audit(env, ctx, stage, result, reason, **audit)
        return {'error': self._face_public_error(reason, ctx['channel'])}

    @staticmethod
    def _face_coords(latitude, longitude):
        try:
            lat, lon = float(latitude), float(longitude)
        except (TypeError, ValueError):
            return None, None
        if not (math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180):
            return None, None
        return lat, lon

    # ------------------------------------------------------------------
    # Pipeline
    # ------------------------------------------------------------------

    def _face_issue_challenge(self, ctx):
        if engine.status() != engine.STATUS_OK:
            return {'error': 'unavailable'}
        company = ctx['company']
        with self._face_side_env() as env:
            Throttle = env['hr.face.throttle']
            fail_keys = [key for key, _limit in self._face_fail_keys(ctx)]
            challenge_limits = self._face_challenge_keys(ctx)
            if Throttle._is_locked(fail_keys + [key for key, _limit in challenge_limits]):
                self._face_audit(env, ctx, 'challenge', 'locked', 'locked')
                return {'error': 'locked'}
            for key, limit in challenge_limits:
                if Throttle._hit(key, limit, company.face_rate_window, company.face_lockout_minutes):
                    self._face_audit(env, ctx, 'challenge', 'locked', 'rate_limited')
                    return {'error': 'rate_limited'}
            nonce, challenge = env['hr.face.challenge']._issue(
                env['res.company'].browse(company.id), ctx['channel'], ctx['ip'],
                env['res.users'].browse(ctx['user'].id) if ctx['user'] else None)
        return {
            'nonce': nonce,
            'challenge': challenge,
            'frames': company.face_frame_count,
            'expires_in': company.face_nonce_ttl,
        }

    def _face_begin_verify(self, ctx, nonce, extra):
        """Lockout check, nonce consumption and tampering check.

        :return: (challenge_row, error_response); exactly one is set.
        """
        company = ctx['company']
        with self._face_side_env() as env:
            if env['hr.face.throttle']._is_locked([key for key, _limit in self._face_fail_keys(ctx)]):
                self._face_audit(env, ctx, 'verify', 'locked', 'locked')
                return None, {'error': 'locked'}
            # The nonce is burnt first, whatever happens next.
            row, reason = env['hr.face.challenge']._consume(
                nonce, env['res.company'].browse(company.id), ctx['channel'],
                env['res.users'].browse(ctx['user'].id) if ctx['user'] else None)
        if FORBIDDEN_PARAMS.intersection(extra):
            return None, self._face_fail(ctx, 'verify', 'tampered')
        if reason:
            return None, self._face_fail(ctx, 'verify', reason)
        return row, None

    def _face_analyze(self, face_engine, frames, row):
        """Decode frames, run the liveness check and build the probe embedding.

        :return: (probe_vector, best_frontal_image)
        :raise engine.FaceInputError: with an auditable reason code
        """
        engine.check_frames_payload(frames, MIN_FRAMES, MAX_FRAMES)
        if len(set(frames)) != len(frames):
            raise engine.FaceInputError('challenge_failed')  # replayed identical frames
        images = [face_engine.decode(frame) for frame in frames]
        faces, first_error = [], None
        for image in images:
            try:
                faces.append(liveness.pick_face(face_engine.detect(image)))
            except engine.FaceInputError as e:
                if e.code == 'multiple_faces':
                    raise
                first_error = first_error or e.code
                faces.append(None)
        if sum(face is not None for face in faces) < MIN_FRAMES:
            raise engine.FaceInputError(first_error or 'no_face')

        embeddings = {}

        def embedding(index):
            if index not in embeddings:
                embeddings[index] = face_engine.embed(images[index], faces[index])
            return embeddings[index]

        checker = liveness.get_checker(row['liveness_method'])
        check = checker.check(faces, row['challenge'], row['elapsed'],
                              lambda i, j: float(embedding(i) @ embedding(j)))
        if not check.ok:
            raise engine.FaceInputError(check.reason)
        np = engine.np
        probe = np.mean([embedding(i) for i in check.frontal], axis=0)
        probe /= np.linalg.norm(probe)
        return probe, images[check.frontal[0]]

    def _face_run(self, ctx, frames, row, match_fn):
        face_engine = engine.get_engine()
        if not face_engine:
            return None, None, self._face_fail(ctx, 'verify', 'engine_unavailable')
        try:
            probe, image = self._face_analyze(face_engine, frames, row)
            result = match_fn(probe)
        except engine.FaceInputError as e:
            return None, None, self._face_fail(ctx, 'verify', e.code)
        except Exception:  # noqa: BLE001 - never leak internals to the client
            _logger.exception("Face verification failed unexpectedly (company=%s)", ctx['company'].id)
            return None, None, self._face_fail(ctx, 'verify', 'error')
        if not result.matched:
            return None, None, self._face_fail(ctx, 'verify', result.status,
                                               score=result.score, second_score=result.second_score)
        return result, image, None

    def _face_record(self, ctx, employee, mode, result, image, latitude, longitude):
        company = ctx['company']
        lat, lon = self._face_coords(latitude, longitude)
        try:
            with request.env.cr.savepoint():
                # sudo: same as the core kiosk routes, the public user cannot write attendances.
                attendance = employee.sudo()._attendance_action_change(
                    self._get_geoip_response(mode, latitude=lat or False, longitude=lon or False))
                face_engine = engine.get_engine()
                if company.face_store_photo and face_engine:
                    photo = face_engine.to_jpeg(image)
                    if photo:
                        field = 'face_photo_out' if attendance.check_out else 'face_photo_in'
                        attendance.sudo().write({field: photo})
        except Exception:  # noqa: BLE001
            _logger.exception("Face attendance: could not record attendance for employee %s", employee.id)
            return self._face_fail(ctx, 'verify', 'attendance_error', employee=employee, score=result.score)
        # Success is audited in the request transaction so it commits with the attendance.
        self._face_audit(request.env(su=True), ctx, 'verify', 'success', 'ok', employee=employee,
                         score=result.score, second_score=result.second_score, attendance=attendance)
        return self._get_employee_info_response(employee)

    # ------------------------------------------------------------------
    # Kiosk routes (auth=public, company kiosk token, 1:N)
    # ------------------------------------------------------------------

    @http.route('/dekad_face/kiosk/config', type='json', auth='public', readonly=True)
    def face_kiosk_config(self, token=None):
        company = self._face_company(token)
        if not company or not company.face_kiosk_enabled:
            return {}
        return {
            'enabled': True,
            'available': engine.status() == engine.STATUS_OK,
            'face_only': company.face_only,
        }

    @http.route('/dekad_face/kiosk/challenge', type='json', auth='public')
    def face_kiosk_challenge(self, token=None):
        company = self._face_company(token)
        if not company or not company.face_kiosk_enabled:
            return {}
        return self._face_issue_challenge(self._face_ctx(company, 'kiosk'))

    @http.route('/dekad_face/kiosk/verify', type='json', auth='public', max_content_length=MAX_REQUEST_BYTES)
    def face_kiosk_verify(self, token=None, nonce=None, frames=None, latitude=None, longitude=None, **kwargs):
        company = self._face_company(token)
        if not company or not company.face_kiosk_enabled:
            return {}
        ctx = self._face_ctx(company, 'kiosk')
        row, error = self._face_begin_verify(ctx, nonce, kwargs)
        if error:
            return error

        def match(probe):
            # sudo: the public kiosk user cannot read templates; only the company's gallery is loaded.
            employee_ids, gallery = request.env['hr.face.sample'].sudo()._face_gallery(company.id)
            return matching.match_one_to_many(
                probe, employee_ids, gallery, company.face_match_threshold, company.face_match_margin)

        result, image, error = self._face_run(ctx, frames, row, match)
        if error:
            return error
        employee = request.env['hr.employee'].sudo().browse(result.employee_id)
        if not employee.active or employee.company_id != company:  # defense in depth
            return self._face_fail(ctx, 'verify', 'error')
        return self._face_record(ctx, employee, 'face_kiosk', result, image, latitude, longitude)

    # ------------------------------------------------------------------
    # Personal device routes (auth=user, no kiosk token, 1:1)
    # ------------------------------------------------------------------

    def _face_my_employee(self):
        employee = request.env.user.employee_id
        return employee, employee.sudo().company_id

    @http.route('/dekad_face/my/config', type='json', auth='user', readonly=True)
    def face_my_config(self):
        employee, company = self._face_my_employee()
        if not employee or not company.face_mobile_enabled or engine.status() != engine.STATUS_OK:
            return {'enabled': False}
        return {
            'enabled': True,
            'require_location': company.face_require_geolocation,
            'face_only': company.face_only,
        }

    @http.route('/dekad_face/my/challenge', type='json', auth='user')
    def face_my_challenge(self):
        employee, company = self._face_my_employee()
        if not employee:
            return {'error': 'no_employee'}
        if not company.face_mobile_enabled:
            return {'error': 'disabled'}
        return self._face_issue_challenge(self._face_ctx(company, 'mobile', request.env.user, employee))

    @http.route('/dekad_face/my/verify', type='json', auth='user', max_content_length=MAX_REQUEST_BYTES)
    def face_my_verify(self, nonce=None, frames=None, latitude=None, longitude=None, **kwargs):
        employee, company = self._face_my_employee()
        if not employee:
            return {'error': 'no_employee'}
        if not company.face_mobile_enabled:
            return {'error': 'disabled'}
        ctx = self._face_ctx(company, 'mobile', request.env.user, employee)
        row, error = self._face_begin_verify(ctx, nonce, kwargs)
        if error:
            return error

        lat, lon = self._face_coords(latitude, longitude)
        location = employee.sudo().work_location_id
        geofence = location and location._face_geofence_active()
        if lat is None and (company.face_require_geolocation or geofence):
            return self._face_fail(ctx, 'verify', 'no_location')
        if geofence and location._face_distance(lat, lon) > location.face_geofence_radius:
            return self._face_fail(ctx, 'verify', 'outside_geofence')

        def match(probe):
            # sudo: an employee cannot read templates; only their own samples are loaded.
            _ids, gallery = request.env['hr.face.sample'].sudo()._face_gallery(company.id, employee_id=employee.id)
            return matching.match_one_to_one(probe, employee.id, gallery, company.face_match_threshold)

        result, image, error = self._face_run(ctx, frames, row, match)
        if error:
            return error
        return self._face_record(ctx, employee, 'face_mobile', result, image, lat, lon)

    # ------------------------------------------------------------------
    # "Face only": server-side refusal of the core methods
    # ------------------------------------------------------------------

    def _face_only_kiosk(self, token):
        company = self._face_company(token)
        return bool(company and company.face_kiosk_enabled and company.face_only)

    @http.route()
    def employee_attendance_data(self, token, employee_id):
        if self._face_only_kiosk(token):
            return {}
        return super().employee_attendance_data(token, employee_id)

    @http.route()
    def scan_barcode(self, token, barcode):
        if self._face_only_kiosk(token):
            return {}
        return super().scan_barcode(token, barcode)

    @http.route()
    def manual_selection_with_geolocation(self, token, employee_id, pin_code, latitude=False, longitude=False):
        if self._face_only_kiosk(token):
            return {}
        return super().manual_selection_with_geolocation(token, employee_id, pin_code, latitude, longitude)

    @http.route()
    def employees_infos(self, token, limit, offset, domain):
        if self._face_only_kiosk(token):
            return []
        return super().employees_infos(token, limit, offset, domain)

    @http.route()
    def systray_attendance(self, latitude=False, longitude=False):
        employee, company = self._face_my_employee()
        if employee and company.face_mobile_enabled and company.face_only:
            return {}
        return super().systray_attendance(latitude, longitude)
