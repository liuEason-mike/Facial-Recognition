# -*- coding: utf-8 -*-
"""
动作单元（AU）强度估计
"""
from typing import Any, Dict, Tuple, List

import numpy as np

from .utils import calculate_distance, get_landmark_coords


def compute_baseline(landmarks: List[Any], w: int, h: int) -> Dict[str, float]:
    """
    计算 AU 强度归一化所需的基准距离
    参数:
        landmarks: MediaPipe 关键点列表
        w: 图像宽度
        h: 图像高度
    返回:
        各项基准距离字典；若眼距异常则返回空字典
    """
    eye_dist = calculate_distance(
        get_landmark_coords(landmarks[33], w, h),
        get_landmark_coords(landmarks[133], w, h)
    )
    if eye_dist < 10:
        return {}
    norm = lambda d: d / (eye_dist + 1e-6)
    return {
        "au1": norm(get_landmark_coords(landmarks[9], w, h)[1] - get_landmark_coords(landmarks[151], w, h)[1]),
        "au2": norm(get_landmark_coords(landmarks[10], w, h)[1] - get_landmark_coords(landmarks[173], w, h)[1]),
        "au4": norm(calculate_distance(get_landmark_coords(landmarks[151], w, h), get_landmark_coords(landmarks[9], w, h))),
        "ear": (norm(calculate_distance(get_landmark_coords(landmarks[159], w, h), get_landmark_coords(landmarks[145], w, h))) +
                norm(calculate_distance(get_landmark_coords(landmarks[386], w, h), get_landmark_coords(landmarks[374], w, h)))) / 2,
        "au6": (norm(calculate_distance(get_landmark_coords(landmarks[159], w, h), get_landmark_coords(landmarks[145], w, h))) +
                norm(calculate_distance(get_landmark_coords(landmarks[386], w, h), get_landmark_coords(landmarks[374], w, h)))) / 2,
        "au9": norm(calculate_distance(get_landmark_coords(landmarks[240], w, h), get_landmark_coords(landmarks[460], w, h))),
        "au10": norm(get_landmark_coords(landmarks[12], w, h)[1] - get_landmark_coords(landmarks[13], w, h)[1]),
        "mouth_w": norm(calculate_distance(get_landmark_coords(landmarks[61], w, h), get_landmark_coords(landmarks[291], w, h))),
        "lip_thick": norm(calculate_distance(get_landmark_coords(landmarks[13], w, h), get_landmark_coords(landmarks[14], w, h))),
        "mouth_open": norm(calculate_distance(get_landmark_coords(landmarks[13], w, h), get_landmark_coords(landmarks[14], w, h))),
        "jaw_drop": norm(get_landmark_coords(landmarks[17], w, h)[1] - get_landmark_coords(landmarks[152], w, h)[1]),
        "au17": norm(get_landmark_coords(landmarks[200], w, h)[1] - get_landmark_coords(landmarks[17], w, h)[1])
    }


