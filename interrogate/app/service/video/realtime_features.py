# -*- coding: utf-8 -*-
"""
实时面部分析主入口
"""
import time
import os
import logging
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from typing import Dict, Any, List

from app.utils.image import b64_to_bgr as _b2b
from .face_analyzer import FaceAnalyzer
from app.repository.emotion_real_time import EmotionRealTimeRepository
from app.repository.emotion_anomaly import EmotionAnomalyRepository
from app.service.video.isolation_forest.iso_forest_detector import IsolationForestDetector, default_model_dir
from app.service.video.emotion_cache import zero_emotion_scores
from app.utils.database import is_database_enabled

_analyzer = FaceAnalyzer()
_repo = EmotionRealTimeRepository()
_anomaly_repo = EmotionAnomalyRepository()
_logger = logging.getLogger(__name__)

# 全局检测器实例
_iso_detector = IsolationForestDetector(model_dir=default_model_dir())

# 基线训练状态按嫌疑人隔离；当前协议还没有 session_id，先沿用 suspect_id 作为状态键。
_BASELINE_MAX_SAMPLES = int(os.getenv("FACE_BASELINE_MAX_SAMPLES", "5000"))
_BASELINE_MIN_SAMPLES = int(os.getenv("FACE_BASELINE_MIN_SAMPLES", "2"))
_BASELINE_TRAIN_EVERY = int(os.getenv("FACE_BASELINE_TRAIN_EVERY", "10"))
_SLOW_FRAME_LOG_MS = int(os.getenv("FACE_SLOW_FRAME_LOG_MS", "200"))
_baseline_executor = ThreadPoolExecutor(
    max_workers=int(os.getenv("FACE_BASELINE_TRAIN_WORKERS", "1")),
    thread_name_prefix="face-baseline",
)
_baseline_lock = Lock()
_baseline_states: Dict[str, Dict[str, Any]] = {}
_released_baselines = set()
_ANOMALY_DOMAINS = ["emotion", "heart_rate", "head_pose", "eye_gaze", "au_intensity"]


def _elapsed_ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 2)


def _attach_performance(data: Dict[str, Any], timings: Dict[str, float], total_started: float) -> Dict[str, Any]:
    """
    将分段耗时写入 WebSocket 回包，便于定位慢帧来源。
    """
    timings["total_ms"] = _elapsed_ms(total_started)
    data["processing_ms"] = timings["total_ms"]
    data["performance"] = timings
    return data


def _fallback_status(sid: str, test_status: int) -> Dict[str, str]:
    """
    分析失败时仍按 test_status 维护基线生命周期，但不采集/训练/评分当前帧。
    """
    if test_status == 2:
        return {
            "baseline_status": _release_baseline(sid),
            "anomaly_status": "released",
        }
    if test_status == 1:
        baseline_status = _freeze_baseline(sid)
        return {
            "baseline_status": baseline_status,
            "anomaly_status": "released" if baseline_status == "released" else "skipped",
        }
    return {
        "baseline_status": _get_baseline_status(sid),
        "anomaly_status": "skipped",
    }


def _build_fallback_analysis_data(
    suspect_id: str,
    test_status: int,
    timings: Dict[str, float],
    total_started: float,
) -> Dict[str, Any]:
    """
    /ws/face 无法得到正常模型结果时返回固定零值情绪结构，避免前端收到缺字段对象。
    """
    sid = str(suspect_id)
    data = {
        "suspect_id": suspect_id,
        "frame": 0,
        "time_sec": int(time.time() * 1000),
        "dominant_emotion": 7,
        "emotion_scores": zero_emotion_scores(),
        "region": {},
        "head_pose": {"pitch": 0.0, "yaw": 0.0, "roll": 0.0},
        "left_eye_gaze": {"horizontal": 0.0, "vertical": 0.0},
        "right_eye_gaze": {"horizontal": 0.0, "vertical": 0.0},
        "heart_rate": 0,
        "gaze_direction": 3,
        "attention": 0,
        "au_intensities": {},
        "au_52": {},
        **_fallback_status(sid, test_status),
    }
    return _attach_performance(data, timings, total_started)


