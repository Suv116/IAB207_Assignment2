from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, logout_user, current_user
from flask_bcrypt import generate_password_hash
from .forms import RegisterForm
from .models import User, Comment, Ticket, Event, EventStatus, Genre, EventImage
from . import db
from .models import Event
from werkzeug.utils import secure_filename
import os
import datetime

main_bp = Blueprint('main', __name__)

# Home page
@main_bp.route('/')
def index():
    today = datetime.datetime.now().date()

    trending_events = (
        Event.query.filter(Event.event_date >= today)
        .order_by(Event.event_date.asc())
        .limit(6)
        .all()
    )

    upcoming_events = (
        Event.query.filter(Event.event_date >= today)
        .order_by(Event.event_date.asc())
        .offset(6)
        .limit(6)
        .all()
    )

    # Fetch top genre events dynamically
    grunge_events = Event.query.filter_by(genre=Genre.GRUNGE).limit(2).all()
    seventies_events = Event.query.filter_by(genre=Genre.SEVENTIES ).limit(2).all()
    southern_rock_events = Event.query.filter_by(genre=Genre.SOUTHERN).limit(2).all()
    metal_events = Event.query.filter_by(genre=Genre.METAL).limit(2).all()

    return render_template(
        "index.html",
        trending_events=trending_events,
        upcoming_events=upcoming_events,
        grunge_events=grunge_events,
        seventies_events= seventies_events,
        southern_rock_events=southern_rock_events,
        metal_events=metal_events
    )


# Events page
@main_bp.route('/events')
def events():
    query = Event.query

    # Get filters
    search_query = request.args.get('q', '').strip()
    max_price = request.args.get('max_price', type=float)
    genres = request.args.getlist('genre')
    status = request.args.get('status')
    location = request.args.get('location', '').strip()

    # Apply filters
    if search_query:
        query = query.filter(Event.title.ilike(f"%{search_query}%"))

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


## Update event page
@main_bp.route('/update-event', methods=['GET', 'POST'])
@login_required
def update_event():
    user_events = Event.query.filter_by(user_id=current_user.id).all()

    # Get selected event from query string or form
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

        # Ticket update
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

        # Date/time update
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

        # Main photo
        photo_file = request.files.get("photo")
        if photo_file and photo_file.filename:
            filename = secure_filename(photo_file.filename)
            photo_file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
            selected_event.photo = filename

        # Carousel images
        carousel_files = request.files.getlist("carousel_images")
        if carousel_files and carousel_files[0].filename:
            EventImage.query.filter_by(event_id=selected_event.id).delete()
            for f in carousel_files:
                if f.filename:
                    filename = secure_filename(f.filename)
                    f.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
                    img = EventImage(event_id=selected_event.id, filename=filename)
                    db.session.add(img)

        if changed:
            db.session.commit()
            flash('Event updated successfully', 'success')
            return redirect(url_for('main.update_event', event_id=selected_event.id))

    return render_template(
        'UpdateEvent.html',
        events=user_events,
        selected_event=selected_event
    )

@main_bp.route('/delete-event/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    event = Event.query.filter_by(id=event_id, user_id=current_user.id).first_or_404()
    
    # Delete info and images
    Ticket.query.filter_by(event_id=event.id).delete()
    EventImage.query.filter_by(event_id=event.id).delete()
    
    db.session.delete(event)
    db.session.commit()
    flash('Event cancelled successfully.', 'success')
    return redirect(url_for('main.update_event'))

# Upcoming events page
@main_bp.route('/upcoming-event')
@login_required
def upcoming_event():
    return render_template('UpcomingEvent.html')

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


