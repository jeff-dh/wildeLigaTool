from wtforms import SelectField, StringField, PasswordField,\
                    IntegerField, TextAreaField

from flask_wtf import FlaskForm
from wtforms.validators import InputRequired, Length, EqualTo, Email, NumberRange
from wtforms import ValidationError
from db import User, Team


class login_form(FlaskForm):
    email = StringField(validators=[InputRequired(), Email(), Length(1, 64)])
    password = PasswordField(validators=[InputRequired(), Length(min=6, max=72)])

class register_form(FlaskForm):
    email = StringField(validators=[InputRequired(), Email(), Length(1, 64)])
    password = PasswordField(validators=[InputRequired(), Length(6, 72)])
    cpassword = PasswordField(
        validators=[
            InputRequired(),
            Length(8, 72),
            EqualTo("password", message="Passwords must match !"),
        ]
    )
    teamname = StringField(validators=[InputRequired(), Length(1, 64)])
    registerPassword = StringField(default="")

    def validate_email(self, email):
        if User.query.filter_by(email=email.data).first():
            raise ValidationError("Email already registered!")

    def validate_teamname(self, teamname):
        if Team.query.filter_by(name=teamname.data).first():
            raise ValidationError("Team name already registered!")

class submitResult_Form(FlaskForm):
    visiting_team = SelectField(coerce=int, validators=[InputRequired()])
    home_team_pts = IntegerField(validators=[InputRequired(), NumberRange(min=0)], default=0)
    visiting_team_pts = IntegerField(validators=[InputRequired(), NumberRange(min=0)], default=0)

class teamInfo_Form(FlaskForm):
    info = TextAreaField()