def _build_repo_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    将分析结果转换为 EmotionRealTime 模型所需字段 存入数据库中
    """
    region = data.get("region", {}) or {}
    face = region.get("face", {}) or {}
    le = region.get("left_eye", {}) or {}
    re = region.get("right_eye", {}) or {}
    lb = region.get("left_eyebrow", {}) or {}
    rb = region.get("right_eyebrow", {}) or {}
    mouth = region.get("mouth", {}) or {}

    lb_w = max(0, int(lb.get("x2", 0)) - int(lb.get("x1", 0)))
    lb_h = max(0, int(lb.get("y2", 0)) - int(lb.get("y1", 0)))
    rb_w = max(0, int(rb.get("x2", 0)) - int(rb.get("x1", 0)))
    rb_h = max(0, int(rb.get("y2", 0)) - int(rb.get("y1", 0)))
    m_w = max(0, int(mouth.get("x2", 0)) - int(mouth.get("x1", 0)))
    m_h = max(0, int(mouth.get("y2", 0)) - int(mouth.get("y1", 0)))

    emo = data.get("emotion_scores", {}) or {}
    hp = data.get("head_pose", {}) or {}
    le_gaze = data.get("left_eye_gaze", {}) or {}
    re_gaze = data.get("right_eye_gaze", {}) or {}
    au = data.get("au_intensities", {}) or {}

    yaw = float(hp.get("yaw", 0) or 0)
    if yaw < -15:
        gaze_dir = 1
    elif yaw > 15:
        gaze_dir = 2
    else:
        gaze_dir = 3

    payload = {
        "suspect_id": str(data.get("suspect_id", "")),
        "frame": int(data.get("frame", 0) or 0),
        "time_sec": int(data.get("time_sec", 0) or 0),
        "dominant_emotion": int(data.get("dominant_emotion", 7) or 7),
        "emotion_angry": float(emo.get("angry", 0.0) or 0.0),

        "emotion_disgust": float(emo.get("disgust", 0.0) or 0.0),
        "emotion_fear": float(emo.get("fear", 0.0) or 0.0),
        "emotion_happy": float(emo.get("happy", 0.0) or 0.0),
        "emotion_sad": float(emo.get("sad", 0.0) or 0.0),
        "emotion_surprise": float(emo.get("surprise", 0.0) or 0.0),
        "emotion_neutral": float(emo.get("neutral", 0.0) or 0.0),
        "face_x": int(face.get("x", 0) or 0),
        "face_y": int(face.get("y", 0) or 0),
        "face_w": int(face.get("w", 0) or 0),
        "face_h": int(face.get("h", 0) or 0),
        "left_eyebrow_x": int(lb.get("x1", 0) or 0),
        "left_eyebrow_y": int(lb.get("y1", 0) or 0),
        "left_eyebrow_w": lb_w,
        "left_eyebrow_h": lb_h,
        "right_eyebrow_x": int(rb.get("x1", 0) or 0),
        "right_eyebrow_y": int(rb.get("y1", 0) or 0),
        "right_eyebrow_w": rb_w,
        "right_eyebrow_h": rb_h,
        "left_eye_x": int(le.get("x", 0) or 0),
        "left_eye_y": int(le.get("y", 0) or 0),
        "left_eye_w": int(le.get("w", 0) or 0),
        "left_eye_h": int(le.get("h", 0) or 0),
        "right_eye_x": int(re.get("x", 0) or 0),
        "right_eye_y": int(re.get("y", 0) or 0),
        "right_eye_w": int(re.get("w", 0) or 0),
        "right_eye_h": int(re.get("h", 0) or 0),
        "mouth_x": int(mouth.get("x1", 0) or 0),
        "mouth_y": int(mouth.get("y1", 0) or 0),
        "mouth_w": m_w,
        "mouth_h": m_h,
        "heart_rate": int(data.get("heart_rate", 0) or 0),
        "gaze_direction": gaze_dir,
        "head_pose_pitch": float(hp.get("pitch", 0) or 0.0),
        "head_pose_yaw": yaw,
        "head_pose_roll": float(hp.get("roll", 0) or 0.0),
        "attention": int(data.get("attention", 0) or 0),
        "au_inner_brow_raiser": float(au.get("inner_brow_raiser", 0.0) or 0.0),
        "au_outer_brow_raiser": float(au.get("outer_brow_raiser", 0.0) or 0.0),
        "au_brow_furrower": float(au.get("brow_furrower", 0.0) or 0.0),
        "au_upper_eyelid_raiser": float(au.get("upper_eyelid_raiser", 0.0) or 0.0),
        "au_cheek_raiser": float(au.get("cheek_raiser", 0.0) or 0.0),
        "au_nose_wrinkler": float(au.get("nose_wrinkler", 0.0) or 0.0),
        "au_upper_lip_raiser": float(au.get("upper_lip_raiser", 0.0) or 0.0),
        "au_lip_corner_puller": float(au.get("lip_corner_puller", 0.0) or 0.0),
        "au_lip_corner_depressor": float(au.get("lip_corner_depressor", 0.0) or 0.0),
        "au_jaw_raiser": float(au.get("jaw_raiser", 0.0) or 0.0),
        "au_lip_stretcher": float(au.get("lip_stretcher", 0.0) or 0.0),
        "au_lip_compressor": float(au.get("lip_compressor", 0.0) or 0.0),
        "au_lip_parter": float(au.get("lip_parter", 0.0) or 0.0),
        "au_jaw_dropper": float(au.get("jaw_dropper", 0.0) or 0.0),
        "au_eye_closure": float(au.get("eye_closure", 0.0) or 0.0),
        "left_eye_gaze_horizontal": float(le_gaze.get("horizontal", 0.0) or 0.0),
        "left_eye_gaze_vertical": float(le_gaze.get("vertical", 0.0) or 0.0),
        "right_eye_gaze_horizontal": float(re_gaze.get("horizontal", 0.0) or 0.0),
        "right_eye_gaze_vertical": float(re_gaze.get("vertical", 0.0) or 0.0),
    }
    return payload


def _build_anomaly_payload(data: Dict[str, Any], anomaly_data: Dict[str, Any], model_dir: str) -> Dict[str, Any]:
    """
    将分析结果与异常分数转换为 EmotionAnomaly 模型所需字段 存入数据库中
    """
    payload = {
        "suspect_id": str(data.get("suspect_id", "")),
        "frame": int(data.get("frame", 0) or 0),
        "time_sec": int(data.get("time_sec", 0) or 0),
        "emotion_score": float(anomaly_data.get("emotion", {}).get("score") or 0.0) if anomaly_data.get("emotion", {}).get("score") is not None else None,
        "emotion_is_anomaly": bool(anomaly_data.get("emotion", {}).get("is_anomaly", False)),
        "heart_rate_score": float(anomaly_data.get("heart_rate", {}).get("score") or 0.0) if anomaly_data.get("heart_rate", {}).get("score") is not None else None,
        "heart_rate_is_anomaly": bool(anomaly_data.get("heart_rate", {}).get("is_anomaly", False)),
        "head_pose_score": float(anomaly_data.get("head_pose", {}).get("score") or 0.0) if anomaly_data.get("head_pose", {}).get("score") is not None else None,
        "head_pose_is_anomaly": bool(anomaly_data.get("head_pose", {}).get("is_anomaly", False)),
        "eye_gaze_score": float(anomaly_data.get("eye_gaze", {}).get("score") or 0.0) if anomaly_data.get("eye_gaze", {}).get("score") is not None else None,
        "eye_gaze_is_anomaly": bool(anomaly_data.get("eye_gaze", {}).get("is_anomaly", False)),
        "au_intensity_score": float(anomaly_data.get("au_intensity", {}).get("score") or 0.0) if anomaly_data.get("au_intensity", {}).get("score") is not None else None,
        "au_intensity_is_anomaly": bool(anomaly_data.get("au_intensity", {}).get("is_anomaly", False)),
        "model_dir": model_dir
    }
    return payload


def _build_detector_record(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    将当前帧转换为孤立森林训练/评分共用结构。
    """
    return {
        "frame": data.get("frame"),
        "time_sec": data.get("time_sec"),
        "emotion_scores": data.get("emotion_scores") or {},
        "heart_rate": data.get("heart_rate"),
        "head_pose": data.get("head_pose") or {},
        "left_eye_gaze": data.get("left_eye_gaze") or {},
        "right_eye_gaze": data.get("right_eye_gaze") or {},
        "au_intensities": data.get("au_intensities") or {},
    }


