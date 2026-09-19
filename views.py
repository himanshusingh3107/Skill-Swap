import os
from flask import session

# Path to HTML templates directory
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")


def render_page(filename, replacements=None, current_user=None):
    """Loads an HTML template and applies dynamic data replacements."""
    template_path = os.path.join(TEMPLATES_DIR, filename)
    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()

    content = content.replace("<!-- NAVBAR -->", render_navbar(current_user))
    content = content.replace("<!-- FLASH -->", render_flash())

    if replacements:
        for key, val in replacements.items():
            content = content.replace(f"<!-- {key} -->", str(val))
            content = content.replace(f"{{{{{key}}}}}", str(val))

    return content


def render_navbar(current_user):
    """Generates the clean responsive navigation bar."""
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
    """Renders temporary flash alerts (success, error, info)."""
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
    """Builds a single service card preview."""
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


# =============================================================================
# HIGH-LEVEL VIEW RENDERING FUNCTIONS (CALLED BY APP.PY)
# =============================================================================

def render_index_view(featured_services, current_user=None):
    """Renders the landing page with top gigs."""
    if featured_services:
        cards_html = "".join(render_service_card(s) for s in featured_services)
    else:
        cards_html = '<p style="color: var(--text-muted); grid-column: 1 / -1; text-align: center; padding: 2rem;">No gigs listed yet.</p>'

    return render_page("index.html", {"FEATURED_SERVICES": cards_html}, current_user)


def render_marketplace_view(services, category, search_query, current_user=None):
    """Renders the full marketplace catalog with filters."""
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
    }, current_user)


def render_service_detail_view(service, current_user=None):
    """Renders the single gig page with reviews and booking modal."""
    user_id = current_user.id if current_user else None

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
    }, current_user)


def render_profile_view(user, services, current_user=None):
    """Renders the creator profile page."""
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
    }, current_user)


def render_register_view(role="creator", prefill_role="creator", current_user=None):
    """Renders the sign up page."""
    active_role = role or prefill_role
    return render_page("register.html", {
        "CHECKED_CREATOR": "checked" if active_role == "creator" else "",
        "CHECKED_CLIENT": "checked" if active_role == "client" else ""
    }, current_user)


def render_login_view(current_user=None):
    """Renders the sign in page."""
    return render_page("login.html", current_user=current_user)


def render_dashboard_view(user, active_view, incoming_bookings, my_services, my_bookings, current_user=None):
    """Renders the dual-hub dashboard (Creator View vs Client View)."""
    tab_creator_active = "active" if active_view == "creator" else ""
    tab_client_active = "active" if active_view == "client" else ""

    if active_view == "creator":
        total_earnings = sum(b.service.price for b in incoming_bookings if b.status in ["accepted", "completed"])

        if incoming_bookings:
            table_rows = []
            for b in incoming_bookings:
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
              <div class="stat-val">{len(incoming_bookings)}</div>
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
    }, current_user)

