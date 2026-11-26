"""Face engine: lazy OpenCV loading, safe image decoding, detection and embeddings.

Nothing in this module logs image bytes or embeddings.
"""
import base64
import binascii
import hashlib
import io
import logging
import os
import threading

_logger = logging.getLogger(__name__)

try:
    import numpy as np
    import cv2
except ImportError:  # optional dependencies, see README.md
    np = cv2 = None

try:
    from PIL import Image
except ImportError:
    Image = None

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'face_models')
DETECTOR_FILE = 'face_detection_yunet_2023mar.onnx'
RECOGNIZER_FILE = 'face_recognition_sface_2021dec.onnx'
MODEL_SHA256 = {
    DETECTOR_FILE: '8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4',
    RECOGNIZER_FILE: '0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79',
}
MODEL_VERSION = 'yunet-2023mar/sface-2021dec'
EMBEDDING_SIZE = 128

# WebP is deliberately excluded: Pillow wheels are not always built with WebP support.
ALLOWED_MIME_TYPES = ('image/jpeg', 'image/png')
PIL_FORMATS = {'image/jpeg': 'JPEG', 'image/png': 'PNG'}

# Limits for kiosk/mobile frames (the client sends ~320px JPEGs of 10-30 KB).
FRAME_MAX_BYTES = 400 * 1024
FRAME_MAX_SIDE = 1280
FRAME_MIN_SIDE = 96
# Limits for enrollment images uploaded by an administrator.
ENROLL_MAX_BYTES = 6 * 1024 * 1024
ENROLL_MAX_SIDE = 6000
# Images are downscaled to this longest side before detection.
WORK_MAX_SIDE = 640

DETECTION_SCORE = 0.7
MIN_FACE_SIDE = 48

STATUS_OK = 'ok'
STATUS_MISSING_LIBS = 'missing_libs'
STATUS_MISSING_MODEL = 'missing_model'
STATUS_CHECKSUM = 'checksum_mismatch'
STATUS_LOAD_ERROR = 'load_error'

_lock = threading.Lock()
_engine = None
_status = None


class FaceInputError(ValueError):
    """Raised on malformed or out-of-policy input. ``code`` is safe to audit."""

    def __init__(self, code='bad_input'):
        super().__init__(code)
        self.code = code


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _load():
    global _engine, _status
    if np is None or cv2 is None or Image is None:
        _status = STATUS_MISSING_LIBS
        return
    if not (hasattr(cv2, 'FaceDetectorYN') and hasattr(cv2, 'FaceRecognizerSF')):
        _status = STATUS_MISSING_LIBS
        return
    paths = {}
    for name, expected in MODEL_SHA256.items():
        path = os.path.join(MODEL_DIR, name)
        if not os.path.isfile(path):
            _status = STATUS_MISSING_MODEL
            return
        if _sha256(path) != expected:
            _logger.error("Face model %s does not match its expected SHA-256 checksum", name)
            _status = STATUS_CHECKSUM
            return
        paths[name] = path
    try:
        _engine = FaceEngine(paths[DETECTOR_FILE], paths[RECOGNIZER_FILE])
        _status = STATUS_OK
    except Exception:  # noqa: BLE001 - any OpenCV failure disables the feature
        _logger.exception("Could not load the face recognition models")
        _status = STATUS_LOAD_ERROR


def status():
    """Return the engine status code; models are loaded once per process."""
    if _status is None:
        with _lock:
            if _status is None:
                _load()
    return _status


def get_engine():
    """Return the process-wide FaceEngine, or None when unavailable."""
    return _engine if status() == STATUS_OK else None


def check_frames_payload(frames, min_count, max_count, max_bytes=FRAME_MAX_BYTES):
    """Cheap structural checks done before any decoding."""
    if not isinstance(frames, list) or not min_count <= len(frames) <= max_count:
        raise FaceInputError('bad_input')
    max_len = (max_bytes * 4) // 3 + 64  # base64 overhead + data-URL header
    for frame in frames:
        if not isinstance(frame, str) or not frame or len(frame) > max_len:
            raise FaceInputError('bad_input')


