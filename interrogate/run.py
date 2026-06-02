import os
import warnings
from flask import abort, send_from_directory
from app import create_app
from flask_sock import Sock
from app.routes.ws.register import register_ws_routes
from werkzeug.security import safe_join
# 关闭警告
warnings.filterwarnings("ignore")
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

# ======================
# Flask + WebSocket 同端口
# ======================
app = create_app()
sock = Sock(app)
app.debug = False

# ======================
# 前端静态页面
# ======================
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_INTERROGATE_DIST = os.path.join(ROOT_DIR, "html-interrogate", "dist")
LEGACY_FRONTEND_FOLDER = os.path.join(ROOT_DIR, "static")


def get_frontend_folder():
    """优先托管 html-interrogate 构建产物，未构建时回退到旧 static。"""
    configured_folder = os.environ.get("FRONTEND_DIST_DIR")
    candidates = [
        os.path.abspath(configured_folder) if configured_folder else "",
        HTML_INTERROGATE_DIST,
        LEGACY_FRONTEND_FOLDER,
    ]

    for folder in candidates:
        if folder and os.path.isfile(os.path.join(folder, "index.html")):
            return folder

    return HTML_INTERROGATE_DIST

@app.route('/')
def index():
    return send_from_directory(get_frontend_folder(), 'index.html')

@app.route('/<path:path>')
def static_proxy(path):
    if path.startswith(("api/", "ws/")):
        abort(404)

    frontend_folder = get_frontend_folder()
    static_file = safe_join(frontend_folder, path)
    if static_file and os.path.isfile(static_file):
        return send_from_directory(frontend_folder, path)

    if os.path.splitext(path)[1]:
        abort(404)

    return send_from_directory(frontend_folder, 'index.html')

# ======================
# WebSocket 路由（同端口）
# ======================

register_ws_routes(app, sock)
# ======================
# 启动（单端口 5000）
# ======================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)
