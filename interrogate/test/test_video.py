import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Flask

from app.constants.codes import Code
from app.routes.api.video import make_mock_emotion_frame, video_bp
import app.routes.ws.video as ws_video


def _create_app() -> Flask:
    app = Flask("test")
    app.register_blueprint(video_bp)
    return app


def test_make_mock_emotion_frame_schema():
    rec = make_mock_emotion_frame("1", frame=3, seed=123)
    assert rec["suspect_id"] == 1
    assert rec["frame"] == 3
    assert "emotion_scores" in rec
    assert "au_intensities" in rec
    assert "head_pose" in rec


def test_mock_frame_endpoint_ok():
    app = _create_app()
    with app.test_client() as c:
        r = c.get("/api/video/mock/frame?suspect_id=1&frame=2&seed=9")
        assert r.status_code == 200
        body = r.get_json()
        assert body["code"] == int(Code.OK)
        assert body["data"]["suspect_id"] == 1
        assert body["data"]["frame"] == 2


def test_mock_frames_endpoint_validation():
    app = _create_app()
    with app.test_client() as c:
        r = c.get("/api/video/mock/frames?suspect_id=1&count=9999")
        assert r.status_code == 400
        body = r.get_json()
        assert body["code"] == int(Code.INVALID_PARAM)


def test_ws_handle_invalid_payload(monkeypatch):
    emitted = []

    def fake_emit(event, payload):
        emitted.append((event, payload))

    monkeypatch.setattr(ws_video, "emit", fake_emit)
    ns = ws_video.FaceNamespace("/ws/face")
    ns._handle("not-a-dict")
    assert emitted
    assert emitted[0][0] == "message"
    assert emitted[0][1]["code"] == int(Code.INVALID_PARAM)


def test_ws_handle_ok(monkeypatch):
    emitted = []

    def fake_emit(event, payload):
        emitted.append((event, payload))

    monkeypatch.setattr(ws_video, "emit", fake_emit)
    monkeypatch.setattr(ws_video, "_call_process_frame", lambda sid, img, frame: {"ok": True, "sid": sid, "frame": frame})

    ns = ws_video.FaceNamespace("/ws/face")
    ns._handle({"id": "u1", "image": "xxx", "frame": 7})
    assert emitted[-1] == ("message", {"ok": True, "sid": "u1", "frame": 7})
