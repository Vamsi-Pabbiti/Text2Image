import os
import logging
import threading
import uuid
from datetime import datetime

from flask import (Flask, render_template, request,
                   jsonify, redirect, url_for, flash)
from flask_login import (LoginManager, login_user, logout_user,
                         login_required, current_user)

from config import Config
from models import db, bcrypt, User, GeneratedImage
from services import MODELS, get_model_ids, generate_image, save_image

# ── App setup ────────────────────────────────────────────────────
app = Flask(__name__)
app.config.from_object(Config)

os.makedirs(app.config["IMAGE_FOLDER"], exist_ok=True)
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ── Extensions ───────────────────────────────────────────────────
db.init_app(app)
bcrypt.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view         = "login"
login_manager.login_message      = "Please log in to generate images."
login_manager.login_message_category = "error"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ── Task store (in-memory, thread-safe) ──────────────────────────
task_store = {}
task_lock  = threading.Lock()

# ── Background generation ────────────────────────────────────────
def run_generation(task_id, user_id, prompt, negative_prompt,
                   model_id, aspect, steps, guidance, seed):
    with app.app_context():
        try:
            with task_lock:
                task_store[task_id] = {"status": "running"}

            api_key = ""
image = generate_image(api_key, prompt, negative_prompt,
                       model_id, aspect, steps, guidance, seed)
            filename = save_image(image, user_id, app.config["IMAGE_FOLDER"])

            record = GeneratedImage(
                user_id         = user_id,
                filename        = filename,
                prompt          = prompt,
                negative_prompt = negative_prompt or "",
                model           = model_id,
                aspect_ratio    = aspect,
            )
            db.session.add(record)
            db.session.commit()

            with task_lock:
                task_store[task_id] = {"status": "done", "image_id": record.id}

            logger.info(f"Task {task_id} done → {filename}")

        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            with task_lock:
                task_store[task_id] = {"status": "error", "error": str(e)}


# ── Routes ───────────────────────────────────────────────────────

@app.route("/")
def index():
    history = []
    if current_user.is_authenticated:
        history = [img.to_dict() for img in
                   GeneratedImage.query
                   .filter_by(user_id=current_user.id)
                   .order_by(GeneratedImage.created_at.desc())
                   .limit(12)]
    return render_template("index.html", history=history, models=MODELS)


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm_password", "")

        if not all([username, email, password]):
            flash("All fields are required.", "error")
        elif password != confirm:
            flash("Passwords do not match.", "error")
        elif len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
        elif User.query.filter_by(username=username).first():
            flash("Username already taken.", "error")
        elif User.query.filter_by(email=email).first():
            flash("Email already registered.", "error")
        else:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Welcome to Text2Image! 🎨", "success")
            return redirect(url_for("index"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user     = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user, remember=bool(request.form.get("remember")))
            return redirect(request.args.get("next") or url_for("index"))

        flash("Invalid email or password.", "error")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/gallery")
@login_required
def gallery():
    page        = request.args.get("page", 1, type=int)
    filter_type = request.args.get("filter", "all")
    query       = GeneratedImage.query.filter_by(user_id=current_user.id)
    if filter_type == "favorites":
        query = query.filter_by(is_favorite=True)
    images = query.order_by(GeneratedImage.created_at.desc()).paginate(page=page, per_page=20)
    return render_template("gallery.html", images=images, filter=filter_type)


@app.route("/generate", methods=["POST"])
@login_required
def generate():
    try:
        prompt = request.form.get("prompt", "").strip()
        if not prompt:
            return jsonify({"error": "Please enter a prompt."})
        if len(prompt) > app.config["MAX_PROMPT_LEN"]:
            return jsonify({"error": "Prompt too long (max 1000 chars)."})

        model_id = request.form.get("model", MODELS[0]["id"])
        if model_id not in get_model_ids():
            model_id = MODELS[0]["id"]

        aspect          = request.form.get("aspect_ratio", "square")
        negative_prompt = request.form.get("negative_prompt", "").strip()

        try:
            steps    = max(20, min(50, int(request.form.get("steps", 30))))
            guidance = max(1.0, min(20.0, float(request.form.get("guidance", 7.5))))
            seed_raw = request.form.get("seed", "").strip()
            seed     = int(seed_raw) if seed_raw else None
        except ValueError:
            return jsonify({"error": "Invalid steps, guidance, or seed."})

        task_id = str(uuid.uuid4())
        with task_lock:
            task_store[task_id] = {"status": "pending"}

        thread = threading.Thread(
            target=run_generation,
            args=(task_id, current_user.id, prompt, negative_prompt,
                  model_id, aspect, steps, guidance, seed),
            daemon=True
        )
        thread.start()

        logger.info(f"Task {task_id} started for user {current_user.id}")
        return jsonify({"task_id": task_id})

    except Exception as e:
        logger.error(f"Generate error: {e}")
        return jsonify({"error": str(e)})


@app.route("/task/<task_id>")
@login_required
def task_status(task_id):
    with task_lock:
        task = task_store.get(task_id)

    if not task:
        return jsonify({"status": "pending"})

    if task["status"] == "done":
        img = GeneratedImage.query.get(task["image_id"])
        if img:
            return jsonify({"status": "done", "image": img.to_dict()})
        return jsonify({"status": "error", "error": "Image not found in DB."})

    if task["status"] == "error":
        return jsonify({"status": "error", "error": task["error"]})

    return jsonify({"status": task["status"]})


@app.route("/image/<int:image_id>/favorite", methods=["POST"])
@login_required
def toggle_favorite(image_id):
    img = GeneratedImage.query.filter_by(
        id=image_id, user_id=current_user.id).first_or_404()
    img.is_favorite = not img.is_favorite
    db.session.commit()
    return jsonify({"is_favorite": img.is_favorite})


@app.route("/image/<int:image_id>/delete", methods=["POST"])
@login_required
def delete_image(image_id):
    img  = GeneratedImage.query.filter_by(
        id=image_id, user_id=current_user.id).first_or_404()
    path = os.path.join(app.config["IMAGE_FOLDER"], img.filename)
    if os.path.exists(path):
        os.remove(path)
    db.session.delete(img)
    db.session.commit()
    return jsonify({"success": True})


# ── Init DB & run ────────────────────────────────────────────────
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)