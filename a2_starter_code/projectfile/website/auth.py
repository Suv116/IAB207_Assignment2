from flask import Blueprint, flash, render_template, request, url_for, redirect
from flask_bcrypt import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from .models import User
from .forms import LoginForm, RegisterForm
from . import db


# Create a blueprint - make sure all BPs have unique names
auth_bp = Blueprint('auth', __name__)

# this is a hint for a login function
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))  # already logged in

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

        existing_user = db.session.scalar(
            db.select(User).where(User.username == username)
        )
        if existing_user:
            flash("Username already exists", "danger")
            return redirect(url_for("auth.signup"))

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
