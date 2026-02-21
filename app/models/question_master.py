from ..extensions import db

class QuestionMaster(db.Model):
    __tablename__ = "question_master"

    id = db.Column(db.Integer, primary_key=True)

    key = db.Column(db.String(50), unique=True)  # プログラム識別子
    title = db.Column(db.String(200))
    type = db.Column(db.String(20))  
    # text / number / bool / single / multi / user_select

