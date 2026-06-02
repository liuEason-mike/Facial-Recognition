import io
import json
import os
import sys
from urllib.error import HTTPError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Flask

from app.constants.codes import Code
from app.routes.api.asr_diarization import asr_diarization_bp
from app.service.audio import speaker_diarization as diarization_module
from app.service.audio.speaker_diarization import (
    PyannoteDiarizationClient,
    PyannoteDiarizationError,
    align_speaker_segments,
    normalize_pyannote_segments,
)


def _create_app() -> Flask:
    app = Flask("test-speaker-diarization")
    app.register_blueprint(asr_diarization_bp)
    return app


def test_normalize_pyannote_response_maps_external_speakers_to_stable_labels():
    payload = {
        "code": 0,
        "message": "success",
        "data": [
            {"speaker": "SPEAKER_01", "start": 0.942, "end": 3.305, "duration": 2.362},
            {"speaker": "SPEAKER_00", "start": 5.06, "end": 8.654, "duration": 3.594},
            {"speaker": "SPEAKER_01", "start": 9.802, "end": 19.285, "duration": 9.484},
            {"speaker": "BROKEN", "start": 20.0},
        ],
    }

    assert normalize_pyannote_segments(payload) == [
        {
            "speaker": "A",
            "external_speaker": "SPEAKER_01",
            "start_sec": 0.942,
            "end_sec": 3.305,
            "duration": 2.362,
            "source": "pyannote",
        },
        {
            "speaker": "B",
            "external_speaker": "SPEAKER_00",
            "start_sec": 5.06,
            "end_sec": 8.654,
            "duration": 3.594,
            "source": "pyannote",
        },
        {
            "speaker": "A",
            "external_speaker": "SPEAKER_01",
            "start_sec": 9.802,
            "end_sec": 19.285,
            "duration": 9.484,
            "source": "pyannote",
        },
    ]


def test_align_speaker_segments_concatenates_asr_by_max_overlap():
    diarized_segments = [
        {"speaker": "A", "start_sec": 0.0, "end_sec": 4.0, "source": "pyannote"},
        {"speaker": "B", "start_sec": 4.0, "end_sec": 8.0, "source": "pyannote"},
    ]
    asr_segments = [
        {"start": 0.5, "end": 2.0, "text": "第一句"},
        {"start": 2.5, "end": 4.5, "text": "交叉片段"},
        {"start": 5.0, "end": 7.0, "text": "第二句"},
    ]

    result = align_speaker_segments(
        diarized_segments,
        asr_segments,
        session_id="session-1",
        suspect_id="suspect-1",
    )

    assert result == [
        {
            "speaker": "A",
            "start": "00:00:00",
            "end": "00:00:04",
            "start_sec": 0.0,
            "end_sec": 4.0,
            "source": "pyannote",
            "session_id": "session-1",
            "suspect_id": "suspect-1",
            "text": "第一句交叉片段",
        },
        {
            "speaker": "B",
            "start": "00:00:04",
            "end": "00:00:08",
            "start_sec": 4.0,
            "end_sec": 8.0,
            "source": "pyannote",
            "session_id": "session-1",
            "suspect_id": "suspect-1",
            "text": "第二句",
        },
    ]


def test_align_speaker_segments_applies_audio_window_offset():
    result = align_speaker_segments(
        [{"speaker": "A", "start_sec": 0.5, "end_sec": 2.2, "source": "pyannote"}],
        [{"start_sec": 10.6, "end_sec": 11.8, "text": "带偏移文本"}],
        offset_sec=10,
    )

    assert result[0]["start"] == "00:00:10"
    assert result[0]["end"] == "00:00:12"
    assert result[0]["start_sec"] == 10.5
    assert result[0]["end_sec"] == 12.2
    assert result[0]["text"] == "带偏移文本"


def test_align_speaker_segments_keeps_empty_text_without_matching_asr():
    result = align_speaker_segments(
        [{"speaker": "A", "start_sec": 0.0, "end_sec": 1.0, "source": "pyannote"}],
        [{"start": 4.0, "end": 5.0, "text": "不重叠"}],
    )

    assert result[0]["text"] == ""


def test_pyannote_client_posts_multipart_file_and_parses_response():
    seen = {}

    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps({
                "code": 0,
                "message": "success",
                "data": [
                    {"speaker": "SPEAKER_00", "start": 0.0, "end": 1.0, "duration": 1.0}
                ],
            }).encode("utf-8")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        seen["timeout"] = timeout
        seen["headers"] = dict(request.header_items())
        seen["body"] = request.data
        return FakeResponse()

    client = PyannoteDiarizationClient(
        endpoint="http://pyannote.example/diarize",
        api_key="test-token",
        timeout=7,
        urlopen=fake_urlopen,
    )

    segments = client.diarize_file(
        b"RIFF-wav-bytes",
        filename="sample.wav",
        content_type="audio/wav",
        speaker_count_hint=2,
    )

    assert segments[0]["speaker"] == "A"
    assert seen["url"] == "http://pyannote.example/diarize"
    assert seen["timeout"] == 7
    assert seen["headers"]["Authorization"] == "Bearer test-token"
    assert b'name="file"; filename="sample.wav"' in seen["body"]
    assert b"Content-Type: audio/wav" in seen["body"]
    assert b"RIFF-wav-bytes" in seen["body"]
    assert b'name="speaker_count_hint"' in seen["body"]