def calculate_au_intensities(landmarks: List[Any], w: int, h: int, baseline: Dict[str, float]) -> Dict[str, float]:
    """
    依据当前帧关键点与基准距离，估计各 AU 的强度（0~1）
    参数:
        landmarks: MediaPipe 关键点列表
        w: 图像宽度
        h: 图像高度
        baseline: 由 compute_baseline 计算得到的基准字典
    返回:
        AU 强度字典；如基准无效返回空字典
    """
    if not baseline:
        return {}

    eye_dist = calculate_distance(
        get_landmark_coords(landmarks[33], w, h),
        get_landmark_coords(landmarks[133], w, h)
    )
    if eye_dist < 10:
        return {}
    norm = lambda d: d / (eye_dist + 1e-6)

    try:
        au_intensities: Dict[str, float] = {}
        ear_l = norm(calculate_distance(get_landmark_coords(landmarks[159], w, h), get_landmark_coords(landmarks[145], w, h))) / baseline["ear"]
        ear_r = norm(calculate_distance(get_landmark_coords(landmarks[386], w, h), get_landmark_coords(landmarks[374], w, h))) / baseline["ear"]

        au_intensities["内眉上提"] = max(0.0, (baseline["au1"] - norm(get_landmark_coords(landmarks[9], w, h)[1] - get_landmark_coords(landmarks[151], w, h)[1])) * 10)
        au_intensities["外眉上提"] = max(0.0, (baseline["au2"] - norm(get_landmark_coords(landmarks[10], w, h)[1] - get_landmark_coords(landmarks[173], w, h)[1])) * 10)
        au_intensities["眉间皱起"] = max(0.0, norm(calculate_distance(get_landmark_coords(landmarks[151], w, h), get_landmark_coords(landmarks[9], w, h))) / baseline["au4"] - 0.85) * 12
        au_intensities["上眼睑提升"] = max(0.0, (2.2 - (ear_l + ear_r)) * 2)
        au_intensities["脸颊提升"] = max(0.0, (baseline["au6"] - (ear_l + ear_r) / 2) * 15)
        au_intensities["鼻翼提起"] = max(0.0, norm(calculate_distance(get_landmark_coords(landmarks[240], w, h), get_landmark_coords(landmarks[460], w, h))) / baseline["au9"] - 0.9) * 12
        au_intensities["上唇上提"] = max(0.0, (baseline["au10"] - norm(get_landmark_coords(landmarks[12], w, h)[1] - get_landmark_coords(landmarks[13], w, h)[1])) * 18)

        left = norm(get_landmark_coords(landmarks[61], w, h)[1] - get_landmark_coords(landmarks[13], w, h)[1])
        right = norm(get_landmark_coords(landmarks[291], w, h)[1] - get_landmark_coords(landmarks[14], w, h)[1])
        au_intensities["嘴角上提"] = max(0.0, (0.035 - (left + right) / 2) * 80)
        au_intensities["落寞"] = max(0.0, ((left + right) / 2 - 0.008) * 120)
        au_intensities["下巴上提"] = max(0.0, (baseline["au17"] - norm(get_landmark_coords(landmarks[200], w, h)[1] - get_landmark_coords(landmarks[17], w, h)[1])) * 15)
        au_intensities["唇角拉伸"] = max(0.0, norm(calculate_distance(get_landmark_coords(landmarks[61], w, h), get_landmark_coords(landmarks[291], w, h))) / baseline["mouth_w"] - 1.0) * 10
        au_intensities["嘴唇收紧"] = max(0.0, (baseline["lip_thick"] - norm(calculate_distance(get_landmark_coords(landmarks[13], w, h), get_landmark_coords(landmarks[14], w, h)))) * 35)
        au_intensities["嘴唇分开"] = max(0.0, norm(calculate_distance(get_landmark_coords(landmarks[13], w, h), get_landmark_coords(landmarks[14], w, h))) / baseline["mouth_open"] - 0.3) * 5
        au_intensities["下颌下降"] = max(0.0, norm(get_landmark_coords(landmarks[17], w, h)[1] - get_landmark_coords(landmarks[152], w, h)[1]) / baseline["jaw_drop"] - 0.9) * 7
        au_intensities["闭眼"] = max(0.0, (0.24 - (ear_l + ear_r) / 2) / 0.24)

        for k in au_intensities:
            # 限制范围在 0.0 ~ 1.0，并保留 4 位小数
            au_intensities[k] = float(round(np.clip(au_intensities[k], 0.0, 1.0), 4))
        return au_intensities
    except Exception:
        return {}


def extract_blendshapes(blendshapes: List[Any]) -> Dict[str, float]:
    """
    从 MediaPipe Blendshapes 中提取 52 类 AU 数据
    参数:
        blendshapes: MediaPipe face_blendshapes[0] 列表
    返回:
        52 类 AU (Blendshapes) 的强度字典 (0.0 ~ 1.0，保留 4 位小数)
    """
    if not blendshapes:
        return {}
    
    # MediaPipe 返回的是 Category 列表，每个 Category 有 category_name 和 score
    res = {}
    for item in blendshapes:
        # 限制范围在 0.0 ~ 1.0，并保留 4 位小数
        res[item.category_name] = float(round(np.clip(item.score, 0.0, 1.0), 4))
    return res
