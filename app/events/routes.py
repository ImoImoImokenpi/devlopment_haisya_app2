from flask import Flask, Blueprint, render_template, request, redirect, url_for, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from ..extensions import db
from ..models.event import Event

events_bp = Blueprint("events", __name__, url_prefix="/events")

from flask import jsonify

@events_bp.route('/api/events')
@login_required
def get_events_json():
    # ログインユーザーに関連するイベントを取得（グループ所属分も含める場合は調整）
    events = Event.query.filter_by(created_by=current_user.id).all()
    
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
    # データベースから該当するイベントを1件取得（なければ404）
    event = Event.query.get_or_404(event_id)
    return render_template('event_detail.html', event=event)
