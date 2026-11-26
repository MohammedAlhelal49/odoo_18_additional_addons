import base64
import itertools
import json
from unittest import SkipTest
from unittest.mock import patch

from odoo.tests import HttpCase, new_test_user

from ..lib import engine, liveness

np = engine.np

# A 1x1 PNG, used as the stored check-in photo by the fake engine.
TINY_PNG = (b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=')


def person_vector(person):
    vector = np.random.default_rng(1000 + person).standard_normal(engine.EMBEDDING_SIZE).astype(np.float32)
    return vector / np.linalg.norm(vector)


class FakeEngine:
    """Deterministic stand-in for FaceEngine.

    A "frame" is a base64 JSON payload describing who is in front of the
    camera and the head yaw, so tests exercise the real controller, nonce,
    rate limiting, liveness and matching code without real images.
    """

    def __init__(self):
        self.counter = itertools.count()
        self.vectors = {}

    def vector(self, person):
        if person not in self.vectors:
            self.vectors[person] = person_vector(person)
        return self.vectors[person]

    def frame(self, person, yaw=0.0, faces=1, size=120):
        payload = {'person': person, 'yaw': yaw, 'faces': faces, 'size': size, 'n': next(self.counter)}
        return base64.b64encode(json.dumps(payload).encode()).decode()

    def frames_for(self, person, challenge, count=5, turn=0.4):
        frontal = max(1, count * 2 // 5)
        sign = 1 if challenge == 'left' else -1
        return [self.frame(person, 0.0 if i < frontal else sign * turn) for i in range(count)]

    def decode(self, value, **kwargs):
        try:
            return json.loads(base64.b64decode(value, validate=True))
        except ValueError:
            raise engine.FaceInputError('bad_input') from None

    def detect(self, image):
        size = image['size']
        nose = 130 + image['yaw'] * 60  # eyes at x=100 and x=160
        face = np.array([80, 60, size, size, 100, 100, 160, 100, nose, 130, 105, 160, 155, 160, 0.95],
                        dtype=np.float32)
        return [face.copy() for _i in range(image['faces'])]

    def embed(self, image, face):
        return self.vector(image['person'])

    def to_jpeg(self, image, quality=80):
        return TINY_PNG


class FaceHttpCase(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if np is None:
            raise SkipTest("numpy is not installed")
        cls.fake = FakeEngine()
        cls.startClassPatcher(patch.object(engine, 'get_engine', return_value=cls.fake))
        cls.startClassPatcher(patch.object(engine, 'status', return_value=engine.STATUS_OK))
        cls.startClassPatcher(patch.object(liveness.HeadTurnLiveness, 'MIN_ELAPSED', 0.0))

        face_settings = {
            'face_kiosk_enabled': True,
            'face_mobile_enabled': True,
            'face_require_geolocation': False,
            'face_match_threshold': 0.40,
            'face_match_margin': 0.06,
        }
        cls.company_a = cls.env.company
        cls.company_a.write(face_settings)
        cls.company_b = cls.env['res.company'].create({'name': 'Face Company B', **face_settings})
        cls.token_a = cls.company_a.sudo().attendance_kiosk_key
        cls.token_b = cls.company_b.sudo().attendance_kiosk_key

        cls.emp_a1 = cls.env['hr.employee'].create({'name': 'Face A1', 'company_id': cls.company_a.id})
        cls.emp_a2 = cls.env['hr.employee'].create({'name': 'Face A2', 'company_id': cls.company_a.id})
        cls.emp_b1 = cls.env['hr.employee'].create({'name': 'Face B1', 'company_id': cls.company_b.id})
        cls.enroll(cls.emp_a1, 1)
        cls.enroll(cls.emp_a2, 2)
        cls.enroll(cls.emp_b1, 3)

    @classmethod
    def enroll(cls, employee, person, vectors=None):
        vectors = vectors if vectors is not None else [cls.fake.vector(person)]
        return cls.env['hr.face.profile'].sudo().create({
            'employee_id': employee.id,
            'consent_given': True,
            'sample_ids': [(0, 0, {
                'embedding': engine.embedding_to_bytes(vector),
                'detection_score': 0.99,
                'model_version': engine.MODEL_VERSION,
            }) for vector in vectors],
        })

    # -- kiosk helpers --------------------------------------------------

    def kiosk(self, route, **params):
        return self.make_jsonrpc_request(f'/dekad_face/kiosk/{route}', params)

    def kiosk_attempt(self, person=1, token=None, frames=None, **extra):
        token = token or self.token_a
        challenge = self.kiosk('challenge', token=token)
        self.assertTrue(challenge.get('nonce'), challenge)
        if frames is None:
            frames = self.fake.frames_for(person, challenge['challenge'], challenge['frames'])
        elif callable(frames):
            frames = frames(challenge)
        return self.kiosk('verify', token=token, nonce=challenge['nonce'], frames=frames, **extra)

    def attempts(self, **domain):
        return self.env['hr.face.attempt'].sudo().search(
            [(key, '=', value) for key, value in domain.items()])

    def new_user(self, login, groups, **kwargs):
        return new_test_user(self.env, login=login, password=login + '_pass1234', groups=groups, **kwargs)
