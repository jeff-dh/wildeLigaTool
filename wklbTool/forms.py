from wtforms import SelectField, StringField, PasswordField,\
                    IntegerField, SubmitField, TextAreaField,\
                    ValidationError

from wtforms.validators import InputRequired, Length, EqualTo,\
                               Email, NumberRange

from flask_wtf import FlaskForm

from .models import User, Team
from . import db


class login_form(FlaskForm):
    email = StringField("E-Mail",
                        validators=[InputRequired(), Email(), Length(1, 64)],
                        render_kw={"autofocus":True})

    password = PasswordField("Passwort",
                             validators=[InputRequired(), Length(min=6, max=72)])
    submit = SubmitField("Einloggen")

class register_form(FlaskForm):
    email = StringField("E-Mail",
                        validators=[InputRequired(), Email(), Length(1, 64)],
                        render_kw={"autofocus":True})

    password = PasswordField("Passwort",
                             validators=[InputRequired(), Length(6, 72)])

    cpassword = PasswordField("Passwort bestätigen",
        validators=[
            InputRequired(),
            Length(6, 72),
            EqualTo("password", message="Passwört stimmen nicht überein!"),
        ]
    )
    teamname = StringField("Team-Name", validators=[InputRequired(), Length(2, 64)])
    registerPassword = StringField("Registrierungs-Code", default="")

    submit = SubmitField("Team anmelden")

    def validate_email(self, email):
        stmt = db.select(User)\
                   .filter_by(email=email.data.lower())
        if db.session.execute(stmt).first():
            raise ValidationError("Email already registered!")

    def validate_teamname(self, teamname):
        stmt = db.select(Team)\
                   .filter_by(name=teamname.data)
        if db.session.execute(stmt).first():
            raise ValidationError("Team name already registered!")

    def validate_registerPassword(self, registerPassword):
        from .config import registerCode
        if registerCode != registerPassword.data:
            raise ValidationError("Registrierungs-Code ist nicht korrekt!")

class submitResult_Form(FlaskForm):
    visiting_team = SelectField(coerce=int, validators=[InputRequired()])
    home_team_pts = IntegerField(validators=[InputRequired(), NumberRange(min=0)], default=0)
    visiting_team_pts = IntegerField(validators=[InputRequired(), NumberRange(min=0)], default=0)
    submit = SubmitField("Ergebnis eintragen")

class teamInfo_Form(FlaskForm):
    info = TextAreaField(render_kw={"autofocus":True})
    submit = SubmitField("Speichern")

class adminSeason_form(FlaskForm):
    name = StringField("Saison-Name",
                       validators=[InputRequired()],
                       render_kw={"autofocus": True})
    submit = SubmitField("Neue Saison starten!")

