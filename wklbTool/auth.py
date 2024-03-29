from flask import Blueprint, render_template, redirect, flash, request, url_for

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from flask_login import LoginManager, login_user, logout_user, login_required
from flask_bcrypt import Bcrypt

from .models import User, Team
from . import db
from .forms import login_form,register_form


login_manager = LoginManager()
login_manager.session_protection = "strong"
login_manager.login_view = "auth.login"
login_manager.login_message = "Bitte einloggen, um diese Seite zu sehen!"
login_manager.login_message_category = "info"

bcrypt = Bcrypt()

bp = Blueprint("auth", __name__, url_prefix="/auth")

def init_auth(app):
    login_manager.init_app(app)
    bcrypt.init_app(app)
    app.register_blueprint(bp)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)

@bp.route("/login/", methods=("GET", "POST"), strict_slashes=False)
def login():
    form = login_form()

    if form.validate_on_submit():
        stmt = db.select(User)\
                   .filter_by(email=form.email.data.lower())
        user = db.session.execute(stmt).scalars().first()

        if user is not None and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            next_page = request.form.get('next_page')
            assert next_page
            if "None" in next_page:
                return redirect("/")
            else:
                return redirect(next_page)

        else:
            flash("Falsche E-Mail oder Passwort!", "danger")

    return render_template("auth/login.html", form=form)


@bp.route("/register/", methods=("GET", "POST"), strict_slashes=False)
def register():
    form = register_form()

    if form.validate_on_submit():
        email = form.email.data.lower()
        password = form.password.data

        pwhash = bcrypt.generate_password_hash(password)
        newuser = User(email=email, password=pwhash) #type: ignore

        try:
            db.session.add(newuser)
            db.session.commit()

            newteam = Team(name = form.teamname.data, user_id=newuser.id)

            db.session.add(newteam)
            db.session.commit()

            flash(f"Team wurde erfolgreich angemeldet!", "success")
            login_user(newuser)
            return redirect("/")

        except IntegrityError:
            db.session.rollback()
            flash(f"User already exists!.", "warning")
        except SQLAlchemyError:
            db.session.rollback()
            flash(f"An database error occured!", "danger")

    return render_template("auth/register.html", form=form)


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


