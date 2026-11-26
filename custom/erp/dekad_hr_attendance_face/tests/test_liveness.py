from unittest import skipIf

from odoo.tests import tagged
from odoo.tests.common import BaseCase

from ..lib import engine, liveness

np = engine.np


def face(yaw=0.0, size=120):
    nose = 130 + yaw * 60
    return np.array([80, 60, size, size, 100, 100, 160, 100, nose, 130, 105, 160, 155, 160, 0.95], dtype=np.float32)


@skipIf(np is None, "numpy is not installed")
@tagged('post_install', '-at_install', 'dekad_face')
class TestHeadTurnLiveness(BaseCase):

    def setUp(self):
        super().setUp()
        self.checker = liveness.HeadTurnLiveness()
        self.same = lambda i, j: 0.9
        self.other = lambda i, j: 0.05

    def check(self, yaws, challenge='left', elapsed=3.0, similarity=None):
        faces = [None if y is None else face(y) for y in yaws]
        return self.checker.check(faces, challenge, elapsed, similarity or self.same)

    def test_yaw_sign(self):
        self.assertGreater(liveness.yaw_ratio(face(0.4)), 0)   # own left
        self.assertLess(liveness.yaw_ratio(face(-0.4)), 0)     # own right
        self.assertAlmostEqual(liveness.yaw_ratio(face(0.0)), 0.0)

    def test_valid_left_and_right(self):
        result = self.check([0, 0, 0.4, 0.4, 0.4], 'left')
        self.assertTrue(result.ok)
        self.assertEqual(result.frontal, [0, 1])
        self.assertTrue(self.check([0, 0, -0.4, -0.4, -0.4], 'right').ok)

    def test_wrong_direction(self):
        self.assertEqual(self.check([0, 0, -0.4, -0.4, -0.4], 'left').reason, 'challenge_failed')

    def test_static_photo(self):
        self.assertEqual(self.check([0, 0, 0, 0, 0]).reason, 'challenge_failed')

    def test_turn_must_follow_frontal(self):
        self.assertEqual(self.check([0.4, 0.4, 0.4, 0, 0]).reason, 'challenge_failed')

    def test_no_frontal(self):
        self.assertEqual(self.check([0.4, 0.4, 0.4, 0.4, 0.4]).reason, 'no_frontal')

    def test_identity_must_not_change(self):
        self.assertEqual(self.check([0, 0, 0.4, 0.4, 0.4], similarity=self.other).reason, 'identity_changed')

    def test_too_fast(self):
        self.checker.MIN_ELAPSED = 1.0
        self.assertEqual(self.check([0, 0, 0.4, 0.4, 0.4], elapsed=0.2).reason, 'too_fast')

    def test_not_enough_faces(self):
        self.assertEqual(self.check([0, None, None, None, 0.4]).reason, 'no_face')

    def test_unknown_challenge(self):
        self.assertEqual(self.check([0, 0, 0.4, 0.4, 0.4], 'up').reason, 'challenge_failed')

    def test_pick_face(self):
        self.assertEqual(liveness.pick_face([face()])[2], 120)
        with self.assertRaises(engine.FaceInputError) as e:
            liveness.pick_face([])
        self.assertEqual(e.exception.code, 'no_face')
        with self.assertRaises(engine.FaceInputError) as e:
            liveness.pick_face([face(), face()])
        self.assertEqual(e.exception.code, 'multiple_faces')
        # A much smaller face in the background is tolerated.
        self.assertTrue(len(liveness.pick_face([face(), face(size=50)])))
        with self.assertRaises(engine.FaceInputError) as e:
            liveness.pick_face([face(size=30)])
        self.assertEqual(e.exception.code, 'face_too_small')

    def test_registry(self):
        self.assertIsInstance(liveness.get_checker('head_turn'), liveness.HeadTurnLiveness)
        self.assertIsInstance(liveness.get_checker('unknown'), liveness.HeadTurnLiveness)
        self.assertIn(self.checker.new_challenge(), ('left', 'right'))
