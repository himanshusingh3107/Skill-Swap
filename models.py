from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default="creator", nullable=False)  # 'creator' or 'client'
    tagline = db.Column(db.String(160), default="")
    bio = db.Column(db.Text, default="")
    rating = db.Column(db.Float, default=5.0)

    # Relationships
    services = db.relationship("Service", backref="creator", lazy="dynamic", cascade="all, delete-orphan")
    bookings = db.relationship("Booking", backref="client", lazy="dynamic", cascade="all, delete-orphan")
    reviews = db.relationship("Review", backref="reviewer", lazy="dynamic")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def completed_gigs_count(self) -> int:
        if self.role == "creator":
            # Gigs completed by this creator across all services
            return Booking.query.join(Service).filter(
                Service.creator_id == self.id,
                Booking.status == "completed"
            ).count()
        # Gigs booked and completed as client
        return self.bookings.filter_by(status="completed").count()

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "tagline": self.tagline,
            "bio": self.bio,
            "rating": self.rating
        }


class Service(db.Model):
    __tablename__ = "services"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(40), nullable=False, index=True)  # 'Design', 'Editing', 'Tutoring', 'Music'
    price = db.Column(db.Float, nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Relationships
    bookings = db.relationship("Booking", backref="service", lazy="dynamic", cascade="all, delete-orphan")
    reviews = db.relationship("Review", backref="service", lazy="dynamic", cascade="all, delete-orphan")

    @property
    def average_rating(self) -> float:
        rev_list = self.reviews.all()
        if not rev_list:
            return 5.0
        return round(sum(r.rating for r in rev_list) / len(rev_list), 1)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "price": self.price,
            "creator_id": self.creator_id,
            "creator_username": self.creator.username if self.creator else None,
            "creator_rating": self.creator.rating if self.creator else 5.0,
            "rating": self.average_rating
        }


class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey("services.id"), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String(20), default="pending", nullable=False)  # 'pending', 'accepted', 'completed', 'cancelled'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "service_id": self.service_id,
            "service_title": self.service.title if self.service else "Unknown",
            "service_price": self.service.price if self.service else 0.0,
            "client_id": self.client_id,
            "client_username": self.client.username if self.client else "Unknown",
            "creator_username": self.service.creator.username if self.service and self.service.creator else "Unknown",
            "status": self.status,
            "created_at": self.created_at.strftime("%b %d, %Y")
        }


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey("services.id"), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    rating = db.Column(db.Integer, default=5, nullable=False)  # 1 to 5
    comment = db.Column(db.Text, default="", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "service_id": self.service_id,
            "reviewer_username": self.reviewer.username if self.reviewer else "Anonymous",
            "rating": self.rating,
            "comment": self.comment,
            "created_at": self.created_at.strftime("%b %d, %Y")
        }

