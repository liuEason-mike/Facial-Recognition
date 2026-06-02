"""
数据库运行时开关。
"""
from flask import current_app, has_app_context


def is_database_enabled() -> bool:
    """
    返回当前 Flask app 是否允许数据库初始化和写入。
    没有 app context 时默认视为关闭，避免后台回调误触发 db.session。
    """
    return has_app_context() and bool(current_app.config.get("DATABASE_ENABLED"))