def _sniff_mime(data):
    if data[:3] == b'\xff\xd8\xff':
        return 'image/jpeg'
    if data[:8] == b'\x89PNG\r\n\x1a\n':
        return 'image/png'
    return None


def decode_payload(value, max_bytes):
    """Decode a base64 string / data URL into raw bytes and its sniffed MIME type."""
    declared = None
    if value.startswith('data:'):
        header, sep, value = value.partition(',')
        if not sep or ';base64' not in header:
            raise FaceInputError('bad_input')
        declared = header[5:].split(';', 1)[0].strip().lower()
        if declared not in ALLOWED_MIME_TYPES:
            raise FaceInputError('bad_input')
    try:
        data = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError):
        raise FaceInputError('bad_input') from None
    if not data or len(data) > max_bytes:
        raise FaceInputError('bad_input')
    mime = _sniff_mime(data)
    if mime is None or (declared and declared != mime):
        raise FaceInputError('bad_input')
    return data, mime


class FaceEngine:
    """Thin wrapper around OpenCV's YuNet detector and SFace recognizer.

    OpenCV DNN objects are not thread-safe; a lock serialises calls in
    threaded (non-prefork) mode. Prefork workers each own their engine.
    """

    def __init__(self, detector_path, recognizer_path):
        cv2.setNumThreads(1)
        self._lock = threading.Lock()
        self.detector = cv2.FaceDetectorYN.create(detector_path, '', (320, 320), DETECTION_SCORE, 0.3, 50)
        self.recognizer = cv2.FaceRecognizerSF.create(recognizer_path, '')

    def decode(self, value, max_bytes=FRAME_MAX_BYTES, max_side=FRAME_MAX_SIDE, min_side=FRAME_MIN_SIDE):
        """Validate and decode one image. Raises FaceInputError on any problem."""
        data, mime = decode_payload(value, max_bytes)
        try:
            # Header-only parse: dimensions are checked before full decoding.
            with Image.open(io.BytesIO(data)) as img:
                if img.format != PIL_FORMATS[mime]:
                    raise FaceInputError('bad_input')
                width, height = img.size
        except FaceInputError:
            raise
        except Exception:  # noqa: BLE001 - malformed images of any kind
            raise FaceInputError('bad_input') from None
        if max(width, height) > max_side or min(width, height) < min_side:
            raise FaceInputError('bad_input')
        image = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is None or image.ndim != 3:
            raise FaceInputError('bad_input')
        scale = WORK_MAX_SIDE / max(image.shape[:2])
        if scale < 1:
            image = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        return image

    def detect(self, image):
        """Return detected faces sorted by area (largest first).

        Each face is a 15-float array: x, y, w, h, right eye (x, y), left eye
        (x, y), nose tip (x, y), right/left mouth corners (x, y), score.
        """
        height, width = image.shape[:2]
        with self._lock:
            self.detector.setInputSize((width, height))
            _retval, faces = self.detector.detect(image)
        if faces is None:
            return []
        return sorted((f for f in faces), key=lambda f: f[2] * f[3], reverse=True)

    def embed(self, image, face):
        """Return the L2-normalised 128-d SFace embedding of ``face``."""
        with self._lock:
            aligned = self.recognizer.alignCrop(image, face)
            feature = self.recognizer.feature(aligned)
        vector = np.asarray(feature, dtype=np.float32).reshape(-1)
        norm = float(np.linalg.norm(vector))
        if not norm:
            raise FaceInputError('no_face')
        return vector / norm

    @staticmethod
    def to_jpeg(image, quality=80):
        ok, buf = cv2.imencode('.jpg', image, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        return base64.b64encode(buf.tobytes()) if ok else False


def embedding_to_bytes(vector):
    return base64.b64encode(np.asarray(vector, dtype=np.float32).tobytes())


def embedding_from_bytes(value):
    raw = base64.b64decode(bytes(value))
    vector = np.frombuffer(raw, dtype=np.float32)
    if vector.shape != (EMBEDDING_SIZE,):
        return None
    return vector
