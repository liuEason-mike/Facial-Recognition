# -*- coding: utf-8 -*-
"""
眼睛与视线估计
"""
from typing import Any, Tuple, List

import numpy as np

from .utils import get_landmark_coords, _EYE_KEYPOINTS


def calculate_eye_movement(landmarks: List[Any], w: int, h: int) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    """
    基于虹膜与眼裂位置计算左右眼的水平与垂直注视角度
    参数:
        landmarks: MediaPipe 关键点列表
        w: 图像宽度
        h: 图像高度
    返回:
        (左眼(水平, 垂直), 右眼(水平, 垂直))，角度单位为度，保留 1 位小数
    """
    left_iris = get_landmark_coords(landmarks[_EYE_KEYPOINTS["left_iris"]], w, h)
    left_inner = get_landmark_coords(landmarks[_EYE_KEYPOINTS["left_eye_inner"]], w, h)
    left_outer = get_landmark_coords(landmarks[_EYE_KEYPOINTS["left_eye_outer"]], w, h)
    left_top = get_landmark_coords(landmarks[_EYE_KEYPOINTS["left_eye_top"]], w, h)
    left_bottom = get_landmark_coords(landmarks[_EYE_KEYPOINTS["left_eye_bottom"]], w, h)

    left_horiz_ratio = (left_iris[0] - left_inner[0]) / (left_outer[0] - left_inner[0] + 1e-6)
    left_vert_ratio = (left_iris[1] - left_top[1]) / (left_bottom[1] - left_top[1] + 1e-6)
    left_horiz_angle = np.clip((left_horiz_ratio - 0.5) * 30, -15, 15)
    left_vert_angle = np.clip((left_vert_ratio - 0.5) * 20, -10, 10)

    right_iris = get_landmark_coords(landmarks[_EYE_KEYPOINTS["right_iris"]], w, h)
    right_inner = get_landmark_coords(landmarks[_EYE_KEYPOINTS["right_eye_inner"]], w, h)
    right_outer = get_landmark_coords(landmarks[_EYE_KEYPOINTS["right_eye_outer"]], w, h)
    right_top = get_landmark_coords(landmarks[_EYE_KEYPOINTS["right_eye_top"]], w, h)
    right_bottom = get_landmark_coords(landmarks[_EYE_KEYPOINTS["right_eye_bottom"]], w, h)

    right_horiz_ratio = (right_iris[0] - right_inner[0]) / (right_outer[0] - right_inner[0] + 1e-6)
    right_vert_ratio = (right_iris[1] - right_top[1]) / (right_bottom[1] - right_top[1] + 1e-6)
    right_horiz_angle = np.clip((right_horiz_ratio - 0.5) * 30, -15, 15)
    right_vert_angle = np.clip((right_vert_ratio - 0.5) * 20, -10, 10)

    return (round(float(left_horiz_angle), 1), round(float(left_vert_angle), 1)), \
           (round(float(right_horiz_angle), 1), round(float(right_vert_angle), 1))
