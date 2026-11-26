"""Tests with the real OpenCV engine and model files (skipped when unavailable)."""
import base64
import io
from unittest import SkipTest
from unittest.mock import patch

from PIL import Image

from odoo.exceptions import UserError
from odoo.tests import HttpCase, tagged
from odoo.tools.misc import file_path

from ..lib import engine, liveness


def encode(image, fmt='JPEG', **kwargs):
    buf = io.BytesIO()
    image.save(buf, format=fmt, **kwargs)
    return base64.b64encode(buf.getvalue()).decode()


@tagged('post_install', '-at_install', 'dekad_face')
class TestRealEngine(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.engine = engine.get_engine()
        if not cls.engine:
            raise SkipTest(f"face engine unavailable: {engine.status()}")
        with Image.open(file_path('hr/static/img/employee_han-image.jpg')) as img:
            cls.face_image = img.convert('RGB').resize((400, 400), Image.LANCZOS)

    def face_variant(self, brightness):
        return encode(self.face_image.point(lambda p: max(0, min(255, int(p * brightness)))), quality=90)

    # -- input hardening -------------------------------------------------

    def assertRejected(self, value, **kwargs):
        with self.assertRaises(engine.FaceInputError) as e:
            self.engine.decode(value, **kwargs)
        self.assertEqual(e.exception.code, 'bad_input')

    def test_decode_valid_formats(self):
        for fmt in ('JPEG', 'PNG'):
            image = self.engine.decode(encode(self.face_image, fmt))
            self.assertEqual(image.shape[2], 3)
        data_url = 'data:image/jpeg;base64,' + encode(self.face_image)
        self.assertEqual(self.engine.decode(data_url).shape[:2], (400, 400))

    def test_decode_rejects_malformed_input(self):
        self.assertRejected('not base64 !!!')
        self.assertRejected(base64.b64encode(b'plain text, not an image').decode())
        self.assertRejected(encode(self.face_image, 'GIF'))                       # not in allow-list
        self.assertRejected(encode(self.face_image, 'BMP'))
        self.assertRejected('data:image/gif;base64,' + encode(self.face_image))    # declared MIME not allowed
        self.assertRejected('data:image/png;base64,' + encode(self.face_image))    # declared/actual mismatch
        self.assertRejected('data:image/jpeg,' + encode(self.face_image))          # not base64 data URL
        truncated = base64.b64decode(encode(self.face_image))[:40]
        self.assertRejected(base64.b64encode(truncated).decode())

    def test_decode_enforces_limits(self):
        self.assertRejected(encode(Image.new('RGB', (2000, 200))))                # too wide for a frame
        self.assertRejected(encode(Image.new('RGB', (60, 60))))                    # too small
        self.assertRejected(encode(self.face_image), max_bytes=1000)              # too heavy
        # Oversized dimensions are refused from the header, before full decoding.
        self.assertRejected(encode(Image.new('L', (7000, 100)), 'PNG'), max_bytes=10 ** 7,
                            max_side=engine.ENROLL_MAX_SIDE)

    def test_frames_payload_limits(self):
        frame = encode(self.face_image)
        for frames in (None, 'x', [frame] * 2, [frame] * 9, [frame, 1, frame], ['a' * 10 ** 6] * 3):
            with self.assertRaises(engine.FaceInputError):
                engine.check_frames_payload(frames, 3, 8)
        engine.check_frames_payload([frame] * 3, 3, 8)

    # -- detection / embedding --------------------------------------------

    def test_detect_and_embed(self):
        image = self.engine.decode(self.face_variant(1.0))
        face = liveness.pick_face(self.engine.detect(image))
        vector = self.engine.embed(image, face)
        self.assertEqual(vector.shape, (engine.EMBEDDING_SIZE,))
        self.assertAlmostEqual(float(vector @ vector), 1.0, places=4)
        other = self.engine.decode(self.face_variant(0.8))
        similarity = float(vector @ self.engine.embed(other, liveness.pick_face(self.engine.detect(other))))
        self.assertGreater(similarity, 0.8)

    def test_no_face_in_noise(self):
        noise = Image.effect_noise((320, 240), 80).convert('RGB')
        self.assertEqual(self.engine.detect(self.engine.decode(encode(noise))), [])

    # -- enrollment + static photo replay ------------------------------------

    def test_enroll_and_static_photo_is_rejected(self):
        company = self.env.company
        company.write({'face_kiosk_enabled': True})
        employee = self.env['hr.employee'].create({'name': 'Real Face', 'company_id': company.id})
        Profile = self.env['hr.face.profile']
        with self.assertRaises(UserError):
            Profile.enroll_samples(employee.id, [self.face_variant(1.0)], True)  # fewer than 3 photos
        result = Profile.enroll_samples(employee.id, [self.face_variant(b) for b in (0.9, 1.0, 1.1)], True)
        self.assertEqual(result['accepted'], 3)
        profile = Profile.search([('employee_id', '=', employee.id)])
        self.assertEqual(len(profile.sample_ids), 3)
        self.assertTrue(profile.consent_given)

        # The same face enrolled for a second employee is refused (would be ambiguous).
        twin = self.env['hr.employee'].create({'name': 'Twin', 'company_id': company.id})
        with self.assertRaises(UserError):
            Profile.enroll_samples(twin.id, [self.face_variant(b) for b in (0.95, 1.05, 1.0)], True)

        # A printed photo held in front of the kiosk: right person, no head turn.
        token = company.sudo().attendance_kiosk_key
        with patch.object(liveness.HeadTurnLiveness, 'MIN_ELAPSED', 0.0):
            challenge = self.make_jsonrpc_request('/dekad_face/kiosk/challenge', {'token': token})
            frames = [self.face_variant(0.9 + i * 0.04) for i in range(challenge['frames'])]
            result = self.make_jsonrpc_request('/dekad_face/kiosk/verify', {
                'token': token, 'nonce': challenge['nonce'], 'frames': frames})
        self.assertEqual(result, {'error': 'liveness_failed'})
        self.assertFalse(employee.attendance_ids)
