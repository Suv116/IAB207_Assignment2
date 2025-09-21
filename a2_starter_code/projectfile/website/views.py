from flask import Blueprint, render_template

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
def create_event():
    return render_template('CreateEvent.html')

# Update event page
@main_bp.route('/update-event')
def update_event():
    return render_template('UpdateEvent.html')

# Upcoming events page
@main_bp.route('/upcoming-event')
def upcoming_event():
    return render_template('UpcomingEvent.html')

# Event history page
@main_bp.route('/history')
def history():
    return render_template('History.html')

# Login page
@main_bp.route('/login')
def login():
    return render_template('Login.html')

# Signup page
@main_bp.route('/signup')
def signup():
    return render_template('Signup.html')