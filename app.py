import os
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect, url_for, flash, session, jsonify
)
from models import db, User, Service, Booking, Review

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "skillswap-insecure-hackathon-key-2026")

    # SQLite database configuration
    os.makedirs(app.instance_path, exist_ok=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(app.instance_path, 'skillswap.db')}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    # Inject current logged-in user into templates
    @app.context_processor
    def inject_user():
        user_id = session.get("user_id")
        current_user = User.query.get(user_id) if user_id else None
        return {"current_user": current_user}

    # =========================================================================
    # PUBLIC & MARKETPLACE ROUTES
    # =========================================================================

    @app.route("/")
    def index():
        featured_services = Service.query.order_by(Service.id.desc()).limit(6).all()
        return render_template("index.html", featured_services=featured_services)

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
        return render_template(
            "marketplace.html",
            services=services,
            selected_category=category,
            search_query=search_query
        )

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
        return render_template("service_detail.html", service=service)

    @app.route("/profile/<username>")
    def profile(username):
        user = User.query.filter_by(username=username).first_or_404()
        return render_template("profile.html", user=user)

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
                return render_template("register.html", role=role)

            if User.query.filter_by(username=username).first():
                flash("Username is already taken. Please pick another.", "error")
                return render_template("register.html", role=role)

            if User.query.filter_by(email=email).first():
                flash("An account with that email already exists.", "error")
                return render_template("register.html", role=role)

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

        return render_template("register.html", role=prefill_role)

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
                return render_template("login.html")

            session["user_id"] = user.id
            flash(f"Welcome back, @{user.username}!", "success")
            return redirect(url_for("dashboard"))

        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.pop("user_id", None)
        flash("You have been signed out.", "info")
        return redirect(url_for("index"))

    # =========================================================================
    # CREATOR & SERVICE MANAGEMENT
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
            price = 25.0

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

        booking = Booking(
            service_id=service.id,
            client_id=user_id,
            status="pending"
        )
        db.session.add(booking)
        db.session.commit()

        flash(f"Booking request sent to @{service.creator.username}! Check your dashboard for updates.", "success")
        return redirect(url_for("dashboard"))

    @app.route("/booking/<int:id>/status", methods=["POST"])
    def update_booking_status(id):
        user_id = session.get("user_id")
        if not user_id:
            flash("Please sign in to manage bookings.", "error")
            return redirect(url_for("login"))

        booking = Booking.query.get_or_404(id)
        new_status = request.form.get("status", "").strip().lower()

        # Only the service creator can accept/complete or cancel
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
    # USER DASHBOARD
    # =========================================================================

    @app.route("/dashboard")
    def dashboard():
        user_id = session.get("user_id")
        if not user_id:
            flash("Please sign in to access your dashboard.", "info")
            return redirect(url_for("login"))

        user = User.query.get(user_id)

        # Creator view data: incoming bookings across all services created by user
        incoming_bookings = Booking.query.join(Service).filter(
            Service.creator_id == user.id
        ).order_by(Booking.id.desc()).all()

        my_services = Service.query.filter_by(creator_id=user.id).all()

        # Calculate estimated creator earnings (sum of accepted & completed bookings)
        total_earnings = sum(
            b.service.price for b in incoming_bookings if b.status in ["accepted", "completed"]
        )

        # Client view data: bookings made by this user as a client
        my_bookings = Booking.query.filter_by(client_id=user.id).order_by(Booking.id.desc()).all()

        return render_template(
            "dashboard.html",
            user=user,
            my_services=my_services,
            incoming_bookings=incoming_bookings,
            my_bookings=my_bookings,
            total_earnings=total_earnings
        )

    return app

# =============================================================================
# DATABASE AUTO-SEED FUNCTION
# =============================================================================

