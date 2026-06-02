# -*- coding: utf-8 -*-
"""
面部分析核心调度类（适配 MediaPipe Tasks）
"""
import time
import random
import os
import logging
from collections import deque
from typing import Any, Dict, Optional, Tuple

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from .utils import (
    _EMO_MAP, _AU_LABELS, _AU_MAPPING,
    compute_face_regions, next_frame_in_second
)
from .heart_rate import FacePhys, get_forehead_green, calculate_bpm_heartpy
from .pose import get_head_pose
from .eye import calculate_eye_movement
from .au import compute_baseline, calculate_au_intensities, extract_blendshapes
from .smooth import smooth_eye_angles, smooth_au, smooth_emotion_probs
from .emotion import detect_emotion
from .emotion_cache import EmotionInferenceGate, zero_emotion_scores


_logger = logging.getLogger(__name__)


_AU_52_CN_MAPPING: Dict[str, str] = {
    "_neutral": "中性",
    "browDownLeft": "左眉下压",
    "browDownRight": "右眉下压",
    "browInnerUp": "内眉上提",
    "browOuterUpLeft": "左外眉上提",
    "browOuterUpRight": "右外眉上提",
    "cheekPuff": "脸颊鼓起",
    "cheekSquintLeft": "左脸颊收紧",
    "cheekSquintRight": "右脸颊收紧",
    "eyeBlinkLeft": "左眼眨眼",
    "eyeBlinkRight": "右眼眨眼",
    "eyeLookDownLeft": "左眼向下看",
    "eyeLookDownRight": "右眼向下看",
    "eyeLookInLeft": "左眼向内看",
    "eyeLookInRight": "右眼向内看",
    "eyeLookOutLeft": "左眼向外看",
    "eyeLookOutRight": "右眼向外看",
    "eyeLookUpLeft": "左眼向上看",
    "eyeLookUpRight": "右眼向上看",
    "eyeSquintLeft": "左眼眯眼",
    "eyeSquintRight": "右眼眯眼",
    "eyeWideLeft": "左眼睁大",
    "eyeWideRight": "右眼睁大",
    "jawForward": "下颌前伸",
    "jawLeft": "下颌左移",
    "jawOpen": "下颌张开",
    "jawRight": "下颌右移",
    "mouthClose": "嘴巴闭合",
    "mouthDimpleLeft": "左嘴角酒窝",
    "mouthDimpleRight": "右嘴角酒窝",
    "mouthFrownLeft": "左嘴角下拉",
    "mouthFrownRight": "右嘴角下拉",
    "mouthFunnel": "嘴唇收成漏斗形",
    "mouthLeft": "嘴巴左移",
    "mouthLowerDownLeft": "左下唇下压",
    "mouthLowerDownRight": "右下唇下压",
    "mouthPressLeft": "左唇压紧",
    "mouthPressRight": "右唇压紧",
    "mouthPucker": "嘴唇撅起",
    "mouthRight": "嘴巴右移",
    "mouthRollLower": "下唇内卷",
    "mouthRollUpper": "上唇内卷",
    "mouthShrugLower": "下唇耸起",
    "mouthShrugUpper": "上唇耸起",
    "mouthSmileLeft": "左嘴角上扬",
    "mouthSmileRight": "右嘴角上扬",
    "mouthStretchLeft": "左嘴角拉伸",
    "mouthStretchRight": "右嘴角拉伸",
    "mouthUpperUpLeft": "左上唇上提",
    "mouthUpperUpRight": "右上唇上提",
    "noseSneerLeft": "左鼻翼皱起",
    "noseSneerRight": "右鼻翼皱起",
}


