import base64
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Flask

from app.routes.ws import audio as audio_route
from app.constants.codes import Code
from app.service.audio import qwen_asr
from app.service.audio.qwen_asr import (
    ASRClient,
    ASR_WS_ENDPOINT,
    build_finish_task_payload,
    build_run_task_payload,
    normalize_dashscope_asr_segments,
)


class DummyThread:
    def __init__(self, target, daemon=False):
        self.target = target
        self.daemon = daemon

    def start(self):
        return None


class FakeWebSocket:
    def __init__(self):
        self.sent = []
        self.closed = False

    def send(self, payload):
        self.sent.append(payload)

    def close(self):
        self.closed = True


def test_dashscope_endpoint_is_the_default_asr_ws_endpoint():
    assert ASR_WS_ENDPOINT == "wss://dashscope.aliyuncs.com/api-ws/v1/inference"


def test_build_run_task_payload_uses_dashscope_realtime_asr_contract():
    payload = build_run_task_payload(
        "task-123",
        model="paraformer-realtime-v2",
        sample_rate=16000,
        audio_format="pcm",
    )

    assert payload == {
        "header": {
            "action": "run-task",
            "task_id": "task-123",
            "streaming": "duplex",
        },
        "payload": {
            "task_group": "audio",
            "task": "asr",
            "function": "recognition",
            "model": "paraformer-realtime-v2",
            "parameters": {
                "sample_rate": 16000,
                "format": "pcm",
                "language_hints": ["zh"],
            },
            "input": {},
        },
    }


def test_build_finish_task_payload_reuses_the_current_task_id():
    payload = build_finish_task_payload("task-123")

    assert payload == {
        "header": {
            "action": "finish-task",
            "task_id": "task-123",
            "streaming": "duplex",
        },
        "payload": {"input": {}},
    }


def test_normalize_dashscope_result_generated_event_to_segments():
    message = {
        "header": {"event": "result-generated"},
        "payload": {
            "output": {
                "sentence": {
                    "begin_time": 500,
                    "end_time": 2100,
                    "text": "我们先看一下",
                    "heartbeat": False,
                }
            }
        },
    }

    assert normalize_dashscope_asr_segments(message) == [
        {"start": 0.5, "end": 2.1, "text": "我们先看一下"}
    ]


def test_normalize_dashscope_result_ignores_empty_or_heartbeat_events():
    assert normalize_dashscope_asr_segments({"header": {"event": "task-started"}, "payload": {}}) == []
    assert normalize_dashscope_asr_segments({
        "header": {"event": "result-generated"},
        "payload": {"output": {"sentence": {"begin_time": 0, "end_time": 100, "text": " ", "heartbeat": False}}},
    }) == []
    assert normalize_dashscope_asr_segments({
        "header": {"event": "result-generated"},
        "payload": {"output": {"sentence": {"begin_time": 0, "end_time": 100, "text": "静音", "heartbeat": True}}},
    }) == []


def test_client_connects_with_authorization_and_sends_run_task(monkeypatch):
    fake_ws = FakeWebSocket()
    seen = {}

    def fake_create_connection(endpoint, timeout=None, header=None):
        seen["endpoint"] = endpoint
        seen["timeout"] = timeout
        seen["header"] = header
        return fake_ws

    monkeypatch.setattr(qwen_asr, "create_connection", fake_create_connection)
    monkeypatch.setattr(qwen_asr.threading, "Thread", DummyThread)

    client = ASRClient(api_key="test-key", task_id_factory=lambda: "task-123")
    client.connect()

    assert seen == {
        "endpoint": ASR_WS_ENDPOINT,
        "timeout": 120.0,
        "header": ["Authorization: Bearer test-key"],
    }
    assert json.loads(fake_ws.sent[0]) == build_run_task_payload("task-123")


def test_client_refreshes_api_key_loaded_after_initialization(monkeypatch):
    fake_ws = FakeWebSocket()
    seen = {}

    monkeypatch.delenv("ASR_DASHSCOPE_API_KEY", raising=False)
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    client = ASRClient(task_id_factory=lambda: "task-123")

    monkeypatch.setenv("DASHSCOPE_API_KEY", "late-loaded-key")

    def fake_create_connection(endpoint, timeout=None, header=None):
        seen["endpoint"] = endpoint
        seen["timeout"] = timeout
        seen["header"] = header
        return fake_ws

    monkeypatch.setattr(qwen_asr, "create_connection", fake_create_connection)
    monkeypatch.setattr(qwen_asr.threading, "Thread", DummyThread)

    client.connect()

    assert seen["header"] == ["Authorization: Bearer late-loaded-key"]
    assert json.loads(fake_ws.sent[0]) == build_run_task_payload("task-123")


