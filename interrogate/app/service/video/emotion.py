# -*- coding: utf-8 -*-
"""
情绪识别
"""
import os
from typing import Dict, Optional

import h5py
import numpy as np
from deepface import DeepFace
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, GlobalAveragePooling2D

# 全局模型缓存
_EMOTION_MODEL = None


def _build_custom_emotion_model() -> Sequential:
    """
    根据 H5 权重文件结构手动构建情绪模型架构
    架构特征：5层卷积 + 全局平均池化 + 3层全连接
    """
    model = Sequential([
        # Block 1
        Conv2D(64, (5, 5), padding="same", activation="relu", input_shape=(48, 48, 1), name="conv2d_1"),
        MaxPooling2D((2, 2)),
        
        # Block 2
        Conv2D(64, (3, 3), padding="same", activation="relu", name="conv2d_2"),
        MaxPooling2D((2, 2)),
        
        # Block 3
        Conv2D(64, (3, 3), padding="same", activation="relu", name="conv2d_3"),
        MaxPooling2D((2, 2)),
        
        # Block 4
        Conv2D(128, (3, 3), padding="same", activation="relu", name="conv2d_4"),
        MaxPooling2D((2, 2)),
        
        # Block 5
        Conv2D(128, (3, 3), padding="same", activation="relu", name="conv2d_5"),
        GlobalAveragePooling2D(),  # 将 (h, w, 128) 转换为 128 维向量
        
        # Dense layers
        Dense(1024, activation="relu", name="dense_1"),
        Dense(1024, activation="relu", name="dense_2"),
        Dense(7, activation="softmax", name="dense_3")
    ])
    return model


def _load_emotion_model():
    """
    延迟加载情绪识别模型并应用本地权重
    """
    global _EMOTION_MODEL
    if _EMOTION_MODEL is not None:
        return _EMOTION_MODEL

    try:
        # 项目根目录 = run.py 所在目录
        BASE_DIR = os.path.dirname(os.path.abspath("run.py"))
        weight_path = os.path.join(BASE_DIR, "deepface", "weight", "facial_expression_model_weights.h5")
        
        if not os.path.exists(weight_path):
            print(f"⚠️ 权重文件不存在: {weight_path}")
            return None

        # 手动构建模型以匹配权重文件结构
        model = _build_custom_emotion_model()
        
        # 加载本地指定的权重
        model.load_weights(weight_path)
        _EMOTION_MODEL = model
        print(f"✅ 已成功从本地加载情绪权重 (自定义架构): {weight_path}")
    except Exception as e:
        print(f"❌ 加载本地情绪权重失败: {e}")
        _EMOTION_MODEL = None

    return _EMOTION_MODEL


def detect_emotion(face_img: np.ndarray) -> Optional[Dict[str, float]]:
    """
    对人脸区域进行情绪识别，返回七类情绪的概率分布
    参数:
        face_img: 人脸裁剪图像（BGR）
    返回:
        情绪概率字典，键包含 angry/disgust/fear/happy/sad/surprise/neutral；
        识别失败返回 None
    """
    if face_img is None or face_img.size == 0:
        return None

    # 获取本地加载的模型
    model = _load_emotion_model()
    # 如果本地加载成功，将其传入 analyze 以避免再次加载默认模型
    models = {"emotion": model} if model else None

    preds = DeepFace.analyze(face_img, actions=["emotion"], models=models, enforce_detection=False, silent=True)
    if isinstance(preds, list):
        preds = preds[0]
    emo = preds.get("emotion", None)
    if not isinstance(emo, dict):
        return None
    # 仅保留需要的七类键
    keys = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]
    out = {k: float(emo.get(k, 0.0)) for k in keys}
    s = sum(out.values())
    if s > 0:
        out = {k: v / s for k, v in out.items()}
    return out