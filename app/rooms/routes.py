from flask import Blueprint, render_template, request, redirect, url_for, abort, flash
from flask_login import login_required, current_user
from ..extensions import db
from ..models.room import Room
from ..models.entry import Entry
from ..models.event_schedule import EventSchedule
from ..models.room_condition import RoomCondition
from datetime import datetime

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
        # まずGETならページを表示
    if request.method == "GET":
        return render_template("create.html")
    
    name = request.form["name"]
    description = request.form["description"]
    event_date = request.form["event_date"]
    deadline = request.form["deadline"]

    
    event_date = datetime.strptime(event_date, "%Y-%m-%d").date()
    deadline = datetime.strptime(deadline, "%Y-%m-%dT%H:%M")

    room = Room(
        name=name, 
        description=description, 
        owner_id=current_user.id,
        event_date=event_date,
        deadline=deadline
    )

    db.session.add(room)
    db.session.flush()

    schedules = request.form.getlist("schedule_label[]")

    order = 1
    for label in schedules:
        if label.strip() == "":
            continue

        s = EventSchedule(
            room_id=room.id,
            order=order,
            label=label
        )
        db.session.add(s)
        order += 1

    db.session.commit()

    return redirect(url_for("rooms.rooms"))

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
    schedules = EventSchedule.query.filter_by(room_id=room_id).order_by(EventSchedule.order).all()

    if request.method == "POST" and not entry:

        has_car = True if request.form.get("has_car") == "on" else False
        capacity = int(request.form.get("capacity") or 0)
        schedule_id = request.form.get("schedule_id")
        genre = request.form.get("genre")
        prefer_with = request.form.get("prefer_with")
        avoid_with = request.form.get("avoid_with")
        start_location = request.form.get("start_location")

        new_entry = Entry(
            user_id=current_user.id,
            room_id=room_id,
            has_car=has_car,
            capacity=capacity,
            schedule_id=schedule_id,
            genre=genre,
            prefer_with=prefer_with,
            avoid_with=avoid_with,
            start_location=start_location
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
