from flask import Blueprint, render_template, request, redirect, url_for, abort, flash
from flask_login import login_required, current_user
from ..extensions import db
from ..models.room import Room
from ..models.entry import Entry
from ..models.question_master import QuestionMaster
from ..models.room_question import RoomQuestion
from ..models.event import Event
from ..models.matching import MatchingResult, CarAssignment
from ..models.group import GroupMember
from ..rooms.matching import assign_to_cars, assign_to_cars_random, assign_to_cars_dokidoki
from datetime import datetime
from werkzeug.utils import secure_filename
import os
from sqlalchemy import asc

UPLOAD_FOLDER = 'app/static/uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

rooms_bp = Blueprint("rooms", __name__, url_prefix="/rooms")


# ─────────────────────────────────────────
# ルーム作成
# ─────────────────────────────────────────
@rooms_bp.route('/create/<int:event_id>', methods=['GET', 'POST'])
@login_required
def create_room(event_id):
    event = Event.query.get_or_404(event_id)
    current_room_count = Room.query.filter_by(event_id=event_id).count()
    next_room_num = current_room_count + 1

    if request.method == 'POST':
        deadline_str = request.form.get('deadline')
        note = request.form.get('note')
        selected_questions = request.form.getlist('selected_questions')

        sections = 1
        if 'q_schedule' in selected_questions:
            sections = request.form.get('sections', type=int) or 1

        new_room = Room(
            event_id=event.id,
            name=request.form.get('car_name') or f"ルーム{next_room_num}",
            description=note,
            sections=sections,
            deadline=datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M') if deadline_str else None,
            created_by=current_user.id
        )

        db.session.add(new_room)
        db.session.flush()

        for q_id_str in selected_questions:
            rq = RoomQuestion(room_id=new_room.id, question_id=q_id_str)
            db.session.add(rq)

        db.session.commit()
        flash('配車ルームを作成しました！', 'success')
        return redirect(url_for('events.event_detail', event_id=event.id))

    return render_template('create_room.html', event=event, next_room_num=next_room_num)


# ─────────────────────────────────────────
# ルーム詳細 + マッチング結果表示 (GET)
# ─────────────────────────────────────────
@rooms_bp.route('/room/<int:room_id>')
@login_required
def room_detail(room_id):
    room = Room.query.get_or_404(room_id)
    participant_count = Entry.query.filter_by(room_id=room_id).count()
    user_entry = Entry.query.filter_by(room_id=room_id, user_id=current_user.id).first()
    room_questions = RoomQuestion.query.filter_by(room_id=room_id).all()
    selected_ids = [rq.question_id for rq in room_questions]

    schedules = []
    if 'q_schedule' in selected_ids:
        num_sections = room.sections if room.sections else 1
        for sec in range(1, num_sections + 1):
            for order in range(1, 16):
                schedules.append({
                    'id': f"{sec}-{order}",
                    'section': sec,
                    'order': order,
                    'label': f"{sec}部 {order}番"
                })

    # マッチング結果を取得
    latest = (
        MatchingResult.query
        .filter_by(room_id=room_id)
        .order_by(MatchingResult.executed_at.desc())
        .first()
    )

    cars_grouped = {}
    unassigned = []
    if latest:
        for assignment in latest.assignments:
            did = assignment.driver_entry_id
            if did not in cars_grouped:
                cars_grouped[did] = {
                    "driver": assignment.driver_entry,
                    "members": [],
                }
            if assignment.passenger_entry_id != assignment.driver_entry_id:
                cars_grouped[did]["members"].append(assignment.passenger_entry)

        unassigned_ids = (
            [int(i) for i in latest.unassigned_user_ids.split(",") if i]
            if latest.unassigned_user_ids else []
        )
        if unassigned_ids:
            unassigned = Entry.query.filter(
                Entry.user_id.in_(unassigned_ids),
                Entry.room_id == room_id,
            ).all()

    # 早帰りメンバーがいる車を上に並べる
    def car_has_early_leaver(car):
        all_members = [car["driver"]] + car["members"]
        return any(m.early_leave for m in all_members)

    cars_grouped = dict(
        sorted(
            cars_grouped.items(),
            key=lambda item: car_has_early_leaver(item[1]),
            reverse=True  # True（早帰りあり）を先頭に
        )
    )
    
    early_leavers = Entry.query.filter_by(
        room_id=room_id,
        early_leave=True
    ).all()

    entries = Entry.query.filter_by(room_id=room_id).all()

    is_admin = False
    group_members = []
    username_to_name = {e.user.username: e.user.name for e in entries}
    if room.event.group:
        memberships = GroupMember.query.filter_by(group_id=room.event.group.id).all()
        group_members = [m.user for m in memberships if m.user_id != current_user.id]
        for m in memberships:
            username_to_name.setdefault(m.user.username, m.user.name)
            if m.user_id == current_user.id and m.role == 'admin':
                is_admin = True

    return render_template(
        'room_detail.html',
        room=room,
        event=room.event,
        participant_count=participant_count,
        entry=user_entry,
        selected_ids=selected_ids,
        schedules=schedules,
        latest=latest,
        cars_grouped=cars_grouped,
        unassigned=unassigned,
        early_leavers=early_leavers,
        entries=entries,
        group_members=group_members,
        is_admin=is_admin,
        username_to_name=username_to_name,
    )


