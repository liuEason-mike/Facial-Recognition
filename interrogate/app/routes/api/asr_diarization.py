# -*- coding: utf-8 -*-
"""
HTTP API：ASR 说话人分离对齐。
"""
import json
from typing import Any, List

from flask import Blueprint, current_app, request

from app.constants.codes import Code
from app.service.audio.speaker_diarization import (
    PyannoteDiarizationError,
    SpeakerDiarizationService,
)
from app.utils.responses import error, ok


asr_diarization_bp = Blueprint("asr_diarization", __name__, url_prefix="/api/asr/diarization")
speaker_diarization_service = SpeakerDiarizationService()


def _parse_segments(raw: str) -> List[Any]:
    try:
        payload = json.loads(raw or "[]")
    except json.JSONDecodeError as exc:
        raise ValueError("segments_invalid") from exc
    if not isinstance(payload, list):
        raise ValueError("segments_invalid")
    return payload


def _parse_offset(raw: str) -> float:
    if raw == "" or raw is None:
        return 0.0
    try:
        return float(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError("offset_sec_invalid") from exc


@asr_diarization_bp.post("/align")
def align_asr_speaker_segments():
    """
    接收前端音频窗口 WAV 文件和 ASR segments，返回 speaker transcript segments。
    """
    upload = request.files.get("file")
    if upload is None:
        return error(Code.INVALID_PARAM, "file_required", http_status=400)

    file_bytes = upload.read()
    if not file_bytes:
        return error(Code.INVALID_PARAM, "file_empty", http_status=400)

    try:
        asr_segments = _parse_segments(request.form.get("segments", "[]"))
        offset_sec = _parse_offset(request.form.get("offset_sec", "0"))
    except ValueError as exc:
        return error(Code.INVALID_PARAM, str(exc), http_status=400)

    session_id = str(request.form.get("session_id") or "")
    suspect_id = str(request.form.get("suspect_id") or "")

    try:
        result = speaker_diarization_service.diarize_and_align(
            file_bytes=file_bytes,
            asr_segments=asr_segments,
            filename=upload.filename or "audio.wav",
            content_type=upload.content_type or "audio/wav",
            session_id=session_id,
            suspect_id=suspect_id,
            offset_sec=offset_sec,
        )
    except PyannoteDiarizationError as exc:
        current_app.logger.warning("说话人分离服务暂不可用: %s", exc)
        return error(
            Code.INTERNAL_ERROR,
            "speaker_diarization_unavailable",
            data={"segments": []},
            http_status=503,
        )
    except Exception:
        current_app.logger.exception("说话人分离处理失败")
        return error(Code.INTERNAL_ERROR, "speaker_diarization_failed", http_status=500)

    return ok(result)
