from datetime import datetime
import json

from flask import (
    Blueprint,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from config import config
from models import Attempt, Content, User, db

admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)


# ---------------- AUTH ---------------- #

def _is_admin_authenticated():
    return bool(session.get("is_admin"))


# ---------------- LOGIN ---------------- #

@admin_bp.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if (
            username == config.ADMIN_USERNAME
            and password == config.ADMIN_PASSWORD
        ):
            session["is_admin"] = True
            return redirect(url_for("admin.dashboard"))

        return render_template(
            "admin/login.html",
            error="Invalid credentials"
        )

    return render_template("admin/login.html")


# ---------------- LOGOUT ---------------- #

@admin_bp.route("/logout")
def logout():
    session.pop("is_admin", None)
    return redirect(url_for("admin.login"))


# ---------------- DASHBOARD ---------------- #

@admin_bp.route("/dashboard")
def dashboard():

    if not _is_admin_authenticated():
        return redirect(url_for("admin.login"))

    contents = Content.query.order_by(
        Content.chapter_number.asc()
    ).all()

    # ✅ FIXED leaderboard query
    total_score_label = db.func.coalesce(
        db.func.sum(Attempt.score), 0
    ).label("total_score")

    leaderboard_rows = (
        db.session.query(
            User.name,
            User.email,
            total_score_label,
        )
        .outerjoin(Attempt, Attempt.user_id == User.id)
        .group_by(User.id, User.name, User.email)
        .order_by(db.desc("total_score"))
        .all()
    )

    leaderboard = [
        {
            "name": row[0],
            "email": row[1],
            "total_score": float(row[2] or 0),
        }
        for row in leaderboard_rows
    ]

    return render_template(
        "admin/dashboard.html",
        contents=contents,
        leaderboard=leaderboard,
    )


# ---------------- CREATE CONTENT ---------------- #

@admin_bp.route(
    "/create-content",
    methods=["GET", "POST"]
)
def create_content():

    if not _is_admin_authenticated():
        return redirect(url_for("admin.login"))

    if request.method == "POST":

        title = request.form.get("title", "").strip()
        chapter_number = request.form.get("chapter_number", "1").strip()
        raw_panels = request.form.get("panels_json", "").strip()

        error = None

        if not title:
            error = "Title required."

        time_limit_int = 0  # Time limit removed — not used for scoring

        try:
            chapter_number_int = int(chapter_number)
        except ValueError:
            chapter_number_int = 1

        if error:
            return render_template(
                "admin/create_content.html",
                error=error,
            )

        # Robust parser: handles plain URL lists AND pasted raw JSON blobs
        import re as _re
        _URL_RE = _re.compile(r'https?://[^\s\'"\\,\]}\)]+')
        panels_list = []
        if raw_panels:
            # First: try to parse as a JSON object with a "panels" key
            try:
                _data = json.loads(raw_panels)
                if isinstance(_data, dict) and "panels" in _data:
                    panels_list = [u.strip().rstrip('\\/\'" \t') for u in _data["panels"] if isinstance(u, str) and u.startswith("http")]
                elif isinstance(_data, list):
                    panels_list = [u.strip().rstrip('\\/\'" \t') for u in _data if isinstance(u, str) and u.startswith("http")]
            except (json.JSONDecodeError, ValueError):
                pass

            # Second: if no URLs found yet, use regex to extract all http(s) URLs
            if not panels_list:
                panels_list = _URL_RE.findall(raw_panels)
                panels_list = [u.rstrip('\\/\'" \t,') for u in panels_list]

            # Filter out any empty or non-http strings
            panels_list = [u for u in panels_list if u.startswith("http")]

        panels_json_string = None
        if panels_list:
            panels_json_string = json.dumps({"panels": panels_list})

        content = Content(
            title=title,
            time_limit=time_limit_int,
            chapter_number=chapter_number_int,
            is_unlocked=True,
            panels_json=panels_json_string,
        )

        db.session.add(content)
        db.session.commit()

        return redirect(url_for("admin.dashboard"))

    return render_template("admin/create_content.html")


# ---------------- TOGGLE ---------------- #

@admin_bp.route("/toggle/<int:content_id>", methods=["POST"])
def toggle_content(content_id):

    if not _is_admin_authenticated():
        return redirect(url_for("admin.login"))

    content = Content.query.get_or_404(content_id)

    content.is_unlocked = not content.is_unlocked
    db.session.commit()

    return redirect(url_for("admin.dashboard"))


# ---------------- DELETE ---------------- #

@admin_bp.route("/delete/<int:content_id>", methods=["POST"])
def delete_content(content_id):
    if not _is_admin_authenticated():
        return redirect(url_for("admin.login"))

    content = Content.query.get_or_404(content_id)

    # First delete any attempts on this content so foreign key constraints don't break
    Attempt.query.filter_by(content_id=content_id).delete()
    
    # Then delete the content itself
    db.session.delete(content)
    db.session.commit()

    return redirect(url_for("admin.dashboard"))



# ---------------- ATTEMPTS ---------------- #

@admin_bp.route("/attempts")
def attempts():

    if not _is_admin_authenticated():
        return redirect(url_for("admin.login"))

    attempts = (
        db.session.query(
            Attempt,
            User,
            Content,
        )
        .join(User, Attempt.user_id == User.id)
        .join(Content, Attempt.content_id == Content.id)
        .order_by(Attempt.start_time.desc())
        .limit(500)
        .all()
    )

    return render_template(
        "admin/attempts.html",
        attempts=attempts,
    )