def _new_baseline_state() -> Dict[str, Any]:
    """
    创建单个嫌疑人的基线训练状态。
    """
    return {
        "records": deque(maxlen=_BASELINE_MAX_SAMPLES),
        "status": "collecting",
        "trained_count": 0,
        "future": None,
        "frozen": False,
        "last_error": None,
    }


def _get_baseline_state(sid: str) -> Dict[str, Any]:
    """
    获取或初始化嫌疑人的基线状态。
    """
    state = _baseline_states.get(sid)
    if state is None:
        state = _new_baseline_state()
        _baseline_states[sid] = state
    return state


def _train_baseline_models(sid: str, records: List[Dict[str, Any]]) -> None:
    """
    后台训练基线模型；不阻塞 WebSocket 单帧响应。
    """
    try:
        with _baseline_lock:
            if sid in _released_baselines:
                return
        saved = _iso_detector.train_baseline_from_records(sid, records)
        with _baseline_lock:
            if sid in _released_baselines:
                _baseline_states.pop(sid, None)
                release_models = getattr(_iso_detector, "release_cached_models", None)
                if callable(release_models):
                    release_models(sid)
                return
            state = _get_baseline_state(sid)
            state["trained_count"] = max(int(state.get("trained_count", 0) or 0), len(records))
            state["status"] = "ready" if saved else "not_ready"
            state["last_error"] = None if saved else "baseline_model_not_saved"
        _logger.info("face baseline trained suspect_id=%s samples=%s models=%s", sid, len(records), list(saved.keys()))
    except Exception as exc:
        with _baseline_lock:
            state = _get_baseline_state(sid)
            state["status"] = "failed"
            state["last_error"] = str(exc)
        _logger.exception("[process_frame_ws_payload] 基线模型后台训练失败 suspect_id=%s", sid)


