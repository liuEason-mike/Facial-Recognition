from app.routes.ws.common import _parse_ws_message, _json_dumps
from app.routes.ws.video import process_raw_ws_request as process_video
from app.routes.ws.audio import process_raw_ws_request as process_audio
from app.routes.ws.audio import close_raw_ws_request as close_audio
from app.utils.responses import ws_error
from app.constants.codes import Code


def register_ws_routes(app, sock):
    @sock.route('/ws/face')
    def ws_face(ws):
        while True:
            try:
                raw = ws.receive()
                if raw is None:
                    break
                payload = _parse_ws_message(raw)
                if payload is None:
                    ws.send(_json_dumps(ws_error(Code.INVALID_PARAM, "invalid_json")))
                    continue
                with app.app_context():
                    resp = process_video(payload)
                ws.send(_json_dumps(resp))
            except Exception:
                break

    @sock.route('/ws/asr')
    def ws_asr(ws):
        try:
            while True:
                try:
                    raw = ws.receive()
                    if raw is None:
                        break
                    payload = _parse_ws_message(raw)
                    if payload is None:
                        ws.send(_json_dumps(ws_error(Code.INVALID_PARAM, "invalid_json")))
                        continue
                    with app.app_context():
                        resp = process_audio(payload, ws)
                    if resp is not None:
                        ws.send(_json_dumps(resp))
                except Exception as e:
                    print(f"ASR路由异常: {e}")
                    break
        finally:
            close_audio(ws)
