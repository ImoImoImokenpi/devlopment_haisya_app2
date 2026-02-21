from ..extensions import db
from datetime import datetime

class Answer(db.Model):
    __tablename__ = "answers"

    id = db.Column(db.Integer, primary_key=True)

    entry_id = db.Column(db.Integer, db.ForeignKey("entries.id"))
    question_id = db.Column(db.Integer, db.ForeignKey("question_master.id"))

    text_value = db.Column(db.String(300))
    number_value = db.Column(db.Integer)
    bool_value = db.Column(db.Boolean)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