def _schedule_baseline_training(sid: str, force: bool = False) -> str:
    """
    在 test_status=0 阶段调度基线训练；基准结束后不再提交新的同步训练。
    """
    records: List[Dict[str, Any]] = []
    should_submit = False
    with _baseline_lock:
        state = _get_baseline_state(sid)
        if state.get("frozen"):
            return str(state.get("status") or "not_ready")

        existing_future = state.get("future")
        if existing_future is not None and not existing_future.done():
            state["status"] = "training"
            return "training"

        records = list(state["records"])
        if len(records) < _BASELINE_MIN_SAMPLES:
            state["status"] = "collecting"
            return "collecting"

        trained_count = int(state.get("trained_count", 0) or 0)
        should_submit = force or (len(records) - trained_count >= _BASELINE_TRAIN_EVERY)
        if not should_submit and state.get("status") == "ready":
            return "ready"
        if not should_submit:
            return str(state.get("status") or "collecting")

        state["status"] = "training"
        state["last_error"] = None

    future = _baseline_executor.submit(_train_baseline_models, sid, records)
    with _baseline_lock:
        state = _get_baseline_state(sid)
        state["future"] = future
        return str(state.get("status") or "training")


def _collect_baseline_frame(sid: str, analysis_data: Dict[str, Any]) -> str:
    """
    test_status=0 表示基线采集中：持续收集样本并异步训练/更新基线模型。
    """
    with _baseline_lock:
        _released_baselines.discard(sid)
        state = _baseline_states.get(sid)
        # 前端重置后重新发送 0，视为新一轮基线采集，避免复用上一轮封板状态。
        if state is None or state.get("frozen"):
            state = _new_baseline_state()
            _baseline_states[sid] = state
        state["records"].append(_build_detector_record(analysis_data))
        if state.get("status") not in {"training", "ready"}:
            state["status"] = "collecting"

    return _schedule_baseline_training(sid)


