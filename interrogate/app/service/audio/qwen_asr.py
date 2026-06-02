# -*- coding: utf-8 -*-
"""
音频识别服务（转发到 DashScope ASR WebSocket）
采用长连接与多线程接收，防止单帧阻塞。
"""
import base64
import binascii
import json
import logging
import os
import threading
import uuid
from typing import Any, Callable, Dict, List, Optional


LOGGER = logging.getLogger(__name__)


def _get_ws_creator():
    try:
        from websocket import create_connection
        return create_connection
    except ImportError:
        import websocket
        if hasattr(websocket, 'create_connection'):
            return websocket.create_connection
        raise RuntimeError("请安装正确的包: pip install websocket-client")


create_connection = _get_ws_creator()
ASR_WS_ENDPOINT = "wss://dashscope.aliyuncs.com/api-ws/v1/inference"
BUILTIN_DASHSCOPE_API_KEY = "sk-5bc44e2db7a04aa7a3bced2861a6f02d"
DEFAULT_ASR_MODEL = "paraformer-realtime-v2"
DEFAULT_ASR_SAMPLE_RATE = 16000
DEFAULT_ASR_AUDIO_FORMAT = "pcm"


def _new_task_id() -> str:
    return uuid.uuid4().hex


def build_run_task_payload(
    task_id: str,
    model: str = DEFAULT_ASR_MODEL,
    sample_rate: int = DEFAULT_ASR_SAMPLE_RATE,
    audio_format: str = DEFAULT_ASR_AUDIO_FORMAT,
) -> Dict[str, Any]:
    """
    构建 DashScope WebSocket run-task 指令。

    DashScope 要求先发文本控制帧启动任务，再等待 `task-started`
    事件后发送二进制音频帧；这里固定为审讯前端当前采集的 16k PCM。
    """
    return {
        "header": {
            "action": "run-task",
            "task_id": task_id,
            "streaming": "duplex",
        },
        "payload": {
            "task_group": "audio",
            "task": "asr",
            "function": "recognition",
            "model": model,
            "parameters": {
                "sample_rate": sample_rate,
                "format": audio_format,
                "language_hints": ["zh"],
            },
            "input": {},
        },
    }


def build_finish_task_payload(task_id: str) -> Dict[str, Any]:
    """
    构建 DashScope WebSocket finish-task 指令，结束当前音频流。
    """
    return {
        "header": {
            "action": "finish-task",
            "task_id": task_id,
            "streaming": "duplex",
        },
        "payload": {"input": {}},
    }


