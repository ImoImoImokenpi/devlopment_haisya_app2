from ..extensions import db
from datetime import datetime

class Entry(db.Model):
    __tablename__ = "entries"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"), nullable=False)
    
    # 車の情報
    has_car = db.Column(db.Boolean, default=False)
    capacity = db.Column(db.Integer, default=0)

    # リハーサル (質問設定で ON の場合に回答)
    has_rehersal = db.Column(db.Boolean, default=False) # ← これを追加しました
    
    # 出番順（例: "1-5" などを文字列として保存するか、整数IDを保存する）
    schedule_id = db.Column(db.String(50)) 
    
    # 配慮事項（名前を直接入力する想定のため String に修正）
    prefer_with = db.Column(db.String(200))
    avoid_with = db.Column(db.String(200))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # リレーションシップ
    user = db.relationship("User", backref=db.backref("entries", lazy=True))
    # room への逆参照は Room モデル側で設定済み（もしくはここで定義）

    def __repr__(self):
        return f'<Entry User:{self.user_id} Room:{self.room_id}>'