def _freeze_baseline(sid: str) -> str:
    """
    test_status=1 表示基线结束：停止继续收集训练样本；模型 ready 后进入异常评分。
    """
    with _baseline_lock:
        if sid in _released_baselines and sid not in _baseline_states:
            return "released"
        state = _get_baseline_state(sid)
        state["frozen"] = True
        if state.get("status") == "collecting":
            state["status"] = "not_ready"
        return str(state.get("status") or "not_ready")


def _release_baseline(sid: str) -> str:
    """
    test_status=2 表示本次审讯结束：释放内存中的基线状态和模型缓存。
    """
    future = None
    with _baseline_lock:
        state = _baseline_states.pop(sid, None)
        _released_baselines.add(sid)
        if state is not None:
            records = state.get("records")
            if hasattr(records, "clear"):
                records.clear()
            future = state.get("future")

    if future is not None and not future.done():
        future.cancel()

    release_models = getattr(_iso_detector, "release_cached_models", None)
    if callable(release_models):
        release_models(sid)
    return "released"


def _get_baseline_status(sid: str) -> str:
    with _baseline_lock:
        state = _baseline_states.get(sid)
        return str((state or {}).get("status") or "not_ready")


def _normalize_anomaly_data(anomaly_res: Dict[str, Any]) -> Dict[str, Any]:
    """
    统一异常评分字段，兼容模型缺失时返回 None 的情况。
    """
    anomaly_data = {}
    for domain in _ANOMALY_DOMAINS:
        value = anomaly_res.get(domain, {"score": 0.0, "is_anomaly": False}) or {}
        score = value.get("score")
        anomaly_data[domain] = {
            "score": 0.0 if score is None else float(score),
            "is_anomaly": bool(value.get("is_anomaly", False)),
        }
    return anomaly_data


def _has_model_score(anomaly_res: Dict[str, Any]) -> bool:
    """
    判断评分是否来自已加载模型；全部为 None 时说明基线模型尚不可用。
    """
    for domain in _ANOMALY_DOMAINS:
        value = anomaly_res.get(domain) or {}
        if value.get("score") is not None or value.get("is_anomaly") is not None:
            return True
    return False


def _score_anomaly(sid: str, analysis_data: Dict[str, Any]) -> bool:
    """
    使用已训练基线模型评分；为排查实时链路性能，当前不写 emotion_anomaly 表。
    """
    anomaly_res = _iso_detector.score_record(sid, analysis_data)
    if not _has_model_score(anomaly_res):
        analysis_data["anomaly_status"] = "skipped"
        return False

    anomaly_data = _normalize_anomaly_data(anomaly_res)
    analysis_data["anomaly_data"] = anomaly_data
    analysis_data["anomaly_status"] = "ready"

    with _baseline_lock:
        state = _get_baseline_state(sid)
        state["status"] = "ready"
        state["last_error"] = None

    return True


def _normalize_test_status(test_status: int) -> int:
    try:
        return int(test_status)
    except (TypeError, ValueError):
        return 0


