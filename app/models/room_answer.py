from ..extensions import db

class RoomAnswer(db.Model):
    __tablename__ = "room_answers"

    id = db.Column(db.Integer, primary_key=True)

    member_id = db.Column(db.Integer, db.ForeignKey("room_members.id"), nullable=False)
    condition_id = db.Column(db.Integer, db.ForeignKey("room_conditions.id"), nullable=False)

    value = db.Column(db.Text)

    member = db.relationship("RoomMember", backref="answers")
    condition = db.relationship("RoomCondition")
