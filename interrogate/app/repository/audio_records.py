# -*- coding: utf-8 -*-
"""
音频记录仓储（Repository）
"""
from typing import Any, Dict, List, Optional

from sqlalchemy import text as sa_text

from app.extensions import db


class AudioRecordsRepository:
    """
    audio_records 表的基础 CRUD
    - create: 新增音频记录
    """

    def create(self, payload: Dict[str, Any], session=None) -> Dict[str, Any]:
        """
        新增音频记录
        参数:
          - payload: 字段字典，支持 keys: suspect_id, text
          - session: 可选 SQLAlchemy 会话（默认使用全局 db.session）
        返回:
          - 刚插入的完整行字典
        """
        s = session or db.session
        insert_sql = sa_text("""
            INSERT INTO audio_records (suspect_id, `text`, create_time, update_time)
            VALUES (:suspect_id, :text, NOW(), NOW())
        """)
        params = {
            "suspect_id": str(payload.get("suspect_id") or ""),
            "text": payload.get("text") or "",
        }
        result = s.execute(insert_sql, params)
        s.commit()
        last_id = result.lastrowid
        # 返回插入后的完整行
        row_sql = sa_text("""
            SELECT id, suspect_id, `text`, create_time, update_time
            FROM audio_records
            WHERE id = :id
            LIMIT 1
        """)
        row = s.execute(row_sql, {"id": last_id}).mappings().first()
        return dict(row) if row else {"id": last_id, **params}
