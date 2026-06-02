"""
WebSocket 路由：音频转文字（/ws/asr）
"""
import traceback
from typing import Any, Dict
from flask import current_app
from app.constants.codes import Code
from app.utils.responses import ws_error
from app.service.audio.qwen_asr import _asr_client, normalize_dashscope_asr_segments
from app.repository.audio_records import AudioRecordsRepository
from app.routes.ws.common import _json_dumps
from app.utils.database import is_database_enabled
from neo4j import GraphDatabase

# 图数据库配置
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "neo4jpassword"
# 初始化 Neo4j 驱动
_neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def insert_to_neo4j(suspect_id: str, text: str):
    try:
        with _neo4j_driver.session() as session:
            # 人物节点 + 文本节点 + 关系
            query = """
            MERGE (p:Suspect {id: $suspect_id})  // 嫌疑人（唯一）
            CREATE (t:AudioText {content: $text, create_time: datetime()})  // 本次30秒文本
            MERGE (p)-[:HAS_RECORD]->(t)  // 关系：该人物产生这段记录
            """
            session.run(query, suspect_id=suspect_id, text=text)
    except Exception as e:
        print(f"Neo4j 插入失败: {e}")


_repo = AudioRecordsRepository()

_active_ws = None
_flask_app = None  # 👈 全局保存 APP
_active_suspect_id = "0"


def _persist_audio_text(suspect_id: str, text: str) -> None:
    """
    数据库开关关闭时只推送 ASR 结果，不触发 SQLAlchemy session。
    """
    if not text:
        return

    def _create_record():
        if not is_database_enabled():
            return
        _repo.create({
            "suspect_id": str(suspect_id),
            "text": text,
        })

    if _flask_app is not None:
        with _flask_app.app_context():
            _create_record()
        return

    _create_record()


def _handle_asr_message(resp: Dict[str, Any]):
    if not _active_ws:
        return
        
    try:
        suspect_id = _active_suspect_id or "0"
        segments = normalize_dashscope_asr_segments(resp)
        if segments:
            for segment in segments:
                text = segment.get("text", "")
                if not text:
                    continue
                try:
                    _persist_audio_text(str(suspect_id), text)
                except Exception as db_err:
                    print(f"音频入库失败: {str(db_err)}")
            # WebSocket 契约：DashScope 原始事件归一化为 [{start,end,text}]，前端直接读取 text 展示。
            _active_ws.send(_json_dumps(segments))
            return

        if isinstance(resp, dict) and resp.get("type") == "segment_result":
            text = resp.get("data", {}).get("text", "")
            if text:
                try:
                    _persist_audio_text(str(suspect_id), text)
                except Exception as db_err:
                    print(f"音频入库失败: {str(db_err)}")
            
            resp.setdefault("suspect_id", str(suspect_id))
            _active_ws.send(_json_dumps(resp))
            return
            
        if isinstance(resp, dict) and resp.get("header", {}).get("event") == "task-failed":
            message = resp.get("header", {}).get("error_message") or "asr_task_failed"
            _active_ws.send(_json_dumps(ws_error(Code.INTERNAL_ERROR, message)))
            return

        if isinstance(resp, dict):
            return
            
    except Exception as e:
        print(f"处理 ASR 响应异常: {e}")

_asr_client.on_message = _handle_asr_message

def close_raw_ws_request(ws=None) -> None:
    """前端 ASR WebSocket 断开时同步释放上游 DashScope 长连接。"""
    global _active_ws, _active_suspect_id
    if ws is not None and ws is not _active_ws:
        return
    _asr_client.close()
    _active_ws = None
    _active_suspect_id = "0"


def process_raw_ws_request(data: Any, ws=None) -> Dict[str, Any]:
    global _active_ws, _flask_app, _active_suspect_id
    if ws:
        _active_ws = ws
    if _flask_app is None:
        _flask_app = current_app._get_current_object()

    try:
        audio_b64 = None
        suspect_id = "0"
        seq = None
        end_packet = False
        if isinstance(data, dict):
            audio_b64 = data.get("audio")
            seq = data.get("seq")
            suspect_id = data.get("suspect_id", "0")
            end_packet = bool(data.get("end"))
            _active_suspect_id = str(suspect_id or "0")

        if not end_packet and not audio_b64:
            return ws_error(Code.INVALID_PARAM, "audio_required")

        if not _asr_client.send(audio_b64 or "", str(suspect_id or "0"), seq, end=end_packet):
            return ws_error(Code.INTERNAL_ERROR, "asr_forward_failed")
        return None
    except ValueError as e:
        return ws_error(Code.INVALID_PARAM, str(e))
    except Exception:
        traceback.print_exc()
        return ws_error(Code.INTERNAL_ERROR, "internal_error")
