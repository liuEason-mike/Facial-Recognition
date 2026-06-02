# -*- coding: utf-8 -*-
"""
孤立森林多域异常检测
- 每个 person_id 训练 5 个独立模型：emotion、heart_rate、head_pose、eye_gaze、au_intensity
- 训练数据取自输入 JSON 的 records 前 N 分钟；模型以 pickle(.pkl) 按需加载
- 单帧推理返回 5 个域的 {score, is_anomaly}，其中 score = IsolationForest.decision_function，越低越异常；is_anomaly 由 predict == -1 判定

依赖
- numpy
- scikit-learn
"""
import os
import json
import pickle
from threading import Lock
from typing import List, Dict, Any, Optional

import numpy as np
from sklearn.ensemble import IsolationForest



class FeatureExtractor:
    """
    将单帧 JSON 记录拆分为 5 个特征域：
    - emotion_scores: 7 维（angry, disgust, fear, happy, sad, surprise, neutral）
    - heart_rate: 1 维
    - head_pose: 3 维（pitch, yaw, roll）
    - eye_gaze: 4 维（左/右眼 水平/垂直）
    - au_intensities: 若干 AU 强度（固定列表）
    """
    def __init__(self):
        self.emotions = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]
        self.au_list = [
            "inner_brow_raiser",
            "outer_brow_raiser",
            "brow_furrower",
            "upper_eyelid_raiser",
            "cheek_raiser",
            "nose_wrinkler",
            "upper_lip_raiser",
            "lip_corner_puller",
            "lip_corner_depressor",
            "jaw_raiser",
            "lip_stretcher",
            "lip_compressor",
            "lip_parter",
            "jaw_dropper",
            "eye_closure",
        ]

    def emotion_features(self, rec: Dict[str, Any]) -> np.ndarray:
        """
        提取情绪概率 7 维向量；缺失记为 NaN，后续用中位数插补
        """
        emo = rec.get("emotion_scores") or {}
        vec: List[float] = []
        for k in self.emotions:
            v = emo.get(k)
            vec.append(float(v) if v is not None else np.nan)
        return np.asarray(vec, dtype=np.float64)

    def heart_rate_features(self, rec: Dict[str, Any]) -> np.ndarray:
        """
        提取心率单维度；缺失记为 NaN
        """
        hr = rec.get("heart_rate")
        v = float(hr) if hr is not None else np.nan
        return np.asarray([v], dtype=np.float64)

    def head_pose_features(self, rec: Dict[str, Any]) -> np.ndarray:
        """
        提取头部姿态 3 维（pitch, yaw, roll）；缺失记为 NaN
        """
        hp = rec.get("head_pose") or {}
        vec = [
            float(hp.get("pitch")) if hp.get("pitch") is not None else np.nan,
            float(hp.get("yaw")) if hp.get("yaw") is not None else np.nan,
            float(hp.get("roll")) if hp.get("roll") is not None else np.nan,
        ]
        return np.asarray(vec, dtype=np.float64)

    def eye_gaze_features(self, rec: Dict[str, Any]) -> np.ndarray:
        """
        提取双眼视线 4 维（左/右眼水平/垂直）；缺失记为 NaN
        """
        le = rec.get("left_eye_gaze") or {}
        re = rec.get("right_eye_gaze") or {}
        vec = [
            float(le.get("horizontal")) if le.get("horizontal") is not None else np.nan,
            float(le.get("vertical")) if le.get("vertical") is not None else np.nan,
            float(re.get("horizontal")) if re.get("horizontal") is not None else np.nan,
            float(re.get("vertical")) if re.get("vertical") is not None else np.nan,
        ]
        return np.asarray(vec, dtype=np.float64)

    def au_features(self, rec: Dict[str, Any]) -> np.ndarray:
        """
        提取 AU 强度，固定列表；缺失记为 NaN
        """
        au = rec.get("au_intensities") or {}
        vec: List[float] = []
        for k in self.au_list:
            v = au.get(k)
            vec.append(float(v) if v is not None else np.nan)
        return np.asarray(vec, dtype=np.float64)

    def impute(self, X: np.ndarray) -> np.ndarray:
        """
        列中位数插补，将 NaN 替换为每列中位数；最终将仍可能存在的 NaN 转为 0
        """
        m = np.nanmedian(X, axis=0)
        inds = np.where(np.isnan(X))
        X[inds] = np.take(m, inds[1])
        X = np.nan_to_num(X, nan=0.0)
        return X


