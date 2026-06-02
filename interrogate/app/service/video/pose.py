# -*- coding: utf-8 -*-
"""
头部姿态估计
"""
from typing import Any, Tuple, List

import cv2
import numpy as np

from .utils import get_landmark_coords


def get_head_pose(landmarks: List[Any], w: int, h: int) -> Tuple[float, float, float]:
    """
    基于 2D-3D 对应点与 PnP 求解头部姿态角（pitch, yaw, roll）
    参数:
        landmarks: MediaPipe 关键点列表
        w: 图像宽度
        h: 图像高度
    返回:
        (pitch, yaw, roll)，单位为度，保留 1 位小数；失败则返回 (0, 0, 0)
    """
    try:
        model_points = np.float32([
            [0.0, 0.0, 0.0],
            [0.0, -330.0, -65.0],
            [-225.0, 170.0, -135.0],
            [225.0, 170.0, -135.0],
            [-150.0, -150.0, -125.0],
            [150.0, -150.0, -125.0]
        ])

        image_points = np.float32([
            get_landmark_coords(landmarks[1], w, h),
            get_landmark_coords(landmarks[152], w, h),
            get_landmark_coords(landmarks[33], w, h),
            get_landmark_coords(landmarks[263], w, h),
            get_landmark_coords(landmarks[61], w, h),
            get_landmark_coords(landmarks[291], w, h)
        ])

        focal_length = w
        center = (w / 2, h / 2)
        camera_matrix = np.array([
            [focal_length, 0, center[0]],
            [0, focal_length, center[1]],
            [0, 0, 1]
        ], dtype=np.float64)
        dist_coeffs = np.zeros((4, 1))

        success, rvec, tvec = cv2.solvePnP(
            model_points, image_points, camera_matrix, dist_coeffs,
            flags=cv2.SOLVEPNP_ITERATIVE
        )
        if not success:
            return 0.0, 0.0, 0.0

        rmat, _ = cv2.Rodrigues(rvec)
        sy = np.sqrt(rmat[0, 0] * rmat[0, 0] + rmat[1, 0] * rmat[1, 0])
        singular = sy < 1e-6

        if not singular:
            yaw = np.arctan2(rmat[2, 0], sy) * 180 / np.pi
            pitch = np.arctan2(-rmat[2, 1], rmat[2, 2]) * 180 / np.pi
            roll = np.arctan2(rmat[1, 0], rmat[0, 0]) * 180 / np.pi
        else:
            yaw = np.arctan2(-rmat[1, 2], rmat[1, 1]) * 180 / np.pi
            pitch = np.arctan2(-rmat[2, 1], rmat[2, 2]) * 180 / np.pi
            roll = 0.0

        if pitch < 0:
            pitch = 180 + pitch
        elif pitch > 0:
            pitch = pitch - 180

        return round(float(pitch), 1), round(float(yaw), 1), round(float(roll), 1)
    except Exception:
        return 0.0, 0.0, 0.0
