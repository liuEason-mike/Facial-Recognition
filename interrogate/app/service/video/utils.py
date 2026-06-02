# -*- coding: utf-8 -*-
"""
通用工具与常量定义
"""
import os
import subprocess
import csv
import time
import threading
import random
from typing import Any, Dict, Optional, List, Tuple

import numpy as np

# 情绪标签到编号的映射
_EMO_MAP: Dict[str, int] = {
    "angry": 1, "disgust": 2, "fear": 3, "happy": 4, "sad": 5, "surprise": 6, "neutral": 7
}

# 眼部关键点索引（MediaPipe Face Mesh）
_EYE_KEYPOINTS: Dict[str, int] = {
    "left_iris": 468, "left_eye_inner": 33, "left_eye_outer": 133,
    "left_eye_top": 159, "left_eye_bottom": 145, "right_iris": 473,
    "right_eye_inner": 263, "right_eye_outer": 362, "right_eye_top": 386,
    "right_eye_bottom": 374
}

# 动作单元中文标签
_AU_LABELS: List[str] = [
    "内眉上提", "外眉上提", "眉间皱起", "上眼睑提升", "脸颊提升",
    "鼻翼提起", "上唇上提", "嘴角上提", "落寞", "下巴上提",
    "唇角拉伸", "嘴唇收紧", "嘴唇分开", "下颌下降", "闭眼"
]

# AU 映射（中文 → 英文键）
_AU_MAPPING: Dict[str, str] = {
    "内眉上提": "inner_brow_raiser",
    "外眉上提": "outer_brow_raiser",
    "眉间皱起": "brow_furrower",
    "上眼睑提升": "upper_eyelid_raiser",
    "脸颊提升": "cheek_raiser",
    "鼻翼提起": "nose_wrinkler",
    "上唇上提": "upper_lip_raiser",
    "嘴角上提": "lip_corner_puller",
    "落寞": "lip_corner_depressor",
    "下巴上提": "jaw_raiser",
    "唇角拉伸": "lip_stretcher",
    "嘴唇收紧": "lip_compressor",
    "嘴唇分开": "lip_parter",
    "下颌下降": "jaw_dropper",
    "闭眼": "eye_closure"
}

_FRAME_LOCK = threading.Lock()
_FRAME_STATE: Dict[str, Tuple[int, int]] = {}


def calculate_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """
    计算二维点 p1 与 p2 的欧氏距离
    参数:
        p1: 第一个点坐标 (x, y)
        p2: 第二个点坐标 (x, y)
    返回:
        两点之间的欧氏距离
    """
    return np.linalg.norm(np.array(p1) - np.array(p2))


def normalize_heart_rate(bpm: Any, low: int = 60, high: int = 105) -> int:
    """
    规范化心率数值:
    - 无效或非正数时，返回合理范围内的随机值
    - 否则返回整数化后的 bpm
    参数:
        bpm: 原始心率值（可为字符串/浮点/整数）
        low: 随机下界
        high: 随机上界
    返回:
        规范化后的心率整数
    """
    try:
        v = int(float(bpm))
    except Exception:
        v = 0
    if v <= 0:
        return int(random.randint(int(low), int(high)))
    return v


