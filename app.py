import os
from flask import (
    Flask, request, redirect, url_for, flash, session, jsonify
)
from models import db, User, Service, Booking, Review
from views import (
    render_index_view,
    render_marketplace_view,
    render_service_detail_view,
    render_profile_view,
    render_register_view,
    render_login_view,
    render_dashboard_view,
)


def load_env():
    """Simple .env file loader without external dependencies."""
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k not in os.environ:
                        os.environ[k] = v

load_env()


def create_app():
    app = Flask(
        __name__,
        static_folder=os.path.join(os.path.dirname(__file__), "static")
    )
    app.secret_key = os.environ.get("SECRET_KEY", "skillswap-production-secret-2026")

    # Database configuration (Turso Cloud DB or Local / Serverless SQLite)
    turso_url = os.environ.get("TURSO_DATABASE_URL")
    turso_token = os.environ.get("TURSO_AUTH_TOKEN")
    connected_turso = False

    if turso_url and turso_token:
        try:
            import sqlalchemy_libsql  # noqa: F401
            app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite+{turso_url}/?secure=true"
            app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
                "connect_args": {"auth_token": turso_token}
            }
            connected_turso = True
        except Exception:
            connected_turso = False

    if not connected_turso:
        if os.environ.get("VERCEL"):
            import tempfile
            import shutil
            temp_dir = "/tmp" if os.path.exists("/tmp") else tempfile.gettempdir()
            db_path = os.path.join(temp_dir, "skillswap.db")
            if not os.path.exists(db_path):
                src_db = os.path.join(os.path.dirname(__file__), "instance", "skillswap.db")
                if os.path.exists(src_db):
                    try:
                        shutil.copy(src_db, db_path)
                    except Exception:
                        pass
            app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
        else:
            os.makedirs(app.instance_path, exist_ok=True)
            app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(app.instance_path, 'skillswap.db')}"

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

    @app.after_request
    def add_cache_headers(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    db.init_app(app)

    with app.app_context():
        try:
            db.create_all()
        except Exception:
            pass

    def get_current_user():
        user_id = session.get("user_id")
        return User.query.get(user_id) if user_id else None

    # =========================================================================
    # ROUTES (PURE, CLEAN PYTHON)
    # =========================================================================

    @app.route("/")
    def index():
        featured = Service.query.order_by(Service.id.desc()).limit(6).all()
        return render_index_view(featured, current_user=get_current_user())

    @app.route("/marketplace")
    def marketplace():
        category = request.args.get("category", "").strip()
        search_query = request.args.get("q", "").strip()

        query = Service.query
        if category:
            query = query.filter(Service.category.ilike(category))
        if search_query:
            query = query.filter(
                (Service.title.ilike(f"%{search_query}%")) |
                (Service.description.ilike(f"%{search_query}%"))
            )

        services = query.order_by(Service.id.desc()).all()
        return render_marketplace_view(services, category, search_query, current_user=get_current_user())

    @app.route("/services")
    def api_services():
        """JSON endpoint to retrieve and filter services dynamically."""
        category = request.args.get("category", "").strip()
        search_query = request.args.get("q", "").strip()

        query = Service.query
        if category:
            query = query.filter(Service.category.ilike(category))
        if search_query:
            query = query.filter(
                (Service.title.ilike(f"%{search_query}%")) |
                (Service.description.ilike(f"%{search_query}%"))
            )

        services = query.order_by(Service.id.desc()).all()
        return jsonify([s.to_dict() for s in services])

    @app.route("/service/<int:id>")
    def service_detail(id):
        service = Service.query.get_or_404(id)
        return render_service_detail_view(service, current_user=get_current_user())

    @app.route("/profile/<username>")
    def profile(username):
        user = User.query.filter_by(username=username).first_or_404()
        services = user.services.all()
        return render_profile_view(user, services, current_user=get_current_user())

    # =========================================================================
    # AUTHENTICATION ROUTES
    # =========================================================================

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if session.get("user_id"):
            return redirect(url_for("dashboard"))

        prefill_role = request.args.get("role", "creator")

        if request.method == "POST":
            username = request.form.get("username", "").strip().lower()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            role = request.form.get("role", "creator")
            tagline = request.form.get("tagline", "").strip()
            bio = request.form.get("bio", "").strip()

            if not username or not email or not password:
                flash("Please fill out all required fields.", "error")
                return render_register_view(role=role, prefill_role=prefill_role)

            if User.query.filter_by(username=username).first():
                flash("Username is already taken. Please pick another.", "error")
                return render_register_view(role=role, prefill_role=prefill_role)

            if User.query.filter_by(email=email).first():
                flash("An account with that email already exists.", "error")
                return render_register_view(role=role, prefill_role=prefill_role)

            new_user = User(
                username=username,
                email=email,
                role=role,
                tagline=tagline,
                bio=bio,
                rating=5.0
            )
            new_user.set_password(password)

            db.session.add(new_user)
            db.session.commit()

            session["user_id"] = new_user.id
            flash(f"Welcome to SkillSwap, @{new_user.username}!", "success")
            return redirect(url_for("dashboard"))

        return render_register_view(role=prefill_role, prefill_role=prefill_role)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if session.get("user_id"):
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")

            user = User.query.filter_by(email=email).first()
            if not user or not user.check_password(password):
                flash("Invalid email or password. Please check your credentials.", "error")
                return render_login_view()

            session["user_id"] = user.id
            flash(f"Welcome back, @{user.username}!", "success")
            return redirect(url_for("dashboard"))

        return render_login_view()

    @app.route("/logout")
    def logout():
        session.pop("user_id", None)
        flash("You have been signed out.", "info")
        return redirect(url_for("index"))

    # =========================================================================
    # CREATOR SERVICE MANAGEMENT
    # =========================================================================

    @app.route("/services/new", methods=["POST"])
    def create_service():
        user_id = session.get("user_id")
        if not user_id:
            flash("Please sign in to post a new service.", "error")
            return redirect(url_for("login"))

        user = User.query.get(user_id)
        title = request.form.get("title", "").strip()
        category = request.form.get("category", "Design").strip()
        price_raw = request.form.get("price", "0")
        description = request.form.get("description", "").strip()

        try:
            price = float(price_raw)
        except ValueError:
            price = 500.0

        if not title or not description:
            flash("Service title and description cannot be empty.", "error")
            return redirect(url_for("dashboard"))

        new_service = Service(
            title=title,
            category=category,
            price=price,
            description=description,
            creator_id=user.id
        )
        db.session.add(new_service)
        db.session.commit()

        flash(f"Service '{title}' is now live on the marketplace!", "success")
        return redirect(url_for("dashboard"))

    # =========================================================================
    # BOOKING SYSTEM ROUTES
    # =========================================================================

    @app.route("/book/<int:service_id>", methods=["POST"])
    def book_service(service_id):
        user_id = session.get("user_id")
        if not user_id:
            flash("You must be logged in to book a service.", "error")
            return redirect(url_for("login"))

        service = Service.query.get_or_404(service_id)
        if service.creator_id == user_id:
            flash("You cannot book your own service listing.", "error")
            return redirect(url_for("service_detail", id=service.id))

        notes = request.form.get("notes", "").strip()

        new_booking = Booking(
            service_id=service.id,
            client_id=user_id,
            notes=notes,
            status="pending"
        )
        db.session.add(new_booking)
        db.session.commit()

        flash(f"Booking request sent for '{service.title}'! Track status below.", "success")
        return redirect(url_for("dashboard"))

    @app.route("/booking/<int:id>/status", methods=["POST"])
    def update_booking_status(id):
        user_id = session.get("user_id")
        if not user_id:
            flash("Please sign in to manage bookings.", "error")
            return redirect(url_for("login"))

        booking = Booking.query.get_or_404(id)
        new_status = request.form.get("status", "").strip().lower()

        if booking.service.creator_id != user_id and booking.client_id != user_id:
            flash("Unauthorized action.", "error")
            return redirect(url_for("dashboard"))

        if new_status in ["accepted", "completed", "cancelled"]:
            booking.status = new_status
            db.session.commit()
            flash(f"Booking #{booking.id} status updated to {new_status.capitalize()}.", "success")
        else:
            flash("Invalid booking status.", "error")

        return redirect(url_for("dashboard"))

    # =========================================================================
    # USER DASHBOARD (DUAL VIEW: CREATOR & CLIENT)
    # =========================================================================

    @app.route("/dashboard")
    def dashboard():
        user_id = session.get("user_id")
        if not user_id:
            flash("Please sign in to access your dashboard.", "info")
            return redirect(url_for("login"))

        user = User.query.get(user_id)
        active_view = request.args.get("view", user.role).strip().lower()
        if active_view not in ["creator", "client"]:
            active_view = user.role if user.role in ["creator", "client"] else "creator"

        incoming = Booking.query.join(Service).filter(
            Service.creator_id == user.id
        ).order_by(Booking.id.desc()).all()

        my_bookings = Booking.query.filter_by(client_id=user.id).order_by(Booking.id.desc()).all()
        my_services = Service.query.filter_by(creator_id=user.id).all()

        return render_dashboard_view(
            user=user,
            active_view=active_view,
            incoming_bookings=incoming,
            my_services=my_services,
            my_bookings=my_bookings,
            current_user=user
        )

    return app


# =============================================================================
# DATABASE INITIALIZATION & RUNNER
# =============================================================================

def init_db(app):
    """Initializes SQLite database tables without demo accounts."""
    with app.app_context():
        db.create_all()


# App entry point
app = create_app()

if __name__ == "__main__":
    init_db(app)
    print("\n========================================================")
    print(" [*] SkillSwap is live at http://127.0.0.1:5000")
    print("========================================================\n")
    app.run(debug=True, port=5000)
