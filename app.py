"""
app.py
------
Main Flask application entry point for Gruha Alankara.

Run with:  python app.py
Then open: http://127.0.0.1:5000
"""

import os
import json
import uuid
from functools import wraps

from flask import (
    Flask, render_template, request, jsonify, redirect, url_for,
    flash, session, send_from_directory
)
from werkzeug.utils import secure_filename

from config import Config
from database.db import init_db
from models import User, Design, Furniture, Booking
from agents.interior_agent import InteriorDesignAgent
from tools.style_suggester import StyleSuggester

# ----------------------------------------------------------------------
# App initialisation
# ----------------------------------------------------------------------
app = Flask(__name__)
app.config.from_object(Config)

# Ensure required directories exist before the first request
for required_dir in [app.config["UPLOAD_FOLDER"], os.path.dirname(app.config["DATABASE_PATH"])]:
    os.makedirs(required_dir, exist_ok=True)

init_db(app)

agent = InteriorDesignAgent()


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]
    )


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def current_user():
    if "user_id" in session:
        return User.find_by_id(session["user_id"])
    return None


@app.context_processor
def inject_globals():
    return {"current_user": current_user()}


# ----------------------------------------------------------------------
# Public pages
# ----------------------------------------------------------------------
@app.route("/")
def index():
    styles = StyleSuggester().list_styles()
    return render_template("index.html", styles=styles)


