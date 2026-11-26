from unittest import skipIf

from odoo.tests import tagged
from odoo.tests.common import BaseCase

from ..lib import engine, matching

np = engine.np


def unit(vector):
    vector = np.asarray(vector, dtype=np.float32)
    return vector / np.linalg.norm(vector)


@skipIf(np is None, "numpy is not installed")
@tagged('post_install', '-at_install', 'dekad_face')
class TestMatchingPolicy(BaseCase):

    def setUp(self):
        super().setUp()
        rng = np.random.default_rng(7)
        self.vectors = [unit(rng.standard_normal(128)) for _i in range(3)]

    def gallery(self, rows):
        ids = np.array([employee_id for employee_id, _v in rows], dtype=np.int64)
        return ids, np.stack([vector for _id, vector in rows])

    def test_match_above_threshold_with_margin(self):
        ids, matrix = self.gallery([(10, self.vectors[0]), (20, self.vectors[1])])
        result = matching.match_one_to_many(self.vectors[0], ids, matrix, threshold=0.4, margin=0.06)
        self.assertEqual(result.status, matching.MATCHED)
        self.assertEqual(result.employee_id, 10)
        self.assertAlmostEqual(result.score, 1.0, places=5)

    def test_below_threshold_rejected(self):
        ids, matrix = self.gallery([(10, self.vectors[0]), (20, self.vectors[1])])
        probe = unit(self.vectors[2])  # unrelated person
        result = matching.match_one_to_many(probe, ids, matrix, threshold=0.4, margin=0.06)
        self.assertEqual(result.status, matching.BELOW_THRESHOLD)
        self.assertIsNone(result.employee_id)

    def test_threshold_boundary(self):
        ids, matrix = self.gallery([(10, self.vectors[0])])
        score = float(matrix[0] @ self.vectors[0])
        self.assertTrue(matching.match_one_to_many(self.vectors[0], ids, matrix, score, 0.0).matched)
        self.assertFalse(matching.match_one_to_many(self.vectors[0], ids, matrix, score + 1e-3, 0.0).matched)

    def test_ambiguous_rejected(self):
        # Two employees almost equally similar to the probe.
        probe = unit(self.vectors[0] + self.vectors[1])
        ids, matrix = self.gallery([(10, self.vectors[0]), (20, self.vectors[1])])
        result = matching.match_one_to_many(probe, ids, matrix, threshold=0.4, margin=0.06)
        self.assertEqual(result.status, matching.AMBIGUOUS)
        self.assertIsNone(result.employee_id)
        # The same probe passes when the margin policy is disabled.
        self.assertTrue(matching.match_one_to_many(probe, ids, matrix, threshold=0.4, margin=0.0).matched)

    def test_margin_uses_best_sample_per_employee(self):
        # Several samples of the same employee must not create an artificial "second best".
        ids, matrix = self.gallery([(10, self.vectors[0]), (10, unit(self.vectors[0] + 0.05)), (20, self.vectors[1])])
        result = matching.match_one_to_many(self.vectors[0], ids, matrix, threshold=0.4, margin=0.06)
        self.assertEqual(result.status, matching.MATCHED)
        self.assertEqual(result.employee_id, 10)
        self.assertLess(result.second_score, 0.4)

    def test_empty_gallery(self):
        result = matching.match_one_to_many(self.vectors[0], np.array([], dtype=np.int64), None, 0.4, 0.06)
        self.assertEqual(result.status, matching.NO_GALLERY)

    def test_one_to_one(self):
        matrix = np.stack([self.vectors[0]])
        self.assertTrue(matching.match_one_to_one(self.vectors[0], 10, matrix, 0.4).matched)
        self.assertEqual(matching.match_one_to_one(self.vectors[1], 10, matrix, 0.4).status, matching.BELOW_THRESHOLD)
        self.assertEqual(matching.match_one_to_one(self.vectors[0], 10, None, 0.4).status, matching.NO_GALLERY)
