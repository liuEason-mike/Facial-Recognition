from typing import Any, Dict, Tuple, Optional
from flask import jsonify
from app.constants.codes import Code


def ok(data: Any = None, msg: str = "ok", code: Code = Code.OK):
    return jsonify({"code": int(code), "msg": msg, "data": data})


def error(code: Code, msg: str, data: Any = None, http_status: int = 400) -> Tuple[Any, int]:
    return jsonify({"code": int(code), "msg": msg, "data": data}), http_status


def ws_ok(data: Any = None, msg: str = "ok", code: Code = Code.OK) -> Dict[str, Any]:
    return {"code": int(code), "msg": msg, "data": data}


def ws_error(code: Code, msg: str, data: Any = None) -> Dict[str, Any]:
    return {"code": int(code), "msg": msg, "data": data}

