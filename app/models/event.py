from ..extensions import db
from datetime import datetime

class Event(db.Model):
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    
    # --- 基本情報 ---
    title = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200))
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    
    # --- 配車・送迎設定 ---
    # checkboxの "on" (True) / なし (False) を格納
    needs_car = db.Column(db.Boolean, default=True)
    
    # --- 管理用メタデータ ---
    # どのルーム（グループ）のイベントか（NULLを許容することで個人利用に対応）
    # group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=True)
    # 誰が作成したか
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Event {self.title}>'