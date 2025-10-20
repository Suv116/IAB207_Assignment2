import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bootstrap5 import Bootstrap

# create a global SQLAlchemy object
db = SQLAlchemy()

def create_app():
    app = Flask(__name__, template_folder="templates")
    app.debug = True
    app.secret_key = "somesecretkey"

    # App configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sitedata.sqlite'
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, 'static/uploads')

    # Initialize extensions
    db.init_app(app)
    Bootstrap(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    # User loader for Flask-Login
    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.scalar(db.select(User).where(User.id == user_id))

    # Register blueprints
    from . import views
    app.register_blueprint(views.main_bp)

    from . import auth
    app.register_blueprint(auth.auth_bp)

    from . import event
    app.register_blueprint(event.event_bp)

    return app