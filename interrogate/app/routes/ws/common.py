import json
from typing import Any, Dict, Optional
from app.constants.codes import Code
from app.utils.responses import ws_error

# ======================
# 工具函数全部保留，正常用
# ======================
def _parse_ws_message(raw: Any) -> Optional[Dict[str, Any]]:
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode("utf-8", errors="ignore")
    if not isinstance(raw, str):
        return None
    try:
        obj = json.loads(raw)
    except Exception:
        return None
    return obj if isinstance(obj, dict) else None


def _json_dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False)