import os

from flask import Blueprint, flash, render_template, request, url_for, redirect, current_app
from flask_login import login_required, current_user
from datetime import datetime
from werkzeug.utils import secure_filename

from .models import EventStatus, User, OrganisationType, Genre, Event, Ticket, EventImage, Comment, Order
from . import db
from sqlalchemy import cast, Date
event_bp = Blueprint("event", __name__)

@event_bp.route("/create-event", methods=["GET", "POST"])
@login_required
def create_event():
    if request.method == "POST":
        try:
            title = request.form.get("title")
            attendees = request.form.get("attendees")
            organisation = request.form.get("organisation")
            date = request.form.get("date")
            start_time = request.form.get("start_time")
            end_time = request.form.get("end_time")
            genre = request.form.get("genre")
            ticket_type = request.form.get("ticket_type")
            price = request.form.get("price")
            venue = request.form.get("venue")
            description = request.form.get("description")

            # Convert date and time
            event_date = datetime.strptime(date, "%Y-%m-%d").date() if date else None
            start_time_obj = datetime.strptime(start_time, "%H:%M").time() if start_time else None
            end_time_obj = datetime.strptime(end_time, "%H:%M").time() if end_time else None

            # Create Event
            event = Event(
                title=title,
                attendees=int(attendees) if attendees else None,
                organisation=OrganisationType(organisation) if organisation else None,
                event_date=event_date,
                start_time=start_time_obj,
                end_time=end_time_obj,
                genre=Genre(genre) if genre else None,
                venue=venue,
                description=description,
                user_id=current_user.id,
            )

            photo_file = request.files.get("photo")
            if photo_file:
                filename = secure_filename(photo_file.filename)
                photo_file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
                event.photo = filename
            db.session.add(event)
            db.session.flush()

            carousel_files = request.files.getlist("carousel_images")
            for f in carousel_files:
                if f:
                    filename = secure_filename(f.filename)
                    f.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
                    img = EventImage(event_id=event.id, filename=filename)
                    db.session.add(img)

            if ticket_type and price:
                ticket = Ticket(
                    ticket_type=ticket_type,
                    price=float(price),
                    event_id=event.id
                )
                db.session.add(ticket)

            db.session.commit()
            flash("Concert created successfully!", "success")
            return redirect(url_for("main.index"))

        except Exception as e:
            db.session.rollback()
            flash("Error creating event. Please check your information and try again.", "danger")

    return render_template("createEvent.html")

@event_bp.route("/event/<int:event_id>/comment", methods=["POST"])
@login_required
def add_comment(event_id):
    content = request.form.get("content")

    if not content or content.strip() == "":
        flash("Comment cannot be empty.", "danger")
        return redirect(url_for("main.details", event_id=event_id))

    # Ensure event exists
    event = Event.query.get_or_404(event_id)

    # Create comment
    comment = Comment(
        content=content.strip(),
        user_id=current_user.id,
        event_id=event.id
    )
    db.session.add(comment)
    db.session.commit()

    flash("Comment added successfully!", "success")
    return redirect(url_for("main.details", event_id=event.id))
# Route for Event Details 
@event_bp.route("/event/<int:event_id>", endpoint="event_details")
@login_required
def event_details(event_id):
    event = Event.query.get_or_404(event_id)
    tickets = event.tickets
    user_orders = Order.query.filter_by(user_id=current_user.id, event_id=event.id).all()
    return render_template("details.html", event=event, tickets=tickets, user_orders=user_orders, datetime=datetime)

# Route for Book Tickets
@event_bp.route("/book_tickets/<int:event_id>", methods=["POST"])
@login_required
def book_tickets(event_id):
    event = Event.query.get_or_404(event_id)
    tickets = event.tickets
    total_booked = sum(order.quantity for order in event.orders)

    total_tickets = 0

    if event.status.name == "INACTIVE" or event.event_date < datetime.now().date():
        flash("This event is no longer active. Ticket booking is closed.", "warning")
        return redirect(url_for("event.event_details", event_id=event.id))
    
    for ticket in tickets:
        qty = int(request.form.get(f"ticket_{ticket.id}", 0))
        if qty > 0:
            # Prevent overbooking
            if event.attendees and (total_booked + qty) > event.attendees:
                flash(f"Cannot book {qty} tickets. Only {event.attendees - total_booked} left.", "warning")
                return redirect(url_for("event.event_details", event_id=event.id))

            order = Order(
                user_id=current_user.id,
                event_id=event.id,
                ticket_id=ticket.id,
                quantity=qty,
                price=ticket.price * qty,
                order_date=datetime.utcnow()
            )
            db.session.add(order)
            total_tickets += qty
            total_booked += qty

    if total_tickets == 0:
        flash("Please select at least one ticket to book.", "warning")
        return redirect(url_for("event.event_details", event_id=event.id))

    try: 
        db.session.commit()
        if event.attendees and total_booked >= event.attendees:
            event.status = EventStatus.SOLD_OUT
            db.session.commit()
            flash("Tickets booked successfully! Event is now SOLD OUT.", "success")
        else:
            flash("Tickets booked successfully!", "success")
    except Exception:
        db.session.rollback()
        flash("Failed to book tickets. Please try again.", "danger")

    return redirect(url_for("event.event_details", event_id=event.id))

# Cancel order 
@event_bp.route("/cancel_order/<int:order_id>", methods=["POST"])
@login_required
def cancel_order(order_id):
    # Get the order
    order = Order.query.get_or_404(order_id)

    # Make sure the current user owns this order
    if order.user_id != current_user.id:
        flash("You are not authorized to cancel this order.", "danger")
        return redirect(url_for("event.upcoming_view"))
    event_title = order.event.title
    ticket_type = order.ticket.ticket_type

    
    # Delete the order
    db.session.delete(order)
    db.session.commit()

    flash(f"Your booking for {order.event.title} ({order.ticket.ticket_type}) has been cancelled.", "success")
    return redirect(url_for("event.upcoming"))
# Upcoming Events Route
@event_bp.route("/upcoming-event", endpoint="upcoming")
@login_required
def upcoming_view():
    """Shows only the user's future event bookings."""
    user_orders = Order.query.filter_by(user_id=current_user.id).all()
    event_ids = {order.event_id for order in user_orders}

    # Only events whose date is in the future or today
    events = Event.query.filter(
        Event.id.in_(event_ids),
        Event.event_date >= datetime.now().date()
    ).order_by(Event.event_date.asc()).all()

    print("=== DEBUG ===")
    print("User Orders:", [(o.id, o.event_id, o.user_id) for o in user_orders])
    print("Events Returned:", [(e.id, e.title) for e in events])
    print("================")

    return render_template("UpcomingEvent.html", events=events, user_orders=user_orders)


# Route for Past Bookings
@login_required
@event_bp.route("/event/history")
def history_view():
    # Get all orders for current user
    user_orders = Order.query.filter_by(user_id=current_user.id).all()

    # Get unique event IDs for events that are in the past
    past_event_ids = {order.event_id for order in user_orders if order.event.event_date < datetime.now().date()}

    # Query those events
    events = Event.query.filter(Event.id.in_(past_event_ids)).order_by(Event.event_date.desc()).all()
    
    return render_template("history.html", events=events, active_tab="past")

    # test