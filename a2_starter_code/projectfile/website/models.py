import enum
from datetime import datetime
from flask_login import UserMixin
from . import db



# User Model
class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    phone_number = db.Column(db.String(150), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    # Relationships
    events = db.relationship(
        "Event", back_populates="creator", lazy=True, cascade="all, delete-orphan"
    )
    comments = db.relationship(
        "Comment", back_populates="user", lazy=True, cascade="all, delete-orphan"
    )
    orders = db.relationship(
        "Order", back_populates="user", lazy=True, cascade="all, delete-orphan"
    )


# Event Status Enum
class EventStatus(enum.Enum):
    OPEN = "open"
    SOLD_OUT = "sold out"
    CANCELLED = "cancelled"
    INACTIVE = "inactive"


# Event Model
class OrganisationType(enum.Enum):
    INDEPENDENT = "independent"
    BAND = "band"
    LABEL = "label"
    PROMOTER = "promoter"

class Genre(enum.Enum):
    GRUNGE = "grunge"
    METAL = "metal"
    TRIBUTE = "tribute"
    CLASSIC = "classic"
    SEVENTIES = "70s"
    EIGHTIES = "80s"
    NINETIES = "90s"
    TWO_THOUSANDS = "00s"
    SOUTHERN = "southern"
    PSYCHEDELIC = "psychedelic"


class Event(db.Model):
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    attendees = db.Column(db.Integer, nullable=True)
    organisation = db.Column(db.Enum(OrganisationType), nullable=True)
    event_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    genre = db.Column(db.Enum(Genre), nullable=True)
    venue = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.Enum(EventStatus), default=EventStatus.OPEN, nullable=False)
    photo = db.Column(db.String(255), nullable=True)  # Main image

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    creator = db.relationship("User", back_populates="events")

    tickets = db.relationship(
        "Ticket", back_populates="event", lazy=True, cascade="all, delete-orphan"
    )
    comments = db.relationship(
        "Comment", back_populates="event", lazy=True, cascade="all, delete-orphan"
    )
    orders = db.relationship(
        "Order", back_populates="event", lazy=True, cascade="all, delete-orphan"
    )

    images = db.relationship(
        "EventImage", back_populates="event", lazy=True, cascade="all, delete-orphan"
    )
    def check_and_update_status(self):
        """Automatically set event as INACTIVE if the date has passed."""
        today = datetime.utcnow().date()
        if self.event_date < today and self.status != EventStatus.INACTIVE:
            self.status = EventStatus.INACTIVE
            db.session.commit()

class EventImage(db.Model):
    __tablename__ = 'event_images'

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)

    event = db.relationship("Event", back_populates="images")


# Ticket Model
class Ticket(db.Model):
    __tablename__ = 'tickets'

    id = db.Column(db.Integer, primary_key=True)
    ticket_type = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)

    # Foreign key to Event
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    event = db.relationship("Event", back_populates="tickets")

    # Relationships
    orders = db.relationship(
        "Order", back_populates="ticket", lazy=True, cascade="all, delete-orphan"
    )



# Comment Model
class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)

    # Relationships
    user = db.relationship("User", back_populates="comments")
    event = db.relationship("Event", back_populates="comments")


# Order Model
class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)

    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), nullable=False)

    # Relationships
    user = db.relationship("User", back_populates="orders")
    event = db.relationship("Event", back_populates="orders")
    ticket = db.relationship("Ticket", back_populates="orders")
