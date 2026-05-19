from flask import Flask
from .extensions import db, login_manager, migrate

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

        # モデルを認識させる
    from .models import User, Room, Entry  # Room/Entry は他 blueprint で参照

    # blueprint 登録
    from .auth.routes import auth_bp
    from .events.routes import events_bp
    from .rooms.routes import rooms_bp
    from .profiles.routes import profile_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(rooms_bp)
    app.register_blueprint(profile_bp)

    @app.route("/")
    def index():
        from flask import render_template
        from flask_login import current_user
        from .models.group import GroupMember
        from .models.room import Room
        from .models.event import Event
        from .models.entry import Entry
        from datetime import datetime, timedelta
        from sqlalchemy.orm import joinedload

        if not current_user.is_authenticated:
            return render_template("home.html", my_groups=[], deadline_rooms=[])

        my_group_memberships = GroupMember.query.filter_by(user_id=current_user.id).all()
        my_group_ids = [gm.group_id for gm in my_group_memberships]

        # 締め切り7日以内のルームを取得（自分が関係するイベントのもの）
        now = datetime.utcnow()
        soon = now + timedelta(days=7)
        deadline_rooms = Room.query.join(Event).options(
            joinedload(Room.event),
            joinedload(Room.entries)
        ).filter(
            (Event.group_id.in_(my_group_ids)) | (Event.created_by == current_user.id),
            Room.deadline != None,
            Room.deadline >= now,
            Room.deadline <= soon
        ).order_by(Room.deadline.asc()).all()

        # 自分が参加済みのルームIDセット
        my_entry_room_ids = {e.room_id for e in Entry.query.filter_by(user_id=current_user.id).all()}

        return render_template(
            "home.html",
            my_groups=my_group_memberships,
            deadline_rooms=deadline_rooms,
            my_entry_room_ids=my_entry_room_ids,
            now=now,
        )

    return app
