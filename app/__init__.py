from flask import Flask
from .extensions import db, login_manager, migrate
from .scheduler import scheduler, check_deadlines

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

        # モデルを認識させる
    from .models import User, Room, Entry

    # blueprint 登録
    from .auth.routes import auth_bp
    from .events.routes import events_bp
    from .rooms.routes import rooms_bp
    from .matching.routes import matching_bp
    from .profiles.routes import profile_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(rooms_bp)
    app.register_blueprint(matching_bp)
    app.register_blueprint(profile_bp)

    @app.route("/")
    def index():
        from flask import render_template
        from flask_login import current_user
        # 必要なモデルをインポート
        from .models.group import GroupMember
        from .models.event import Event
        from .models.entry import Entry
        from datetime import datetime
        from sqlalchemy.orm import joinedload

        # 未ログイン時はログイン画面へ（または紹介用トップページへ）
        if not current_user.is_authenticated:
            return render_template("home.html", my_groups=[], joined_rooms=[])

        # 1. 自分が所属しているグループを取得
        my_group_memberships = GroupMember.query.filter_by(user_id=current_user.id).all()
        my_group_ids = [gm.group_id for gm in my_group_memberships]

        # 2. 自分が参加中のルーム情報の取得（IDリスト）
        my_entries = Entry.query.filter_by(user_id=current_user.id).all()
        joined_room_ids = [e.room_id for e in my_entries]
        
        # 3. 募集中のルームを取得
        # Eventを結合(Join)することで、room.event.group.name にアクセス可能にします
        now = datetime.utcnow()
        available_rooms = Room.query.join(Event).options(
            joinedload(Room.event),
            joinedload(Room.entries).joinedload(Entry.user)  # ← 追加
        ).filter(
            (Event.group_id.in_(my_group_ids)) | (Event.created_by == current_user.id),
            (Room.deadline > now) | (Room.deadline == None)
        ).all()

        return render_template(
            "home.html", 
            my_groups=my_group_memberships, 
            available_rooms=available_rooms,
            joined_room_ids=joined_room_ids
        )

    return app
