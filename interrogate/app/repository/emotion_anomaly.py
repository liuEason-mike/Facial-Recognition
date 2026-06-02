from typing import Any, Dict, List, Optional
from app.extensions import db
from app.models.emotion_anomaly import EmotionAnomaly


class EmotionAnomalyRepository:
    """
    异常数据仓储（emotion_anomaly）
    - 负责 emotion_anomaly 表的增删查改封装
    - 默认使用 app.extensions.db.session，也支持外部注入 session（便于测试/事务控制）
    """
    def create(self, payload: Dict[str, Any], session=None) -> EmotionAnomaly:
        """
        创建一条异常记录并提交事务
        参数:
          - payload: 字段字典（需与 EmotionAnomaly 字段匹配）
          - session: 可选，外部注入 SQLAlchemy session
        返回:
          - EmotionAnomaly ORM 实例
        """
        s = session or db.session
        obj = EmotionAnomaly(**payload)
        s.add(obj)
        s.commit()
        s.refresh(obj)
        return obj

   