def test_client_uses_builtin_api_key_when_env_is_missing(monkeypatch):
    fake_ws = FakeWebSocket()
    seen = {}

    monkeypatch.delenv("ASR_DASHSCOPE_API_KEY", raising=False)
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    monkeypatch.setattr(qwen_asr, "BUILTIN_DASHSCOPE_API_KEY", "builtin-test-key")

    def fake_create_connection(endpoint, timeout=None, header=None):
        seen["header"] = header
        return fake_ws

    monkeypatch.setattr(qwen_asr, "create_connection", fake_create_connection)
    monkeypatch.setattr(qwen_asr.threading, "Thread", DummyThread)

    client = ASRClient(task_id_factory=lambda: "task-123")
    client.connect()

    assert seen["header"] == ["Authorization: Bearer builtin-test-key"]


def test_client_sends_audio_as_binary_after_task_started():
    fake_ws = FakeWebSocket()
    client = ASRClient(api_key="test-key", task_id_factory=lambda: "task-123")
    client.ws = fake_ws
    client.running = True
    client.task_id = "task-123"
    client.task_started.set()

    client.send(base64.b64encode(b"pcm-bytes").decode("ascii"), suspect_id="1", seq=7)

    assert fake_ws.sent == [b"pcm-bytes"]


def test_client_sends_finish_task_for_end_packet():
    fake_ws = FakeWebSocket()
    client = ASRClient(api_key="test-key", task_id_factory=lambda: "task-123")
    client.ws = fake_ws
    client.running = True
    client.task_id = "task-123"
    client.task_started.set()

    client.send("", suspect_id="1", seq=8, end=True)

    assert json.loads(fake_ws.sent[0]) == build_finish_task_payload("task-123")


def test_audio_route_returns_error_when_asr_forwarding_fails(monkeypatch):
    app = Flask("test-audio-forward-failure")

    class FailingClient:
        def send(self, audio_b64, suspect_id, seq, end=False):
            return False

    monkeypatch.setattr(audio_route, "_asr_client", FailingClient())
    monkeypatch.setattr(audio_route, "_flask_app", app)

    with app.app_context():
        resp = audio_route.process_raw_ws_request({
            "type": "audio",
            "audio": base64.b64encode(b"pcm-bytes").decode("ascii"),
            "seq": 1,
            "suspect_id": "1",
        })

    assert resp == {"code": int(Code.INTERNAL_ERROR), "msg": "asr_forward_failed", "data": None}


def test_audio_route_closes_matching_asr_client(monkeypatch):
    class ClosingClient:
        def __init__(self):
            self.closed = 0

        def close(self):
            self.closed += 1

    client = ClosingClient()
    ws = FakeWebSocket()
    other_ws = FakeWebSocket()

    monkeypatch.setattr(audio_route, "_asr_client", client)
    monkeypatch.setattr(audio_route, "_active_ws", ws)

    audio_route.close_raw_ws_request(other_ws)
    assert client.closed == 0

    audio_route.close_raw_ws_request(ws)
    assert client.closed == 1
    assert audio_route._active_ws is None


def test_audio_route_forwards_normalized_segments_and_persists_text(monkeypatch):
    class FrontendWebSocket:
        def __init__(self):
            self.messages = []

        def send(self, payload):
            self.messages.append(payload)

    created = []
    frontend_ws = FrontendWebSocket()
    app = Flask("test-audio-route")
    app.config["DATABASE_ENABLED"] = True

    monkeypatch.setattr(audio_route, "_active_ws", frontend_ws)
    monkeypatch.setattr(audio_route, "_flask_app", app)
    monkeypatch.setattr(audio_route, "_active_suspect_id", "suspect-1", raising=False)
    monkeypatch.setattr(audio_route._repo, "create", lambda payload: created.append(payload))

    audio_route._handle_asr_message({
        "header": {"event": "result-generated"},
        "payload": {
            "output": {
                "sentence": {
                    "begin_time": 500,
                    "end_time": 2100,
                    "text": "我们先看一下",
                    "heartbeat": False,
                }
            }
        },
    })

    assert json.loads(frontend_ws.messages[0]) == [
        {"start": 0.5, "end": 2.1, "text": "我们先看一下"}
    ]
    assert created == [{"suspect_id": "suspect-1", "text": "我们先看一下"}]


def test_audio_route_forwards_segments_without_database_when_disabled(monkeypatch):
    class FrontendWebSocket:
        def __init__(self):
            self.messages = []

        def send(self, payload):
            self.messages.append(payload)

    created = []
    frontend_ws = FrontendWebSocket()
    app = Flask("test-audio-route-db-disabled")
    app.config["DATABASE_ENABLED"] = False

    monkeypatch.setattr(audio_route, "_active_ws", frontend_ws)
    monkeypatch.setattr(audio_route, "_flask_app", app)
    monkeypatch.setattr(audio_route, "_active_suspect_id", "suspect-1", raising=False)
    monkeypatch.setattr(audio_route._repo, "create", lambda payload: created.append(payload))

    audio_route._handle_asr_message({
        "header": {"event": "result-generated"},
        "payload": {
            "output": {
                "sentence": {
                    "begin_time": 500,
                    "end_time": 2100,
                    "text": "我们先看一下",
                    "heartbeat": False,
                }
            }
        },
    })

    assert json.loads(frontend_ws.messages[0]) == [
        {"start": 0.5, "end": 2.1, "text": "我们先看一下"}
    ]
    assert created == []
