from ..extensions import db
from datetime import datetime

class Room(db.Model):
    __tablename__ = "rooms"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    sections = db.Column(db.Integer)

    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    event_date = db.Column(db.Date)
    deadline = db.Column(db.DateTime)

    matching_method = db.Column(db.String(50), default="default")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    owner = db.relationship("User", backref="owned_rooms")
