from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Chapter reveal config
CHAPTER_REVEAL_TRIGGER = 6
HIDDEN_CHAPTERS = (7, 8)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    attempts = db.relationship(
        "Attempt",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User {self.id} {self.email}>"



class Content(db.Model):
    __tablename__ = "contents"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    time_limit = db.Column(db.Integer, nullable=False)
    is_unlocked = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    chapter_number = db.Column(db.Integer, default=1, nullable=False)
    unlock_time = db.Column(db.DateTime, nullable=True)
    requires_previous_completion = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    panels_json = db.Column(db.Text, nullable=True)

    attempts = db.relationship(
        "Attempt",
        back_populates="content",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Content {self.id} {self.title}>"



class Attempt(db.Model):
    __tablename__ = "attempts"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    content_id = db.Column(
        db.Integer,
        db.ForeignKey("contents.id"),
        nullable=False
    )

    start_time = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    end_time = db.Column(db.DateTime, nullable=True)
    time_taken = db.Column(db.Integer, nullable=True)
    completed = db.Column(db.Boolean, default=False, nullable=False)
    score = db.Column(db.Float, nullable=True)

    # ✅ Prevent duplicate attempts exploit
    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "content_id",
            name="unique_user_content_attempt"
        ),
    )

    user = db.relationship("User", back_populates="attempts")
    content = db.relationship("Content", back_populates="attempts")

    def __repr__(self):
        return f"<Attempt user={self.user_id} content={self.content_id}>"