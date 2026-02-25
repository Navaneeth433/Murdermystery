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

    db.init_app(app)
    Migrate(app, db)

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