def process_frame_ws_payload(image_b64: str, suspect_id: str, test_status: int = 0) -> Dict[str, Any]:
    """
    WebSocket/HTTP 路由复用入口:
    - 输入: base64 编码的图像字符串
    - 输出: 实时面部分析的结构化结果
    参数:
        image_b64: base64 图像字符串（BGR）
        suspect_id: 对象/人员标识/
        test_status: 0采集基线，1基线结束并评分，2审讯结束并释放模型缓存
    返回:
        分析结果字典（兼容旧接口）
    """
    total_started = time.perf_counter()
    timings = {
        "decode_ms": 0.0,
        "emotion_ms": 0.0,
        "face_analyze_ms": 0.0,
        "face_landmark_ms": 0.0,
        "db_ms": 0.0,
        "baseline_ms": 0.0,
        "anomaly_ms": 0.0,
        "total_ms": 0.0,
    }
    try:
        test_status = _normalize_test_status(test_status)
        sid = str(suspect_id)

        decode_started = time.perf_counter()
        image = _b2b(image_b64)
        timings["decode_ms"] = _elapsed_ms(decode_started)

        analyze_started = time.perf_counter()
        try:
            _, _, analysis_data = _analyzer.process_frame(image)
        finally:
            timings["face_analyze_ms"] = _elapsed_ms(analyze_started)
        if not analysis_data:
            _logger.warning("process_frame_ws_payload empty face analysis suspect_id=%s test_status=%s", sid, test_status)
            return _build_fallback_analysis_data(suspect_id, test_status, timings, total_started)
        face_performance = analysis_data.pop("_performance", {}) or {}
        timings["face_landmark_ms"] = float(face_performance.get("face_landmark_ms", 0.0) or 0.0)
        timings["emotion_ms"] = float(face_performance.get("emotion_ms", 0.0) or 0.0)
        analysis_data["suspect_id"] = suspect_id
        analysis_data["time_sec"] = int(time.time() * 1000)
        pitch = float(analysis_data.get("head_pose", {}).get("pitch", 0.0) or 0.0)
        yaw = float(analysis_data.get("head_pose", {}).get("yaw", 0.0) or 0.0)
        analysis_data["attention"] = 1 if abs(pitch) < 20 and abs(yaw) < 20 else 2
        
        # 数据库启用时才落库 emotion_real_time；实时检测展示不依赖数据库写入。
        db_started = time.perf_counter()
        try:
            if is_database_enabled():
                payload = _build_repo_payload(analysis_data)
                obj = _repo.create(payload)
                _logger.info("process_frame_ws_payload: DB persisted id=%s ts=%s", getattr(obj, "id", None), payload.get("time_sec"))
        except Exception as db_err:
            _logger.exception("[process_frame_ws_payload] DB 写入失败")
        finally:
            timings["db_ms"] = _elapsed_ms(db_started)

        # 孤立森林模型逻辑:
        # 0=采集并异步训练基线；1=停止采集并在 ready 时评分；2=审讯结束并释放缓存。
        if test_status == 0:
            baseline_started = time.perf_counter()
            baseline_status = _collect_baseline_frame(sid, analysis_data)
            timings["baseline_ms"] = _elapsed_ms(baseline_started)
            analysis_data["baseline_status"] = baseline_status
            analysis_data["anomaly_status"] = "collecting"

        elif test_status == 1:
            baseline_started = time.perf_counter()
            baseline_status = _freeze_baseline(sid)
            timings["baseline_ms"] = _elapsed_ms(baseline_started)
            analysis_data["baseline_status"] = baseline_status
            if baseline_status == "ready":
                anomaly_started = time.perf_counter()
                _score_anomaly(sid, analysis_data)
                timings["anomaly_ms"] = _elapsed_ms(anomaly_started)
            elif baseline_status == "released":
                analysis_data["anomaly_status"] = "released"
            else:
                analysis_data["anomaly_status"] = "skipped"

        elif test_status == 2:
            baseline_started = time.perf_counter()
            baseline_status = _release_baseline(sid)
            timings["baseline_ms"] = _elapsed_ms(baseline_started)
            analysis_data["baseline_status"] = baseline_status
            analysis_data["anomaly_status"] = "released"

        _attach_performance(analysis_data, timings, total_started)
        if _SLOW_FRAME_LOG_MS >= 0 and timings["total_ms"] >= _SLOW_FRAME_LOG_MS:
            # 慢帧日志只记录分段耗时和状态，避免把原始图片或 Base64 写入日志。
            _logger.info(
                "process_frame_ws_payload slow frame suspect_id=%s test_status=%s baseline_status=%s anomaly_status=%s performance=%s",
                sid,
                test_status,
                analysis_data.get("baseline_status"),
                analysis_data.get("anomaly_status"),
                timings,
            )
        return analysis_data
    except Exception as e:
        _logger.exception("[process_frame_ws_payload] 未捕获错误")
        try:
            normalized_status = _normalize_test_status(locals().get("test_status", 0))
            fallback_suspect = str(locals().get("suspect_id", "unknown"))
            return _build_fallback_analysis_data(fallback_suspect, normalized_status, timings, total_started)
        except Exception:
            _logger.exception("[process_frame_ws_payload] 兜底回包构建失败")
            return {}
