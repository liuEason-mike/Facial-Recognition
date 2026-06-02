import os
import sys
import types
from types import SimpleNamespace

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def _analysis_frame():
    return {
        "frame": 1,
        "dominant_emotion": 7,
        "emotion_scores": {},
        "region": {},
        "head_pose": {},
        "left_eye_gaze": {},
        "right_eye_gaze": {},
        "heart_rate": 0,
        "au_intensities": {},
    }


class FakeAnalyzer:
    def process_frame(self, _image):
        return None, "", _analysis_frame()


class EmptyAnalyzer:
    def process_frame(self, _image):
        return None, "未检测到人脸", {}


class RaisingAnalyzer:
    def process_frame(self, _image):
        raise RuntimeError("face analyzer unavailable")


face_analyzer_stub = types.ModuleType("app.service.video.face_analyzer")
face_analyzer_stub.FaceAnalyzer = lambda: FakeAnalyzer()
sys.modules["app.service.video.face_analyzer"] = face_analyzer_stub


class FakeRepo:
    def __init__(self):
        self.created = []
        self.list_calls = 0

    def create(self, payload):
        self.created.append(payload)
        return SimpleNamespace(id=len(self.created))

    def list_by_suspect_id(self, *_args, **_kwargs):
        self.list_calls += 1
        raise AssertionError("test_status=1 must not query historical records for synchronous baseline training")


class FakeAnomalyRepo:
    def __init__(self):
        self.created = []

    def create(self, payload):
        self.created.append(payload)
        return SimpleNamespace(id=len(self.created))


class FakeDetector:
    model_dir = "/tmp/test-models"

    def __init__(self):
        self.train_calls = []
        self.score_calls = []
        self.release_calls = []

    def train_baseline_from_records(self, suspect_id, records):
        self.train_calls.append((suspect_id, list(records)))
        return {"emotion": "fake-model.pkl"}

    def score_record(self, suspect_id, record):
        self.score_calls.append((suspect_id, record))
        return {
            "emotion": {"score": 0.1, "is_anomaly": False},
            "heart_rate": {"score": 0.1, "is_anomaly": False},
            "head_pose": {"score": 0.1, "is_anomaly": False},
            "eye_gaze": {"score": 0.1, "is_anomaly": False},
            "au_intensity": {"score": 0.1, "is_anomaly": False},
        }

    def release_cached_models(self, suspect_id):
        self.release_calls.append(suspect_id)


iso_detector_stub = types.ModuleType("app.service.video.isolation_forest.iso_forest_detector")
iso_detector_stub.IsolationForestDetector = lambda model_dir: FakeDetector()
iso_detector_stub.default_model_dir = lambda: "/tmp/test-models"
sys.modules["app.service.video.isolation_forest.iso_forest_detector"] = iso_detector_stub

from app.service.video import realtime_features as rf


class ImmediateExecutor:
    def submit(self, fn, *args, **kwargs):
        fn(*args, **kwargs)
        return SimpleNamespace(done=lambda: True)


def _patch_realtime_dependencies(monkeypatch):
    fake_repo = FakeRepo()
    fake_anomaly_repo = FakeAnomalyRepo()
    fake_detector = FakeDetector()
    monkeypatch.setattr(rf, "_b2b", lambda _image_b64: object())
    monkeypatch.setattr(rf, "_analyzer", FakeAnalyzer())
    monkeypatch.setattr(rf, "_repo", fake_repo)
    monkeypatch.setattr(rf, "_anomaly_repo", fake_anomaly_repo)
    monkeypatch.setattr(rf, "_iso_detector", fake_detector)
    monkeypatch.setattr(rf, "is_database_enabled", lambda: True, raising=False)
    if hasattr(rf, "_baseline_states"):
        rf._baseline_states.clear()
    if hasattr(rf, "_released_baselines"):
        rf._released_baselines.clear()
    return fake_repo, fake_anomaly_repo, fake_detector


ZERO_EMOTION_SCORES = {
    "angry": 0,
    "disgust": 0,
    "fear": 0,
    "happy": 0,
    "sad": 0,
    "surprise": 0,
    "neutral": 0,
}


def test_status_one_stops_baseline_without_sync_training(monkeypatch):
    fake_repo, _fake_anomaly_repo, fake_detector = _patch_realtime_dependencies(monkeypatch)

    result = rf.process_frame_ws_payload("image", "suspect-1", test_status=1)

    assert fake_repo.list_calls == 0
    assert fake_detector.train_calls == []
    assert result["baseline_status"] in {"ready", "training", "not_ready", "failed"}


def test_status_one_scores_ready_baseline_without_anomaly_db_write(monkeypatch):
    _fake_repo, fake_anomaly_repo, fake_detector = _patch_realtime_dependencies(monkeypatch)
    rf._baseline_states["suspect-1"] = {
        "records": rf.deque(maxlen=10),
        "status": "ready",
        "trained_count": 1,
        "future": None,
        "frozen": False,
        "last_error": None,
    }

    result = rf.process_frame_ws_payload("image", "suspect-1", test_status=1)

    assert result["baseline_status"] == "ready"
    assert result["anomaly_status"] == "ready"
    assert "anomaly_data" in result
    assert len(fake_detector.score_calls) == 1
    assert fake_anomaly_repo.created == []


