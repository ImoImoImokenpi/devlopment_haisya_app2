from ..extensions import db
from flask_login import UserMixin
from ..extensions import login_manager

class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    icon = db.Column(db.String(200), default="default.png")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
