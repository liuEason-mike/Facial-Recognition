# -*- coding: utf-8 -*-
"""
孤立森林多域离线分析脚本
- 按 person_id 将输入 JSON 的前 N 分钟作为基线，训练 5 个独立的 IsolationForest 模型
- 遍历 records 逐帧推理，输出包含 frame、time_sec 与 5 个域 {score, is_anomaly} 的结果 JSON
"""
import os
import json
import argparse
from typing import Any, Dict, Optional, Tuple

from .iso_forest_detector import IsolationForestDetector, train_models_from_json, default_model_dir


def score_anomaly_record(person_id: str, record: Dict[str, Any], model_dir: str = None) -> Tuple[Dict[str, Any], str]:
    """
    孤立森林单帧异常检测（在线/WS 场景使用）
    参数:
      - person_id: 模型标识（通常使用 suspect_id）
      - record: 单帧特征记录（需包含 emotion_scores/heart_rate/head_pose/left_eye_gaze/right_eye_gaze/au_intensities 等字段）
      - model_dir: 模型目录；不传则使用默认目录
    返回:
      - (anomaly_data, model_dir)
      - anomaly_data 结构：{emotion/heart_rate/head_pose/eye_gaze/au_intensity: {score, is_anomaly}}
    """
    md = model_dir or default_model_dir()
    try:
        det = IsolationForestDetector(model_dir=md)
        out = det.score_record(person_id, record) or {}
        anomaly_data = {
            "emotion": out.get("emotion"),
            "heart_rate": out.get("heart_rate"),
            "head_pose": out.get("head_pose"),
            "eye_gaze": out.get("eye_gaze"),
            "au_intensity": out.get("au_intensity"),
        }
        return anomaly_data, md
    except Exception:
        anomaly_data = {
            "emotion": {"score": None, "is_anomaly": None},
            "heart_rate": {"score": None, "is_anomaly": None},
            "head_pose": {"score": None, "is_anomaly": None},
            "eye_gaze": {"score": None, "is_anomaly": None},
            "au_intensity": {"score": None, "is_anomaly": None},
        }
        return anomaly_data, md


def analyse(person_id: str, json_path: str, out_path: str = None, minutes: float = 5.0, model_dir: str = None) -> str:
    """
    参数：
      person_id: 模型标识，决定 pkl 文件命名前缀
      json_path: 含有 records 列表的输入 JSON 路径
      out_path: 输出 JSON 路径；未指定时输出到与输入同目录
      minutes: 基线训练窗口，单位：分钟；用于筛选 time_sec <= minutes*60 的记录
      model_dir: 模型保存与加载目录；未指定时使用默认 models 目录
    返回：
      实际写入的输出 JSON 路径
    """
    model_dir = model_dir or default_model_dir()
    train_models_from_json(person_id, json_path, minutes)
    det = IsolationForestDetector(model_dir=model_dir)
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    records = data.get("records") or []
    rows = []
    for rec in records:
        r = det.score_record(person_id, rec)
        rows.append(r)
    out = {
        "person_id": person_id,
        "input_json": json_path,
        "model_dir": model_dir,
        "minutes": minutes,
        "records": rows,
    }
    if out_path is None:
        jbn = os.path.basename(json_path)
        jstem = os.path.splitext(jbn)[0]
        out_path = os.path.join(os.path.dirname(json_path), f"{jstem}__iso_multi_analysis_{person_id}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    return out_path


