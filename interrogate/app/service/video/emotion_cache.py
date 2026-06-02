# -*- coding: utf-8 -*-
"""
情绪识别缓存与兜底工具
"""
from typing import Dict, Union


EMOTION_SCORE_KEYS = ("angry", "disgust", "fear", "happy", "sad", "surprise", "neutral")


def zero_emotion_scores() -> Dict[str, int]:
    """
    /ws/face 情绪识别不可用时的固定兜底结构。
    """
    return {key: 0 for key in EMOTION_SCORE_KEYS}


class EmotionInferenceGate:
    """
    控制重型情绪模型推理频率：已有缓存时只按间隔重新推理，其余帧复用上次分布。
    """

    def __init__(self, interval: Union[int, str, None] = 1):
        try:
            parsed = int(interval or 1)
        except (TypeError, ValueError):
            parsed = 1
        self.interval = max(1, parsed)
        self._frame_count = 0

    def should_infer(self, has_cached_scores: bool) -> bool:
        self._frame_count += 1
        if not has_cached_scores:
            return True
        return self.interval <= 1 or self._frame_count % self.interval == 0
