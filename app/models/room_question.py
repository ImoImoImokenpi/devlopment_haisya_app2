from ..extensions import db

class RoomQuestion(db.Model):
    __tablename__ = "room_questions"

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"))
    question_id = db.Column(db.Integer, db.ForeignKey("question_master.id"))

    required = db.Column(db.Boolean, default=True)

    question = db.relationship("QuestionMaster")
