# -*- coding: utf-8 -*-
"""
ASR 审讯关键词提炼服务。
"""
import json
import logging
import os
import re
import urllib.request
from typing import Any, Dict, List, Optional


KEYWORD_CATEGORIES = ("人物", "时间", "地点", "行为", "事件")
FILLER_WORDS = {"嗯", "啊", "哦", "呃", "这个", "那个", "然后", "就是", "没有", "不知道"}
MAX_KEYWORDS = 100
DASHSCOPE_CHAT_COMPLETIONS_ENDPOINT = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
DEFAULT_KEYWORD_LLM_MODEL = "qwen3-max"
LOGGER = logging.getLogger(__name__)


def build_keyword_prompt(text: str, context: str = "") -> str:
    """
    构建审讯场景关键词提炼提示词，要求模型只返回稳定 JSON，便于后端解析。
    """
    # context_part = f"\n可参考的上下文：{context.strip()}" if context and context.strip() else ""
    # return (
    #     "你是审讯文本分析助手。请从输入的 ASR 中文转写中抽取审讯场景关键词，"
    #     "不要编造输入文本中不存在的信息。\n"
    #     "分类只能使用：人物、时间、地点、行为、事件。\n"
    #     "过滤语气词、无意义短句、重复表达，关键词应是有审讯价值的短语。\n"
    #     f"最多返回 {MAX_KEYWORDS} 个关键词。\n"
    #     "只输出 JSON 数组，不要输出 Markdown 或解释文字。\n"
    #     "数组元素格式："
    #     "{\"text\":\"前往上海\",\"category\":\"地点\",\"confidence\":0.91,"
    #     "\"source\":\"凌晨三四点前往上海\"}。\n"
    #     f"{context_part}\n"
    #     f"输入文本：{text.strip()}"
    # )context_part = f"\n可参考的上下文：{context.strip()}" if context and context.strip() else ""
    context_part = f"\n可参考的上下文：{context.strip()}" if context and context.strip() else ""
    return (
    "你是审讯文本分析助手。请严格从输入的 ASR 中文转写中提取审讯场景关键词，"
    "不要编造输入文本中不存在的信息。\n"
    "关键词分类限：人物、时间、地点、行为、事件。\n"
    "重点关注时间、地点、行为/动作、人物和关键事件，忽略无意义短语、语气词、重复表达，"
    "确保所有行为/动作关键词真实存在于输入文本中。\n"
    "如果存在数字转为阿拉伯数字提取出来\n"
    f"最多返回 {MAX_KEYWORDS} 个关键词。\n"
    "仅输出 JSON 数组，不要输出 Markdown 或任何解释文字。\n"
    "数组元素格式示例："
    "{\"text\":\"前往上海\",\"category\":\"地点\",\"confidence\":0.91,"
    "\"source\":\"凌晨三四点前往上海\"}。\n"
    f"{context_part}\n"
    f"输入文本：{text.strip()}"
    )      


def _strip_json_fence(raw: str) -> str:
    content = raw.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content, flags=re.IGNORECASE)
        content = re.sub(r"\s*```$", "", content)
    return content.strip()


def _coerce_json_payload(raw: str) -> Any:
    content = _strip_json_fence(raw)
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"(\[[\s\S]*\]|\{[\s\S]*\})", content)
        if not match:
            raise
        return json.loads(match.group(1))


def _normalize_category(category: Any) -> Optional[str]:
    if not isinstance(category, str):
        return None
    category = category.strip()
    return category if category in KEYWORD_CATEGORIES else None


def _normalize_keyword_item(item: Any) -> Optional[Dict[str, Any]]:
    if isinstance(item, str):
        text = item.strip()
        category = "事件"
        confidence = 1.0
        source = ""
    elif isinstance(item, dict):
        text = str(item.get("text") or item.get("word") or "").strip()
        category = _normalize_category(item.get("category")) or ""
        confidence = item.get("confidence", 1.0)
        source = str(item.get("source") or "").strip()
    else:
        return None

    if not text or text in FILLER_WORDS or len(text) < 2:
        return None

    if not category:
        category = "事件"

    try:
        confidence_value = float(confidence)
    except (TypeError, ValueError):
        confidence_value = 1.0

    return {
        "text": text,
        "category": category,
        "confidence": max(0.0, min(1.0, confidence_value)),
        "source": source,
        "count": 1,
    }


