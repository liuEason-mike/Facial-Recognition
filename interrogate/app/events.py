"""
事件载荷类型与 API 错误
- 统一 WS/HTTP 的消息契约
- ApiError：API 层用于返回结构化错误
"""
from typing import TypedDict, Optional, Dict, Any, List


class ApiError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


class StartSessionPayload(TypedDict):
    person_id: str


class StartAck(TypedDict):
    session_key: str
    storage_dir: str
    video_path: str


class VideoFramePayload(TypedDict):
    session_key: str
    frame_b64: str
    ts: float


class AnalysisResult(TypedDict, total=False):
    frame_index: int
    time_sec: float
    emotion: Dict[str, Any]
    heart_rate: Dict[str, Any]
    head_pose: Dict[str, Any]
    eye_gaze: Dict[str, Any]
    au_intensity: Dict[str, Any]


class ErrorEvent(TypedDict):
    error: str
    detail: Optional[str]
