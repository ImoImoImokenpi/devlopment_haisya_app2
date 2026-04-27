from flask import Blueprint, render_template, request, redirect, url_for, abort, flash
from flask_login import login_required, current_user
from ..extensions import db
from ..models.room import Room
from ..models.entry import Entry
from ..models.question_master import QuestionMaster
from ..models.room_question import RoomQuestion
from ..models.event import Event
from datetime import datetime
from werkzeug.utils import secure_filename
import os
from sqlalchemy import asc

UPLOAD_FOLDER = 'app/static/uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

rooms_bp = Blueprint("rooms", __name__, url_prefix="/rooms")

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
        
        # UIの部数設定を取得（q_scheduleが選ばれている場合のみ反映、それ以外は1）
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

        # 選択された質問を保存（q_schedule も含む）
        for q_id_str in selected_questions:
            rq = RoomQuestion(
                room_id=new_room.id,
                question_id=q_id_str
            )
            db.session.add(rq)

        db.session.commit()
        flash('配車ルームを作成しました！', 'success')
        return redirect(url_for('events.event_detail', event_id=event.id))

    return render_template('create_room.html', event=event, next_room_num=next_room_num)


@rooms_bp.route('/entry/<int:room_id>', methods=['GET', 'POST']) # URLをentryに変更
@login_required
def entry_room(room_id):
    room = Room.query.get_or_404(room_id)
    participant_count = Entry.query.filter_by(room_id=room_id).count()
    user_entry = Entry.query.filter_by(room_id=room_id, user_id=current_user.id).first()
    room_questions = RoomQuestion.query.filter_by(room_id=room_id).all()
    selected_ids = [rq.question_id for rq in room_questions]

    # スケジュール選択肢の生成（出演順の質問が設定されている場合のみ）
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

    if request.method == 'POST':
        # 参加情報の取得
        has_car_val = request.form.get('has_car') == 'yes'

        new_entry = Entry(
            room_id=room.id,
            user_id=current_user.id,
            schedule_id=request.form.get('schedule_id') if 'q_schedule' in selected_ids else None,
            has_car=has_car_val,
            capacity=request.form.get('capacity', type=int) if has_car_val else 0,
            has_rehersal=request.form.get('has_rehersal') == 'yes', # Entryモデルにこのカラムがある前提
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

        return redirect(url_for('events.event_detail', event_id=room.event_id))

    return render_template('entry.html', 
                           room=room,
                           participant_count=participant_count,
                           event=room.event, 
                           selected_ids=selected_ids,
                           schedules=schedules,
                           entry=user_entry)