from flask import Blueprint, render_template, request, redirect, url_for, abort, flash
from flask_login import login_required, current_user
from ..extensions import db
from ..models.room import Room
from ..models.entry import Entry
from ..models.event_schedule import EventSchedule
from ..models.room_attachment import RoomAttachment
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
    # 紐づけるイベントが存在するか確認
    event = Event.query.get_or_404(event_id)

    # 現在のこの予定に紐づくルーム数をカウント
    current_room_count = Room.query.filter_by(event_id=event_id).count()
    next_room_num = current_room_count + 1

    if request.method == 'POST':
        # 1. フォームデータの取得
        deadline_str = request.form.get('deadline')
        note = request.form.get('note')
        selected_questions = request.form.getlist('selected_questions') # ['q_genre', 'q_car'...]

        # 2. ルームの作成と保存
        # ※ モデルの構成に合わせて調整してください
        new_room = Room(
            event_id=event.id,
            name=request.form.get('car_name') or f"ルーム{next_room_num}", # デフォルト名
            description=note,
            deadline=datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M') if deadline_str else None,
            created_by=current_user.id
        )
        
        db.session.add(new_room)
        db.session.flush() # IDを確定させるために一度流す

        # 3. 選択された質問の紐付け
        # selected_questions に入っている ID ('q_car' など) を RoomQuestion に登録
        for q_id_str in selected_questions:
            # 既存の QuestionMaster から ID を引くか、
            # もし ID がそのまま数値なら int(q_id_str) で処理
            rq = RoomQuestion(
                room_id=new_room.id,
                question_id=q_id_str # 文字列IDをそのまま保存するか、数値に変換するかはDB設計次第
            )
            db.session.add(rq)

        db.session.commit()
        flash('配車ルームを作成しました！', 'success')
        
        return redirect(url_for('events.event_detail', event_id=event.id))

    # GET時の処理
    return render_template('create_room.html', event=event, next_room_num=next_room_num)

@rooms_bp.route('/<int:room_id>', methods=['GET', 'POST'])
@login_required
def entry_room(room_id):
    # 指定されたルームを取得
    room = Room.query.get_or_404(room_id)
    # そのルームに紐づく質問設定を取得
    room_questions = RoomQuestion.query.filter_by(room_id=room_id).all()
    # 質問IDのリストを作成（テンプレートでの出し分け用）
    selected_ids = [rq.question_id for rq in room_questions]

    if request.method == 'POST':
        # 1. フォームから回答を取得
        # ※ get('name', default) を使って、未チェック項目のエラーを防ぐ
        has_car_val = request.form.get('has_car') == 'yes'
        
        new_entry = Entry(
            room_id=room.id,
            user_id=current_user.id,
            # 回答内容を各カラムに保存（Entryモデルのカラム名に合わせて調整してください）
            section=request.form.get('answer_section'),
            genre=request.form.get('answer_genre'),
            has_car=has_car_val,
            capacity=request.form.get('capacity', type=int) if has_car_val else 0,
            avoid_name=request.form.get('answer_avoid'),
            entry_at=datetime.utcnow()
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

    # GET時：回答フォームを表示
    return render_template('entry.html', 
                           room=room, 
                           event=room.event, 
                           selected_ids=selected_ids)