# -*- coding: utf-8 -*-
"""
基于绿色通道与频域方法的心率估计
"""
from typing import Optional, List, Any
from collections import deque

import cv2
import numpy as np
import heartpy as hp


class FacePhys:
    """
    简化的频域心率估计器
    """
    def __init__(self, sample_rate: float = 60.0):
        """
        初始化估计器
        参数:
            sample_rate: 采样率（帧率）
        """
        self.sample_rate = sample_rate

    def estimate_bpm(self, signal: List[float]) -> Optional[int]:
        """
        基于频域峰值估计心率
        参数:
            signal: 绿色通道序列
        返回:
            合理范围内的 bpm（整数）；失败返回 None
        """
        if signal is None or len(signal) < 160:
            return None
        data = np.asarray(signal, dtype=np.float64)
        data = data - np.mean(data)
        if np.std(data) < 1e-6:
            return None
        window = np.hanning(data.size)
        spec = np.fft.rfft(data * window)
        freqs = np.fft.rfftfreq(data.size, d=1.0 / self.sample_rate)
        mask = (freqs >= 0.7) & (freqs <= 3.0)
        if not np.any(mask):
            return None
        power = np.abs(spec) ** 2
        band_freqs = freqs[mask]
        band_power = power[mask]
        peak_hz = float(band_freqs[np.argmax(band_power)])
        bpm = int(round(peak_hz * 60.0))
        return bpm if 40 <= bpm <= 180 else None


def get_forehead_green(image: np.ndarray, landmarks: Any, w: int, h: int) -> Optional[float]:
    """
    估计额头区域的绿色通道均值（用于心率信号）
    参数:
        image: BGR 图像
        landmarks: MediaPipe 关键点列表
        w: 图像宽度
        h: 图像高度
    返回:
        绿色通道均值；失败返回 None
    """
    try:
        cx = w // 2
        cy = h // 2 + h // 12
        size_x = w // 4
        size_y = h // 4
        x1 = max(20, cx - size_x)
        y1 = max(20, cy - size_y)
        x2 = min(w - 20, cx + size_x)
        y2 = min(h - 20, cy + size_y)
        roi = image[y1:y2, x1:x2]
        if roi.size == 0:
            return None
        roi = cv2.GaussianBlur(roi, (21, 21), 0)
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 6)
        cv2.putText(image, "HR ZONE", (x1 + 10, y1 + 40),
                    cv2.FONT_HERSHEY_DUPLEX, 1.2, (0, 255, 0), 3)
        return float(np.mean(roi[:, :, 1]))
    except Exception:
        return None


def calculate_bpm_heartpy(green_buffer: deque) -> Optional[int]:
    """
    使用 heartpy 对绿色通道序列进行心率估计
    参数:
        green_buffer: 绿色通道值的滑动窗口
    返回:
        合理范围内的 bpm（整数）；失败返回 None
    """
    if len(green_buffer) < 160:
        return None
    try:
        data = np.array(green_buffer)
        working_data, measures = hp.process(
            data,
            sample_rate=60.0,
            high_precision=True,
            clean_rr=True,
            bpmmin=10,
            bpmmax=180,
            reject_segmentwise=False,
            calc_freq=True
        )
        bpm = measures['bpm']
        if not np.isnan(bpm) and 40 <= bpm <= 180:
            return int(bpm)
        return None
    except hp.exceptions.BadSignalWarning:
        return None