def test_pyannote_client_uses_direct_opener_to_bypass_system_proxy(monkeypatch):
    seen = {}

    class FakeProxyHandler:
        def __init__(self, proxies):
            seen["proxies"] = proxies

    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps({"code": 0, "message": "success", "data": []}).encode("utf-8")

    class FakeOpener:
        def open(self, request, timeout):
            seen["url"] = request.full_url
            seen["timeout"] = timeout
            return FakeResponse()

    def fake_build_opener(handler):
        seen["handler"] = handler
        return FakeOpener()

    monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:7890")
    monkeypatch.setattr("app.service.audio.speaker_diarization.ProxyHandler", FakeProxyHandler, raising=False)
    monkeypatch.setattr("app.service.audio.speaker_diarization.build_opener", fake_build_opener, raising=False)

    client = PyannoteDiarizationClient(
        endpoint="http://192.168.1.12:8188/diarize",
        timeout=7,
    )

    assert client.diarize_file(b"RIFF-wav-bytes") == []
    assert seen["proxies"] == {}
    assert seen["url"] == "http://192.168.1.12:8188/diarize"
    assert seen["timeout"] == 7


def test_pyannote_client_resolves_endpoint_after_initialization(monkeypatch):
    seen = {}

    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps({"code": 0, "message": "success", "data": []}).encode("utf-8")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return FakeResponse()

    monkeypatch.delenv("PYANNOTE_DIARIZATION_ENDPOINT", raising=False)
    client = PyannoteDiarizationClient(urlopen=fake_urlopen)
    monkeypatch.setenv("PYANNOTE_DIARIZATION_ENDPOINT", "http://192.168.1.12:8188/diarize")

    assert client.diarize_file(b"RIFF-wav-bytes") == []
    assert seen["url"] == "http://192.168.1.12:8188/diarize"


def test_pyannote_client_reads_project_env_file_when_process_env_missing(monkeypatch, tmp_path):
    seen = {}

    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps({"code": 0, "message": "success", "data": []}).encode("utf-8")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return FakeResponse()

    (tmp_path / ".env").write_text(
        "PYANNOTE_DIARIZATION_ENDPOINT=http://192.168.1.12:8188/diarize\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("PYANNOTE_DIARIZATION_ENDPOINT", raising=False)
    monkeypatch.setattr(diarization_module, "PROJECT_ROOT", str(tmp_path))

    client = PyannoteDiarizationClient(urlopen=fake_urlopen)

    assert client.diarize_file(b"RIFF-wav-bytes") == []
    assert seen["url"] == "http://192.168.1.12:8188/diarize"


def test_pyannote_client_masks_external_http_errors():
    def fake_urlopen(request, timeout):
        raise HTTPError(request.full_url, 500, "internal", {}, io.BytesIO(b"boom"))

    client = PyannoteDiarizationClient(
        endpoint="http://pyannote.example/diarize",
        timeout=7,
        urlopen=fake_urlopen,
    )

    try:
        client.diarize_file(b"RIFF-wav-bytes")
    except PyannoteDiarizationError as exc:
        assert "http_500" in str(exc)
    else:
        raise AssertionError("expected PyannoteDiarizationError")


def test_diarization_endpoint_returns_aligned_segments(monkeypatch):
    def fake_diarize_and_align(**kwargs):
        assert kwargs["file_bytes"] == b"RIFF-wav-bytes"
        assert kwargs["filename"] == "sample.wav"
        assert kwargs["content_type"] == "audio/wav"
        assert kwargs["session_id"] == "session-1"
        assert kwargs["suspect_id"] == "suspect-1"
        assert kwargs["offset_sec"] == 15.0
        assert kwargs["asr_segments"] == [{"start": 15.2, "end": 16.0, "text": "收到"}]
        return {
            "provider": "pyannote",
            "segments": [
                {
                    "speaker": "A",
                    "start": "00:00:15",
                    "end": "00:00:16",
                    "start_sec": 15.0,
                    "end_sec": 16.0,
                    "text": "收到",
                }
            ],
        }

    monkeypatch.setattr(
        "app.routes.api.asr_diarization.speaker_diarization_service.diarize_and_align",
        fake_diarize_and_align,
    )
    app = _create_app()

    with app.test_client() as client:
        response = client.post(
            "/api/asr/diarization/align",
            data={
                "file": (io.BytesIO(b"RIFF-wav-bytes"), "sample.wav", "audio/wav"),
                "segments": json.dumps([{"start": 15.2, "end": 16.0, "text": "收到"}]),
                "session_id": "session-1",
                "suspect_id": "suspect-1",
                "offset_sec": "15",
            },
            content_type="multipart/form-data",
        )

    body = response.get_json()
    assert response.status_code == 200
    assert body["code"] == int(Code.OK)
    assert body["data"]["segments"][0]["speaker"] == "A"
    assert body["data"]["segments"][0]["text"] == "收到"


def test_diarization_endpoint_rejects_missing_file():
    app = _create_app()

    with app.test_client() as client:
        response = client.post(
            "/api/asr/diarization/align",
            data={"segments": "[]"},
            content_type="multipart/form-data",
        )

    body = response.get_json()
    assert response.status_code == 400
    assert body["code"] == int(Code.INVALID_PARAM)
    assert body["msg"] == "file_required"