def test_status_two_releases_models_after_returning_realtime_detection(monkeypatch):
    fake_repo, fake_anomaly_repo, fake_detector = _patch_realtime_dependencies(monkeypatch)
    rf._baseline_states["suspect-1"] = {
        "records": rf.deque(maxlen=10),
        "status": "ready",
        "trained_count": 1,
        "future": None,
        "frozen": True,
        "last_error": None,
    }

    result = rf.process_frame_ws_payload("image", "suspect-1", test_status=2)

    assert result["frame"] == 1
    assert result["dominant_emotion"] == 7
    assert "emotion_scores" in result
    assert "head_pose" in result
    assert "left_eye_gaze" in result
    assert "right_eye_gaze" in result
    assert "heart_rate" in result
    assert "au_intensities" in result
    assert len(fake_repo.created) == 1
    assert result["baseline_status"] == "released"
    assert result["anomaly_status"] == "released"
    assert "suspect-1" not in rf._baseline_states
    assert fake_detector.release_calls == ["suspect-1"]
    assert fake_detector.score_calls == []
    assert fake_anomaly_repo.created == []


def test_status_one_after_release_keeps_realtime_detection_without_scoring(monkeypatch):
    fake_repo, fake_anomaly_repo, fake_detector = _patch_realtime_dependencies(monkeypatch)
    rf._released_baselines.add("suspect-1")

    result = rf.process_frame_ws_payload("image", "suspect-1", test_status=1)

    assert result["frame"] == 1
    assert result["dominant_emotion"] == 7
    assert "emotion_scores" in result
    assert "head_pose" in result
    assert "left_eye_gaze" in result
    assert "right_eye_gaze" in result
    assert "heart_rate" in result
    assert "au_intensities" in result
    assert len(fake_repo.created) == 1
    assert result["baseline_status"] == "released"
    assert result["anomaly_status"] == "released"
    assert "suspect-1" not in rf._baseline_states
    assert fake_detector.score_calls == []
    assert fake_anomaly_repo.created == []


def test_status_zero_collects_and_trains_baseline(monkeypatch):
    _fake_repo, _fake_anomaly_repo, fake_detector = _patch_realtime_dependencies(monkeypatch)
    monkeypatch.setattr(rf, "_baseline_executor", ImmediateExecutor())
    monkeypatch.setattr(rf, "_BASELINE_MIN_SAMPLES", 1)
    monkeypatch.setattr(rf, "_BASELINE_TRAIN_EVERY", 1)

    result = rf.process_frame_ws_payload("image", "suspect-1", test_status=0)

    assert len(fake_detector.train_calls) == 1
    suspect_id, records = fake_detector.train_calls[0]
    assert suspect_id == "suspect-1"
    assert len(records) == 1
    assert "anomaly_data" not in result
    assert result["baseline_status"] in {"collecting", "training", "ready"}


def test_process_frame_returns_performance_timings(monkeypatch):
    _fake_repo, _fake_anomaly_repo, _fake_detector = _patch_realtime_dependencies(monkeypatch)

    result = rf.process_frame_ws_payload("image", "suspect-1", test_status=0)

    assert result["processing_ms"] >= 0
    assert set(result["performance"]) == {
        "decode_ms",
        "emotion_ms",
        "face_analyze_ms",
        "face_landmark_ms",
        "db_ms",
        "baseline_ms",
        "anomaly_ms",
        "total_ms",
    }
    assert result["performance"]["total_ms"] == result["processing_ms"]


def test_process_frame_skips_realtime_db_write_when_database_disabled(monkeypatch):
    fake_repo, _fake_anomaly_repo, _fake_detector = _patch_realtime_dependencies(monkeypatch)
    monkeypatch.setattr(rf, "is_database_enabled", lambda: False, raising=False)

    result = rf.process_frame_ws_payload("image", "suspect-1", test_status=0)

    assert result["frame"] == 1
    assert fake_repo.created == []


def test_process_frame_returns_zero_emotion_scores_when_face_analysis_is_empty(monkeypatch):
    fake_repo, _fake_anomaly_repo, fake_detector = _patch_realtime_dependencies(monkeypatch)
    monkeypatch.setattr(rf, "_analyzer", EmptyAnalyzer())

    result = rf.process_frame_ws_payload("image", "suspect-1", test_status=0)

    assert result["suspect_id"] == "suspect-1"
    assert result["dominant_emotion"] == 7
    assert result["emotion_scores"] == ZERO_EMOTION_SCORES
    assert result["anomaly_status"] == "skipped"
    assert result["baseline_status"] == "not_ready"
    assert result["performance"]["total_ms"] == result["processing_ms"]
    assert fake_repo.created == []
    assert fake_detector.train_calls == []


def test_process_frame_returns_zero_emotion_scores_when_face_analysis_raises(monkeypatch):
    fake_repo, _fake_anomaly_repo, fake_detector = _patch_realtime_dependencies(monkeypatch)
    monkeypatch.setattr(rf, "_analyzer", RaisingAnalyzer())

    result = rf.process_frame_ws_payload("image", "suspect-1", test_status=1)

    assert result["suspect_id"] == "suspect-1"
    assert result["emotion_scores"] == ZERO_EMOTION_SCORES
    assert result["baseline_status"] == "not_ready"
    assert result["anomaly_status"] == "skipped"
    assert fake_repo.created == []
    assert fake_detector.score_calls == []


def test_raw_ws_request_echoes_client_seq(monkeypatch):
    from app.routes.ws import video as ws_video

    monkeypatch.setattr(
        ws_video,
        "process_frame_ws_payload",
        lambda *_args, **_kwargs: {"frame": 1},
    )

    result = ws_video.process_raw_ws_request({
        "id": "suspect-1",
        "image": "image",
        "test_status": 0,
        "client_seq": 12,
    })

    assert result["client_seq"] == 12
