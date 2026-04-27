from ..extensions import db

class Group(db.Model):
    __tablename__ = 'groups'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    # グループ加入用のコード（一度入ればOK）
    invite_code = db.Column(db.String(10), unique=True, nullable=False)
    
    events = db.relationship('Event', backref='group', lazy=True)

class GroupMember(db.Model):
    __tablename__ = 'group_members'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), primary_key=True)

    # relationshipを追加しておくと便利です
    group = db.relationship('Group', backref=db.backref('members', lazy=True))
    user = db.relationship('User', backref=db.backref('memberships', lazy=True))