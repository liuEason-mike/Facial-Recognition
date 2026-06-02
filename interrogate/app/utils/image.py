"""
图像工具函数
- b64_to_bgr：将 base64 编码图像解码为 OpenCV BGR 数组
"""
import base64
from typing import Optional


def b64_to_bgr(data: str):
    """
    将 base64 编码的图像（JPEG/PNG）解码为 BGR 图像
    返回：
      - numpy.ndarray (BGR) 或 None（解码失败）
    """
    try:
        import cv2
        import numpy as np
        raw = base64.b64decode(data.split(",")[-1])
        arr = np.frombuffer(raw, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        return img
    except Exception:
        return None
