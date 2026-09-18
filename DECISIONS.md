# Architectural Decision Records (ADR) — SkillSwap

This document details three critical architectural decisions made during the design and implementation of **SkillSwap**, outlining the context, considered alternatives, chosen solution, and trade-offs.

---

## Decision 1: Lightweight Monolithic Flask + SQLite over Decoupled SPA & Microservices

### Context & Problem Statement
SkillSwap was engineered for rapid iteration, instant local setup, and zero-latency performance during the Code2Career hackathon. Modern web apps frequently default to decoupled single-page application (SPA) architectures (e.g., React/Next.js frontend with FastAPI/Node backend and PostgreSQL). However, this introduces substantial operational overhead:
* Multi-process dev environments (`npm run dev` + Python API server).
* Complex state hydration, CORS configurations, and dual authentication synchronization.
* External database setup (Docker/local Postgres service).

### Considered Options
1. **Decoupled SPA + REST API:** React/Vite frontend with an asynchronous backend API.
2. **Server-Side Rendered (SSR) Monolith:** Python 3 + Flask + Flask-SQLAlchemy with SQLite in `instance/`.

### Decision & Rationale
We chose **Option 2: SSR Monolith with Flask and SQLite**.
* **Zero Barrier to Entry:** Anyone can clone the repository and run `python app.py` immediately without configuring external database services or installing hundreds of megabytes of `node_modules`.
* **Atomic Transactions & Fast Queries:** SQLite delivers sub-millisecond local reads and writes for small-to-medium datasets without network round-trips.
* **Jinja2 Context Simplicity:** Eliminates JSON API boilerplate and token handshake synchronization by maintaining secure, native HTTP-only cookie sessions.

### Trade-offs & Mitigation
* *Trade-off:* Monolithic SQLite is not naturally horizontally scalable across distributed cloud pods.
* *Mitigation:* The database layer is encapsulated cleanly inside SQLAlchemy models (`models.py`). Migrating to a managed PostgreSQL cluster (e.g., AWS RDS or Supabase) requires simply switching `SQLALCHEMY_DATABASE_URI` in production without altering business logic.

---

## Decision 2: Relational Peer-to-Peer State Machine for Gig Lifecycles

### Context & Problem Statement
Unlike traditional employer-employee freelance platforms where corporate clients hire contractors with complex escrow contracts, SkillSwap is tailored for peer-to-peer exchanges among students and young indie creators. The booking system required an intuitive, transparent workflow that protects both parties without cumbersome bureaucracy.

### Considered Options
1. **Freeform Direct Messaging Only:** Users negotiate solely in unstructured chat before paying off-platform.
2. **Strict Multi-Phase Escrow System:** Complex hold-and-release fund locks requiring third-party payment gateway integration.
3. **Structured Relational Finite State Machine (FSM):** A state-driven `Booking` entity (`pending` &rarr; `accepted` / `cancelled` &rarr; `completed`) linked directly to creators and clients.

### Decision & Rationale
We chose **Option 3: Structured Relational FSM**.
* **Predictable Workflow:** Every order moves through explicit lifecycle stages:
  - `pending`: Client submits a request with clear terms.
  - `accepted`: Creator reviews requirements and commits to delivery.
  - `completed`: Work is shipped and marked fulfilled, unlocking creator portfolio credit and reviews.
  - `cancelled`: Either party can back out gracefully before work begins.
* **Dual-View Dashboard Separation:** A single logged-in user can act as both a service creator and a hiring client. The state machine allows the `/dashboard` route to segment data cleanly into "Creator View" (earnings summary, incoming approvals) and "Client View" (active orders, tracking).

### Trade-offs & Mitigation
* *Trade-off:* Does not enforce automatic monetary payment capture at the instant of order creation.
* *Mitigation:* Service listings clearly state rates up front, and the database schema is architected to seamlessly attach a Stripe `payment_intent_id` to the `Booking` model whenever paid checkout is activated.

---

## Decision 3: Zero-Build Native CSS Design System with CSS Variables

### Context & Problem Statement
Design fidelity and visual polish are paramount for a creator-centric marketplace. The target aesthetic called for a soft ice-blue (`#EAF4FC`) to pastel purple (`#E8D7F9`) ambient gradient, modern glassmorphism navbar, and clean rounded card components. Using CSS preprocessors or utility CLI bundlers (like Tailwind build tools) would introduce external build-step requirements.

### Considered Options
1. **Tailwind CLI / PostCSS:** Utility-first class generation requiring Node.js toolchains.
2. **Third-party CSS Component Frameworks (Bootstrap / Bulma):** Opinionated styles that look generic and require overriding default themes.
3. **Vanilla CSS3 Design System with Custom Properties (CSS Variables):** A modular stylesheet leveraging modern CSS capabilities (`backdrop-filter`, CSS grid, custom variables).

### Decision & Rationale
We chose **Option 3: Vanilla CSS3 Design System**.
* **Zero Build Overhead:** Modifying styling is instantaneous—save the file and refresh the browser. No background watchers or bundlers needed.
* **Theme Consistency:** Centralized design tokens defined in `:root` (`--primary: #1D6AE5`, `--bg-gradient`, `--shadow-card`) make color and radius adjustments globally cohesive.
* **Native Glassmorphism:** CSS `backdrop-filter: blur(...)` combined with translucent rgba backgrounds creates a premium, lightweight UI with zero rendering lag.

### Trade-offs & Mitigation
* *Trade-off:* Utility classes are not auto-generated for one-off arbitrary values.
* *Mitigation:* The design system specifies clear reusable component classes (`.btn`, `.card`, `.badge`, `.table-card`, `.stat-item`) and allows scoped inline overrides where specific layout tweaks are needed.

