from flask import Flask, Blueprint, render_template, request, redirect, url_for, jsonify, flash
from flask_login import login_required, current_user
from datetime import datetime
from ..extensions import db
from ..models.event import Event
from ..models.entry import Entry
from ..models.group import Group, GroupMember
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
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
            'backgroundColor': event.group.color if event.group_id and event.group else '#adb5bd',
            'borderColor': event.group.color if event.group_id and event.group else '#adb5bd',
            'textColor': '#ffffff',
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
                new_member = GroupMember(
                    group_id=group.id, 
                    user_id=current_user.id,
                    role='member'
                )
                db.session.add(new_member)
                db.session.commit()
                flash(f'グループ「{group.name}」に参加しました！', 'success')
            else:
                flash(f'既に「{group.name}」のメンバーです。', 'info')
            return redirect(url_for('index')) # カレンダーへ

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
        return render_template('create_group.html')
    
    if request.method == 'POST':
        group_name = request.form.get('name')
        color = request.form.get('color') or '#20c997'  # ← 追加
        
        # 1. グループの作成
        new_group = Group(
            name=group_name,
            invite_code=Group.generate_unique_code(),
            color=color
        )
        db.session.add(new_group)
        db.session.flush() # IDを確定させる
        
        # 2. 作成者を最初のメンバー(管理者)として登録
        member = GroupMember(
            user_id=current_user.id, 
            group_id=new_group.id,
            role='admin'
        )
        db.session.add(member)
        
        db.session.commit()
        
        flash(f"グループ「{group_name}」を作成しました！", "success")
        # 作成完了後、コードを表示するために詳細画面かメインへ
        return render_template('create_group.html', group=new_group)

@events_bp.route("/group/<int:group_id>")
@login_required
def group_detail(group_id):

    # グループ取得
    group = Group.query.get_or_404(group_id)

    # 自分が所属しているか確認
    membership = GroupMember.query.filter_by(
        group_id=group.id,
        user_id=current_user.id
    ).first()

    # 非メンバーは閲覧不可
    if not membership:
        flash("このグループを見る権限がありません。", "danger")
        return redirect(url_for("index"))

    # メンバー一覧取得
    members = (
        GroupMember.query
        .filter_by(group_id=group.id)
        .options(joinedload(GroupMember.user))
        .all()
    )

    # グループイベント取得
    events = Event.query.filter_by(
        group_id=group.id
    ).order_by(Event.start_time.desc()).all()

    # 管理者かどうか
    is_admin = membership.role == "admin"

    return render_template(
        "group_detail.html",
        group=group,
        members=members,
        events=events,
        is_admin=is_admin
    )


@events_bp.route("/group/<int:group_id>/leave", methods=["POST"])
@login_required
def leave_group(group_id):

    group = Group.query.get_or_404(group_id)

    membership = GroupMember.query.filter_by(
        group_id=group.id,
        user_id=current_user.id
    ).first()

    if not membership:
        flash("グループに所属していません。", "danger")
        return redirect(url_for("index"))

    # 管理者人数確認
    if membership.role == "admin":

        admin_count = GroupMember.query.filter_by(
            group_id=group.id,
            role="admin"
        ).count()

        # 最後の管理者なら脱退不可
        if admin_count <= 1:

            total_members = GroupMember.query.filter_by(
                group_id=group.id
            ).count()

            # 自分しかいないならグループ削除
            if total_members == 1:

                db.session.delete(membership)
                db.session.delete(group)

                db.session.commit()

                flash("グループを削除しました。", "success")

                return redirect(url_for("index"))

            flash(
                "最後の管理者は脱退できません。管理者を引き継いでください。",
                "warning"
            )

            return redirect(
                url_for("events.group_detail", group_id=group.id)
            )

    # 通常脱退
    db.session.delete(membership)
    db.session.commit()

    flash(f"「{group.name}」から脱退しました。", "success")

    return redirect(url_for("index"))


