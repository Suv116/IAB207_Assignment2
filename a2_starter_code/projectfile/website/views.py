from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, logout_user, current_user
from flask_bcrypt import generate_password_hash
from .forms import RegisterForm
from .models import User, Comment
from . import db
from .models import Event
import datetime

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
@main_bp.route('/update-event', methods=['GET', 'POST'])
@login_required
def update_event():
    
    user_events = Event.query.filter_by(user_id=current_user.id).all()

   
    event_id = request.args.get('event_id') or request.form.get('event_id')
    selected_event = Event.query.filter_by(id=event_id, user_id=current_user.id).first() if event_id else None

    if request.method == 'POST' and selected_event:
       
        
        title = request.form.get('title')

        if not title:
            flash('Event name cannot be empty.', 'danger')
            return redirect(url_for('main.update_event', event_id=selected_event.id))

       
        selected_event.title = title
        selected_event.description = request.form.get('description')
        selected_event.venue = request.form.get('venue')
        selected_event.ticket_price = request.form.get('ticket_price')
        selected_event.genre = request.form.get('genre')

        
        for field, fmt in [('event_date', "%Y-%m-%d"), ('start_time', "%H:%M:%S"), ('end_time', "%H:%M:%S")]:
            value = request.form.get(field)
            if value:
                setattr(selected_event, field, datetime.datetime.strptime(value, fmt).date() if 'date' in field else datetime.datetime.strptime(value, fmt).time())

        db.session.commit()
        flash('Event updated successfully', 'success')
        return redirect(url_for('main.update_event', event_id=selected_event.id))

    return render_template('UpdateEvent.html', events=user_events, selected_event=selected_event)


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


