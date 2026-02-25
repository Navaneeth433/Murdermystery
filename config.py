import os


class Config:
    """Base configuration."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DB_PATH = os.path.join(BASE_DIR, "database.db")

    # Support Render's PostgreSQL (DATABASE_URL) or local SQLite fallback
    _db_url = os.environ.get("DATABASE_URL", "")
    # Render provides postgres://, but SQLAlchemy requires postgresql://
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _db_url if _db_url else f"sqlite:///{DB_PATH}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Server config — DEBUG off by default in production
    HOST  = os.environ.get("FLASK_RUN_HOST", "0.0.0.0")
    PORT  = int(os.environ.get("FLASK_RUN_PORT", "5000"))
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"

    # Admin credentials — always set these via environment variables in prod
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "changeme")


config = Config()
