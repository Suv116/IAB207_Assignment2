from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, logout_user, current_user
from flask_bcrypt import generate_password_hash
from .forms import RegisterForm
from .models import User, Comment
from . import db
from .models import Event, Order, EventStatus
from datetime import datetime, date

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
    return render_template('events.html')

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
    today = date.today()
    events = (
        Event.query
        .join(Order)
        .filter(
            Order.user_id == current_user.id,
            Event.event_date >= today,
            Event.status == EventStatus.OPEN
        )
        .order_by(Event.event_date.asc())
        .all()
    )

    return render_template('UpcomingEvent.html', events=events)

# Event history page
@main_bp.route('/history')
@login_required
def history():
    return render_template('history.html')

# Logout
@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


