# -*- coding: utf-8 -*-
"""
平滑算法模块
"""
from collections import deque
from typing import Dict, Tuple, List

import numpy as np


def smooth_au(au_values: Dict[str, float],
              au_smooth_bufs: Dict[str, deque],
              au_last: Dict[str, float]) -> Dict[str, float]:
    """
    平滑 AU 强度值
    参数:
        au_values: 当前帧的 AU 强度字典
        au_smooth_bufs: 每个 AU 对应的平滑缓存队列
        au_last: 上一次输出的 AU 强度（用于去抖）
    返回:
        平滑后的 AU 强度字典
    """
    smoothed: Dict[str, float] = {}
    for k, v in au_values.items():
        val = float(v) if isinstance(v, (int, float)) else 0.0
        buf = au_smooth_bufs[k]
        buf.append(val)

        avg = float(np.mean(buf))
        last = au_last[k]
        if last is None or abs(avg - last) >= 0.03:
            au_last[k] = avg
            smoothed[k] = avg
        else:
            smoothed[k] = last

        smoothed[k] = float(np.clip(smoothed[k], 0.0, 1.0))
    return smoothed


def smooth_eye_angles(left_eye: Tuple[float, float],
                      right_eye: Tuple[float, float],
                      eye_smooth_bufs: Dict[str, deque],
                      eye_last: Dict[str, float]) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    """
    平滑双眼的水平/垂直角度
    参数:
        left_eye: 左眼 (水平角, 垂直角)
        right_eye: 右眼 (水平角, 垂直角)
        eye_smooth_bufs: 每个通道的平滑缓存队列
        eye_last: 上一次输出的角度（用于去抖）
    返回:
        (左眼平滑角度, 右眼平滑角度)
    """
    lh, lv = left_eye
    rh, rv = right_eye

    for key, val in [("lh", lh), ("lv", lv), ("rh", rh), ("rv", rv)]:
        buf = eye_smooth_bufs[key]
        buf.append(float(val))
        avg = float(np.mean(buf))
        if eye_last[key] is None or abs(avg - eye_last[key]) >= 0.8:
            eye_last[key] = avg

    left_smoothed = (
        round(eye_last["lh"] if eye_last["lh"] is not None else lh, 1),
        round(eye_last["lv"] if eye_last["lv"] is not None else lv, 1)
    )
    right_smoothed = (
        round(eye_last["rh"] if eye_last["rh"] is not None else rh, 1),
        round(eye_last["rv"] if eye_last["rv"] is not None else rv, 1)
    )
    return left_smoothed, right_smoothed


def smooth_emotion_probs(probs: Dict[str, float],
                         emo_smooth_buf: deque,
                         emo_last: List[float]) -> Tuple[str, Dict[str, float], List[float]]:
    """
    平滑情绪概率分布并返回主导情绪
    参数:
        probs: 原始情绪概率字典（键顺序可乱序）
        emo_smooth_buf: 历史平滑缓存（长度建议 5）
        emo_last: 上一次的平滑向量，用于去抖
    返回:
        (当前主导情绪名（首字母大写）, 百分比情绪分布, 更新后的 emo_last)
    """
    emo_order = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]
    vec = [float(probs.get(k, 0.0)) for k in emo_order]
    s = sum(vec)
    if s > 0:
        vec = [v / s for v in vec]

    emo_smooth_buf.append(vec)
    avg_vec = np.mean(np.array(emo_smooth_buf), axis=0).tolist()

    if emo_last is None:
        emo_last = avg_vec
    else:
        delta = sum(abs(a - b) for a, b in zip(avg_vec, emo_last))
        if delta >= 0.08:
            emo_last = avg_vec

    idx = int(np.argmax(emo_last))
    current_emotion = emo_order[idx].capitalize()
    current_emotion_probs = {emo_order[i]: float(emo_last[i]) * 100 for i in range(len(emo_order))}
    return current_emotion, current_emotion_probs, emo_last
