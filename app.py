from flask import Flask
from flask_migrate import Migrate

from config import config
from models import db
from routes.admin_routes import admin_bp
from routes.user_routes import user_bp


def create_app() -> Flask:
    app = Flask(__name__)

    app.config["SECRET_KEY"] = config.SECRET_KEY
    app.config["SQLALCHEMY_DATABASE_URI"] = config.SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = config.SQLALCHEMY_ENGINE_OPTIONS

    db.init_app(app)
    Migrate(app, db)

    # ✅ Always ensure tables exist (safe no-op if they already do)
    with app.app_context():
        db.create_all()

    # ── Inject current user's total score into every template ──────────────
    @app.context_processor
    def inject_user_score():
        from flask import session as _session
        from models import Attempt as _Attempt, db as _db
        user_id = _session.get("user_id")
        if user_id:
            total = (
                _db.session.query(
                    _db.func.coalesce(_db.func.sum(_Attempt.score), 0)
                )
                .filter(_Attempt.user_id == user_id)
                .scalar()
            )
            return {"user_total_score": int(total or 0)}
        return {"user_total_score": None}

    # ✅ Register blueprints ONLY
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )