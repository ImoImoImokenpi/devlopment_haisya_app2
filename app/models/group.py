import random
import string
from datetime import datetime
from ..extensions import db

class Group(db.Model):
    __tablename__ = 'groups'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    # 招待コード（インデックスを貼って検索を高速化）
    invite_code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # リレーションシップ
    events = db.relationship('Event', backref='group', lazy=True, cascade="all, delete-orphan")

    @staticmethod
    def generate_unique_code():
        """
        見間違いにくい英数字（I, O, 1, 0を除外）を使用して
        重複のない8桁のコードを生成します。
        """
        chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        while True:
            code = ''.join(random.choices(chars, k=8))
            # データベースに同じコードがないか確認
            if not Group.query.filter_by(invite_code=code).first():
                return code

    def __repr__(self):
        return f'<Group {self.name} ({self.invite_code})>'


class GroupMember(db.Model):
    __tablename__ = 'group_members'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), primary_key=True)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 役割（'admin' または 'member'）を持たせると将来的に権限管理が楽になります
    role = db.Column(db.String(20), default='member')

    # relationship
    group = db.relationship('Group', backref=db.backref('membership_list', lazy='dynamic', cascade="all, delete-orphan"))
    user = db.relationship('User', backref=db.backref('group_memberships', lazy='dynamic'))

    def __repr__(self):
        return f'<GroupMember User:{self.user_id} Group:{self.group_id}>'