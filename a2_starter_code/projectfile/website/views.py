from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, logout_user, current_user
from flask_bcrypt import generate_password_hash
from .forms import RegisterForm
from .models import User, Comment, Ticket, Event, EventStatus, Genre, EventImage
from . import db
from werkzeug.utils import secure_filename
import os
from datetime import datetime  # keep this

main_bp = Blueprint('main', __name__)


# Home page
@main_bp.route('/')
def index():
    today = datetime.now().date()  # correct usage

    # Mark past events as INACTIVE
    past_events = Event.query.filter(Event.event_date < today, Event.status != EventStatus.INACTIVE).all()
    for event in past_events:
        event.status = EventStatus.INACTIVE
    if past_events:
        db.session.commit()

    trending_events = (
        Event.query.filter(Event.event_date >= today)
        .order_by(Event.event_date.asc())
        .limit(6)
        .all()
    )

    upcoming_events = (
        Event.query.filter(Event.event_date >= today, Event.status != EventStatus.INACTIVE)
        .order_by(Event.event_date.asc())
        .offset(6)
        .limit(6)
        .all()
    )
    previous_events = (
        Event.query.filter(Event.status == EventStatus.INACTIVE)
        .order_by(Event.event_date.desc())
        .all()
    )

    # Fetch top genre events dynamically
    grunge_events = Event.query.filter_by(genre=Genre.GRUNGE).limit(2).all()
    seventies_events = Event.query.filter_by(genre=Genre.SEVENTIES).limit(2).all()
    southern_rock_events = Event.query.filter_by(genre=Genre.SOUTHERN).limit(2).all()
    metal_events = Event.query.filter_by(genre=Genre.METAL).limit(2).all()

    return render_template(
        "index.html",
        trending_events=trending_events,
        upcoming_events=upcoming_events,
        grunge_events=grunge_events,
        seventies_events=seventies_events,
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
    user_orders = []
    tickets = event.tickets
    return render_template("details.html", event=event, comments=comments, tickets=tickets, user_orders=user_orders,
                           datetime=datetime)


# Update event page
@main_bp.route('/update-event', methods=['GET', 'POST'])
@login_required
def update_event():
    user_events = Event.query.filter_by(user_id=current_user.id).all()
    event_id = request.args.get('event_id') or request.form.get('event_id')
    selected_event = Event.query.filter_by(id=event_id, user_id=current_user.id).first() if event_id else None

    if request.method == 'POST' and selected_event:
        # Basic info
        title = request.form.get('title')
        if not title:
            flash('Event name cannot be empty.', 'danger')
            return redirect(url_for('main.update_event', event_id=selected_event.id))
        selected_event.title = title
        selected_event.description = request.form.get('description', selected_event.description)
        selected_event.venue = request.form.get('venue', selected_event.venue)

        # Genre
        genre_type = request.form.get('genre')
        if genre_type:
            try:
                selected_event.genre = Genre(genre_type)
            except KeyError:
                flash('Invalid genre selected.', 'danger')
                return redirect(url_for('main.update_event', event_id=selected_event.id))

        # Date & time
        try:
            event_date_str = request.form.get('event_date')
            if event_date_str:
                selected_event.event_date = datetime.strptime(event_date_str, "%Y-%m-%d").date()
            start_time_str = request.form.get('start_time')
            if start_time_str:
                selected_event.start_time = datetime.strptime(start_time_str, "%H:%M").time()
            end_time_str = request.form.get('end_time')
            if end_time_str:
                selected_event.end_time = datetime.strptime(end_time_str, "%H:%M").time()
        except ValueError:
            flash("Invalid date or time format.", "danger")
            return redirect(url_for('main.update_event', event_id=selected_event.id))

        # Update existing tickets
        for ticket in selected_event.tickets:
            ticket_type = request.form.get(f"existing_ticket_type_{ticket.id}")
            ticket_price = request.form.get(f"existing_ticket_price_{ticket.id}")
            if ticket_type:
                ticket.ticket_type = ticket_type.strip()
            if ticket_price:
                try:
                    ticket.price = float(ticket_price)
                except ValueError:
                    ticket.price = 0.0

        # Add new tickets
        new_types = request.form.getlist('new_ticket_type[]')
        new_prices = request.form.getlist('new_ticket_price[]')
        for t_type, t_price in zip(new_types, new_prices):
            if t_type.strip():
                try:
                    price_val = float(t_price)
                except ValueError:
                    price_val = 0.0
                ticket = Ticket(ticket_type=t_type.strip(), price=price_val, event_id=selected_event.id)
                db.session.add(ticket)

        # Main Image
        photo_file = request.files.get("photo")
        if photo_file and photo_file.filename:
            filename = secure_filename(photo_file.filename)
            photo_file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
            selected_event.photo = filename

        # Carousel Images
        carousel_files = request.files.getlist("carousel_images")
        if carousel_files and carousel_files[0].filename:
            EventImage.query.filter_by(event_id=selected_event.id).delete()
            for f in carousel_files:
                if f.filename:
                    filename = secure_filename(f.filename)
                    f.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
                    img = EventImage(event_id=selected_event.id, filename=filename)
                    db.session.add(img)

        db.session.commit()
        flash('Event updated successfully!', 'success')
        return redirect(url_for('main.update_event', event_id=selected_event.id))

    return render_template('UpdateEvent.html', events=user_events, selected_event=selected_event,
                           EventStatus=EventStatus)



# Delete event
@main_bp.route('/delete-event/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    event = Event.query.filter_by(id=event_id, user_id=current_user.id).first_or_404()

    # Toggle event status correctly using Enum
    if event.status == EventStatus.CANCELLED:
        event.status = EventStatus.OPEN
        flash('Event re-opened successfully.', 'success')
    else:
        event.status = EventStatus.CANCELLED
        flash('Event cancelled successfully.', 'success')

    db.session.commit()
    return redirect(url_for('main.update_event', event_id=event.id))


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
