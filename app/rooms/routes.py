from flask import Blueprint, render_template, request, redirect, url_for, abort, flash
from flask_login import login_required, current_user
from ..extensions import db
from ..models.room import Room
from ..models.entry import Entry
from ..models.event_schedule import EventSchedule
from ..models.room_attachment import RoomAttachment
from ..models.question_master import QuestionMaster
from ..models.room_question import RoomQuestion
from datetime import datetime
from werkzeug.utils import secure_filename
import os
from sqlalchemy import asc

UPLOAD_FOLDER = 'app/static/uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

rooms_bp = Blueprint("rooms", __name__, url_prefix="/rooms")

@rooms_bp.route("/")
@login_required
def rooms():
    # 参加募集されたルームが表示される
    rooms = Room.query.all()

    my_entries = Entry.query.filter_by(user_id=current_user.id).all()
    registered_room_ids = {e.room_id for e in my_entries}

    return render_template(
        "rooms.html",
        rooms=rooms,
        registered_room_ids=registered_room_ids
    )

@rooms_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_room():
    if request.method == "POST":

        name = request.form.get("name")
        description = request.form.get("description")
        event_date_str = request.form.get("event_date")
        deadline_str = request.form.get("deadline")
        sections = int(request.form.get("sections", 1))

        # Date (YYYY-MM-DD)
        event_date = None
        if event_date_str:
            event_date = datetime.strptime(event_date_str, "%Y-%m-%d").date()

        # DateTime (YYYY-MM-DDTHH:MM)
        deadline = None
        if deadline_str:
            deadline = datetime.strptime(deadline_str, "%Y-%m-%dT%H:%M")


        # ① Room作成
        room = Room(
            name=name,
            description=description,
            event_date=event_date,
            deadline=deadline,
            owner_id=current_user.id
        )
        db.session.add(room)
        db.session.flush() 

        PER_SECTION = 15  # 1部あたりの出番数

        for section in range(1, sections + 1):
            for order in range(1, PER_SECTION + 1):
                schedule = EventSchedule(
                    room_id=room.id,
                    section=section,
                    order=order
                )
                db.session.add(schedule)


        # ③ 質問ON/OFF保存
        selected_questions = request.form.getlist("questions")

        for qid in selected_questions:
            rq = RoomQuestion(
                room_id=room.id,
                question_id=int(qid)
            )
            db.session.add(rq)

        # ④ 添付ファイル
        file = request.files.get("attachment")
        if file and file.filename:
            filename = secure_filename(file.filename)
            path = os.path.join("app/static/uploads", filename)
            file.save(path)

            attach = RoomAttachment(
                room_id=room.id,
                filename=filename,
                filepath=path
            )
            db.session.add(attach)

        db.session.commit()

        return redirect(url_for("rooms.rooms"))

    # GET：質問一覧を取得
    questions = QuestionMaster.query.all()
    return render_template("create.html", questions=questions)

@rooms_bp.route("/<int:room_id>/delete", methods=["POST"])
@login_required
def delete_room(room_id):
    room = Room.query.get_or_404(room_id)

    # 管理者以外は削除不可
    if room.owner_id != current_user.id:
        abort(403)

    # 参加メンバーも消す
    Entry.query.filter_by(room_id=room_id).delete()

    db.session.delete(room)
    db.session.commit()

    flash("ルームを削除しました")
    return redirect(url_for("rooms.rooms"))


@rooms_bp.route("/<int:room_id>", methods=["GET", "POST"])
@login_required
def room_detail(room_id):

    room = Room.query.get_or_404(room_id)

    # このユーザが既に登録しているか確認
    entry = Entry.query.filter_by(
        room_id=room_id,
        user_id=current_user.id
    ).first()

    # 出番一覧
    schedules = (
        EventSchedule.query
        .filter_by(room_id=room_id)
        .order_by(asc(EventSchedule.section), asc(EventSchedule.order))
        .all()
    )

    if request.method == "POST" and not entry:

        has_car = True if request.form.get("has_car") == "on" else False
        capacity = int(request.form.get("capacity") or 0)
        schedule_id = request.form.get("schedule_id")
        genre = request.form.get("genre")
        prefer_with = request.form.get("prefer_with")
        avoid_with = request.form.get("avoid_with")

        new_entry = Entry(
            user_id=current_user.id,
            room_id=room_id,
            has_car=has_car,
            capacity=capacity,
            schedule_id=schedule_id,
            genre=genre,
            prefer_with=prefer_with,
            avoid_with=avoid_with,
        )

        db.session.add(new_entry)
        db.session.commit()

        return redirect(url_for("matching.preview", room_id=room_id))

    # 登録人数
    entry_count = Entry.query.filter_by(room_id=room_id).count()

    return render_template(
        "detail.html",
        room=room,
        entry=entry,
        schedules=schedules,
        entry_count=entry_count
    )
