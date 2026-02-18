from ..extensions import db

class Entry(db.Model):
    __tablename__ = "entries"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"), nullable=False)

    # 車
    has_car = db.Column(db.Boolean, default=False)
    capacity = db.Column(db.Integer)

    # 出番
    schedule_id = db.Column(db.Integer, db.ForeignKey("event_schedules.id"))

    # 条件
    genre = db.Column(db.String(50))
    prefer_with = db.Column(db.String(100))
    avoid_with = db.Column(db.String(100))
    start_location = db.Column(db.String(100))