# ─────────────────────────────────────────
# エントリー登録 (POST専用)
# ─────────────────────────────────────────
@rooms_bp.route('/entry/<int:room_id>', methods=['POST'])
@login_required
def entry_room(room_id):
    room = Room.query.get_or_404(room_id)
    room_questions = RoomQuestion.query.filter_by(room_id=room_id).all()
    selected_ids = [rq.question_id for rq in room_questions]

    has_car_val = request.form.get('has_car') == 'yes'
    has_rehersal = request.form.get('has_rehersal') == 'yes'

    new_entry = Entry(
        room_id=room.id,
        user_id=current_user.id,
        schedule_id=request.form.get('schedule_id') if 'q_schedule' in selected_ids else None,
        has_car=has_car_val,
        capacity=request.form.get('capacity', type=int) if has_car_val else 0,
        has_rehersal=request.form.get('has_rehersal') == 'yes',
        prefer_with=request.form.get('prefer_with'),
        avoid_with=request.form.get('avoid_with'),
        created_at=datetime.utcnow()
    )

    try:
        db.session.add(new_entry)
        db.session.commit()
        flash(f'{room.name} に参加しました！', 'success')
    except Exception as e:
        db.session.rollback()
        flash('参加処理に失敗しました。', 'danger')
        print(f"Error: {e}")

    # 登録後はルーム詳細へ
    return redirect(url_for('rooms.room_detail', room_id=room_id))

# ─────────────────────────────────────────
# マッチング実行 (POST専用)
# ─────────────────────────────────────────
@rooms_bp.route('/room/<int:room_id>/start_matching', methods=['POST'])
@login_required
def matching(room_id):
    room = Room.query.get_or_404(room_id)

    if room.event.created_by != current_user.id:
        flash("権限がありません", "danger")
        return redirect(url_for('rooms.room_detail', room_id=room_id))

    matching_type = request.form.get('matching_type', 'score')
    if matching_type == 'random':
        cars, unassigned = assign_to_cars_random(room_id)
    elif matching_type == 'dokidoki':
        cars, unassigned = assign_to_cars_dokidoki(room_id)
    else:
        cars, unassigned = assign_to_cars(room_id)

    if not cars:
        flash("車を登録しているメンバーがいません", "warning")
        return redirect(url_for('rooms.room_detail', room_id=room_id))

    # 既存結果を削除（再実行時に上書き）
    old_results = MatchingResult.query.filter_by(room_id=room_id).all()
    for r in old_results:
        db.session.delete(r)

    unassigned_ids = ",".join(str(e.user_id) for e in unassigned)
    result = MatchingResult(
        room_id=room_id,
        executed_by=current_user.id,
        unassigned_user_ids=unassigned_ids,
    )
    db.session.add(result)
    db.session.flush()

    for car in cars:
        driver_entry = car["driver_entry"]
        for member_entry in car["members"]:
            assignment = CarAssignment(
                matching_result_id=result.id,
                driver_entry_id=driver_entry.id,
                passenger_entry_id=member_entry.id,
            )
            db.session.add(assignment)

    db.session.commit()

    if unassigned:
        names = ", ".join(e.user.username for e in unassigned)
        flash(f"割り当てできなかったメンバー: {names}", "warning")

    flash(f"{room.name} のマッチングを完了しました", "success")
    return redirect(url_for('rooms.room_detail', room_id=room_id))

@rooms_bp.route('/entry/<int:room_id>/early_leave', methods=['POST'])
@login_required
def early_leave(room_id):
    entry = Entry.query.filter_by(
        room_id=room_id,
        user_id=current_user.id
    ).first_or_404()

    entry.early_leave = not entry.early_leave
    db.session.commit()

    return redirect(url_for('rooms.room_detail', room_id=room_id))