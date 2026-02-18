from ..extensions import db

class RoomCondition(db.Model):
    __tablename__ = "room_conditions"

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"), nullable=False)

    # 質問文
    label = db.Column(db.String(100), nullable=False)

    # text / select / bool / number
    input_type = db.Column(db.String(20), nullable=False)

    # select用（JSON文字列で保存）
    options = db.Column(db.Text)

    required = db.Column(db.Boolean, default=True)

    room = db.relationship("Room", backref="conditions")
