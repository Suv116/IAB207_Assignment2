import enum

from . import db
from datetime import datetime
from flask_login import UserMixin


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    phone_number = db.Column(db.String(150), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    # Relationships
    comments = db.relationship("Comment", backref="users", lazy=True, cascade="all, delete-orphan")
    orders = db.relationship("Order", backref="users", lazy=True, cascade="all, delete-orphan")
    events = db.relationship("Event", back_populates="users", lazy=True, cascade="all, delete-orphan")




class EventStatus(enum.Enum):
    OPEN = "open"
    SOLD_OUT = "sold out"
    CANCELLED = "cancelled"
    INACTIVE = "inactive"


class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    creator = db.relationship("User", back_populates="events")

    status = db.Column(db.Enum(EventStatus), nullable=False, default=EventStatus.OPEN)

    photo = db.Column(db.String(255), nullable=True)


    # Relationships
    orders = db.relationship("Order", backref="event", lazy=True, cascade="all, delete-orphan")
    comments = db.relationship("Comment", backref="event", lazy=True, cascade="all, delete-orphan")
    tickets = db.relationship("Ticket", back_populates="event", lazy=True, cascade="all, delete-orphan")



class Ticket(db.Model):
    __tablename__ = "tickets"

    id = db.Column(db.Integer, primary_key=True)
    ticket_type = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)

    # Foreign key to Event
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)

    # Relationship back to Event
    event = db.relationship("Event", back_populates="tickets")
    orders = db.relationship("Order", back_populates="ticket", lazy=True, cascade="all, delete-orphan")




class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)

    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), nullable=False)

    # Relationships
    ticket = db.relationship("Ticket", back_populates="orders")