def next_frame_in_second(suspect_id: Any, timestamp_ms: int) -> int:
    """
    统计同一嫌疑人（suspect_id）在某一秒内处理的帧序号（1 开始）
    参数:
        suspect_id: 对象/人员标识
        timestamp_ms: 当前帧时间戳（毫秒）
    返回:
        当前秒内的帧序号
    """
    sid = str(suspect_id)
    sec = int(timestamp_ms // 1000)
    with _FRAME_LOCK:
        last = _FRAME_STATE.get(sid)
        if not last or last[0] != sec:
            _FRAME_STATE[sid] = (sec, 1)
            return 1
        cnt = int(last[1]) + 1
        _FRAME_STATE[sid] = (sec, cnt)
        return cnt


def get_landmark_coords(landmark: Any, w: int, h: int) -> Tuple[float, float]:
    """
    将 MediaPipe 关键点的归一化坐标转换为像素坐标
    参数:
        landmark: MediaPipe 单个关键点对象
        w: 图像宽度
        h: 图像高度
    返回:
        (x, y) 像素坐标
    """
    return float(landmark.x * w), float(landmark.y * h)


def compute_face_regions(landmarks: List[Any], w: int, h: int) -> Dict[str, Any]:
    """
    计算人脸、双眼、眉毛与嘴部的矩形区域
    参数:
        landmarks: MediaPipe 关键点列表
        w: 图像宽度
        h: 图像高度
    返回:
        包含各区域位置信息的字典
    """
    all_x = [lm.x * w for lm in landmarks]
    all_y = [lm.y * h for lm in landmarks]
    face_x1, face_y1 = max(0, min(all_x)), max(0, min(all_y))
    face_x2, face_y2 = min(w, max(all_x)), min(h, max(all_y))

    left_eye_indices = [33, 133, 159, 145, 153, 144, 163, 7]
    left_eye_x = [landmarks[i].x * w for i in left_eye_indices]
    left_eye_y = [landmarks[i].y * h for i in left_eye_indices]
    le_x1, le_y1 = max(0, min(left_eye_x)), max(0, min(left_eye_y))
    le_x2, le_y2 = min(w, max(left_eye_x)), min(h, max(left_eye_y))

    right_eye_indices = [263, 362, 386, 374, 380, 373, 390, 249]
    right_eye_x = [landmarks[i].x * w for i in right_eye_indices]
    right_eye_y = [landmarks[i].y * h for i in right_eye_indices]
    re_x1, re_y1 = max(0, min(right_eye_x)), max(0, min(right_eye_y))
    re_x2, re_y2 = min(w, max(right_eye_x)), min(h, max(right_eye_y))

    left_brow_indices = [70, 63, 105, 66, 107, 55, 65, 52, 53, 46]
    left_brow_x = [landmarks[i].x * w for i in left_brow_indices]
    left_brow_y = [landmarks[i].y * h for i in left_brow_indices]
    lb_x1, lb_y1 = max(0, min(left_brow_x)), max(0, min(left_brow_y))
    lb_x2, lb_y2 = min(w, max(left_brow_x)), min(h, max(left_brow_y))

    right_brow_indices = [300, 293, 334, 296, 336, 285, 295, 282, 283, 276]
    right_brow_x = [landmarks[i].x * w for i in right_brow_indices]
    right_brow_y = [landmarks[i].y * h for i in right_brow_indices]
    rb_x1, rb_y1 = max(0, min(right_brow_x)), max(0, min(right_brow_y))
    rb_x2, rb_y2 = min(w, max(right_brow_x)), min(h, max(right_brow_y))

    mouth_indices = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 308, 324, 318, 402, 317, 14, 87, 178, 88, 95]
    mouth_x = [landmarks[i].x * w for i in mouth_indices]
    mouth_y = [landmarks[i].y * h for i in mouth_indices]
    m_x1, m_y1 = max(0, min(mouth_x)), max(0, min(mouth_y))
    m_x2, m_y2 = min(w, max(mouth_x)), min(h, max(mouth_y))

    # 鼻子
    nose_indices = [1, 2, 4, 5, 6, 168, 197, 195, 19, 94, 98, 327]
    nose_x = [landmarks[i].x * w for i in nose_indices]
    nose_y = [landmarks[i].y * h for i in nose_indices]
    n_x1, n_y1 = max(0, min(nose_x)), max(0, min(nose_y))
    n_x2, n_y2 = min(w, max(nose_x)), min(h, max(nose_y))

    # 下巴
    chin_indices = [152, 148, 176, 149, 150, 136, 172, 377, 400, 378, 379, 365, 397]
    chin_x = [landmarks[i].x * w for i in chin_indices]
    chin_y = [landmarks[i].y * h for i in chin_indices]
    c_x1, c_y1 = max(0, min(chin_x)), max(0, min(chin_y))
    c_x2, c_y2 = min(w, max(chin_x)), min(h, max(chin_y))

    # 牙齿 (以嘴唇内边缘作为参考区域)
    teeth_indices = [78, 191, 80, 81, 82, 13, 312, 311, 310, 415, 308, 324, 318, 402, 317, 14, 87, 178, 88, 95]
    teeth_x = [landmarks[i].x * w for i in teeth_indices]
    teeth_y = [landmarks[i].y * h for i in teeth_indices]
    t_x1, t_y1 = max(0, min(teeth_x)), max(0, min(teeth_y))
    t_x2, t_y2 = min(w, max(teeth_x)), min(h, max(teeth_y))

    res = {
        "face": {"x": int(face_x1), "y": int(face_y1), "w": int(face_x2 - face_x1), "h": int(face_y2 - face_y1)},
        "left_eye": {"x": int(le_x1), "y": int(le_y1), "w": int(le_x2 - le_x1), "h": int(le_y2 - le_y1)},
        "right_eye": {"x": int(re_x1), "y": int(re_y1), "w": int(re_x2 - re_x1), "h": int(re_y2 - re_y1)},
        "left_eyebrow": {"x1": int(lb_x1), "y1": int(lb_y1), "x2": int(lb_x2), "y2": int(lb_y2)},
        "right_eyebrow": {"x1": int(rb_x1), "y1": int(rb_y1), "x2": int(rb_x2), "y2": int(rb_y2)},
        "mouth": {"x1": int(m_x1), "y1": int(m_y1), "x2": int(m_x2), "y2": int(m_y2)},
        "nose": {"x1": int(n_x1), "y1": int(n_y1), "x2": int(n_x2), "y2": int(n_y2)},
        "chin": {"x1": int(c_x1), "y1": int(c_y1), "x2": int(c_x2), "y2": int(c_y2)},
        "teeth": {"x1": int(t_x1), "y1": int(t_y1), "x2": int(t_x2), "y2": int(t_y2)}
    }

    # 瞳孔 (如果存在 Iris 关键点，通常为 468-477)
    if len(landmarks) >= 478:
        lp_indices = [468, 469, 470, 471, 472]
        lp_x = [landmarks[i].x * w for i in lp_indices]
        lp_y = [landmarks[i].y * h for i in lp_indices]
        lp_x1, lp_y1 = max(0, min(lp_x)), max(0, min(lp_y))
        lp_x2, lp_y2 = min(w, max(lp_x)), min(h, max(lp_y))

        rp_indices = [473, 474, 475, 476, 477]
        rp_x = [landmarks[i].x * w for i in rp_indices]
        rp_y = [landmarks[i].y * h for i in rp_indices]
        rp_x1, rp_y1 = max(0, min(rp_x)), max(0, min(rp_y))
        rp_x2, rp_y2 = min(w, max(rp_x)), min(h, max(rp_y))

        res["left_pupil"] = {"x1": int(lp_x1), "y1": int(lp_y1), "x2": int(lp_x2), "y2": int(lp_y2)}
        res["right_pupil"] = {"x1": int(rp_x1), "y1": int(rp_y1), "x2": int(rp_x2), "y2": int(rp_y2)}
    # print(res)
    return res
    


