from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, logout_user, current_user
from flask_bcrypt import generate_password_hash
from .forms import RegisterForm
from .models import User, Comment, Ticket, Event, EventStatus, Genre
from . import db
from .models import Event

main_bp = Blueprint('main', __name__)

# Home page
@main_bp.route('/')
def index():
    trending_events = Event.query.order_by(Event.event_date.asc()).limit(6).all()
    upcoming_events = Event.query.order_by(Event.event_date.asc()).offset(6).limit(6).all()

    return render_template(
        "index.html",
        trending_events=trending_events,
        upcoming_events=upcoming_events
    )

# Events page
@main_bp.route('/events')
def events():
    query = Event.query

    # Filters
    max_price = request.args.get('max_price', type=float)
    genres = request.args.getlist('genre')
    status = request.args.get('status')
    location = request.args.get('location', '').strip()

    # Apply filters
    if max_price is not None:
        query = query.outerjoin(Ticket).filter((Ticket.price <= max_price) | (Ticket.id.is_(None)))

    if genres:
        try:
            enum_genres = [Genre[g.upper()] for g in genres if g.upper() in Genre.__members__]
            query = query.filter(Event.genre.in_(enum_genres))
        except KeyError:
            pass

    if status:
        status_key = status.replace(" ", "").upper()
        if status_key in EventStatus.__members__:
            query = query.filter(Event.status == EventStatus[status_key])

    if location:
        query = query.filter(Event.venue.ilike(f"%{location}%"))

    events = query.distinct().order_by(Event.event_date.asc()).all()

    return render_template("events.html", events=events)


# Event detail page
@main_bp.route('/details/<int:event_id>')
def details(event_id):
    event = Event.query.get_or_404(event_id)
    comments = Comment.query.filter_by(event_id=event.id).order_by(Comment.created_at.desc()).all()
    return render_template("details.html", event=event, comments=comments)


# Update event page
@main_bp.route('/update-event')
@login_required
def update_event():
    return render_template('UpdateEvent.html')

# Upcoming events page
@main_bp.route('/upcoming-event')
@login_required
def upcoming_event():
    return render_template('UpcomingEvent.html')

# Event history page
@main_bp.route('/history')
@login_required
def history():
    return render_template('History.html')

# Logout
@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


