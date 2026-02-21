from ..extensions import db
from datetime import datetime

class RoomAttachment(db.Model):
    __tablename__ = "room_attachments"

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"))
    filename = db.Column(db.String(200))
    filepath = db.Column(db.String(300))

    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