def seed_database(app):
    """Populates SQLite with test creators, services, and reviews on first launch."""
    with app.app_context():
        db.create_all()

        if User.query.first() is not None:
            return  # Database already seeded

        print("--> Auto-seeding SkillSwap SQLite database with initial data...")

        # 1. Creators
        aria = User(
            username="aria_design",
            email="aria@skillswap.io",
            role="creator",
            tagline="Brand Identity Designer & Design System Lead",
            bio="Hey! I'm Aria, a 3rd year visual communications student. I design modern brand kits, typography hierarchies, and vector assets that help indie projects stand out.",
            rating=4.9
        )
        aria.set_password("creator123")

        marcus = User(
            username="marcus_edits",
            email="marcus@skillswap.io",
            role="creator",
            tagline="Fast-Paced YouTube, TikTok & Reels Editor",
            bio="Cinematic video editor with 4+ years of Premiere Pro and After Effects experience. I specialize in fast pacing, sound design, and viral retention storytelling.",
            rating=5.0
        )
        marcus.set_password("creator123")

        priya = User(
            username="priya_tutors",
            email="priya@skillswap.io",
            role="creator",
            tagline="Python, Algorithms & Calculus Peer Mentor",
            bio="CS sophomore passionate about making complex programming concepts stick. I break down data structures, recursion, and web basics step-by-step.",
            rating=4.8
        )
        priya.set_password("creator123")

        liam = User(
            username="liam_beats",
            email="liam@skillswap.io",
            role="creator",
            tagline="Audio Engineer & Chill Lo-Fi Producer",
            bio="Music producer crafting royalty-free custom background music, game audio assets, and pristine podcast vocal mix/mastering.",
            rating=4.9
        )
        liam.set_password("creator123")

        # 2. Clients
        jordan = User(
            username="jordan_maker",
            email="jordan@skillswap.io",
            role="client",
            tagline="Indie Hacker & Web App Builder",
            bio="Building bootstrapped SaaS tools and looking for talented creators to partner with on visual branding and promotional videos.",
            rating=5.0
        )
        jordan.set_password("client123")

        sam = User(
            username="sam_green",
            email="sam@skillswap.io",
            role="client",
            tagline="Student Filmmaker & Creator",
            bio="Producing student documentaries and short web series. Constantly searching for original sound tracks and motion graphic titles.",
            rating=5.0
        )
        sam.set_password("client123")

        db.session.add_all([aria, marcus, priya, liam, jordan, sam])
        db.session.commit()

        # 3. Services Across Categories
        s1 = Service(
            title="Minimalist Brand Identity & Logo Suite",
            description="Complete vector logo marks, color palette guide, and typography pairings delivered in Figma, SVG, and high-res PNG. Includes 2 revision rounds and direct handoff.",
            category="Design",
            price=65.0,
            creator_id=aria.id
        )

        s2 = Service(
            title="Modern UI/UX Wireframe & Figma Component Kit",
            description="Turn your product idea into sleek, accessible interface prototypes. Includes component library, mobile & desktop responsive layouts, and interactive click-through.",
            category="Design",
            price=90.0,
            creator_id=aria.id
        )

        s3 = Service(
            title="High-Retention YouTube & Short-Form Reel Editing",
            description="Dynamic cuts, subtitling animations, sound effects, B-roll integration, and pacing optimized to hold audience attention on TikTok, Reels, or YouTube.",
            category="Editing",
            price=45.0,
            creator_id=marcus.id
        )

        s4 = Service(
            title="Podcast Audio Polish & Noise Reduction Master",
            description="Remove background hiss, mouth clicks, and room echo. Balanced EQ, loudness normalization (-16 LUFS), and custom intro/outro placement.",
            category="Editing",
            price=35.0,
            creator_id=marcus.id
        )

        s5 = Service(
            title="1-on-1 Python & Data Structures Crash Course",
            description="60-minute interactive live coding session. We conquer OOP, list comprehensions, recursion, or debug your course projects together.",
            category="Tutoring",
            price=40.0,
            creator_id=priya.id
        )

        s6 = Service(
            title="Calculus & Linear Algebra Problem-Solving Clinic",
            description="No robotic formulas—just intuitive explanations and walkthroughs for derivatives, integrals, matrix transformations, and exam prep.",
            category="Tutoring",
            price=35.0,
            creator_id=priya.id
        )

        s7 = Service(
            title="Custom Chill Lo-Fi & Synthwave Background Beats",
            description="Exclusive, 100% royalty-free instrumental audio for your YouTube videos, game soundtracks, or streaming channel. Includes stem audio files.",
            category="Music",
            price=50.0,
            creator_id=liam.id
        )

        s8 = Service(
            title="Vocal Tuning, Mixing & Stereo Master",
            description="Bring clarity and punch to your vocal recordings. Includes Pitch Correction (Melodyne style), reverb shaping, and master bus compression.",
            category="Music",
            price=55.0,
            creator_id=liam.id
        )

        db.session.add_all([s1, s2, s3, s4, s5, s6, s7, s8])
        db.session.commit()

        # 4. Realistic Reviews
        r1 = Review(
            service_id=s1.id,
            reviewer_id=jordan.id,
            rating=5,
            comment="Aria crushed our brand identity! The color palette and logo variations were ready to ship right away. Super prompt communication."
        )
        r2 = Review(
            service_id=s3.id,
            reviewer_id=sam.id,
            rating=5,
            comment="Marcus cut my documentary trailer down to a gripping 60-second teaser. The sound design timing was spot on."
        )
        r3 = Review(
            service_id=s5.id,
            reviewer_id=jordan.id,
            rating=5,
            comment="Priya helped me understand graph traversal algorithms in 45 minutes when my professor's lecture made zero sense. Highly recommend!"
        )
        r4 = Review(
            service_id=s7.id,
            reviewer_id=sam.id,
            rating=5,
            comment="The lo-fi background track Liam produced fit the mood of my short film flawlessly. Real instrumentation and great warmth."
        )

        # 5. Sample Bookings
        b1 = Booking(
            service_id=s1.id,
            client_id=jordan.id,
            status="completed",
            created_at=datetime.utcnow()
        )
        b2 = Booking(
            service_id=s3.id,
            client_id=sam.id,
            status="accepted",
            created_at=datetime.utcnow()
        )
        b3 = Booking(
            service_id=s7.id,
            client_id=jordan.id,
            status="pending",
            created_at=datetime.utcnow()
        )

        db.session.add_all([r1, r2, r3, r4, b1, b2, b3])
        db.session.commit()
        print("--> Auto-seeding complete! Test accounts and services ready.")


# App entry point
app = create_app()

if __name__ == "__main__":
    seed_database(app)
    print("\n========================================================")
    print(" 🚀 SkillSwap is live at http://127.0.0.1:5000")
    print(" Demo Accounts:")
    print("   Creator: aria@skillswap.io / creator123")
    print("   Creator: marcus@skillswap.io / creator123")
    print("   Client:  jordan@skillswap.io / client123")
    print("========================================================\n")
    app.run(debug=True, port=5000)