def _dedupe_keywords(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    deduped: Dict[str, Dict[str, Any]] = {}
    for item in items:
        key = f"{item['category']}::{item['text']}"
        if key in deduped:
            deduped[key]["count"] += item.get("count", 1)
            deduped[key]["confidence"] = max(deduped[key]["confidence"], item["confidence"])
            if not deduped[key]["source"] and item.get("source"):
                deduped[key]["source"] = item["source"]
            continue
        deduped[key] = dict(item)
    return list(deduped.values())[:MAX_KEYWORDS]


def parse_keyword_response(raw: str) -> List[Dict[str, Any]]:
    """
    解析大模型返回内容，兼容 JSON 数组、包含 keywords 字段的对象和 Markdown fence。
    """
    payload = _coerce_json_payload(raw)
    if isinstance(payload, dict):
        raw_items = payload.get("keywords") or payload.get("data") or []
    else:
        raw_items = payload

    if not isinstance(raw_items, list):
        return []

    normalized = [_normalize_keyword_item(item) for item in raw_items]
    return _dedupe_keywords([item for item in normalized if item is not None])


def fallback_extract_keywords(text: str) -> List[Dict[str, Any]]:
    """
    大模型未配置或调用失败时的审讯关键词规则兜底，只使用输入文本中的原文片段。
    """
    patterns = [
        ("人物", r"[\u4e00-\u9fa5]{1,3}某|[\u4e00-\u9fa5]{2,4}(?:先生|女士|经理|主任|老板)"),
        ("时间", r"(?:凌晨|早上|上午|中午|下午|晚上|夜里)?[一二三四五六七八九十\d]{1,2}[点时](?:半|多|左右)?|[一二三四五六七八九十\d]{1,2}月[一二三四五六七八九十\d]{1,2}[日号]"),
        ("地点", r"(?:北京|上海|广州|深圳|杭州|南京|海州区|物流园|仓库|公司|银行|酒店|车站|机场)"),
        ("行为", r"(?:前往|到达|离开|签署|转账|收款|付款|联系|见面|进入|拿走|交付)[\u4e00-\u9fa5A-Za-z0-9]{0,8}"),
        ("事件", r"(?:仓储合同|预付款转出|预付款|合同诈骗|虚假仓储|资金去向|门禁记录|转账流水)"),
    ]
    items: List[Dict[str, Any]] = []
    for category, pattern in patterns:
        for match in re.finditer(pattern, text):
            keyword = match.group(0).strip("，。！？、；：,.!?;: ")
            item = _normalize_keyword_item({
                "text": keyword,
                "category": category,
                "confidence": 0.6,
                "source": keyword,
            })
            if item:
                items.append(item)
    return _dedupe_keywords(items)


class KeywordModelClient:
    """
    调用环境变量配置的大模型接口，默认按 OpenAI-compatible chat completions 格式发送。
    """

    def __init__(self):
        # 默认接入 DashScope OpenAI-compatible Chat Completions；密钥仍只从环境变量读取。
        self.endpoint = (
            os.getenv("KEYWORD_LLM_ENDPOINT")
            or os.getenv("BAIYING_LLM_ENDPOINT")
            or os.getenv("DASHSCOPE_LLM_ENDPOINT")
            or DASHSCOPE_CHAT_COMPLETIONS_ENDPOINT
        )
        self.api_key = (
            os.getenv("KEYWORD_LLM_API_KEY")
            or os.getenv("BAIYING_LLM_API_KEY")
            or os.getenv("DASHSCOPE_API_KEY")
            or ""
        )
        self.model = (
            os.getenv("KEYWORD_LLM_MODEL")
            or os.getenv("BAIYING_LLM_MODEL")
            or os.getenv("DASHSCOPE_LLM_MODEL")
            or DEFAULT_KEYWORD_LLM_MODEL
        )
        self.timeout = float(os.getenv("KEYWORD_LLM_TIMEOUT", "12"))

    @property
    def configured(self) -> bool:
        return bool(self.endpoint and self.api_key)

    def complete(self, prompt: str) -> str:
        payload: Dict[str, Any] = {
            "messages": [
                {"role": "system", "content": "你只输出 JSON。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
        }
        if self.model:
            payload["model"] = self.model

        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            body = json.loads(response.read().decode("utf-8"))

        choices = body.get("choices")
        if isinstance(choices, list) and choices:
            message = choices[0].get("message") or {}
            content = message.get("content")
            if isinstance(content, str):
                return content
        content = body.get("content") or body.get("text")
        if isinstance(content, str):
            return content
        return json.dumps(body, ensure_ascii=False)


class KeywordExtractionService:
    """
    关键词提炼门面：优先调用大模型，失败时降级到规则兜底。
    """

    def __init__(self, model_client: Optional[KeywordModelClient] = None):
        self.model_client = model_client or KeywordModelClient()

    def extract(
        self,
        text: str,
        window_id: str = "",
        suspect_id: str = "",
        session_id: str = "",
        context: str = "",
    ) -> Dict[str, Any]:
        prompt = build_keyword_prompt(text, context=context)
        provider = "fallback"
        keywords: List[Dict[str, Any]] = []

        if self.model_client.configured:
            try:
                raw_response = self.model_client.complete(prompt)
                keywords = parse_keyword_response(raw_response)
                provider = "llm"
            except Exception as exc:
                # 大模型属于外部依赖；任何请求、解析或响应结构异常都降级到规则兜底，避免接口返回 500。
                LOGGER.warning(
                    "ASR 关键词模型调用失败，已降级为规则兜底: %s",
                    exc.__class__.__name__,
                )
                keywords = []

        if not keywords:
            keywords = fallback_extract_keywords(text)
            provider = "fallback"

        return {
            "window_id": window_id,
            "suspect_id": suspect_id,
            "session_id": session_id,
            "provider": provider,
            "keywords": keywords,
        }
