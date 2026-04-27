from flask import Flask, Blueprint, render_template, request, redirect, url_for, jsonify, flash
from flask_login import login_required, current_user
from datetime import datetime
from ..extensions import db
from ..models.event import Event
from ..models.entry import Entry
from ..models.group import Group, GroupMember
from sqlalchemy import or_
from flask import jsonify


events_bp = Blueprint("events", __name__, url_prefix="/events")

@events_bp.route('/api/events')
@login_required
def get_events_json():
    # 1. 自分が所属しているグループのIDを取得
    my_group_ids = [gm.group_id for gm in GroupMember.query.filter_by(user_id=current_user.id).all()]
    
    # 2. 「自分が作成したイベント」または「所属グループのイベント」を取得
    events = Event.query.filter(
        or_(
            Event.created_by == current_user.id,
            Event.group_id.in_(my_group_ids) if my_group_ids else False
        )
    ).all()

    event_list = []
    for event in events:
        event_list.append({
            'id': event.id,
            'title': event.title,
            'start': event.start_time.isoformat(),
            'end': event.end_time.isoformat() if event.end_time else None,
            # 配車ありの場合はクラスを付与して🚗アイコンを表示
            'className': 'event-needs-car' if event.needs_car else '',
            # デザイン用の色設定
            'backgroundColor': 'rgba(32, 201, 151, 0.1)' if event.needs_car else '#f8f9fa',
            'borderColor': 'var(--walica-green)' if event.needs_car else '#dee2e6',
            'textColor': 'var(--walica-green)' if event.needs_car else '#666',
        })
    
    return jsonify(event_list)

@events_bp.route('/join', methods=['GET', 'POST'])
@login_required
def join_by_code():
    if request.method == 'POST':
        code = request.form.get('code').upper().strip()
        
        # まずはグループ招待コードを検索
        group = Group.query.filter_by(invite_code=code).first()
        if group:
            # 既にメンバーか確認
            is_member = GroupMember.query.filter_by(group_id=group.id, user_id=current_user.id).first()
            if not is_member:
                new_member = GroupMember(group_id=group.id, user_id=current_user.id)
                db.session.add(new_member)
                db.session.commit()
                flash(f'グループ「{group.name}」に参加しました！', 'success')
            else:
                flash(f'既に「{group.name}」のメンバーです。', 'info')
            return redirect(url_for('main.index')) # カレンダーへ

        # 次に単発イベントの招待コードを検索
        event = Event.query.filter_by(join_code=code).first()
        if event:
            return redirect(url_for('events.event_detail', event_id=event.id))
        
        flash("有効なコードが見つかりませんでした。", "danger")
    
    return render_template('join_code.html')

@events_bp.route('/group', methods=['GET', 'POST'])
@login_required
def create_group():
    if request.method == 'GET':  
        return render_template('create_event.html')
    if request.method == 'POST':        
        return render_template('create_event.html')

@events_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_event():
    if request.method == 'GET':
        # クエリパラメータから日付を取得 (なければ今日)
        date_str = request.args.get('date')
        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        default_start = f"{date_str}T10:00"
        default_end = f"{date_str}T11:00"
        
        return render_template('create_event.html', default_start=default_start, default_end=default_end)

    if request.method == 'POST':
        # フォームデータの保存処理
        title = request.form.get('title')
        location = request.form.get('location')
        start_str = request.form.get('start_time')
        end_str = request.form.get('end_time')
        
        # チェックボックスはチェックされている時だけ 'on' という文字列が飛ぶ
        needs_car = True if request.form.get('needs_car') == 'on' else False
        # 文字列をPythonのdatetime型に変換
        start_time = datetime.strptime(start_str, '%Y-%m-%dT%H:%M')
        end_time = datetime.strptime(end_str, '%Y-%m-%dT%H:%M') if end_str else None

        # インスタンス作成
        new_event = Event(
            title=title,
            location=location,
            start_time=start_time,
            end_time=end_time,
            needs_car=needs_car,
            created_by=current_user.id
            # group_id は現在選択中のルームIDがあればセット
        )

        db.session.add(new_event)
        db.session.commit()

        return redirect(url_for('events.event_detail', event_id=new_event.id))


@events_bp.route('/detail/<int:event_id>')
@login_required
def event_detail(event_id):
    event = Event.query.get_or_404(event_id)
    
    # 現在のユーザーがこのイベント内のどのルームに参加しているか IDを取得
    joined_room_ids = [
        entry.room_id for entry in Entry.query.filter_by(user_id=current_user.id).all()
    ]
    
    return render_template('event_detail.html', 
                           event=event, 
                           joined_room_ids=joined_room_ids)

# 実装イメージ
@events_bp.route('/join', methods=['POST'])
@login_required
def join():
    code = request.form.get('code').upper()
    event = Event.query.filter_by(join_code=code).first()
    if event:
        return redirect(url_for('events.event_detail', event_id=event.id))
    flash("コードが正しくありません")
    return redirect(url_for('events.index'))