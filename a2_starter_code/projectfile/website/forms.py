from flask_wtf import FlaskForm
from wtforms import DateTimeLocalField, SelectField, FloatField
from wtforms.fields import TextAreaField, SubmitField, StringField, PasswordField
from wtforms.validators import InputRequired, Length, Email, EqualTo, Regexp, DataRequired, ValidationError
from .models import User

# creates the login information
class LoginForm(FlaskForm):
    user_name = StringField("User Name", validators=[InputRequired('Enter user name')])
    password = PasswordField("Password", validators=[InputRequired('Enter user password')])
    submit = SubmitField("Login")


# this is the registration form
class RegisterForm(FlaskForm):
    user_name = StringField(
        "User Name",
        validators=[InputRequired("Please enter your username")]
    )

    email = StringField(
        "Email Address",
        validators=[InputRequired("Please enter your email"), Email("Please enter a valid email")]
    )

    phone_number = StringField(
        "Phone Number",
        validators=[
            InputRequired("Please enter your phone number"),
            Length(min=8, max=15, message="Phone number must be between 8 and 15 digits"),
            Regexp(
                regex=r'^[\d\s+\-()]+$',
                message="Phone number can only contain digits, spaces, '+', '-', or parentheses"
            )
        ]
    )

    password = PasswordField(
        "Password",
        validators=[
            InputRequired("Please enter your password"),
            Length(min=6, message="Password must be at least 6 characters long"),
            Regexp(
                regex=r'^(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>]).+$',
                message="Password must contain at least one number and one special character"
            )
        ]
    )

    confirm = PasswordField(
        "Confirm Password",
        validators=[
            InputRequired("Please confirm your password"),
            EqualTo('password', message="Passwords must match")
        ]
    )

    submit = SubmitField("Register")

    # --- Custom validator for unique email ---
    def validate_email(self, email):
        existing_user = User.query.filter_by(email=email.data).first()
        if existing_user:
            raise ValidationError("This email is already registered. Please use a different one.")

    # --- Optional: custom validator for unique username ---
    def validate_user_name(self, user_name):
        existing_user = User.query.filter_by(username=user_name.data).first()
        if existing_user:
            raise ValidationError("This username is already taken. Please choose another.")


class EventForm(FlaskForm):
    title = StringField("Concert Name", validators=[DataRequired(), Length(max=200)])
    description = TextAreaField("Description", validators=[Length(max=1000)])
    date = DateTimeLocalField("Date & Time", format="%Y-%m-%dT%H:%M", validators=[DataRequired()])
    status = SelectField("Status", choices=[
        ("open", "Open"),
        ("sold out", "Sold Out"),
        ("cancelled", "Cancelled"),
        ("inactive", "Inactive")
    ])
    ticket_type = StringField("Ticket Type", validators=[DataRequired()])
    price = FloatField("Ticket Price", validators=[DataRequired()])
    venue = StringField("Venue", validators=[DataRequired()])
    submit = SubmitField("Create Concert")

class CommentForm(FlaskForm):
    content = TextAreaField("Comment", validators=[DataRequired(), Length(max=500)])
    submit = SubmitField("Post Comment")