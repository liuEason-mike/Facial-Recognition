from datetime import datetime
from app.extensions import db


class AudioRecord(db.Model):
    __tablename__ = "audio_records"
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    suspect_id = db.Column(db.String(64), index=True)
    text = db.Column(db.Text)
    create_time = db.Column(db.DateTime, default=datetime.now)
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
