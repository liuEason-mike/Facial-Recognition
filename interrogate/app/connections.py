"""
关系型数据库连接（MySQL）
- get_sql_db：返回 Flask‑SQLAlchemy 引擎实例
- 仅保留 MySQL 场景所需的接口，移除图数据库相关实现
"""
from .extensions import db


def get_sql_db():
    """
    获取关系型数据库 ORM 引擎（MySQL）
    返回：
      - Flask‑SQLAlchemy 实例（app.extensions.db）
    用法：
      >>> from app.connections import get_sql_db
      >>> s = get_sql_db().session
    """
    return db
