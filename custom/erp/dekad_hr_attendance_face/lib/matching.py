"""Matching policy: similarity threshold plus a margin between the top two employees."""

try:
    import numpy as np
except ImportError:
    np = None

MATCHED = 'matched'
BELOW_THRESHOLD = 'below_threshold'
AMBIGUOUS = 'ambiguous'
NO_GALLERY = 'no_gallery'


class MatchResult:
    __slots__ = ('status', 'employee_id', 'score', 'second_score')

    def __init__(self, status, employee_id=None, score=0.0, second_score=0.0):
        self.status = status
        self.employee_id = employee_id
        self.score = score
        self.second_score = second_score

    @property
    def matched(self):
        return self.status == MATCHED


def best_scores(probe, employee_ids, matrix):
    """Best cosine similarity per employee (vectors are L2-normalised)."""
    scores = matrix @ probe
    unique, inverse = np.unique(employee_ids, return_inverse=True)
    best = np.full(len(unique), -np.inf, dtype=np.float32)
    np.maximum.at(best, inverse, scores)
    return unique, best


def match_one_to_many(probe, employee_ids, matrix, threshold, margin):
    """1:N identification. Rejects when below threshold or when the best
    employee is not ahead of the second best by at least ``margin``."""
    if matrix is None or not len(employee_ids):
        return MatchResult(NO_GALLERY)
    unique, best = best_scores(probe, employee_ids, matrix)
    order = np.argsort(best)[::-1]
    top1 = float(best[order[0]])
    top2 = float(best[order[1]]) if len(order) > 1 else -1.0
    employee_id = int(unique[order[0]])
    if top1 < threshold:
        return MatchResult(BELOW_THRESHOLD, None, top1, top2)
    if len(order) > 1 and top1 - top2 < margin:
        return MatchResult(AMBIGUOUS, None, top1, top2)
    return MatchResult(MATCHED, employee_id, top1, top2)


def match_one_to_one(probe, employee_id, matrix, threshold):
    """1:1 verification against the samples of one claimed employee."""
    if matrix is None or not len(matrix):
        return MatchResult(NO_GALLERY)
    score = float(np.max(matrix @ probe))
    if score < threshold:
        return MatchResult(BELOW_THRESHOLD, None, score)
    return MatchResult(MATCHED, employee_id, score)
