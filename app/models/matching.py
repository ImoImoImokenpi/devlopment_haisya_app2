# models/matching.py

from ..extensions import db
from datetime import datetime


class MatchingResult(db.Model):
    """
    マッチングの実行履歴。
    1ルームで何度も実行し直せるよう、実行ごとにレコードを作る。
    """
    __tablename__ = "matching_results"

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"), nullable=False)
    executed_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    executed_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 未割り当てが出た場合に記録（user_id をカンマ区切りで保存）
    unassigned_user_ids = db.Column(db.Text, default="")

    # リレーション
    room = db.relationship("Room", backref=db.backref("matching_results", lazy=True))
    executor = db.relationship("User", backref=db.backref("executed_matchings", lazy=True))
    assignments = db.relationship(
        "CarAssignment",
        backref="matching_result",
        lazy=True,
        cascade="all, delete-orphan",  # 結果削除時に割り当ても消える
    )

    def __repr__(self):
        return f"<MatchingResult room:{self.room_id} at:{self.executed_at}>"


class CarAssignment(db.Model):
    """
    誰がどのドライバーの車に乗るか。
    driver_entry_id = has_car=True の Entry.id を指す。
    """
    __tablename__ = "car_assignments"

    id = db.Column(db.Integer, primary_key=True)
    matching_result_id = db.Column(
        db.Integer, db.ForeignKey("matching_results.id"), nullable=False
    )

    # ドライバー（has_car=True の Entry）
    driver_entry_id = db.Column(db.Integer, db.ForeignKey("entries.id"), nullable=False)

    # 乗客（ドライバー自身も含む）
    passenger_entry_id = db.Column(db.Integer, db.ForeignKey("entries.id"), nullable=False)

    # リレーション
    driver_entry = db.relationship(
        "Entry", foreign_keys=[driver_entry_id],
        backref=db.backref("driven_assignments", lazy=True)
    )
    passenger_entry = db.relationship(
        "Entry", foreign_keys=[passenger_entry_id],
        backref=db.backref("ride_assignments", lazy=True)
    )

    def __repr__(self):
        return f"<CarAssignment driver:{self.driver_entry_id} passenger:{self.passenger_entry_id}>"