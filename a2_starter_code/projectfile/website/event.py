import os

from flask import Blueprint, flash, render_template, request, url_for, redirect, current_app
from flask_login import login_required, current_user
from datetime import datetime
from werkzeug.utils import secure_filename

from .models import User, OrganisationType, Genre, Event, Ticket, EventImage, Comment
from . import db

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
            flash(f"Error creating concert: {str(e)}", "danger")

    return render_template("CreateEvent.html")

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
