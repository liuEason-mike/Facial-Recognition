import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.service.video.emotion_cache import EmotionInferenceGate, zero_emotion_scores


def test_zero_emotion_scores_returns_hardcoded_ws_face_fallback_shape():
    assert zero_emotion_scores() == {
        "angry": 0,
        "disgust": 0,
        "fear": 0,
        "happy": 0,
        "sad": 0,
        "surprise": 0,
        "neutral": 0,
    }


def test_emotion_inference_gate_reuses_cached_scores_between_intervals():
    gate = EmotionInferenceGate(interval=3)

    assert gate.should_infer(has_cached_scores=False) is True
    assert gate.should_infer(has_cached_scores=True) is False
    assert gate.should_infer(has_cached_scores=True) is True
    assert gate.should_infer(has_cached_scores=True) is False