def _milliseconds_to_seconds(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return round(float(value) / 1000, 3)
    except (TypeError, ValueError):
        return None


def normalize_dashscope_asr_segments(message: Any) -> List[Dict[str, Any]]:
    """
    将 DashScope `result-generated` 事件归一化为前端展示和后续说话人分离需要的段格式。
    """
    if isinstance(message, list):
        segments = []
        for item in message:
            if not isinstance(item, dict):
                continue
            text = str(item.get("text") or "").strip()
            if text:
                segments.append({
                    "start": item.get("start"),
                    "end": item.get("end"),
                    "text": text,
                })
        return segments

    if not isinstance(message, dict):
        return []

    if message.get("header", {}).get("event") != "result-generated":
        return []

    output = message.get("payload", {}).get("output") or {}
    sentence = output.get("sentence") or message.get("payload", {}).get("sentence") or {}
    if sentence.get("heartbeat"):
        return []

    text = str(sentence.get("text") or "").strip()
    if not text:
        return []

    return [{
        "start": _milliseconds_to_seconds(sentence.get("begin_time")),
        "end": _milliseconds_to_seconds(sentence.get("end_time")),
        "text": text,
    }]


class ASRClient:
    """管理到 DashScope ASR 的长连接与双向通信"""

    def __init__(
        self,
        endpoint: Optional[str] = None,
        timeout: float = 120.0,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        sample_rate: Optional[int] = None,
        audio_format: Optional[str] = None,
        task_id_factory: Callable[[], str] = _new_task_id,
        start_timeout: float = 10.0,
    ):
        self._endpoint_from_arg = endpoint is not None
        self._api_key_from_arg = api_key is not None
        self._model_from_arg = model is not None
        self._sample_rate_from_arg = sample_rate is not None
        self._audio_format_from_arg = audio_format is not None
        self.endpoint = endpoint or os.getenv("ASR_DASHSCOPE_ENDPOINT") or ASR_WS_ENDPOINT
        self.timeout = timeout
        self.api_key = api_key if api_key is not None else self._read_api_key_from_env()
        self.model = model or os.getenv("ASR_DASHSCOPE_MODEL") or DEFAULT_ASR_MODEL
        self.sample_rate = int(sample_rate or os.getenv("ASR_SAMPLE_RATE", str(DEFAULT_ASR_SAMPLE_RATE)))
        self.audio_format = audio_format or os.getenv("ASR_AUDIO_FORMAT") or DEFAULT_ASR_AUDIO_FORMAT
        self.task_id_factory = task_id_factory
        self.start_timeout = start_timeout
        self.ws = None
        self.running = False
        self.task_id = ""
        self.task_started = threading.Event()
        self.task_finished = threading.Event()
        self._lock = threading.Lock()
        self.on_message: Callable[[Dict[str, Any]], None] = None

    @staticmethod
    def _read_api_key_from_env() -> str:
        return os.getenv("ASR_DASHSCOPE_API_KEY") or os.getenv("DASHSCOPE_API_KEY") or BUILTIN_DASHSCOPE_API_KEY

    def _refresh_runtime_config(self) -> None:
        """
        刷新来自环境变量的配置，兼容 app 初始化时才加载 .env 的场景。
        """
        if not self._endpoint_from_arg:
            self.endpoint = os.getenv("ASR_DASHSCOPE_ENDPOINT") or ASR_WS_ENDPOINT
        if not self._api_key_from_arg:
            self.api_key = self._read_api_key_from_env()
        if not self._model_from_arg:
            self.model = os.getenv("ASR_DASHSCOPE_MODEL") or DEFAULT_ASR_MODEL
        if not self._sample_rate_from_arg:
            self.sample_rate = int(os.getenv("ASR_SAMPLE_RATE", str(DEFAULT_ASR_SAMPLE_RATE)))
        if not self._audio_format_from_arg:
            self.audio_format = os.getenv("ASR_AUDIO_FORMAT") or DEFAULT_ASR_AUDIO_FORMAT

    def _auth_headers(self) -> List[str]:
        return [f"Authorization: Bearer {self.api_key}"]

    def _send_json(self, payload: Dict[str, Any]) -> None:
        self.ws.send(json.dumps(payload, ensure_ascii=False))

    def connect(self) -> bool:
        with self._lock:
            if self.ws is not None and self.running:
                return True
            self._refresh_runtime_config()
            if not self.api_key:
                LOGGER.error("DashScope ASR 未配置 API Key，请设置 DASHSCOPE_API_KEY 或 ASR_DASHSCOPE_API_KEY")
                return False

            try:
                self.ws = create_connection(
                    self.endpoint,
                    timeout=self.timeout,
                    header=self._auth_headers(),
                )
                self.running = True
                self.task_id = self.task_id_factory()
                self.task_started.clear()
                self.task_finished.clear()
                # DashScope 先建立任务再接收音频，接收线程负责释放 task-started 事件。
                threading.Thread(target=self._recv_loop, daemon=True).start()
                self._send_json(build_run_task_payload(
                    self.task_id,
                    model=self.model,
                    sample_rate=self.sample_rate,
                    audio_format=self.audio_format,
                ))
                LOGGER.info("已连接 DashScope ASR WebSocket")
                return True
            except Exception as exc:
                LOGGER.error("连接 DashScope ASR 失败: %s", exc.__class__.__name__)
                self.ws = None
                self.running = False
                return False

    def send(self, audio_b64: str, suspect_id: str, seq: int, end: bool = False) -> bool:
        if not self.connect():
            return False
        if not self.ws or not self.running:
            return False

        try:
            if end:
                self._send_json(build_finish_task_payload(self.task_id))
                return True

            if not audio_b64:
                return False

            if not self.task_started.wait(self.start_timeout):
                LOGGER.warning("DashScope ASR task-started 等待超时，丢弃当前音频包 seq=%s", seq)
                return False

            audio_bytes = base64.b64decode(audio_b64, validate=True)
            if hasattr(self.ws, "send_binary"):
                self.ws.send_binary(audio_bytes)
            else:
                self.ws.send(audio_bytes)
            return True
        except (binascii.Error, ValueError):
            LOGGER.warning("收到非法音频 Base64，已丢弃 seq=%s", seq)
            return False
        except Exception as exc:
            LOGGER.error("向 DashScope ASR 发送数据失败: %s", exc.__class__.__name__)
            self.close()
            return False

    def _recv_loop(self):
        while self.running and self.ws:
            try:
                resp = self.ws.recv()
                if resp:
                    data = json.loads(resp)
                    event = data.get("header", {}).get("event")
                    if event == "task-started":
                        self.task_started.set()
                    elif event in {"task-finished", "task-failed"}:
                        self.task_finished.set()
                    if self.on_message:
                        self.on_message(data)
                    if event in {"task-finished", "task-failed"}:
                        break
            except Exception as e:
                if self.running:
                    LOGGER.error("接收 DashScope ASR 数据异常: %s", e.__class__.__name__)
                break
        self.close()

    def close(self):
        with self._lock:
            self.running = False
            if self.ws:
                try:
                    self.ws.close()
                except Exception:
                    pass
                self.ws = None
            self.task_started.clear()
            self.task_finished.set()


# 全局单例
_asr_client = ASRClient()
