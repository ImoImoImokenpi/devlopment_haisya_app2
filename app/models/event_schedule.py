from ..extensions import db

class EventSchedule(db.Model):
    __tablename__ = "event_schedules"

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"), nullable=False)
    label = db.Column(db.String(100), nullable=False)  # 例: 1部-3番目
    order = db.Column(db.Integer, nullable=False)
