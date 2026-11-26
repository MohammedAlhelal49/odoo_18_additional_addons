from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.tests import tagged

from ..lib import engine
from .common import FaceHttpCase, np


@tagged('post_install', '-at_install', 'dekad_face')
class TestFaceKiosk(FaceHttpCase):

    # -- kiosk token ----------------------------------------------------

    def test_invalid_token_gets_nothing(self):
        for token in ('wrong-token', '', None, ['list'], 12345):
            self.assertEqual(self.kiosk('config', token=token), {})
            self.assertEqual(self.kiosk('challenge', token=token), {})
            self.assertEqual(self.kiosk('verify', token=token, nonce='x' * 40, frames=[]), {})
        self.assertFalse(self.env['hr.face.challenge'].sudo().search([]))
        self.assertFalse(self.attempts())

    def test_disabled_kiosk_gets_nothing(self):
        self.company_a.face_kiosk_enabled = False
        self.assertEqual(self.kiosk('config', token=self.token_a), {})
        self.assertEqual(self.kiosk('challenge', token=self.token_a), {})

    def test_config(self):
        config = self.kiosk('config', token=self.token_a)
        self.assertEqual(config, {'enabled': True, 'available': True, 'face_only': False})

    # -- recognition ----------------------------------------------------

    def test_successful_check_in_and_out(self):
        result = self.kiosk_attempt(person=1)
        self.assertEqual(result['id'], self.emp_a1.id)
        self.assertEqual(result['employee_name'], 'Face A1')
        attendance = self.emp_a1.last_attendance_id
        self.assertEqual(attendance.in_mode, 'face_kiosk')
        self.assertFalse(attendance.check_out)
        attempt = self.attempts(result='success')
        self.assertEqual(attempt.employee_id, self.emp_a1)
        self.assertEqual(attempt.attendance_id, attendance)
        self.assertEqual(attempt.reason, 'ok')

        self.kiosk_attempt(person=1)
        self.assertTrue(attendance.check_out)
        self.assertEqual(attendance.out_mode, 'face_kiosk')

    def test_unknown_face_not_recognized(self):
        result = self.kiosk_attempt(person=99)
        self.assertEqual(result, {'error': 'not_recognized'})
        self.assertFalse(self.emp_a1.last_attendance_id)
        self.assertEqual(self.attempts(result='failure').reason, 'below_threshold')

    def test_ambiguous_match_rejected(self):
        # Person 50 looks equally like A1 and A2.
        mixed = self.fake.vector(1) + self.fake.vector(2)
        self.fake.vectors[50] = mixed / np.linalg.norm(mixed)
        self.addCleanup(self.fake.vectors.pop, 50)
        result = self.kiosk_attempt(person=50)
        self.assertEqual(result, {'error': 'not_recognized'})
        self.assertEqual(self.attempts(result='failure').reason, 'ambiguous')

    def test_liveness_failure(self):
        static = lambda challenge: [self.fake.frame(1) for _i in range(challenge['frames'])]  # noqa: E731
        self.assertEqual(self.kiosk_attempt(frames=static), {'error': 'liveness_failed'})
        self.assertEqual(self.attempts(result='failure').reason, 'challenge_failed')
        self.assertFalse(self.emp_a1.last_attendance_id)

    def test_wrong_direction(self):
        def wrong(challenge):
            return self.fake.frames_for(1, 'right' if challenge['challenge'] == 'left' else 'left', challenge['frames'])
        self.assertEqual(self.kiosk_attempt(frames=wrong), {'error': 'liveness_failed'})

    def test_identical_frames_rejected(self):
        same = self.fake.frame(1)
        self.assertEqual(self.kiosk_attempt(frames=lambda c: [same] * c['frames']), {'error': 'liveness_failed'})

    def test_multiple_faces(self):
        def crowd(challenge):
            frames = self.fake.frames_for(1, challenge['challenge'], challenge['frames'])
            frames[0] = self.fake.frame(1, faces=2)
            return frames
        self.assertEqual(self.kiosk_attempt(frames=crowd), {'error': 'multiple_faces'})

    # -- nonce ----------------------------------------------------------

    def test_nonce_single_use(self):
        challenge = self.kiosk('challenge', token=self.token_a)
        frames = self.fake.frames_for(1, challenge['challenge'], challenge['frames'])
        first = self.kiosk('verify', token=self.token_a, nonce=challenge['nonce'], frames=frames)
        self.assertEqual(first['id'], self.emp_a1.id)
        replay = self.kiosk('verify', token=self.token_a, nonce=challenge['nonce'],
                            frames=self.fake.frames_for(1, challenge['challenge'], challenge['frames']))
        self.assertEqual(replay, {'error': 'expired'})
        self.assertEqual(self.attempts(result='failure').reason, 'invalid_nonce')
        self.assertEqual(len(self.emp_a1.attendance_ids), 1)

    def test_nonce_burnt_even_on_failure(self):
        challenge = self.kiosk('challenge', token=self.token_a)
        self.kiosk('verify', token=self.token_a, nonce=challenge['nonce'], frames=['bad'])
        frames = self.fake.frames_for(1, challenge['challenge'], challenge['frames'])
        self.assertEqual(self.kiosk('verify', token=self.token_a, nonce=challenge['nonce'], frames=frames),
                         {'error': 'expired'})

    def test_expired_nonce(self):
        challenge = self.kiosk('challenge', token=self.token_a)
        self.env['hr.face.challenge'].sudo().search([]).write(
            {'expires_at': fields.Datetime.now() - timedelta(seconds=1)})
        frames = self.fake.frames_for(1, challenge['challenge'], challenge['frames'])
        self.assertEqual(self.kiosk('verify', token=self.token_a, nonce=challenge['nonce'], frames=frames),
                         {'error': 'expired'})
        self.assertEqual(self.attempts(result='failure').reason, 'expired_nonce')

    def test_unbound_or_forged_nonce(self):
        frames = self.fake.frames_for(1, 'left')
        self.assertEqual(self.kiosk('verify', token=self.token_a, nonce='f' * 43, frames=frames), {'error': 'expired'})
        self.assertEqual(self.kiosk('verify', token=self.token_a, nonce=None, frames=frames), {'error': 'expired'})
        # A nonce issued for kiosk B cannot be used on kiosk A.
        challenge_b = self.kiosk('challenge', token=self.token_b)
        frames = self.fake.frames_for(1, challenge_b['challenge'], challenge_b['frames'])
        self.assertEqual(self.kiosk('verify', token=self.token_a, nonce=challenge_b['nonce'], frames=frames),
                         {'error': 'expired'})
        self.assertEqual(self.attempts(reason='nonce_mismatch').company_id, self.company_a)

    def test_only_nonce_hash_is_stored(self):
        challenge = self.kiosk('challenge', token=self.token_a)
        record = self.env['hr.face.challenge'].sudo().search([])
        self.assertEqual(len(record), 1)
        self.assertNotEqual(record.nonce_hash, challenge['nonce'])
        self.assertEqual(record.challenge, challenge['challenge'])

    # -- client-sent identity ------------------------------------------

    def test_client_sent_identity_rejected(self):
        for extra in ({'employee_id': self.emp_a2.id}, {'embedding': [0.1] * 128}, {'match': True},
                      {'score': 0.99}, {'company_id': self.company_b.id}):
            result = self.kiosk_attempt(person=1, **extra)
            self.assertEqual(result, {'error': 'error'}, extra)
        self.assertFalse(self.emp_a1.attendance_ids | self.emp_a2.attendance_ids)
        self.assertEqual(set(self.attempts(result='failure').mapped('reason')), {'tampered'})

    def test_response_contains_no_biometric_data(self):
        result = self.kiosk_attempt(person=1)
        flat = str(result).lower()
        for word in ('embedding', 'score', 'sample', 'descriptor'):
            self.assertNotIn(word, flat)

    # -- company isolation ---------------------------------------------

    def test_company_isolation(self):
        # Person 3 is enrolled in company B only.
        self.assertEqual(self.kiosk_attempt(person=3, token=self.token_a), {'error': 'not_recognized'})
        result = self.kiosk_attempt(person=3, token=self.token_b)
        self.assertEqual(result['id'], self.emp_b1.id)
        # And company B's kiosk cannot recognise company A employees.
        self.assertEqual(self.kiosk_attempt(person=1, token=self.token_b), {'error': 'not_recognized'})

    def test_employee_moved_to_other_company(self):
        self.assertEqual(self.kiosk_attempt(person=1)['id'], self.emp_a1.id)
        self.emp_a1.company_id = self.company_b
        self.assertEqual(self.kiosk_attempt(person=1), {'error': 'not_recognized'})

    def test_archived_employee_not_recognized(self):
        self.emp_a1.action_archive()
        self.assertFalse(self.env['hr.face.profile'].sudo().search([('employee_id', '=', self.emp_a1.id)]))
        self.assertEqual(self.kiosk_attempt(person=1), {'error': 'not_recognized'})

    # -- rate limiting --------------------------------------------------

    def test_failure_lockout_per_ip(self):
        self.company_a.face_max_failures_ip = 3
        for _i in range(3):
            self.assertEqual(self.kiosk_attempt(person=99), {'error': 'not_recognized'})
        # Locked: even a valid face is refused, and no new challenge is issued.
        self.assertEqual(self.kiosk('challenge', token=self.token_a), {'error': 'locked'})
        self.assertFalse(self.emp_a1.attendance_ids)
        self.assertTrue(self.attempts(result='locked'))

    def test_lockout_blocks_verify(self):
        self.company_a.face_max_failures_ip = 2
        challenge = self.kiosk('challenge', token=self.token_a)
        for _i in range(2):
            self.kiosk_attempt(person=99)
        frames = self.fake.frames_for(1, challenge['challenge'], challenge['frames'])
        self.assertEqual(self.kiosk('verify', token=self.token_a, nonce=challenge['nonce'], frames=frames),
                         {'error': 'locked'})

    def test_failure_lockout_per_kiosk(self):
        self.company_a.write({'face_max_failures_ip': 100, 'face_max_failures_kiosk': 2})
        for _i in range(2):
            self.kiosk_attempt(person=99)
        self.assertEqual(self.kiosk('challenge', token=self.token_a), {'error': 'locked'})
        # Another kiosk on the same IP keeps working (different kiosk key, IP limit not reached).
        self.assertTrue(self.kiosk('challenge', token=self.token_b).get('nonce'))

    def test_challenge_rate_limit(self):
        self.company_a.face_max_challenges = 3
        for _i in range(2):
            self.assertTrue(self.kiosk('challenge', token=self.token_a).get('nonce'))
        self.assertEqual(self.kiosk('challenge', token=self.token_a), {'error': 'rate_limited'})
        self.assertEqual(self.kiosk('challenge', token=self.token_a), {'error': 'locked'})

    def test_lockout_expires(self):
        self.company_a.face_max_failures_ip = 1
        self.kiosk_attempt(person=99)
        self.assertEqual(self.kiosk('challenge', token=self.token_a), {'error': 'locked'})
        self.env['hr.face.throttle'].sudo().search([]).write(
            {'locked_until': fields.Datetime.now() - timedelta(seconds=1)})
        self.assertEqual(self.kiosk_attempt(person=1)['id'], self.emp_a1.id)

    # -- input ----------------------------------------------------------

    def test_frame_count_limits(self):
        self.assertEqual(self.kiosk_attempt(frames=lambda c: [self.fake.frame(1)] * 2), {'error': 'bad_input'})
        many = lambda c: [self.fake.frame(1) for _i in range(9)]  # noqa: E731
        self.assertEqual(self.kiosk_attempt(frames=many), {'error': 'bad_input'})
        self.assertEqual(self.kiosk_attempt(frames=lambda c: 'not-a-list'), {'error': 'bad_input'})
        self.assertEqual(self.kiosk_attempt(frames=lambda c: [1, 2, 3]), {'error': 'bad_input'})

    def test_photo_storage(self):
        self.company_a.face_store_photo = True
        self.kiosk_attempt(person=1)
        attendance = self.emp_a1.last_attendance_id
        self.assertTrue(attendance.face_photo_in)
        # Purge after retention.
        attachments = self.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'hr.attendance'), ('res_id', '=', attendance.id), ('res_field', '=', 'face_photo_in')])
        self.env.cr.execute("UPDATE ir_attachment SET create_date = %s WHERE id IN %s",
                            (fields.Datetime.now() - timedelta(days=31), tuple(attachments.ids)))
        attachments.invalidate_recordset()
        self.env['hr.attendance']._cron_face_purge_photos()
        attendance.invalidate_recordset()
        self.assertFalse(attendance.face_photo_in)

    # -- face only ------------------------------------------------------

    def test_face_only_blocks_core_kiosk_methods(self):
        self.emp_a1.barcode = 'FACEA1'
        result = self.make_jsonrpc_request('/hr_attendance/manual_selection', {
            'token': self.token_a, 'employee_id': self.emp_a1.id, 'pin_code': False})
        self.assertEqual(result['id'], self.emp_a1.id)  # standard behaviour unchanged

        self.company_a.face_only = True
        self.assertEqual(self.make_jsonrpc_request('/hr_attendance/manual_selection', {
            'token': self.token_a, 'employee_id': self.emp_a2.id, 'pin_code': False}), {})
        self.assertEqual(self.make_jsonrpc_request('/hr_attendance/attendance_barcode_scanned', {
            'token': self.token_a, 'barcode': 'FACEA1'}), {})
        self.assertEqual(self.make_jsonrpc_request('/hr_attendance/employees_infos', {
            'token': self.token_a, 'limit': 10, 'offset': 0, 'domain': []}), [])
        self.assertFalse(self.emp_a2.attendance_ids)
        # Face recognition still works.
        self.assertEqual(self.kiosk_attempt(person=2)['id'], self.emp_a2.id)
        # Kiosk B (face only disabled) is unaffected.
        self.assertTrue(self.make_jsonrpc_request('/hr_attendance/manual_selection', {
            'token': self.token_b, 'employee_id': self.emp_b1.id, 'pin_code': False}))

    def test_engine_unavailable(self):
        with patch.object(engine, 'status', return_value=engine.STATUS_MISSING_LIBS), \
                patch.object(engine, 'get_engine', return_value=None):
            self.assertEqual(self.kiosk('challenge', token=self.token_a), {'error': 'unavailable'})
            self.assertEqual(self.kiosk('config', token=self.token_a)['available'], False)
