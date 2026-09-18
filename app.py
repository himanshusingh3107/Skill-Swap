import os
from datetime import datetime
from flask import (
    Flask, request, redirect, url_for, flash, session, jsonify, abort
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

    # =========================================================================
    # PURE PYTHON HTML RENDERING HELPERS (ZERO JINJA2)
    # =========================================================================

    def render_navbar(current_user):
        if current_user:
            auth_links = f'''
              <li><a href="/dashboard">Dashboard</a></li>
              <li><a href="/profile/{current_user.username}">Profile</a></li>
              <li><a href="/logout" class="nav-btn">Logout ({current_user.username})</a></li>
            '''
        else:
            auth_links = '''
              <li><a href="/login">Sign In</a></li>
              <li><a href="/register" class="nav-btn">Register</a></li>
            '''
        return f'''
        <header class="navbar-wrapper">
          <nav class="navbar" aria-label="Main Navigation">
            <a href="/" class="brand-link">
              Skill<span>Swap</span>
            </a>
            <ul class="nav-links">
              <li><a href="/">Explore</a></li>
              <li><a href="/marketplace">Marketplace</a></li>
              {auth_links}
            </ul>
          </nav>
        </header>
        '''

    def render_flash():
        messages = session.pop("_flashes", [])
        if not messages:
            return ""
        html = '<div class="flash-container">'
        for category, message in messages:
            cat_class = "danger" if category in ["error", "danger"] else category
            html += f'<div class="alert alert-{cat_class}"><span>{message}</span></div>'
        html += '</div>'
        return html

    def render_service_card(s):
        cat_lower = s.category.lower()
        creator_name = s.creator.username if s.creator else "Creator"
        creator_initial = creator_name[0].upper() if creator_name else "C"
        creator_tagline = s.creator.tagline or "Creator" if s.creator else "Creator"
        price_str = f"{s.price:.0f}"

        return f'''
        <a href="/service/{s.id}" class="service-card">
          <div>
            <div class="service-card-top">
              <span class="badge badge-{cat_lower}">{s.category}</span>
              <span style="font-size: 0.85rem; font-weight: 600; color: #f59e0b;">★ {s.average_rating}</span>
            </div>
            <h3 class="service-title">{s.title}</h3>
            <p class="service-desc">{s.description}</p>
          </div>
          <div class="service-footer">
            <div class="creator-snippet">
              <div class="avatar-circle">{creator_initial}</div>
              <div>
                <div class="creator-name">@{creator_name}</div>
                <div style="font-size: 0.75rem; color: var(--text-muted);">{creator_tagline}</div>
              </div>
            </div>
            <div class="service-price">₹{price_str}</div>
          </div>
        </a>
        '''

    def render_page(filename, replacements=None):
        template_path = os.path.join(os.path.dirname(__file__), "templates", filename)
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()

        user_id = session.get("user_id")
        current_user = User.query.get(user_id) if user_id else None

        content = content.replace("<!-- NAVBAR -->", render_navbar(current_user))
        content = content.replace("<!-- FLASH -->", render_flash())

        if replacements:
            for key, val in replacements.items():
                content = content.replace(f"<!-- {key} -->", str(val))
                content = content.replace(f"{{{{{key}}}}}", str(val))

        return content

    # =========================================================================
    # PUBLIC & MARKETPLACE ROUTES
    # =========================================================================

    @app.route("/")
    def index():
        featured = Service.query.order_by(Service.id.desc()).limit(6).all()
        if featured:
            cards_html = "".join(render_service_card(s) for s in featured)
        else:
            cards_html = '<p style="color: var(--text-muted); grid-column: 1 / -1; text-align: center; padding: 2rem;">No gigs listed yet.</p>'

        return render_page("index.html", {"FEATURED_SERVICES": cards_html})

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

        if services:
            services_html = "".join(render_service_card(s) for s in services)
        else:
            services_html = '''
            <div style="grid-column: 1 / -1; text-align: center; padding: 4rem 1rem; background: var(--surface); border-radius: var(--radius-lg); border: 1px solid var(--border);">
              <h3 style="font-size: 1.25rem; font-weight: 700; margin-bottom: 0.5rem;">No gigs found</h3>
              <p style="color: var(--text-muted); margin-bottom: 1.5rem;">Try tweaking your search term or category filter.</p>
              <a href="/marketplace" class="btn btn-outline-primary btn-sm">Clear Filters</a>
            </div>
            '''

        # Build category pills HTML
        q_param = f"&q={search_query}" if search_query else ""
        all_active = "active" if not category else ""
        des_active = "active" if category.lower() == "design" else ""
        edi_active = "active" if category.lower() == "editing" else ""
        tut_active = "active" if category.lower() == "tutoring" else ""
        mus_active = "active" if category.lower() == "music" else ""

        category_pills_html = f'''
          <a href="/marketplace{('?q=' + search_query) if search_query else ''}" class="pill-btn {all_active}">All Categories</a>
          <a href="/marketplace?category=Design{q_param}" class="pill-btn {des_active}">🎨 Design</a>
          <a href="/marketplace?category=Editing{q_param}" class="pill-btn {edi_active}">🎬 Editing</a>
          <a href="/marketplace?category=Tutoring{q_param}" class="pill-btn {tut_active}">📚 Tutoring</a>
          <a href="/marketplace?category=Music{q_param}" class="pill-btn {mus_active}">🎵 Music</a>
        '''

        hidden_cat = f'<input type="hidden" name="category" value="{category}" />' if category else ""
        clear_btn = f'<a href="/marketplace{("?category=" + category) if category else ""}" class="btn btn-secondary btn-sm" style="border-radius: var(--radius-full); text-decoration: none;">Clear</a>' if search_query else ""

        return render_page("marketplace.html", {
            "SEARCH_QUERY": search_query,
            "HIDDEN_CATEGORY_INPUT": hidden_cat,
            "CLEAR_SEARCH_BTN": clear_btn,
            "CATEGORY_PILLS": category_pills_html,
            "SERVICES_GRID": services_html
        })

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
        user_id = session.get("user_id")

        # Build booking action button
        if user_id:
            if user_id == service.creator_id:
                booking_action = '''
                <div style="background: var(--surface-alt); padding: 0.75rem; border-radius: var(--radius-sm); text-align: center; font-size: 0.85rem; color: var(--text-muted);">
                  This is your own listing
                </div>
                '''
            else:
                booking_action = '''
                <a href="#booking-modal" class="btn btn-primary btn-block" style="text-decoration: none;">
                  Request Service Booking
                </a>
                '''
        else:
            booking_action = '''
            <a href="/login" class="btn btn-primary btn-block">
              Sign In to Book This Service
            </a>
            '''

        # Build reviews HTML
        reviews = service.reviews.all()
        if reviews:
            rev_items = []
            for r in reviews:
                reviewer_name = r.reviewer.username if r.reviewer else "Anonymous"
                reviewer_initial = reviewer_name[0].upper() if reviewer_name else "A"
                stars = "★" * r.rating
                date_str = r.created_at.strftime("%B %d, %Y")
                rev_items.append(f'''
                <div style="padding: 1.25rem 0; border-bottom: 1px solid var(--border);">
                  <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.5rem;">
                    <div style="display: flex; align-items: center; gap: 0.6rem;">
                      <div class="avatar-circle" style="width: 28px; height: 28px; font-size: 0.75rem;">{reviewer_initial}</div>
                      <span style="font-weight: 600; font-size: 0.9rem;">@{reviewer_name}</span>
                    </div>
                    <span style="color: #f59e0b; font-size: 0.85rem; font-weight: 600;">{stars}</span>
                  </div>
                  <p style="color: var(--text-muted); font-size: 0.9rem; line-height: 1.5;">"{r.comment}"</p>
                  <div style="font-size: 0.75rem; color: var(--text-subtle); margin-top: 0.4rem;">{date_str}</div>
                </div>
                ''')
            reviews_html = "".join(rev_items)
        else:
            reviews_html = '<p style="color: var(--text-muted); font-size: 0.9rem; text-align: center; padding: 1.5rem 0;">No reviews yet. Be the first to book and rate this service!</p>'

        creator_name = service.creator.username if service.creator else "Creator"
        creator_bio = service.creator.bio or "Active SkillSwap creator."
        if len(creator_bio) > 140:
            creator_bio = creator_bio[:140] + "..."

        return render_page("service_detail.html", {
            "SERVICE_ID": service.id,
            "SERVICE_TITLE": service.title,
            "SERVICE_DESCRIPTION": service.description,
            "SERVICE_CATEGORY": service.category,
            "SERVICE_CATEGORY_LOWER": service.category.lower(),
            "SERVICE_RATING": service.average_rating,
            "SERVICE_PRICE": f"{service.price:.0f}",
            "REVIEWS_COUNT": len(reviews),
            "REVIEWS_LIST": reviews_html,
            "BOOKING_ACTION": booking_action,
            "CREATOR_USERNAME": creator_name,
            "CREATOR_AVATAR": creator_name[0].upper() if creator_name else "C",
            "CREATOR_TAGLINE": service.creator.tagline or "Active Creator",
            "CREATOR_BIO_SNIPPET": creator_bio
        })

    @app.route("/profile/<username>")
    def profile(username):
        user = User.query.filter_by(username=username).first_or_404()
        services = user.services.all()

        if services:
            gigs_html = "".join(f'''
            <a href="/service/{s.id}" class="service-card">
              <div>
                <div class="service-card-top">
                  <span class="badge badge-{s.category.lower()}">{s.category}</span>
                  <span style="font-size: 0.85rem; font-weight: 600; color: #f59e0b;">★ {s.average_rating}</span>
                </div>
                <h3 class="service-title">{s.title}</h3>
                <p class="service-desc">{s.description}</p>
              </div>
              <div class="service-footer">
                <div class="creator-name">Book Now &rarr;</div>
                <div class="service-price">₹{s.price:.0f}</div>
              </div>
            </a>
            ''' for s in services)

            categories = list(set(s.category for s in services))
            skills_html = "".join(f'<span class="skill-tag">{cat}</span>' for cat in categories)
            skills_html += '<span class="skill-tag">Collaborative Feedback</span><span class="skill-tag">Fast Turnaround</span>'
        else:
            gigs_html = '<p style="color: var(--text-muted); grid-column: 1 / -1; text-align: center; padding: 2rem; background: var(--surface); border-radius: var(--radius-lg);">No active services listed currently.</p>'
            skills_html = '<span class="skill-tag">General Creative</span><span class="skill-tag">Problem Solving</span>'

        return render_page("profile.html", {
            "USER_USERNAME": user.username,
            "USER_AVATAR": user.username[0].upper() if user.username else "U",
            "USER_TAGLINE": user.tagline or "Creative Specialist & Community Member",
            "USER_BIO": user.bio or "This creator has not added a detailed bio yet. Check out their active listings below!",
            "USER_RATING": user.rating,
            "USER_COMPLETED_GIGS": user.completed_gigs_count,
            "USER_SKILLS": skills_html,
            "CREATOR_SERVICES": gigs_html
        })

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
                return render_page("register.html", {
                    "CHECKED_CREATOR": "checked" if role == "creator" else "",
                    "CHECKED_CLIENT": "checked" if role == "client" else ""
                })

            if User.query.filter_by(username=username).first():
                flash("Username is already taken. Please pick another.", "error")
                return render_page("register.html", {
                    "CHECKED_CREATOR": "checked" if role == "creator" else "",
                    "CHECKED_CLIENT": "checked" if role == "client" else ""
                })

            if User.query.filter_by(email=email).first():
                flash("An account with that email already exists.", "error")
                return render_page("register.html", {
                    "CHECKED_CREATOR": "checked" if role == "creator" else "",
                    "CHECKED_CLIENT": "checked" if role == "client" else ""
                })

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

        return render_page("register.html", {
            "CHECKED_CREATOR": "checked" if prefill_role == "creator" else "",
            "CHECKED_CLIENT": "checked" if prefill_role == "client" else ""
        })

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
                return render_page("login.html")

            session["user_id"] = user.id
            flash(f"Welcome back, @{user.username}!", "success")
            return redirect(url_for("dashboard"))

        return render_page("login.html")

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
    # USER DASHBOARD (CREATOR & CLIENT DUAL VIEW)
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

        tab_creator_active = "active" if active_view == "creator" else ""
        tab_client_active = "active" if active_view == "client" else ""

        if active_view == "creator":
            incoming = Booking.query.join(Service).filter(
                Service.creator_id == user.id
            ).order_by(Booking.id.desc()).all()

            my_services = Service.query.filter_by(creator_id=user.id).all()
            total_earnings = sum(b.service.price for b in incoming if b.status in ["accepted", "completed"])

            # Build incoming bookings table rows
            if incoming:
                table_rows = []
                for b in incoming:
                    c_name = b.client.username if b.client else "Client"
                    c_init = c_name[0].upper() if c_name else "C"
                    date_str = b.created_at.strftime("%b %d, %Y")
                    
                    if b.status == "pending":
                        actions = f'''
                        <form action="/booking/{b.id}/status" method="POST" style="display: inline;">
                          <input type="hidden" name="status" value="accepted" />
                          <button type="submit" class="btn btn-primary btn-sm" style="padding: 0.25rem 0.65rem; font-size: 0.75rem;">Accept</button>
                        </form>
                        <form action="/booking/{b.id}/status" method="POST" style="display: inline;">
                          <input type="hidden" name="status" value="cancelled" />
                          <button type="submit" class="btn btn-secondary btn-sm" style="padding: 0.25rem 0.65rem; font-size: 0.75rem;">Decline</button>
                        </form>
                        '''
                    elif b.status == "accepted":
                        actions = f'''
                        <form action="/booking/{b.id}/status" method="POST" style="display: inline;">
                          <input type="hidden" name="status" value="completed" />
                          <button type="submit" class="btn btn-primary btn-sm" style="background: #10b981; border-color: #10b981; padding: 0.25rem 0.65rem; font-size: 0.75rem;">Mark Done</button>
                        </form>
                        '''
                    else:
                        actions = '<span style="color: var(--text-subtle); font-size: 0.8rem;">Completed</span>'

                    table_rows.append(f'''
                    <tr>
                      <td>
                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                          <div class="avatar-circle" style="width: 26px; height: 26px; font-size: 0.75rem;">{c_init}</div>
                          <strong>@{c_name}</strong>
                        </div>
                      </td>
                      <td>{b.service.title}</td>
                      <td><strong>₹{b.service.price:.0f}</strong></td>
                      <td style="color: var(--text-muted); font-size: 0.85rem;">{date_str}</td>
                      <td><span class="status-badge status-{b.status}">{b.status.capitalize()}</span></td>
                      <td>{actions}</td>
                    </tr>
                    ''')
                bookings_tbody = "".join(table_rows)
            else:
                bookings_tbody = '<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 2.5rem;">No incoming booking requests right now.</td></tr>'

            # Build active services grid
            if my_services:
                services_grid = "".join(f'''
                <div class="service-card" style="cursor: default;">
                  <div>
                    <div class="service-card-top">
                      <span class="badge badge-{s.category.lower()}">{s.category}</span>
                      <span style="font-size: 0.85rem; font-weight: 600; color: #f59e0b;">★ {s.average_rating}</span>
                    </div>
                    <h3 class="service-title">{s.title}</h3>
                    <p class="service-desc">{s.description}</p>
                  </div>
                  <div class="service-footer">
                    <a href="/service/{s.id}" style="font-size: 0.85rem; color: var(--primary); text-decoration: none; font-weight: 600;">Preview Listing &rarr;</a>
                    <div class="service-price">₹{s.price:.0f}</div>
                  </div>
                </div>
                ''' for s in my_services)
            else:
                services_grid = '''
                <div style="grid-column: 1 / -1; padding: 2rem; text-align: center; background: var(--surface); border-radius: var(--radius-lg);">
                  <p style="color: var(--text-muted); margin-bottom: 1rem;">You haven't posted any service listings yet.</p>
                  <a href="#new-service-modal" class="btn btn-primary btn-sm">Create Your First Listing</a>
                </div>
                '''

            view_content = f'''
            <section>
              <div class="stats-row" style="margin-bottom: 2.5rem;">
                <div class="stat-item" style="background: var(--surface);">
                  <div class="stat-val">₹{total_earnings:.0f}</div>
                  <div class="stat-lbl">Estimated Earnings</div>
                </div>
                <div class="stat-item" style="background: var(--surface);">
                  <div class="stat-val">{len(incoming)}</div>
                  <div class="stat-lbl">Incoming Requests</div>
                </div>
                <div class="stat-item" style="background: var(--surface);">
                  <div class="stat-val">{len(my_services)}</div>
                  <div class="stat-lbl">Active Listings</div>
                </div>
              </div>

              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
                <h2 style="font-size: 1.35rem; font-weight: 700;">Incoming Service Requests</h2>
                <a href="#new-service-modal" class="btn btn-primary btn-sm">+ Post New Service</a>
              </div>

              <div class="table-card">
                <div class="table-responsive">
                  <table class="data-table">
                    <thead>
                      <tr>
                        <th>Client</th>
                        <th>Service</th>
                        <th>Price</th>
                        <th>Requested Date</th>
                        <th>Status</th>
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {bookings_tbody}
                    </tbody>
                  </table>
                </div>
              </div>

              <h2 style="font-size: 1.35rem; font-weight: 700; margin-bottom: 1rem;">My Active Services</h2>
              <div class="service-grid">
                {services_grid}
              </div>
            </section>
            '''
        else:
            # Client view
            my_bookings = Booking.query.filter_by(client_id=user.id).order_by(Booking.id.desc()).all()
            if my_bookings:
                rows = []
                for b in my_bookings:
                    cr_name = b.service.creator.username if b.service and b.service.creator else "Creator"
                    date_str = b.created_at.strftime("%b %d, %Y")
                    rows.append(f'''
                    <tr>
                      <td><a href="/service/{b.service.id}" style="font-weight: 600; color: var(--text-main); text-decoration: none;">{b.service.title}</a></td>
                      <td><a href="/profile/{cr_name}" style="color: var(--primary); text-decoration: none; font-weight: 500;">@{cr_name}</a></td>
                      <td><span class="badge badge-{b.service.category.lower()}">{b.service.category}</span></td>
                      <td><strong>₹{b.service.price:.0f}</strong></td>
                      <td style="color: var(--text-muted); font-size: 0.85rem;">{date_str}</td>
                      <td><span class="status-badge status-{b.status}">{b.status.capitalize()}</span></td>
                    </tr>
                    ''')
                tbody = "".join(rows)
            else:
                tbody = '''
                <tr>
                  <td colspan="6" style="text-align: center; color: var(--text-muted); padding: 3rem;">
                    You haven't booked any services yet.
                    <div style="margin-top: 1rem;">
                      <a href="/marketplace" class="btn btn-primary btn-sm">Explore Marketplace</a>
                    </div>
                  </td>
                </tr>
                '''

            view_content = f'''
            <section>
              <div style="margin-bottom: 1.5rem;">
                <h2 style="font-size: 1.35rem; font-weight: 700;">My Booked Services</h2>
                <p class="section-desc">Track progress, statuses, and deliveries from creators</p>
              </div>

              <div class="table-card">
                <div class="table-responsive">
                  <table class="data-table">
                    <thead>
                      <tr>
                        <th>Service</th>
                        <th>Creator</th>
                        <th>Category</th>
                        <th>Price</th>
                        <th>Order Date</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {tbody}
                    </tbody>
                  </table>
                </div>
              </div>
            </section>
            '''

        return render_page("dashboard.html", {
            "CURRENT_USERNAME": user.username,
            "CURRENT_ROLE": user.role.capitalize(),
            "TAB_CREATOR_ACTIVE": tab_creator_active,
            "TAB_CLIENT_ACTIVE": tab_client_active,
            "VIEW_CONTENT": view_content
        })

    return app

# =============================================================================
# DATABASE INITIALIZATION
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
    print(" 🚀 SkillSwap is live at http://127.0.0.1:5000")
    print("========================================================\n")
    app.run(debug=True, port=5000)
