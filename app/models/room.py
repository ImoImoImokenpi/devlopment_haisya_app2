from ..extensions import db
from datetime import datetime

class Room(db.Model):
    __tablename__ = "rooms"

    id = db.Column(db.Integer, primary_key=True)
    # ルーム名（例：「〇〇合宿の配車」など）
    name = db.Column(db.String(200), nullable=False)
    # ルームの備考・説明
    description = db.Column(db.Text)
    # 選択された「部数」（もし配車に関係なければ削除可）
    sections = db.Column(db.Integer, default=1)

    # どの「イベント」に紐づいているか
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    # 誰がこのルーム（車割り）の管理者か
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # 募集締切（これ以降は参加・変更不可にする用）
    deadline = db.Column(db.DateTime)
    # マッチングアルゴリズムの指定（デフォルト：default）
    matching_method = db.Column(db.String(50), default="default")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # リレーションシップ
    # event.rooms でイベントに紐づく全ルームを取得可能に
    event = db.relationship("Event", backref=db.backref("rooms", lazy=True))
    # creator.rooms でユーザーが作った全ルームを取得可能に
    creator = db.relationship("User", backref=db.backref("rooms", lazy=True))

    def __repr__(self):
        return f'<Room {self.name}>'