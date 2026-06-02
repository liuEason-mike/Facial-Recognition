# -*- coding: utf-8 -*-
"""
说话人分离服务适配层。

本模块只处理 pyannote 外部服务协议转换和 ASR 时间片对齐，不参与实时 ASR
WebSocket 主链路，外部失败时由调用方做非阻塞降级。
"""
import json
import logging
import os
import time
import uuid
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener


LOGGER = logging.getLogger(__name__)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DEFAULT_TIMEOUT_SECONDS = 15.0
DEFAULT_SPEAKER_COUNT_HINT = 2


class PyannoteDiarizationError(RuntimeError):
    """外部 pyannote 服务不可用或响应不符合契约。"""


def _strip_env_value(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    if " #" in value:
        value = value.split(" #", 1)[0].rstrip()
    return value


def _read_env_file_value(name: str) -> str:
    """
    无依赖读取项目 env 文件中的单个变量，兜底处理 python-dotenv 未加载的启动方式。
    """
    candidates = [os.path.join(PROJECT_ROOT, ".env")]
    env_file = os.getenv("ENV_FILE")
    if env_file:
        candidates.append(env_file if os.path.isabs(env_file) else os.path.join(PROJECT_ROOT, env_file))
    profile = os.getenv("APP_PROFILE")
    if profile:
        candidates.append(os.path.join(PROJECT_ROOT, f".env.{profile}"))

    resolved = ""
    for path in candidates:
        if not os.path.isfile(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as env_file_obj:
                for raw_line in env_file_obj:
                    line = raw_line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if line.startswith("export "):
                        line = line[len("export "):].strip()
                    if "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    if key.strip() == name:
                        resolved = _strip_env_value(value)
        except OSError:
            continue
    return resolved


def _resolve_env_value(name: str, default: Any = "") -> Any:
    value = os.getenv(name)
    if value is not None and str(value).strip():
        return value
    file_value = _read_env_file_value(name)
    if file_value:
        return file_value
    return default


def _to_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return round(float(value), 3)
    if isinstance(value, str) and ":" in value:
        parts = value.split(":")
        try:
            numbers = [float(part) for part in parts]
        except ValueError:
            return None
        if len(numbers) == 3:
            return round(numbers[0] * 3600 + numbers[1] * 60 + numbers[2], 3)
        if len(numbers) == 2:
            return round(numbers[0] * 60 + numbers[1], 3)
    try:
        return round(float(value), 3)
    except (TypeError, ValueError):
        return None


def _format_seconds(value: float) -> str:
    total = max(0, int(value))
    hours = total // 3600
    minutes = (total % 3600) // 60
    seconds = total % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def _extract_raw_segments(payload: Any) -> List[Any]:
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []
    if isinstance(payload.get("data"), list):
        return payload["data"]
    if isinstance(payload.get("segments"), list):
        return payload["segments"]
    return []


def _speaker_label(index: int) -> str:
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if index < len(alphabet):
        return alphabet[index]
    return f"S{index + 1}"


def normalize_pyannote_segments(payload: Any) -> List[Dict[str, Any]]:
    """
    将外部 pyannote 返回统一为会话内稳定 speaker 片段。

    外部服务当前示例为 `{code,message,data:[{speaker,start,end,duration}]}`，
    这里也兼容 `{segments:[...]}` 和直接数组，避免外部差异泄漏到前端。
    """
    speaker_map: Dict[str, str] = {}
    normalized: List[Dict[str, Any]] = []

    for item in _extract_raw_segments(payload):
        if not isinstance(item, dict):
            continue
        start_sec = _to_float(item.get("start_sec", item.get("start")))
        end_sec = _to_float(item.get("end_sec", item.get("end")))
        if start_sec is None or end_sec is None or end_sec <= start_sec:
            LOGGER.warning("pyannote segment 字段缺失或非法，已过滤")
            continue

        external_speaker = str(
            item.get("speaker") or item.get("label") or item.get("speaker_id") or "unknown"
        ).strip() or "unknown"
        if external_speaker not in speaker_map:
            speaker_map[external_speaker] = _speaker_label(len(speaker_map))

        duration = _to_float(item.get("duration"))
        confidence = _to_float(item.get("confidence"))
        segment: Dict[str, Any] = {
            "speaker": speaker_map[external_speaker],
            "external_speaker": external_speaker,
            "start_sec": start_sec,
            "end_sec": end_sec,
            "duration": duration if duration is not None else round(end_sec - start_sec, 3),
            "source": "pyannote",
        }
        if confidence is not None:
            segment["confidence"] = confidence
        normalized.append(segment)

    return normalized


def _overlap(left_start: float, left_end: float, right_start: float, right_end: float) -> float:
    return max(0.0, min(left_end, right_end) - max(left_start, right_start))


def _normalize_asr_segments(asr_segments: Iterable[Any]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for item in asr_segments:
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or "").strip()
        if not text:
            continue
        start_sec = _to_float(item.get("start_sec", item.get("start")))
        end_sec = _to_float(item.get("end_sec", item.get("end")))
        if start_sec is None or end_sec is None or end_sec <= start_sec:
            continue
        normalized.append({
            "start_sec": start_sec,
            "end_sec": end_sec,
            "text": text,
        })
    return sorted(normalized, key=lambda segment: segment["start_sec"])


def align_speaker_segments(
    diarized_segments: Iterable[Dict[str, Any]],
    asr_segments: Iterable[Any],
    *,
    session_id: str = "",
    suspect_id: str = "",
    offset_sec: float = 0.0,
) -> List[Dict[str, Any]]:
    """
    按最大时间重叠将 ASR 文本归属到 speaker 片段。

    `offset_sec` 用于前端按固定音频窗口上传时，将 pyannote 的窗口内相对时间
    平移为审讯会话内时间，避免每个 15 秒窗口都从 00:00:00 开始展示。
    """
    offset = float(offset_sec or 0.0)
    speaker_segments: List[Dict[str, Any]] = []
    for segment in diarized_segments:
        start = _to_float(segment.get("start_sec", segment.get("start")))
        end = _to_float(segment.get("end_sec", segment.get("end")))
        if start is None or end is None or end <= start:
            continue
        item = dict(segment)
        item["start_sec"] = round(start + offset, 3)
        item["end_sec"] = round(end + offset, 3)
        speaker_segments.append(item)

    speaker_segments.sort(key=lambda segment: segment["start_sec"])
    assignments: List[List[Dict[str, Any]]] = [[] for _ in speaker_segments]

    for asr_segment in _normalize_asr_segments(asr_segments):
        best_index = -1
        best_overlap = 0.0
        for index, speaker_segment in enumerate(speaker_segments):
            overlap = _overlap(
                asr_segment["start_sec"],
                asr_segment["end_sec"],
                speaker_segment["start_sec"],
                speaker_segment["end_sec"],
            )
            if overlap > best_overlap:
                best_overlap = overlap
                best_index = index
        if best_index >= 0:
            assignments[best_index].append(asr_segment)

    result: List[Dict[str, Any]] = []
    for index, segment in enumerate(speaker_segments):
        assigned_text = "".join(item["text"] for item in assignments[index])
        item: Dict[str, Any] = {
            "speaker": str(segment.get("speaker") or "unknown"),
            "start": _format_seconds(segment["start_sec"]),
            "end": _format_seconds(segment["end_sec"]),
            "start_sec": segment["start_sec"],
            "end_sec": segment["end_sec"],
            "source": segment.get("source") or "pyannote",
            "text": assigned_text,
        }
        for field in ("duration", "confidence", "external_speaker"):
            if field in segment:
                item[field] = segment[field]
        if session_id:
            item["session_id"] = session_id
        if suspect_id:
            item["suspect_id"] = suspect_id
        result.append(item)

    return result


def _build_multipart_body(
    *,
    file_bytes: bytes,
    filename: str,
    content_type: str,
    fields: Dict[str, str],
) -> Tuple[bytes, str]:
    boundary = f"----interrogate-pyannote-{uuid.uuid4().hex}"
    chunks: List[bytes] = []
    for name, value in fields.items():
        chunks.extend([
            f"--{boundary}\r\n".encode("utf-8"),
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"),
            str(value).encode("utf-8"),
            b"\r\n",
        ])
    safe_filename = filename or "audio.wav"
    chunks.extend([
        f"--{boundary}\r\n".encode("utf-8"),
        f'Content-Disposition: form-data; name="file"; filename="{safe_filename}"\r\n'.encode("utf-8"),
        f"Content-Type: {content_type or 'audio/wav'}\r\n\r\n".encode("utf-8"),
        file_bytes,
        b"\r\n",
        f"--{boundary}--\r\n".encode("utf-8"),
    ])
    return b"".join(chunks), boundary


def _build_direct_urlopen() -> Callable[..., Any]:
    """
    为 pyannote 外部服务创建直连 HTTP opener。

    部署机器可能设置 HTTP_PROXY/HTTPS_PROXY；内网 pyannote 服务应绕过代理，
    否则 Python urllib 会把请求发到代理端口并导致 TimeoutError。
    """
    opener = build_opener(ProxyHandler({}))
    return opener.open


class PyannoteDiarizationClient:
    """调用外部 pyannote HTTP 服务，当前按 multipart 文件上传适配。"""

    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[float] = None,
        urlopen: Optional[Callable[..., Any]] = None,
    ):
        self._endpoint_explicit = endpoint is not None
        self._api_key_explicit = api_key is not None
        self.endpoint = endpoint if endpoint is not None else _resolve_env_value("PYANNOTE_DIARIZATION_ENDPOINT", "")
        self.api_key = api_key if api_key is not None else _resolve_env_value("PYANNOTE_API_KEY", "")
        self.timeout = float(
            timeout if timeout is not None else _resolve_env_value(
                "PYANNOTE_TIMEOUT_SECONDS",
                DEFAULT_TIMEOUT_SECONDS,
            )
        )
        self.urlopen = urlopen or _build_direct_urlopen()

    def _current_endpoint(self) -> str:
        if not self._endpoint_explicit:
            resolved = _resolve_env_value("PYANNOTE_DIARIZATION_ENDPOINT", self.endpoint)
            if resolved:
                self.endpoint = resolved
        return str(self.endpoint or "").strip()

    def _current_api_key(self) -> str:
        if not self._api_key_explicit:
            resolved = _resolve_env_value("PYANNOTE_API_KEY", self.api_key)
            if resolved:
                self.api_key = resolved
        return str(self.api_key or "").strip()

    @property
    def configured(self) -> bool:
        return bool(self._current_endpoint())

    def diarize_file(
        self,
        file_bytes: bytes,
        *,
        filename: str = "audio.wav",
        content_type: str = "audio/wav",
        session_id: str = "",
        suspect_id: str = "",
        speaker_count_hint: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        endpoint = self._current_endpoint()
        if not endpoint:
            raise PyannoteDiarizationError("endpoint_required")
        if not file_bytes:
            raise PyannoteDiarizationError("empty_audio")

        fields = {
            "speaker_count_hint": str(
                speaker_count_hint
                if speaker_count_hint is not None
                else os.getenv("PYANNOTE_SPEAKER_COUNT_HINT", DEFAULT_SPEAKER_COUNT_HINT)
            ),
        }
        if session_id:
            fields["session_id"] = session_id
        if suspect_id:
            fields["suspect_id"] = suspect_id

        body, boundary = _build_multipart_body(
            file_bytes=file_bytes,
            filename=filename,
            content_type=content_type,
            fields=fields,
        )
        headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        }
        api_key = self._current_api_key()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        request = Request(endpoint, data=body, headers=headers, method="POST")
        started_at = time.perf_counter()
        try:
            with self.urlopen(request, timeout=self.timeout) as response:
                status = int(getattr(response, "status", 200) or 200)
                response_bytes = response.read()
        except HTTPError as exc:
            raise PyannoteDiarizationError(f"http_{exc.code}") from exc
        except (TimeoutError, URLError, OSError) as exc:
            raise PyannoteDiarizationError(exc.__class__.__name__) from exc

        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        if status >= 400:
            raise PyannoteDiarizationError(f"http_{status}")
        try:
            payload = json.loads(response_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise PyannoteDiarizationError("invalid_json") from exc

        if isinstance(payload, dict) and "code" in payload:
            try:
                ok_code = int(payload.get("code")) == 0
            except (TypeError, ValueError):
                ok_code = False
            if not ok_code:
                raise PyannoteDiarizationError("provider_error")

        segments = normalize_pyannote_segments(payload)
        LOGGER.info("pyannote diarization 完成，耗时=%sms，segments=%s", elapsed_ms, len(segments))
        return segments


class SpeakerDiarizationService:
    """说话人分离业务服务：调用外部服务并返回前端契约结果。"""

    def __init__(self, client: Optional[PyannoteDiarizationClient] = None):
        self.client = client or PyannoteDiarizationClient()

    def diarize_and_align(
        self,
        *,
        file_bytes: bytes,
        asr_segments: Iterable[Any],
        filename: str = "audio.wav",
        content_type: str = "audio/wav",
        session_id: str = "",
        suspect_id: str = "",
        offset_sec: float = 0.0,
    ) -> Dict[str, Any]:
        started_at = time.perf_counter()
        diarized = self.client.diarize_file(
            file_bytes,
            filename=filename,
            content_type=content_type,
            session_id=session_id,
            suspect_id=suspect_id,
        )
        segments = align_speaker_segments(
            diarized,
            asr_segments,
            session_id=session_id,
            suspect_id=suspect_id,
            offset_sec=offset_sec,
        )
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        LOGGER.info("说话人分离对齐完成，耗时=%sms，segments=%s", elapsed_ms, len(segments))
        return {
            "provider": "pyannote",
            "segments": segments,
        }
