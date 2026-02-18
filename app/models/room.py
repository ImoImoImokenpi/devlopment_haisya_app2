from ..extensions import db
from datetime import datetime

class Room(db.Model):
    __tablename__ = "rooms"

    id = db.Column(db.Integer, primary_key=True)

    # 基本情報
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)

    # イベント情報
    event_date = db.Column(db.Date, nullable=False)
    deadline = db.Column(db.DateTime, nullable=False)

    # ファイル添付
    file_path = db.Column(db.String(200))

    # 管理者
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # 作成時刻
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # リレーション
    owner = db.relationship("User", backref="owned_rooms")
    schedules = db.relationship("EventSchedule", backref="room", cascade="all, delete-orphan")
    entries = db.relationship("Entry", backref="room", cascade="all, delete-orphan")
