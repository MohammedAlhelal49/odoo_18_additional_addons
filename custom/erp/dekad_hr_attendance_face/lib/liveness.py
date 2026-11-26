"""Pluggable liveness checks.

A checker issues a random challenge when the nonce is created and later
validates the captured frames against it. New checkers (e.g. an
anti-spoofing model) register themselves with :func:`register` and become
selectable in the Attendance settings.
"""
import math
import secrets

from .engine import MIN_FACE_SIDE, FaceInputError

_REGISTRY = {}

# YuNet landmark offsets in a face row (see FaceEngine.detect).
_RIGHT_EYE_X, _LEFT_EYE_X, _NOSE_X = 4, 6, 8


def register(cls):
    _REGISTRY[cls.code] = cls
    return cls


def get_checker(code):
    return _REGISTRY.get(code, HeadTurnLiveness)()


def selection():
    return [(cls.code, cls.label) for cls in _REGISTRY.values()]


def pick_face(faces):
    """Return the main face of a frame, or raise when the frame is unusable."""
    if not faces:
        raise FaceInputError('no_face')
    main = faces[0]
    if len(faces) > 1 and faces[1][2] * faces[1][3] > 0.5 * main[2] * main[3]:
        raise FaceInputError('multiple_faces')
    if min(main[2], main[3]) < MIN_FACE_SIDE:
        raise FaceInputError('face_too_small')
    return main


def yaw_ratio(face):
    """Horizontal nose offset from the eye midpoint, in inter-ocular units.

    Positive when the person turns towards their own left (the nose moves to
    the right of an un-mirrored camera image), negative towards their right.
    """
    right_eye, left_eye, nose = face[_RIGHT_EYE_X], face[_LEFT_EYE_X], face[_NOSE_X]
    inter = abs(left_eye - right_eye)
    if inter < 1:
        return math.nan
    return (nose - (right_eye + left_eye) / 2.0) / inter


class LivenessResult:
    __slots__ = ('ok', 'reason', 'frontal')

    def __init__(self, ok, reason=None, frontal=()):
        self.ok = ok
        self.reason = reason
        self.frontal = list(frontal)


class BaseLiveness:
    code = None
    label = None

    def new_challenge(self):
        raise NotImplementedError

    def check(self, faces, challenge, elapsed, similarity):
        """Validate the frames.

        :param faces: per-frame main face rows (``None`` for frames without a usable face)
        :param challenge: the challenge issued with the nonce
        :param elapsed: seconds between nonce issue and verification
        :param similarity: ``similarity(i, j)`` cosine similarity of frames i and j
        :return: LivenessResult with the indexes of frontal frames usable for matching
        """
        raise NotImplementedError


@register
class HeadTurnLiveness(BaseLiveness):
    """Frontal frames followed by a head turn in the challenged direction.

    Stops static photos and replayed captures (single-use nonce + random
    direction). Does not stop a recorded video that happens to show the
    right turn or a live deepfake: see the threat model in README.md.
    """

    code = 'head_turn'
    label = 'Head turn challenge'

    FRONTAL_MAX = 0.12
    TURN_MIN = 0.25
    CONSISTENCY_MIN = 0.28
    MIN_ELAPSED = 1.0
    MIN_FACES = 3

    def new_challenge(self):
        return secrets.choice(('left', 'right'))

    def check(self, faces, challenge, elapsed, similarity):
        if challenge not in ('left', 'right'):
            return LivenessResult(False, 'challenge_failed')
        if elapsed < self.MIN_ELAPSED:
            return LivenessResult(False, 'too_fast')
        present = [i for i, face in enumerate(faces) if face is not None]
        if len(present) < self.MIN_FACES:
            return LivenessResult(False, 'no_face')
        yaws = {i: yaw_ratio(faces[i]) for i in present}
        frontal = [i for i in present if abs(yaws[i]) <= self.FRONTAL_MAX]
        if not frontal:
            return LivenessResult(False, 'no_frontal')
        sign = 1 if challenge == 'left' else -1
        turned = [i for i in present if i > frontal[0] and sign * yaws[i] >= self.TURN_MIN]
        if not turned:
            return LivenessResult(False, 'challenge_failed')
        # The turned face must belong to the same person as the frontal one.
        if similarity(frontal[0], turned[-1]) < self.CONSISTENCY_MIN:
            return LivenessResult(False, 'identity_changed')
        return LivenessResult(True, frontal=frontal[:2])
