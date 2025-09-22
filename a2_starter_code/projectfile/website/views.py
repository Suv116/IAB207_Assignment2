from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, logout_user, current_user
from flask_bcrypt import generate_password_hash
from .forms import RegisterForm
from .models import User
from . import db

main_bp = Blueprint('main', __name__)

# Home page
@main_bp.route('/')
def index():
    return render_template('index.html')

# Events page
@main_bp.route('/events')
def events():
    return render_template('events.html')

# Event details page
@main_bp.route('/details')
def details():
    return render_template('details.html')

# Create event page
@main_bp.route('/create-event')
@login_required
def create_event():
    return render_template('CreateEvent.html')

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
