from datetime import datetime
from app.extensions import db


class EmotionAnomaly(db.Model):
    __tablename__ = "emotion_anomaly"
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    suspect_id = db.Column(db.String(50), nullable=False, index=True)
    frame = db.Column(db.Integer)
    time_sec = db.Column(db.BigInteger)
    emotion_score = db.Column(db.Float)
    emotion_is_anomaly = db.Column(db.Boolean)
    heart_rate_score = db.Column(db.Float)
    heart_rate_is_anomaly = db.Column(db.Boolean)
    head_pose_score = db.Column(db.Float)
    head_pose_is_anomaly = db.Column(db.Boolean)
    eye_gaze_score = db.Column(db.Float)
    eye_gaze_is_anomaly = db.Column(db.Boolean)
    au_intensity_score = db.Column(db.Float)
    au_intensity_is_anomaly = db.Column(db.Boolean)
    model_dir = db.Column(db.String(255))
    create_time = db.Column(db.DateTime, default=datetime.now)
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
