from ..extensions import db

class EventSchedule(db.Model):
    __tablename__ = "event_schedule"

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"), nullable=False)

    section = db.Column(db.Integer, nullable=False)   # 何部か
    order = db.Column(db.Integer, nullable=False)     # 何番目か

    rooms = db.relationship("Room", backref="schedules")

    __table_args__ = (
        db.UniqueConstraint("room_id", "section", "order", name="unique_schedule"),
    )
