from ..extensions import db
from flask_login import UserMixin
from ..extensions import login_manager

class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    display_name = db.Column(db.String(50))
    icon = db.Column(db.String(200), default="default.png")

    @property
    def name(self):
        return self.display_name or self.username

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
