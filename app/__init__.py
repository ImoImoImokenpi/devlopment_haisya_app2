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
    from .models import user, room

    # blueprint 登録
    from .auth.routes import auth_bp
    from .rooms.routes import rooms_bp
    from .matching.routes import matching_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(rooms_bp)
    app.register_blueprint(matching_bp)

    @app.route("/")
    def index():
        from flask import render_template
        return render_template("home.html")

    return app
