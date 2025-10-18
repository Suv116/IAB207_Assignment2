from flask import Blueprint, render_template, redirect, url_for, flash, request, url_for, current_app
from flask_login import login_required, current_user
from flask_login import login_required, logout_user, current_user
from flask_bcrypt import generate_password_hash
from .forms import RegisterForm
from .models import User, Comment, Ticket, Genre, EventImage, Event
from . import db
from werkzeug.utils import secure_filename
import datetime
import os



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
        genre_type = request.form.get('genre')
        if genre_type:
            try:
                selected_event.genre = Genre(genre_type)
            except KeyError:
                flash('Invalid genre selected.', 'danger')
                return redirect(url_for('main.update_event', event_id=selected_event.id))


          # Ticket Change
        ticket_type = request.form.get('ticket_type') or "General Admission"
        ticket_price = request.form.get('ticket_price')

        try:
            price_change = float(ticket_price) if ticket_price else 0.0
        except ValueError:
            flash('Invalid ticket price.', 'danger')
            return redirect(url_for('main.update_event', event_id=selected_event.id))

        ticket = Ticket.query.filter_by(event_id=selected_event.id).first()
        if ticket:
            ticket.ticket_type = ticket_type
            ticket.price = price_change
        else:
            ticket = Ticket(ticket_type=ticket_type, price=price_change, event_id=selected_event.id)
            db.session.add(ticket)

        
        # Date change
        changed = False
        for field, fmt in [
            ('event_date', "%Y-%m-%d"),
            ('start_time', "%H:%M"),
            ('end_time', "%H:%M"),
        ]:
            value = request.form.get(field)
            if value:
                if 'date' in field:
                    setattr(selected_event, field, datetime.datetime.strptime(value, fmt).date())
                else:
                    try:
                        setattr(selected_event, field, datetime.datetime.strptime(value, "%H:%M:%S").time())
                    except ValueError:
                        setattr(selected_event, field, datetime.datetime.strptime(value, "%H:%M").time())
                changed = True

        # Update main photo
        photo_file = request.files.get("photo")
        if photo_file and photo_file.filename:
            filename = secure_filename(photo_file.filename)
            photo_file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
            selected_event.photo = filename

        # Update carousel images
        carousel_files = request.files.getlist("carousel_images")
        if carousel_files and carousel_files[0].filename:
           
            EventImage.query.filter_by(event_id=selected_event.id).delete()
            for f in carousel_files:
                if f:
                    filename = secure_filename(f.filename)
                    f.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
                    img = EventImage(event_id=selected_event.id, filename=filename)
                    db.session.add(img)

        if changed:
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


