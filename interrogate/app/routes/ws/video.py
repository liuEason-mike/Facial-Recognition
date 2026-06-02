"""
WebSocket 路由：面部分析实时帧（/ws/face）
- 接收前端发送的 JSON：{ id: 嫌疑人编号, image: Base64,test_status:0开始检测，1基础检测结束 2检测完成}
- 调用服务层生成 EmotionFrame，入库并将结果实时返回给前端
"""
import traceback
from typing import Any, Dict

from app.constants.codes import Code
from app.service.video.realtime_features import process_frame_ws_payload
from app.utils.responses import ws_error


def process_raw_ws_request(data: Any) -> Dict[str, Any]:
    """
    原生 WebSocket 消息处理入口（请求 JSON -> 响应 JSON）
    参数:
      - data: 已反序列化的 JSON 对象
    返回:
      - 标准 EmotionFrame 或标准错误对象
    """
    try:
        print("✅ WebSocket 开始处理请求")
        
        # 从前端传的 {id, image} 里取出 image(base64)
        image_b64 = data.get("image", "")
        suspect_id = data.get("id", "unknown")
        test_status = data.get("test_status", 0)
        client_seq = data.get("client_seq")

        # 传给服务层处理
        result = process_frame_ws_payload(image_b64, suspect_id, test_status)
        if client_seq is not None and isinstance(result, dict):
            result["client_seq"] = client_seq
        result["id"] = suspect_id
        return result
    except ValueError as e:
        return ws_error(Code.INVALID_PARAM, str(e))
    except Exception as e:
        traceback.print_exc()
        return ws_error(Code.INTERNAL_ERROR, "internal_error")