class IsolationForestDetector:
    """
    负责 5 个域的孤立森林模型训练与推理：
    - 训练：从 JSON records 前 N 分钟抽取样本，按域训练并保存 pkl
    - 推理：按需加载各域模型，对单帧返回每域 {score, is_anomaly}
    """
    def __init__(self, model_dir: str):
        self.model_dir = model_dir
        os.makedirs(self.model_dir, exist_ok=True)
        self.fe = FeatureExtractor()
        self.domains = ["emotion", "heart_rate", "head_pose", "eye_gaze", "au_intensity"]
        self._model_cache: Dict[str, Any] = {}
        self._cache_lock = Lock()

    def _model_path(self, person_id: str, domain: str) -> str:
        """
        返回模型文件路径：{models}/{person_id}__{domain}.pkl
        """
        safe_id = str(person_id).replace("/", "_")
        return os.path.join(self.model_dir, f"{safe_id}__{domain}.pkl")

    def _cache_key(self, person_id: str, domain: str) -> str:
        """
        生成内存模型缓存 key，和模型文件命名保持一致。
        """
        safe_id = str(person_id).replace("/", "_")
        return f"{safe_id}__{domain}"

    def _remember_model(self, person_id: str, domain: str, clf: Any) -> None:
        """
        训练或首次加载后缓存模型，避免异常评分阶段每帧重复反序列化 pkl。
        """
        with self._cache_lock:
            self._model_cache[self._cache_key(person_id, domain)] = clf

    def _train_domain(self, rows: List[Dict[str, Any]], domain: str) -> Optional[IsolationForest]:
        """
        针对指定域训练 IsolationForest；样本不足（<2 行）返回 None
        """
        if IsolationForest is None:
            raise ImportError("scikit-learn 未安装")
        if domain == "emotion":
            X = np.vstack([self.fe.emotion_features(r) for r in rows]) if rows else np.empty((0, 0))
        elif domain == "heart_rate":
            X = np.vstack([self.fe.heart_rate_features(r) for r in rows]) if rows else np.empty((0, 0))
        elif domain == "head_pose":
            X = np.vstack([self.fe.head_pose_features(r) for r in rows]) if rows else np.empty((0, 0))
        elif domain == "eye_gaze":
            X = np.vstack([self.fe.eye_gaze_features(r) for r in rows]) if rows else np.empty((0, 0))
        elif domain == "au_intensity":
            X = np.vstack([self.fe.au_features(r) for r in rows]) if rows else np.empty((0, 0))
        else:
            return None
        if X.size == 0 or X.shape[0] < 2:
            return None
        X = self.fe.impute(X)
        # contamination 越小 → 阈值越靠左 → 异常越少 → 取值范围是0-0.5
        clf = IsolationForest(n_estimators=300, max_samples="auto", contamination=0.01, random_state=42)
        clf.fit(X)
        return clf

    def train_baseline(self, person_id: str, json_path: str, minutes: float = 5.0) -> Dict[str, str]:
        """
        从 JSON 的 records 前 N 分钟作为基线训练 5 个域的模型
        返回：{domain: model_path} 已保存模型的映射
        """
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        records = data.get("records") or []
        cutoff = minutes * 60.0
        base_rows = [r for r in records if float(r.get("time_sec", 0.0)) <= cutoff] or records
        saved: Dict[str, str] = {}
        for d in self.domains:
            clf = self._train_domain(base_rows, d)
            if clf is None:
                continue
            mp = self._model_path(person_id, d)
            with open(mp, "wb") as f:
                pickle.dump(clf, f)
            self._remember_model(person_id, d, clf)
            saved[d] = mp
        return saved

    def train_baseline_from_records(self, person_id: str, records: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        从内存 records 训练并保存 5 个域的模型（在线/WS 场景使用）
        参数:
          - person_id: 模型标识，决定 pkl 文件命名前缀
          - records: 单帧记录列表（每条为 dict，字段结构与 score_record 输入一致）
        返回:
          - {domain: model_path} 已保存模型的映射
        """
        saved: Dict[str, str] = {}
        for d in self.domains:
            clf = self._train_domain(records, d)
            if clf is None:
                continue
            mp = self._model_path(person_id, d)
            with open(mp, "wb") as f:
                pickle.dump(clf, f)
            self._remember_model(person_id, d, clf)
            saved[d] = mp
        return saved

    def load_model(self, person_id: str, domain: str):
        """
        加载指定域模型；优先读内存缓存，不存在则从 pkl 读取并缓存。
        """
        cache_key = self._cache_key(person_id, domain)
        with self._cache_lock:
            cached = self._model_cache.get(cache_key)
        if cached is not None:
            return cached

        mp = self._model_path(person_id, domain)
        if not os.path.exists(mp):
            return None
        with open(mp, "rb") as f:
            clf = pickle.load(f)
        self._remember_model(person_id, domain, clf)
        return clf

    def release_cached_models(self, person_id: str) -> int:
        """
        释放单个嫌疑人的 5 个域模型缓存；test_status=2 结束审讯时调用。
        """
        safe_id = str(person_id).replace("/", "_")
        prefix = f"{safe_id}__"
        with self._cache_lock:
            keys = [key for key in self._model_cache if key.startswith(prefix)]
            for key in keys:
                self._model_cache.pop(key, None)
        return len(keys)

    def _score_vec(self, clf, x: np.ndarray) -> Dict[str, Any]:
        """
        对单条向量计算 score 与 is_anomaly；模型不存在时返回空结果
        """
        if clf is None:
            return {"score": None, "is_anomaly": None}
        x = x.reshape(1, -1)
        x = self.fe.impute(x)
        s = float(clf.decision_function(x)[0])
        p = int(clf.predict(x)[0])
        return {"score": s, "is_anomaly": bool(p == -1)}

    def score_record(self, person_id: str, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        对单帧 JSON 记录进行多域异常评分
        返回结构：
        {
          "frame": int,
          "time_sec": float,
          "emotion": {"score": float|None, "is_anomaly": bool|None},
          "heart_rate": {...},
          "head_pose": {...},
          "eye_gaze": {...},
          "au_intensity": {...}
        }
        """
        emo_clf = self.load_model(person_id, "emotion")
        hr_clf = self.load_model(person_id, "heart_rate")
        hp_clf = self.load_model(person_id, "head_pose")
        eg_clf = self.load_model(person_id, "eye_gaze")
        au_clf = self.load_model(person_id, "au_intensity")
        out = {
            "frame": record.get("frame"),
            "time_sec": record.get("time_sec"),
            "emotion": self._score_vec(emo_clf, self.fe.emotion_features(record)),
            "heart_rate": self._score_vec(hr_clf, self.fe.heart_rate_features(record)),
            "head_pose": self._score_vec(hp_clf, self.fe.head_pose_features(record)),
            "eye_gaze": self._score_vec(eg_clf, self.fe.eye_gaze_features(record)),
            "au_intensity": self._score_vec(au_clf, self.fe.au_features(record)),
        }
        return out


def default_model_dir() -> str:
    """
    返回默认的模型目录路径：位于当前文件旁的 models 目录
    """
    base = os.path.dirname(__file__)
    return os.path.join(base, "models")


def train_models_from_json(person_id: str, json_path: str, minutes: float = 5.0) -> Dict[str, str]:
    """
    便捷入口：训练并保存 5 个域的模型
    """
    det = IsolationForestDetector(model_dir=default_model_dir())
    return det.train_baseline(person_id, json_path, minutes)
