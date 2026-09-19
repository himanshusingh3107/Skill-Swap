# SkillSwap 🤝
### *A Peer-to-Peer Marketplace for Young Creators*

> **Hackathon ID:** `[C2C-AI-SKILLSWAP-2026]`  
> **Event:** Code2Career AI Hackathon  
> **Stack:** Python 3, Flask, SQLite (SQLAlchemy ORM), Semantic HTML5, Pure CSS3 (Zero JavaScript)  

---

## What is SkillSwap?

Ever needed a standout logo, polished video edits, or quick Python debugging help, but got tired of agency price-gouging and platforms taking 20% cuts? At the same time, you probably have a creative skill someone else would gladly pay or trade for.

**SkillSwap** bridges that gap. It is a modern, community-driven marketplace built specifically for young creators, indie makers, and students to list creative services, discover talented peers, and collaborate directly without corporate middlemen.

---

## ✨ Core Features

* **🎨 Creator & Client Dual Hub:** Users can browse listings as a client or switch to their Creator View on the dashboard to manage bookings, track earnings, and launch new services.
* **🔍 Dynamic Marketplace:** Search gigs or filter by creative disciplines:
  * 🎨 **Design** (Brand identity, Figma kits, UI/UX)
  * 🎬 **Editing** (Short-form Reels, YouTube pacing, podcast sound clean-up)
  * 📚 **Tutoring** (Python, algorithms, STEM problem-solving)
  * 🎵 **Music** (Custom beats, stem mastering, vocal tuning)
* **📑 Detailed Gig Pages & Instant Booking:** Transparent scope breakdown, deliverables list, verified reviews, and a clean booking modal.
* **👤 Creator Profiles:** Overlapping avatar header, tagline, skills chips, bio, and vital stats (average rating, completed gigs, response time).
* **⚡ State-Driven Booking Workflow:** Structured booking lifecycle (`pending` &rarr; `accepted` &rarr; `completed`) with creator approval controls.
* **🚫 Pure HTML5/CSS3 (Zero JS):** Fully functional using native server-side rendering, GET search parameters, and pure CSS `:target` modals without a single line of JavaScript.

---

## 🛠️ Architecture & Tech Stack

```
Skill-Swap/
├── app.py                     # Application factory, routing, auth & rendering
├── models.py                  # SQLAlchemy models (User, Service, Booking, Review)
├── requirements.txt           # Python dependencies
├── README.md                  # Project overview & quickstart
├── static/
│   └── css/
│       └── style.css          # Cohesive design system & pure CSS modal mechanics
└── templates/
    ├── index.html             # Landing page with hero & featured gigs
    ├── login.html             # Polished minimalist sign-in
    ├── register.html          # Registration with creator/client role picker
    ├── marketplace.html       # Filterable & searchable service catalog (pure HTML)
    ├── service_detail.html    # Detailed gig view, reviews & pure CSS booking modal
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
