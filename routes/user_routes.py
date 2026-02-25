import json
from datetime import datetime

from flask import (
    Blueprint,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from models import Attempt, Content, User, db
from utils.chapter_config import (
    get_visible_contents_for_user,
    can_access_content,
)
from utils.score_calculator import calculate_score

user_bp = Blueprint("user", __name__)


# ---------------- INDEX ---------------- #

@user_bp.route("/")
def home():
    """Landing page with video background. No login required."""
    return render_template("home.html")


# ---------------- CHAPTERS (was INDEX) ---------------- #

@user_bp.route("/chapters")
def index():

    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("user.register"))

    from types import SimpleNamespace
    from models import HIDDEN_CHAPTERS, CHAPTER_REVEAL_TRIGGER

    real_contents, chapters_revealed = (
        get_visible_contents_for_user(user_id)
    )

    # Build a lookup: chapter_number -> real Content object
    real_by_num = {c.chapter_number: c for c in real_contents}

    # Slots 1-6: always displayed (real or placeholder)
    contents = []
    for num in range(1, 7):
        if num in real_by_num:
            contents.append(real_by_num[num])
        else:
            # Locked placeholder — no DB row yet
            contents.append(SimpleNamespace(
                id=None,
                chapter_number=num,
                title="Classified",
                accessible=False,
                is_placeholder=True,
                chapter_number_for_template=num,
            ))

    # Slots 7-8: only shown after chapter 6 is completed
    if chapters_revealed:
        for num in HIDDEN_CHAPTERS:
            if num in real_by_num:
                contents.append(real_by_num[num])
            else:
                contents.append(SimpleNamespace(
                    id=None,
                    chapter_number=num,
                    title="Classified",
                    accessible=False,
                    is_placeholder=True,
                ))

    leaderboard_rows = (
        db.session.query(
            User.id,
            User.name,
            User.email,
            db.func.coalesce(
                db.func.sum(Attempt.score), 0
            ).label("total_score"),
        )
        .outerjoin(Attempt)
        .group_by(User.id, User.name, User.email)
        .order_by(db.desc("total_score"))
        .limit(100)
        .all()
    )

    leaderboard = [
        {
            "user_id": r[0],
            "name": r[1],
            "email": r[2],
            "total_score": float(r[3] or 0),
        }
        for r in leaderboard_rows
    ]

    return render_template(
        "index.html",
        contents=contents,
        leaderboard=leaderboard,
        chapters_revealed=chapters_revealed,
    )


# ---------------- LOGIN & LOGOUT ---------------- #

@user_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()

        if not email:
            return render_template("login.html", error="Email required.")

        user = User.query.filter_by(email=email).first()

        if not user:
            return render_template(
                "login.html",
                error="Identity not found. Unauthorized.",
                email=email,
            )

        session["user_id"] = user.id
        session["user_name"] = user.name
        session["user_email"] = user.email

        return redirect(url_for("user.index"))

    return render_template("login.html")


@user_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("user.login"))


# ---------------- REGISTER ---------------- #

@user_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()

        if not name or not email:
            return render_template(
                "register.html",
                error="Name and email required.",
                name=name,
                email=email,
            )

        user = User.query.filter_by(email=email).first()

        if user:
            return render_template(
                "register.html",
                error="Identity already registered. Proceed to Login.",
                name=name,
                email=email,
            )

        user = User(name=name, email=email)
        db.session.add(user)
        db.session.commit()

        session["user_id"] = user.id
        session["user_name"] = user.name
        session["user_email"] = user.email

        return redirect(url_for("user.index"))

    return render_template("register.html")


# ---------------- START ---------------- #

@user_bp.route("/start/<int:content_id>", methods=["POST"])
def start_challenge(content_id):

    if "user_id" not in session:
        return jsonify({"ok": False}), 401

    user_id = session["user_id"]

    content = Content.query.get_or_404(content_id)

    if not can_access_content(user_id, content_id):
        return jsonify({"ok": False, "error": "Locked"}), 403

    existing = Attempt.query.filter_by(
        user_id=user_id,
        content_id=content_id,
    ).first()

    if existing:
        return jsonify({"ok": False, "error": "Exists"}), 403

    attempt = Attempt(
        user_id=user_id,
        content_id=content_id,
        start_time=datetime.utcnow(),
    )

    db.session.add(attempt)
    db.session.commit()

    return jsonify(
        {
            "ok": True,
            "attempt_id": attempt.id,
            "time_limit": content.time_limit,
        }
    )


# ---------------- CONTENT PAGE ---------------- #

@user_bp.route("/content/<int:content_id>")
def content_page(content_id):

    is_preview = request.args.get("preview") == "1"
    is_admin = session.get("is_admin")

    if is_preview and is_admin:
        # Admin Preview Bypass
        content = Content.query.get_or_404(content_id)
        attempted = False
    else:
        # Normal User Flow
        if "user_id" not in session:
            return redirect(url_for("user.register"))

        user_id = session["user_id"]
        content = Content.query.get_or_404(content_id)

        if not can_access_content(user_id, content_id):
            return "Locked", 403

        existing = Attempt.query.filter_by(
            user_id=user_id,
            content_id=content_id,
        ).first()

        attempted = existing is not None

    panels = []

    if content.panels_json:
        try:
            data = json.loads(content.panels_json)
            panels = data.get("panels", [])
        except Exception:
            panels = []

    return render_template(
        "content.html",
        content=content,
        attempted=attempted,
        panels=panels,
        is_preview=(is_preview and is_admin),
    )


# ---------------- SUBMIT ---------------- #


@user_bp.route("/api/me")
def api_me():
    if "user_id" not in session:
        return jsonify({"authenticated": False})

    return jsonify({
        "authenticated": True,
        "user": {
            "id": session["user_id"],
            "name": session.get("user_name"),
            "email": session.get("user_email"),
        },
    })

@user_bp.route("/submit/<int:content_id>", methods=["POST"])
def submit_result(content_id):

    if "user_id" not in session:
        return jsonify({"ok": False}), 401

    user_id = session["user_id"]

    content = Content.query.get_or_404(content_id)

    # ✅ Access validation added
    if not can_access_content(user_id, content_id):
        return jsonify({"ok": False, "error": "Locked"}), 403

    attempt = Attempt.query.filter_by(
        user_id=user_id,
        content_id=content_id,
    ).first()

    if not attempt:
        return jsonify({"ok": False}), 400

    if attempt.completed:
        return jsonify({"ok": False}), 400

    data = request.get_json() or {}
    completed = bool(data.get("completed"))

    end_time = datetime.utcnow()

    time_taken = int(
        (end_time - attempt.start_time).total_seconds()
    )

    attempt.end_time = end_time
    attempt.time_taken = time_taken
    attempt.completed = completed
    attempt.score = calculate_score(
        time_taken,
        content.time_limit,
        completed,
    )

    db.session.commit()

    revealed = (
        completed
        and content.chapter_number == 6
    )

    return jsonify(
        {
            "ok": True,
            "score": attempt.score,
            "revealed": revealed,
        }
    )