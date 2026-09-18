# SkillSwap 🤝
### *A Peer-to-Peer Marketplace for Young Creators*

> **Hackathon ID:** `[C2C-AI-SKILLSWAP-2026]`  
> **Event:** Code2Career AI Hackathon  
> **Stack:** Python 3, Flask, SQLite (SQLAlchemy ORM), HTML5, CSS3, Vanilla JS  

---

## What is SkillSwap?

Ever needed a standout logo, polished video edits, or quick Python debugging help, but got tired of agency price-gouging and platforms taking 20% cuts? At the same time, you probably have a creative skill someone else would gladly pay or trade for.

**SkillSwap** bridges that gap. It is a modern, community-driven marketplace built specifically for young creators, indie makers, and students to list creative services, discover talented peers, and collaborate directly without corporate middlemen.

---

## ✨ Core Features

* **🎨 Creator & Client Dual Hub:** Users can browse listings as a client or switch to their Creator View on the dashboard to manage bookings, track earnings, and launch new services.
* **🔍 Dynamic Marketplace:** Search gigs in real-time or filter by disciplines:
  * 🎨 **Design** (Brand identity, Figma kits, UI/UX)
  * 🎬 **Editing** (Short-form Reels, YouTube pacing, podcast sound clean-up)
  * 📚 **Tutoring** (Python, algorithms, STEM problem-solving)
  * 🎵 **Music** (Custom beats, stem mastering, vocal tuning)
* **📑 Detailed Gig Pages & Instant Booking:** Transparent scope breakdown, deliverables list, verified reviews, and a clean booking modal.
* **👤 Creator Profiles:** Overlapping avatar header, tagline, skills chips, bio, and vital stats (average rating, completed gigs, response time).
* **⚡ State-Driven Booking Workflow:** Structured booking lifecycle (`pending` &rarr; `accepted` &rarr; `completed`) with creator approval controls.
* **🌱 Auto-Seeded Database:** Zero manual setup required—launches pre-populated with realistic creators, services, bookings, and reviews on first boot.

---

## 🛠️ Architecture & Tech Stack

```
Skill-Swap/
├── app.py                     # Application factory, routing, auth & auto-seed
├── models.py                  # SQLAlchemy models (User, Service, Booking, Review)
├── requirements.txt           # Python dependencies
├── DECISIONS.md               # 3 Key Architectural Decision Records
├── README.md                  # Project overview & quickstart
├── static/
│   ├── css/
│   │   └── style.css          # Cohesive design system & CSS variables
│   └── js/
│       └── main.js            # Client-side tabs, modal logic & live filtering
└── templates/
    ├── base.html              # Floating glass nav & flash messages
    ├── index.html             # Landing page with hero & featured gigs
    ├── login.html             # Polished 16:9 minimalist sign-in
    ├── register.html          # Registration with creator/client role picker
    ├── marketplace.html       # Filterable & searchable service catalog
    ├── service_detail.html    # Detailed gig view, reviews & booking modal
    ├── profile.html           # Creator profile with avatar, skills & stats
    └── dashboard.html         # Dual-view dashboard (Creator View vs. Client View)
```

---

## 🚀 Quickstart Guide

### 1. Clone & Enter Repository
```bash
git clone https://github.com/himanshusingh3107/Skill-Swap.git
cd Skill-Swap
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Application
```bash
python app.py
```
Open your browser at **`http://127.0.0.1:5000`**.

---

## 👥 Demo Test Accounts

The SQLite database (`instance/skillswap.db`) seeds automatically on initial startup with these ready-to-test accounts:

| Role | Username | Email | Password | Notable Offering |
| :--- | :--- | :--- | :--- | :--- |
| **Creator** | `aria_design` | `aria@skillswap.io` | `creator123` | Minimalist Brand Identity & Logo Suite ($65) |
| **Creator** | `marcus_edits` | `marcus@skillswap.io` | `creator123` | High-Retention Video & Reels Editing ($45) |
| **Creator** | `priya_tutors` | `priya@skillswap.io` | `creator123` | 1-on-1 Python & STEM Tutoring ($40) |
| **Creator** | `liam_beats` | `liam@skillswap.io` | `creator123` | Custom Lo-Fi & Synthwave Beats ($50) |
| **Client** | `jordan_maker` | `jordan@skillswap.io` | `client123` | Active client with booked gigs & reviews |
| **Client** | `sam_green` | `sam@skillswap.io` | `client123` | Student filmmaker exploring sound & edit gigs |

---

## 🏛️ Architectural Decisions

Refer to [DECISIONS.md](file:///c:/Users/vs623/OneDrive/Desktop/Skill-Swap/DECISIONS.md) for full Architectural Decision Records regarding:
1. Monolithic Flask + SQLite vs. Decoupled Single-Page App (SPA).
2. Relational Peer-to-Peer State Machine for Gig Lifecycles.
3. Zero-Build Native CSS Design System with CSS Variables.
