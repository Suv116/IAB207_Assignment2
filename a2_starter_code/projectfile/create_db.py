from website import create_app, db  # replace 'your_package_name' with the folder name where __init__.py is
from website.models import *  # imports User, Event, Ticket, Comment, Order

app = create_app()

with app.app_context():
    db.create_all()
    print("Database and tables created successfully!")