# ----------------------------------------------------------------------
# Authentication
# ----------------------------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not username or not email or not password:
            flash("All fields are required.", "error")
            return redirect(url_for("register"))

        if User.find_by_email(email):
            flash("An account with that email already exists.", "error")
            return redirect(url_for("register"))

        if User.find_by_username(username):
            flash("That username is taken.", "error")
            return redirect(url_for("register"))

        user_id = User.create(username, email, password)
        session["user_id"] = user_id
        flash("Welcome to Gruha Alankara!", "success")
        return redirect(url_for("index"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.find_by_email(email)
        if user is None or not User.verify_password(user, password):
            flash("Invalid email or password.", "error")
            return redirect(url_for("login"))

        session["user_id"] = user["id"]
        flash(f"Welcome back, {user['username']}!", "success")
        return redirect(url_for("index"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))


# ----------------------------------------------------------------------
# Room analysis
# ----------------------------------------------------------------------
@app.route("/analyze")
@login_required
def analyze_page():
    return render_template("analyze.html")


@app.route("/api/analyze", methods=["POST"])
@login_required
def api_analyze():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]
    room_type = request.form.get("room_type", "living room")

    if file.filename == "" or not allowed_file(file.filename):
        return jsonify({"error": "Invalid or missing image file"}), 400

    filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    try:
        analysis = agent.room_analyzer.analyze(filepath, room_type)
    except Exception as exc:  # pragma: no cover - defensive
        return jsonify({"error": f"Analysis failed: {exc}"}), 500

    return jsonify({
        "analysis": analysis,
        "image_url": url_for("uploaded_file", filename=filename),
        "image_path": filepath,
    })


# ----------------------------------------------------------------------
# Design Studio
# ----------------------------------------------------------------------
@app.route("/design")
@login_required
def design_studio():
    styles = StyleSuggester().list_styles()
    return render_template("design.html", styles=styles)


@app.route("/api/generate-design", methods=["POST"])
@login_required
def api_generate_design():
    data = request.get_json(force=True)

    image_path = data.get("image_path")
    room_type = data.get("room_type", "living room")
    style_theme = data.get("style_theme", "Modern Minimalist")
    budget = float(data.get("budget", 5000))
    analysis_data = data.get("analysis")

    try:
        result = agent.generate_design(
            image_path=image_path,
            room_type=room_type,
            style_theme=style_theme,
            budget=budget,
            analysis_data=analysis_data,
        )
    except Exception as exc:  # pragma: no cover - defensive
        return jsonify({"error": f"Design generation failed: {exc}"}), 500

    return jsonify(result)


@app.route("/api/save-design", methods=["POST"])
@login_required
def api_save_design():
    data = request.get_json(force=True)
    try:
        design_id = agent.save_design(
            user_id=session["user_id"],
            room_type=data.get("room_type", "living room"),
            style_theme=data.get("style_theme", "Modern Minimalist"),
            budget=float(data.get("budget", 5000)),
            image_path=data.get("image_path"),
            result=data.get("result"),
        )
    except Exception as exc:  # pragma: no cover - defensive
        return jsonify({"error": f"Could not save design: {exc}"}), 500

    return jsonify({"design_id": design_id})


# ----------------------------------------------------------------------
# AR / Live camera views
# ----------------------------------------------------------------------
@app.route("/ar-viewer/<int:design_id>")
@login_required
def ar_viewer(design_id):
    design = Design.find_by_id(design_id)
    if design is None or design["user_id"] != session["user_id"]:
        flash("Design not found.", "error")
        return redirect(url_for("catalog"))
    furniture = Furniture.find_by_design(design_id)
    return render_template("ar_viewer.html", design=design, furniture=furniture)


@app.route("/live-ar-camera")
@login_required
def live_ar_camera():
    return render_template("live_ar_camera.html")


# ----------------------------------------------------------------------
# Voice assistant / booking agent
# ----------------------------------------------------------------------
@app.route("/api/agent/chat", methods=["POST"])
@login_required
def api_agent_chat():
    data = request.get_json(force=True)
    text = data.get("text", "")
    language = data.get("language", "en")
    design_id = data.get("design_id")

    result = agent.handle_message(design_id, text, language)
    return jsonify(result)


@app.route("/api/bookings/<int:design_id>")
@login_required
def api_list_bookings(design_id):
    bookings = Booking.find_by_design(design_id)
    return jsonify([dict(b) for b in bookings])


# ----------------------------------------------------------------------
# Catalog
# ----------------------------------------------------------------------
@app.route("/catalog")
@login_required
def catalog():
    style = request.args.get("style", "all")
    room_type = request.args.get("room_type", "all")
    sort = request.args.get("sort", "newest")

    designs = Design.find_by_user(
        session["user_id"], style=style, room_type=room_type, order_by=sort
    )
    parsed = []
    for d in designs:
        design_dict = dict(d)
        try:
            design_dict["design_data"] = json.loads(d["design_data"]) if d["design_data"] else {}
        except (TypeError, ValueError):
            design_dict["design_data"] = {}
        parsed.append(design_dict)

    return render_template("catalog.html", designs=parsed)


@app.route("/catalog/<int:design_id>/delete", methods=["POST"])
@login_required
def delete_design(design_id):
    Design.delete(design_id, session["user_id"])
    flash("Design removed from catalog.", "success")
    return redirect(url_for("catalog"))


@app.route("/catalog/<int:design_id>/duplicate", methods=["POST"])
@login_required
def duplicate_design(design_id):
    design = Design.find_by_id(design_id)
    if design is None or design["user_id"] != session["user_id"]:
        flash("Design not found.", "error")
        return redirect(url_for("catalog"))

    new_id = Design.create(
        user_id=session["user_id"],
        room_type=design["room_type"],
        style=design["style"],
        budget=design["budget"],
        image_path=design["image_path"],
        analysis_data=json.loads(design["analysis_data"]) if design["analysis_data"] else None,
        design_data=json.loads(design["design_data"]) if design["design_data"] else None,
    )
    furniture_items = Furniture.find_by_design(design_id)
    if furniture_items:
        Furniture.bulk_create(new_id, [dict(f) for f in furniture_items])

    flash("Design duplicated.", "success")
    return redirect(url_for("catalog"))


# ----------------------------------------------------------------------
# Static uploads
# ----------------------------------------------------------------------
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == "__main__":
    # debug=True enables auto-reload during development.
    # host="0.0.0.0" makes it reachable on your local network (e.g. from a
    # phone browser, useful for testing camera/AR features on mobile).
    app.run(host="0.0.0.0", port=5000, debug=True)
