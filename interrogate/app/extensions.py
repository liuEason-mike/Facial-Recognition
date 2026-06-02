"""
应用扩展
- db：SQLAlchemy ORM 引擎（通过 DATABASE_URL 指向 MySQL/SQLite）
- socketio：Flask‑SocketIO 实例
"""
from typing import Any

try:
    from flask_sqlalchemy import SQLAlchemy
except Exception:
    SQLAlchemy = None

try:
    from flask_socketio import SocketIO
except Exception:
    SocketIO = None


class _DBStub:
    def init_app(self, app: Any) -> None:
        return

    def create_all(self) -> None:
        return

    session = None

    def __getattr__(self, name: str):
        raise RuntimeError("缺少依赖 Flask-SQLAlchemy：请执行 pip install Flask-SQLAlchemy")


class _SocketIOStub:
    def init_app(self, app: Any, **kwargs: Any) -> None:
        return

    def on_namespace(self, namespace: Any) -> None:
        return

    def __getattr__(self, name: str):
        raise RuntimeError("缺少依赖 flask-socketio：请执行 pip install flask-socketio")

db = SQLAlchemy() if SQLAlchemy is not None else _DBStub()
socketio = SocketIO() if SocketIO is not None else _SocketIOStub()
