# -*- coding: utf-8 -*-
"""
HTTP API：ASR 审讯关键词提炼。
"""
from flask import Blueprint, current_app, request

from app.constants.codes import Code
from app.service.audio.keyword_extraction import KeywordExtractionService
from app.utils.responses import error, ok


asr_keywords_bp = Blueprint("asr_keywords", __name__, url_prefix="/api/asr/keywords")
keyword_extractor = KeywordExtractionService()


@asr_keywords_bp.post("/extract")
def extract_asr_keywords():
    """
    接收前端累计 ASR 文本，返回审讯场景关键词。
    """
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text") or "").strip()
    if not text:
        return error(Code.INVALID_PARAM, "text_required", http_status=400)
    if len(text) > 12000:
        return error(Code.INVALID_PARAM, "text_too_long", http_status=400)

    window_id = str(payload.get("window_id") or "")
    suspect_id = str(payload.get("suspect_id") or "")
    session_id = str(payload.get("session_id") or "")
    context = str(payload.get("context") or "")

    try:
        result = keyword_extractor.extract(
            text=text,
            window_id=window_id,
            suspect_id=suspect_id,
            session_id=session_id,
            context=context,
        )
    except Exception:
        current_app.logger.exception("ASR 关键词提炼失败")
        return error(Code.INTERNAL_ERROR, "keyword_extract_failed", http_status=500)

    return ok(result)
