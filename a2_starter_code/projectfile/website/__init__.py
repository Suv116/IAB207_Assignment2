import os
from flask import Flask, session, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, logout_user
from flask_bootstrap5 import Bootstrap

# create a global SQLAlchemy object
db = SQLAlchemy()

def create_app():
    app = Flask(__name__, instance_relative_config=True, template_folder="templates")
    app.debug = True
    app.secret_key = "somesecretkey"

    # Absolute path to the database in the instance folder
    os.makedirs(app.instance_path, exist_ok=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'sitedata.sqlite')
    print("DB path:", os.path.join(app.instance_path, 'sitedata.sqlite'))
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "static", "uploads")

    # Initialize extensions
    db.init_app(app)
    Bootstrap(app)

    with app.app_context():
        print("Creating tables if they do not exist...")
        db.create_all()
        print("Tables are ready!")

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    # User loader for Flask-Login
    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.scalar(db.select(User).where(User.id == user_id))

    @app.before_request
    def clear_login_once():
        if not hasattr(app, "_login_cleared"):
            from flask_login import logout_user
            from flask import session

            session.clear()
            logout_user()
            app._login_cleared = True  # ensures this runs only once

    # Register blueprints
    from . import views
    app.register_blueprint(views.main_bp)

    from . import auth
    app.register_blueprint(auth.auth_bp)

    from . import event
    app.register_blueprint(event.event_bp)

    from . import models

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500
    
    return app