from ..extensions import db
from datetime import datetime

class Entry(db.Model):
    __tablename__ = "entries"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"))
    has_car = db.Column(db.Boolean, default=False)
    capacity = db.Column(db.Integer)
    genre = db.Column(db.String)
    prefer_with = db.Column(db.Integer)
    avoid_with = db.Column(db.Integer)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User")
    schedule_id = db.Column(db.Integer, db.ForeignKey("event_schedule.id"))

