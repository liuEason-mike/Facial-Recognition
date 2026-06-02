"""
审讯实时情绪数据仓储（Repository）
- 提供 EmotionRealTime 表的基础 CRUD
- 方法支持传入外部 session，便于单元测试与事务控制
"""
from typing import Optional, List, Dict, Any
from app.extensions import db
from app.models.emotion_real_time import EmotionRealTime


class EmotionRealTimeRepository:
    """
    EmotionRealTime 仓储
    - create: 新增记录
    - list_by_suspect_id: 按嫌疑人编号查询最近 N 条
    - get_latest: 查询最新一条
    """
    def create(self, payload: Dict[str, Any], session=None) -> EmotionRealTime:
        """
        新增实时情绪记录
        参数:
          - payload: 与 EmotionRealTime 模型字段一致的字典
          - session: 可选 SQLAlchemy 会话（默认使用全局 db.session）
        返回:
          - EmotionRealTime 实例（已持久化）
        """
        
        s = session or db.session
        obj = EmotionRealTime(**payload)
        # print(obj)
        # print(payload)
        # print("添加数据")
        s.add(obj)
        s.commit()
        s.refresh(obj)
        return obj

    def list_by_suspect_id(self, suspect_id: str, limit: int = 5000, session=None) -> List[EmotionRealTime]:
        """
        查询某嫌疑人的最近 N 条记录（按 time_sec 升序，便于时序分析）
        """
        s = session or db.session
        q = (
            s.query(EmotionRealTime)
            .filter(EmotionRealTime.suspect_id == str(suspect_id))
            .order_by(EmotionRealTime.time_sec.asc())
            .limit(limit)
        )
        return q.all()

    