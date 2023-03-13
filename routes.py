from flask import render_template, redirect, flash, request, url_for, session

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from flask_bcrypt import check_password_hash
from flask_login import login_user, current_user, logout_user, login_required

from markupsafe import Markup
from datetime import timedelta

from app import create_app, db, login_manager, bcrypt
from db import User, Team, Game
from forms import login_form,register_form, submitResult_Form, teamInfo_Form
from config import registerCode


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app = create_app()

@app.before_request
def session_handler():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=30)


@app.route("/standings", methods=("GET", "POST"), strict_slashes=False)
def standings():
    numberOfResults = db.session.query(func.count(Game.id)).\
                        filter(or_(Game.home_team_id == Team.id,\
                                   Game.visiting_team_id == Team.id)).\
                        label("numberOfResults")

    gamesWon = db.session.query(func.count(Game.id)).\
                        filter(or_(and_(Game.home_team_id == Team.id,\
                               Game.home_team_pts - Game.visiting_team_pts > 1),
                                   and_(Game.visiting_team_id == Team.id,
                                        Game.visiting_team_pts - Game.home_team_pts > 1))).\
                        label("wins")

    gamesLost = db.session.query(func.count(Game.id)).\
                        filter(or_(and_(Game.home_team_id == Team.id,\
                               Game.home_team_pts - Game.visiting_team_pts < -1),
                                   and_(Game.visiting_team_id == Team.id,
                                        Game.visiting_team_pts - Game.home_team_pts < -1))).\
                        label("loses")

    drawWon = db.session.query(func.count(Game.id)).\
                        filter(or_(and_(Game.home_team_id == Team.id,\
                               Game.home_team_pts - Game.visiting_team_pts == 1),
                                   and_(Game.visiting_team_id == Team.id,
                                        Game.visiting_team_pts - Game.home_team_pts == 1))).\
                        label("drawWins")

    drawLost = db.session.query(func.count(Game.id)).\
                        filter(or_(and_(Game.home_team_id == Team.id,\
                               Game.home_team_pts - Game.visiting_team_pts == -1),
                                   and_(Game.visiting_team_id == Team.id,
                                        Game.visiting_team_pts - Game.home_team_pts == -1))).\
                        label("drawLoses")

    pts = (gamesWon * 4 + gamesLost * 1 + drawLost * 2 + drawWon * 3).label("pts")

    table = db.session.query(Team.id, Team.name, numberOfResults, gamesWon,
                             drawWon, drawLost, gamesLost, pts)\
                                    .order_by(desc("pts")).all()

    return render_template("standings.html", table=table)


@app.route("/deleteResult/<id>", methods=("GET", "POST"), strict_slashes=False)
def deleteResult(id):
    if request.method == "POST":
        try:
            db.session.query(Game).filter_by(id=id).delete()
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            flash(f"An database error occured!", "danger")
        return redirect(url_for("results"))
    else:
        g = db.session.query(Game).filter_by(id=id).first()

        if not current_user.is_authenticated or g.home_team != current_user.team:
            return redirect(url_for("results"))

        return render_template("deleteResult.html",
                               team1_name=g.home_team.name,
                               team2_name=g.visiting_team.name,
                               id=g.id)

@app.route("/results", methods=("GET", "POST"), strict_slashes=False)
def results():
    res = db.session.query(Game).order_by(desc("id")).all()

    return render_template("results.html", rows=res)

@app.route("/teamInfo/<id>", methods=("GET", "POST"), strict_slashes=False)
@login_required
def teamInfo(id):
    form = teamInfo_Form()
    t = db.session.query(Team).filter_by(id=id).first()

    if form.validate_on_submit():
        t.info = form.info.data.replace("\n", "<br>")
        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            flash(f"An database error occured!", "danger")

    form.info.data = t.info.replace("<br>", "\n")
    t.info = Markup(t.info)
    return render_template("teamInfo.html", team=t, form=form)

@app.route("/", strict_slashes=False)
@app.route("/info", strict_slashes=False)
def info():
    return render_template("info.html", registerCode=registerCode)

@app.route("/login/", methods=("GET", "POST"), strict_slashes=False)
def login():
    form = login_form()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user is not None and check_password_hash(user.password, form.password.data):
            login_user(user)
            next_page = request.form.get('next_page')
            assert next_page
            if "None" in next_page:
                return redirect(url_for("info"))
            else:
                return redirect(next_page)

        else:
            flash("Invalid email or password!", "danger")

    return render_template("auth.html", form=form, text="Login",
                           btn_action="Anmelden")


@app.route("/register/", methods=("GET", "POST"), strict_slashes=False)
def register():
    form = register_form()

    if form.validate_on_submit():

        if  form.registerPassword.data != registerCode:
            flash("Registrierungs-Code ist nicht korrekt", "warning")
        else:
            try:
                email = form.email.data.lower()
                password = form.password.data

                newuser = User(email=email, #type: ignore
                               password=bcrypt.generate_password_hash(password))

                db.session.add(newuser)
                db.session.commit()

                newteam = Team(name = form.teamname.data, info="", user_id=newuser.id)
                db.session.add(newteam)
                db.session.commit()

                flash(f"Account Succesfully created", "success")
                return redirect(url_for("login"))

            except IntegrityError:
                db.session.rollback()
                flash(f"User already exists!.", "warning")
            except SQLAlchemyError:
                db.session.rollback()
                flash(f"An database error occured!", "danger")

    return render_template("auth.html", form=form, text="Create account",
                           btn_action="Team registrieren")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('info'))


@app.route("/submitResult", methods=("GET", "POST"))
@login_required
def submitResult():
    form = submitResult_Form()

    played_teams = db.session.query(Game.visiting_team_id).\
                        filter_by(home_team_id=current_user.team.id)

    teams = db.session.query(Team).\
                filter(Team.id != current_user.team.id).\
                filter(Team.id.not_in(played_teams)).all()

    visiting_teams = [(t.id, t.name) for t in teams]
    form.visiting_team.choices = visiting_teams


    if form.validate_on_submit():
        g = Game(home_team_id=current_user.team.id,
                 visiting_team_id=form.visiting_team.data,
                 home_team_pts=form.home_team_pts.data,
                 visiting_team_pts=form.visiting_team_pts.data)

        try:
            db.session.add(g)
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            flash(f"An database error occured!", "danger")

        return redirect(url_for("standings"))

    return render_template("submitResult.html", form=form,
                           home_team=current_user.team.name, text="Submit Game")


if __name__ == "__main__":
    app.run(debug=True)

