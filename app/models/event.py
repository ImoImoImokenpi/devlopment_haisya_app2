import string
import random
from ..extensions import db
from datetime import datetime

class Event(db.Model):
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    
    # --- 基本情報 ---
    title = db.Column(db.String(100), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=True)
    location = db.Column(db.String(200))
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    
    # --- 共有設定 (Teams風の招待コード) ---
    # ランダムな6桁程度のコード。一意(unique)にして検索を高速化
    join_code = db.Column(db.String(10), unique=True, nullable=False)
    
    # --- 配車・送迎設定 ---
    needs_car = db.Column(db.Boolean, default=True)
    
    # --- 管理用メタデータ ---
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # リレーションシップ（もし必要なら）
    creator = db.relationship("User", backref=db.backref("created_events", lazy=True))

    def __init__(self, **kwargs):
        super(Event, self).__init__(**kwargs)
        # インスタンス作成時に招待コードがなければ自動生成
        if not self.join_code:
            self.join_code = self.generate_unique_code()

    @staticmethod
    def generate_unique_code(length=6):
        """英数字（混同しやすい文字を除く）で重複しないコードを生成"""
        # I, O, l, 0 などの見間違いやすい文字を除いた文字セット
        chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        while True:
            code = ''.join(random.choices(chars, k=length))
            # データベースに同じコードがないかチェック
            if not Event.query.filter_by(join_code=code).first():
                return code

    def __repr__(self):
        return f'<Event {self.title} Code:{self.join_code}>'