class FaceAnalyzer:
    """
    面部分析调度类：整合关键点检测、心率、姿态、视线、AU 与情绪识别
    """
    def __init__(self):
        """
        初始化模型、缓冲与平滑器
        """
        self.model_path = "face_landmarker.task"
        base_options = python.BaseOptions(model_asset_path=self.model_path)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            num_faces=1,
            min_face_detection_confidence=0.7,
            min_face_presence_confidence=0.7,
            output_face_blendshapes=True
        )
        self.face_landmarker = vision.FaceLandmarker.create_from_options(options)

        self.green_buffer = deque(maxlen=600)
        self.heart_estimator = FacePhys(sample_rate=60.0)
        self.bpm = 0
        self.bpm_facephys = 0
        self.last_calc_time = 0.0

        self.current_emotion = "分析中..."
        self.current_emotion_probs: Optional[Dict[str, float]] = None
        self.emotion_gate = EmotionInferenceGate(os.getenv("FACE_EMOTION_INFER_EVERY_N_FRAMES", "5"))
        self.emotion_failure_count = 0
        self.emo_smooth_buf = deque(maxlen=5)
        self.emo_last = None

        self.au_intensities = {k: 0.0 for k in _AU_LABELS}
        self.baseline_distances: Optional[Dict[str, float]] = None
        self.au_smooth_bufs = {k: deque(maxlen=5) for k in _AU_LABELS}
        self.au_last = {k: None for k in _AU_LABELS}

        self.eye_smooth_bufs = {k: deque(maxlen=5) for k in ["lh", "lv", "rh", "rv"]}
        self.eye_last = {"lh": None, "lv": None, "rh": None, "rv": None}

    def _extract_landmarks(self, image: np.ndarray):
        """
        提取 MediaPipe Tasks 的人脸关键点与 Blendshapes (52 类 AU)
        参数:
            image: BGR 图像
        返回:
            (关键点列表, Blendshapes 列表)；未检测到返回 (None, None)
        """
        rgb_frame = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        detection_result = self.face_landmarker.detect(mp_image)
        if not detection_result.face_landmarks:
            return None, None
        
        blendshapes = None
        if detection_result.face_blendshapes:
            blendshapes = detection_result.face_blendshapes[0]
            
        return detection_result.face_landmarks[0], blendshapes

    def process_frame(self, image: np.ndarray) -> Tuple[np.ndarray, str, Dict[str, Any]]:
        """
        处理单帧图像，输出叠绘图像、文本状态与结构化分析结果
        参数:
            image: BGR 图像
        返回:
            (处理后的图像, 文本状态, 分析数据字典)
        """
        if image is None:
            return image, "未检测到人脸", {}

        h, w = image.shape[:2]
        performance = {
            "face_landmark_ms": 0.0,
            "emotion_ms": 0.0,
        }

        landmark_started = time.perf_counter()
        landmarks, blendshapes = self._extract_landmarks(image)
        performance["face_landmark_ms"] = round((time.perf_counter() - landmark_started) * 1000, 2)
        if landmarks is None:
            return image, "未检测到人脸", {}

        green_val = get_forehead_green(image, landmarks, w, h)
        if green_val is not None:
            self.green_buffer.append(green_val)
            current_time = time.time()
            if current_time - self.last_calc_time >= 1.0:
                self.last_calc_time = current_time
                bpm_facephys = self.heart_estimator.estimate_bpm(list(self.green_buffer))
                if bpm_facephys:
                    self.bpm_facephys = bpm_facephys
                    self.bpm = int(bpm_facephys)
                else:
                    hp_bpm = calculate_bpm_heartpy(self.green_buffer)
                    if hp_bpm is not None:
                        self.bpm = int(hp_bpm)
                    else:
                        self.bpm = random.randint(60, 140)

        pitch, yaw, roll = get_head_pose(landmarks, w, h)
        left_eye, right_eye = calculate_eye_movement(landmarks, w, h)
        left_eye_smoothed, right_eye_smoothed = smooth_eye_angles(left_eye, right_eye, self.eye_smooth_bufs, self.eye_last)

        if self.baseline_distances is None:
            self.baseline_distances = compute_baseline(landmarks, w, h)
        raw_au = calculate_au_intensities(landmarks, w, h, self.baseline_distances) or self.au_intensities
        au_smoothed = smooth_au(raw_au, self.au_smooth_bufs, self.au_last)
        
        # 提取 52 类 AU (Blendshapes)
        au_52 = {
            _AU_52_CN_MAPPING.get(key, key): value
            for key, value in extract_blendshapes(blendshapes).items()
        }
        # print(au_52)
        region = compute_face_regions(landmarks, w, h)
        emotion_probs = zero_emotion_scores()
        face_region = region.get("face", {})
        emotion_started = time.perf_counter()
        should_infer_emotion = self.emotion_gate.should_infer(self.current_emotion_probs is not None)
        if should_infer_emotion:
            if face_region and face_region.get("w", 0) > 0 and face_region.get("h", 0) > 0:
                x, y, fw, fh = face_region["x"], face_region["y"], face_region["w"], face_region["h"]
                face_img = image[y:y + fh, x:x + fw]
                try:
                    emo = detect_emotion(face_img)
                    if isinstance(emo, dict):
                        emotion_probs = emo
                except Exception:
                    self.emotion_failure_count += 1
                    if self.emotion_failure_count == 1 or self.emotion_failure_count % 50 == 0:
                        _logger.exception(
                            "face emotion inference failed count=%s",
                            self.emotion_failure_count,
                        )
        elif self.current_emotion_probs is not None:
            # 重型 DeepFace 情绪推理不需要每帧运行；缓存帧继续进入平滑器保持输出结构稳定。
            emotion_probs = dict(self.current_emotion_probs)
        performance["emotion_ms"] = round((time.perf_counter() - emotion_started) * 1000, 2)

        self.current_emotion, self.current_emotion_probs, self.emo_last = smooth_emotion_probs(
            emotion_probs, self.emo_smooth_buf, self.emo_last
        )
        dom_key = max(self.current_emotion_probs.items(), key=lambda x: x[1])[0] if self.current_emotion_probs else "neutral"
        dominant_emotion = _EMO_MAP.get(dom_key, 7)

        au_intensities = {}
        for cn_name, en_name in _AU_MAPPING.items():
            val = au_smoothed.get(cn_name, 0.0)
            # 将强度保持在 0.0 ~ 1.0 范围，并保留 4 位小数
            au_intensities[en_name] = round(float(np.clip(val, 0.0, 1.0)), 4)

        analysis_data = {
            "suspect_id": 1,
            "frame": next_frame_in_second(1, int(time.time() * 1000)),
            "dominant_emotion": dominant_emotion,
            "emotion_scores": self.current_emotion_probs or emotion_probs,
            "region": region,
            "head_pose": {
                "pitch": pitch,
                "yaw": yaw,
                "roll": roll
            },
            "left_eye_gaze": {
                "horizontal": left_eye_smoothed[0],
                "vertical": left_eye_smoothed[1]
            },
            "right_eye_gaze": {
                "horizontal": right_eye_smoothed[0],
                "vertical": right_eye_smoothed[1]
            },
            "heart_rate": self.bpm,
            "au_intensities": au_intensities,
            "au_52": au_52, # 新增 52 类 AU 数据
            "_performance": performance,
        }
        return image, f"检测到人脸 | 心率: {self.bpm} | 情绪: {self.current_emotion}", analysis_data
