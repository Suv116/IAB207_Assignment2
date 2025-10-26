from flask import Blueprint, flash, render_template, request, url_for, redirect
from flask_bcrypt import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from wtforms.fields import datetime

from .models import User, OrganisationType, Genre
from .forms import LoginForm, RegisterForm
from . import db
from .forms import EventForm
from .models import Event, Ticket


# Create a blueprint - make sure all BPs have unique names
auth_bp = Blueprint('auth', __name__)

# this is a hint for a login function
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for(" "))  # already logged in

    form = LoginForm()
    if form.validate_on_submit():
        username = form.user_name.data
        password = form.password.data

        user = db.session.scalar(db.select(User).where(User.username == username))

        if not user:
            flash("Incorrect username", "danger")
        elif not check_password_hash(user.password_hash, password):
            flash("Incorrect password", "danger")
        else:
            login_user(user)
            next_page = request.args.get("next")
            if not next_page or not next_page.startswith("/"):
                next_page = url_for("main.index")
            return redirect(next_page)

    return render_template("login.html", form=form, heading="Login")

@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = RegisterForm()
    if form.validate_on_submit():
        username = form.user_name.data
        email = form.email.data
        phone_number = form.phone_number.data
        password = form.password.data

        # Check username
        if User.query.filter_by(username=username).first():
            form.user_name.errors.append("Username already exists. Please choose another.")
            return render_template("signup.html", form=form, heading="Sign Up")

        # Check email
        if User.query.filter_by(email=email).first():
            form.email.errors.append("Email already in use. Please choose another.")
            return render_template("signup.html", form=form, heading="Sign Up")

        # Check phone
        if User.query.filter_by(phone_number=phone_number).first():
            form.phone_number.errors.append("Phone number already in use. Please use another.")
            return render_template("signup.html", form=form, heading="Sign Up")

        # Hash password
        hashed_password = generate_password_hash(password).decode("utf-8")

        # Create user
        new_user = User(
            username=username,
            email=email,
            phone_number=phone_number,
            password_hash=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Account created! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("signup.html", form=form, heading="Sign Up")



