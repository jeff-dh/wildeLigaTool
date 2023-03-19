from wtforms import SelectField, StringField, PasswordField,\
                    IntegerField, SubmitField, TextAreaField,\
                    ValidationError

from wtforms.validators import InputRequired, Length, EqualTo,\
                               Email, NumberRange

from flask_wtf import FlaskForm

from .models import User, Team, db


class login_form(FlaskForm):
    email = StringField("E-Mail", validators=[InputRequired(), Email(), Length(1, 64)])
    password = PasswordField("Passwort", validators=[InputRequired(), Length(min=6, max=72)])
    submit = SubmitField("Einloggen")

class register_form(FlaskForm):
    email = StringField("E-Mail", validators=[InputRequired(), Email(), Length(1, 64)])
    password = PasswordField("Passwort", validators=[InputRequired(), Length(6, 72)])
    cpassword = PasswordField("Passwort bestätigen",
        validators=[
            InputRequired(),
            Length(6, 72),
            EqualTo("password", message="Passwords must match !"),
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

    def validate_visiting_team_pts(self, visiting_team_pts):
        if visiting_team_pts.data == self.home_team_pts.data:
            raise ValidationError("Unentschieden gibt es nach den Regeln nicht....")

class teamInfo_Form(FlaskForm):
    info = TextAreaField()
    submit = SubmitField("Speichern")