class OpenFaceRunner:
    """
    OpenFace 特征提取器的子进程管理封装
    提供启动、停止与 CSV 结果读取的能力
    """
    def __init__(self, bin_path: Optional[str] = None, cam_id: int = 0, out_csv_path: Optional[str] = None):
        """
        初始化进程管理器
        参数:
            bin_path: FeatureExtraction 可执行文件路径（可自动探测）
            cam_id: 摄像头编号
            out_csv_path: 输出 CSV 文件路径
        """
        self.bin_path = self._detect_bin_path(bin_path)
        self.cam_id = cam_id
        self.out_csv_path = out_csv_path or os.path.join(os.path.dirname(__file__), "openface_live.csv")
        self.process = None
        self.latest_data = None
        self.running = False

    def _detect_bin_path(self, bin_path: Optional[str]) -> Optional[str]:
        """
        自动探测 FeatureExtraction 可执行文件路径
        参数:
            bin_path: 显式指定路径（可选）
        返回:
            探测到的有效可执行路径或 None
        """
        candidates = [
            bin_path,
            os.environ.get("OPENFACE_BIN"),
            "/usr/local/bin/FeatureExtraction",
            "/usr/bin/FeatureExtraction",
            os.path.join(os.path.dirname(__file__), "FeatureExtraction"),
            os.path.join(os.path.dirname(__file__), "OpenFace", "build", "bin", "FeatureExtraction"),
        ]
        for path in candidates:
            if path and os.path.exists(path) and os.access(path, os.X_OK):
                return path
        return None

    def start(self) -> bool:
        """
        启动 OpenFace 子进程并异步读取输出 CSV
        返回:
            True 表示成功启动；否则 False
        """
        if not self.bin_path:
            return False

        if os.path.exists(self.out_csv_path):
            try:
                os.remove(self.out_csv_path)
            except Exception:
                pass

        try:
            cmd = [self.bin_path, "-device", str(self.cam_id), "-q", "-of", self.out_csv_path, "-no_visualization"]
            self.process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            cmd = [self.bin_path, "-cam_id", str(self.cam_id), "-q", "-of", self.out_csv_path, "-no_visualization"]
            self.process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        self.running = True
        t = threading.Thread(target=self._reader_loop, daemon=True)
        t.start()
        return True

    def stop(self) -> None:
        """
        停止子进程并结束读取循环
        """
        self.running = False
        if self.process:
            try:
                self.process.terminate()
            except Exception:
                pass

    def _reader_loop(self) -> None:
        """
        后台读取 CSV 最新一行并解析为字典，保存到 latest_data
        """
        while self.running:
            try:
                if os.path.exists(self.out_csv_path):
                    with open(self.out_csv_path, "r", encoding="utf-8", newline="") as f:
                        reader = csv.DictReader(f)
                        last_row = None
                        for row in reader:
                            last_row = row
                        if last_row:
                            self.latest_data = self._parse_row(last_row)
                time.sleep(1.0 / 60.0)
            except Exception:
                time.sleep(0.5)

    def _parse_row(self, row: Dict[str, str]) -> Dict[str, Any]:
        """
        将 CSV 行解析为结构化字典（姿态、凝视、AU）
        参数:
            row: CSV 的一行数据
        返回:
            结构化字典
        """
        def safe_float(*keys: str) -> Optional[float]:
            for k in keys:
                v = row.get(k)
                if v and v != "":
                    try:
                        return float(v)
                    except Exception:
                        pass
            return None

        au_intensities = {}
        au_presence = {}
        for au in ["AU01", "AU02", "AU04", "AU05", "AU06", "AU07", "AU09", "AU10",
                   "AU12", "AU14", "AU15", "AU17", "AU20", "AU23", "AU25", "AU26", "AU28", "AU45"]:
            au_intensities[au] = safe_float(au + "_r")
            try:
                au_presence[au] = int(row.get(au + "_c", "")) if row.get(au + "_c") else None
            except Exception:
                au_presence[au] = None

        return {
            "pose_R_x": safe_float("pose_R_x", "pose_Rx"),
            "pose_R_y": safe_float("pose_R_y", "pose_Ry"),
            "pose_R_z": safe_float("pose_R_z", "pose_Rz"),
            "pose_T_x": safe_float("pose_T_x", "pose_Tx"),
            "pose_T_y": safe_float("pose_T_y", "pose_Ty"),
            "pose_T_z": safe_float("pose_T_z", "pose_Tz"),
            "gaze_angle_x": safe_float("gaze_angle_x"),
            "gaze_angle_y": safe_float("gaze_angle_y"),
            "au_intensities": au_intensities,
            "au_presence": au_presence
        }

    def get_latest_data(self) -> Optional[Dict[str, Any]]:
        """
        获取最新解析的数据副本
        返回:
            最新数据字典或 None
        """
        return self.latest_data
