import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Flask

from app.constants.codes import Code
from app.routes.api.asr_keywords import asr_keywords_bp
from app.service.audio.keyword_extraction import (
    KeywordExtractionService,
    KeywordModelClient,
    build_keyword_prompt,
    fallback_extract_keywords,
    parse_keyword_response,
)


def _create_app() -> Flask:
    app = Flask("test-asr-keywords")
    app.register_blueprint(asr_keywords_bp)
    return app


def test_build_keyword_prompt_constrains_interrogation_categories():
    prompt = build_keyword_prompt("周某凌晨三四点前往上海签署仓储合同。")

    assert "审讯场景" in prompt
    assert "人物" in prompt
    assert "时间" in prompt
    assert "地点" in prompt
    assert "行为" in prompt
    assert "事件" in prompt
    assert "不要编造" in prompt
    assert "JSON" in prompt


def test_parse_keyword_response_accepts_array_and_normalizes_fields():
    raw = """
    ```json
    [
      {"text": "前往上海", "category": "地点", "confidence": 0.91},
      {"word": "凌晨三四点", "category": "时间", "source": "凌晨三四点前往上海"},
      {"text": "嗯", "category": "语气词"}
    ]
    ```
    """

    keywords = parse_keyword_response(raw)

    assert keywords == [
        {
            "text": "前往上海",
            "category": "地点",
            "confidence": 0.91,
            "source": "",
            "count": 1,
        },
        {
            "text": "凌晨三四点",
            "category": "时间",
            "confidence": 1.0,
            "source": "凌晨三四点前往上海",
            "count": 1,
        },
    ]


def test_fallback_extract_keywords_covers_interrogation_categories():
    keywords = fallback_extract_keywords(
        "周某说凌晨三四点前往上海，随后签署仓储合同，并把预付款转出。"
    )
    pairs = {(item["text"], item["category"]) for item in keywords}

    assert ("周某", "人物") in pairs
    assert ("凌晨三四点", "时间") in pairs
    assert ("上海", "地点") in pairs
    assert ("签署仓储合同", "行为") in pairs
    assert ("预付款转出", "事件") in pairs


def test_keyword_model_client_defaults_to_dashscope_qwen3_max(monkeypatch):
    for key in (
        "KEYWORD_LLM_ENDPOINT",
        "KEYWORD_LLM_API_KEY",
        "KEYWORD_LLM_MODEL",
        "BAIYING_LLM_ENDPOINT",
        "BAIYING_LLM_API_KEY",
        "BAIYING_LLM_MODEL",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-dashscope-key")

    client = KeywordModelClient()

    assert client.configured
    assert client.api_key == "test-dashscope-key"
    assert client.endpoint == "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    assert client.model == "qwen3-max"


def test_keyword_extraction_falls_back_when_model_client_raises_unexpected_error():
    class BrokenModelClient:
        configured = True

        def complete(self, prompt):
            raise RuntimeError("upstream response shape changed")

    service = KeywordExtractionService(model_client=BrokenModelClient())

    result = service.extract("周某凌晨三四点前往上海，随后签署仓储合同。")

    assert result["provider"] == "fallback"
    assert any(item["text"] == "上海" for item in result["keywords"])


def test_extract_endpoint_returns_keywords(monkeypatch):
    def fake_extract(text, window_id="", suspect_id="", session_id="", context=""):
        return {
            "window_id": window_id,
            "provider": "test",
            "keywords": [
                {
                    "text": "前往上海",
                    "category": "地点",
                    "confidence": 1.0,
                    "source": text,
                    "count": 1,
                }
            ],
        }

    monkeypatch.setattr("app.routes.api.asr_keywords.keyword_extractor.extract", fake_extract)
    app = _create_app()

    with app.test_client() as client:
        response = client.post(
            "/api/asr/keywords/extract",
            json={
                "window_id": "asr-keywords-1",
                "suspect_id": "1",
                "text": "周某凌晨三四点前往上海。",
            },
        )

    body = response.get_json()
    assert response.status_code == 200
    assert body["code"] == int(Code.OK)
    assert body["data"]["window_id"] == "asr-keywords-1"
    assert body["data"]["keywords"][0]["text"] == "前往上海"


def test_extract_endpoint_rejects_empty_text():
    app = _create_app()

    with app.test_client() as client:
        response = client.post("/api/asr/keywords/extract", json={"text": "   "})

    body = response.get_json()
    assert response.status_code == 400
    assert body["code"] == int(Code.INVALID_PARAM)
    assert body["msg"] == "text_required"