@events_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_event():

    if request.method == 'GET':
        # 自分が「管理者」として所属しているグループだけを抽出
        admin_memberships = GroupMember.query.filter_by(
            user_id=current_user.id, 
            role='admin'
        ).all()
        admin_groups = [gm.group for gm in admin_memberships]

        # クエリパラメータから日付を取得 (なければ今日)
        date_str = request.args.get('date')
        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        default_start = f"{date_str}T10:00"
        default_end = f"{date_str}T11:00"
        
        return render_template('create_event.html', admin_groups=admin_groups, default_start=default_start, default_end=default_end)
    
    if request.method == 'POST':
        # フォームデータの保存処理
        group_id = request.form.get('group_id')
        title = request.form.get('title')
        location = request.form.get('location')
        start_str = request.form.get('start_time')
        end_str = request.form.get('end_time')

        # セキュリティチェック（送られてきたgroup_idの管理者か？）
        final_group_id = None
        if group_id:
            is_admin = GroupMember.query.filter_by(
                group_id=group_id, 
                user_id=current_user.id, 
                role='admin'
            ).first()
            if is_admin:
                final_group_id = group_id
        
        # チェックボックスはチェックされている時だけ 'on' という文字列が飛ぶ
        needs_car = True if request.form.get('needs_car') == 'on' else False
        # 文字列をPythonのdatetime型に変換
        start_time = datetime.strptime(start_str, '%Y-%m-%dT%H:%M')
        end_time = datetime.strptime(end_str, '%Y-%m-%dT%H:%M') if end_str else None

        # インスタンス作成
        new_event = Event(
            group_id=final_group_id,
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

    # is_admin を計算して渡す
    is_admin = False
    if event.group_id:
        membership = GroupMember.query.filter_by(
            group_id=event.group_id,
            user_id=current_user.id,
            role='admin'
        ).first()
        is_admin = membership is not None
    
    return render_template('event_detail.html', 
                           event=event, 
                           joined_room_ids=joined_room_ids,
                           is_admin=is_admin)

@events_bp.route('/detail/<int:event_id>/delete', methods=['POST'])
@login_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)

    # 権限チェック
    is_creator = (event.created_by == current_user.id)
    is_group_admin = False
    if event.group_id:
        membership = GroupMember.query.filter_by(
            group_id=event.group_id,
            user_id=current_user.id,
            role='admin'
        ).first()
        is_group_admin = membership is not None

    if not is_creator and not is_group_admin:
        flash("このイベントを削除する権限がありません。", "danger")
        return redirect(url_for('events.event_detail', event_id=event_id))

    title = event.title
    db.session.delete(event)  # cascade により Room→Entry→Matching も連鎖削除
    db.session.commit()

    flash(f"イベント「{title}」を削除しました。", "success")
    return redirect(url_for('index'))


@events_bp.route('/room/<int:room_id>/delete', methods=['POST'])
@login_required
def delete_room(room_id):
    from ..models.room import Room

    room = Room.query.get_or_404(room_id)
    event = Event.query.get_or_404(room.event_id)

    # 権限チェック
    is_creator = (event.created_by == current_user.id)
    is_group_admin = False
    if event.group_id:
        membership = GroupMember.query.filter_by(
            group_id=event.group_id,
            user_id=current_user.id,
            role='admin'
        ).first()
        is_group_admin = membership is not None

    if not is_creator and not is_group_admin:
        flash("このルームを削除する権限がありません。", "danger")
        return redirect(url_for('events.event_detail', event_id=event.id))

    name = room.name
    db.session.delete(room)  # cascade により Entry→Matching も連鎖削除
    db.session.commit()

    flash(f"ルーム「{name}」を削除しました。", "success")
    return redirect(url_for('events.event_detail', event_id=event.id))

# 実装イメージ
@events_bp.route('/join', methods=['POST'])
@login_required
def join():
    code = request.form.get('code').upper()
    event = Event.query.filter_by(join_code=code).first()
    if event:
        return redirect(url_for('events.event_detail', event_id=event.id))
    flash("コードが正しくありません")
    return redirect(url_for('index'))