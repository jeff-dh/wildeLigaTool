from flask import Blueprint, render_template, redirect, flash, request, url_for

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.exc import SQLAlchemyError
from flask_login import current_user, login_required

from .models import Team, Game, db
from .forms import teamInfo_Form, submitResult_Form
from .config import registerCode

bp = Blueprint("wklb", __name__)

def init_wklb(app):
    app.register_blueprint(bp)

@bp.route("/standings", methods=("GET", "POST"), strict_slashes=False)
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

    return render_template("wklb/standings.html", table=table)


@bp.route("/deleteResult/<id>", methods=("GET", "POST"), strict_slashes=False)
def deleteResult(id):
    if request.method == "POST":
        try:
            db.session.query(Game).filter_by(id=id).delete()
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            flash(f"An database error occured!", "danger")
        return redirect(url_for("wklb.results"))
    else:
        g = db.session.query(Game).filter_by(id=id).first()

        if not current_user.is_authenticated or g.home_team != current_user.team:
            return redirect(url_for("wklb.results"))

        return render_template("wklb/deleteResult.html",
                               team1_name=g.home_team.name,
                               team2_name=g.visiting_team.name,
                               id=g.id)

@bp.route("/results", methods=("GET", "POST"), strict_slashes=False)
def results():
    res = db.session.query(Game).order_by(desc("id")).all()

    return render_template("wklb/results.html", rows=res)

@bp.route("/teamInfo/<id>", methods=("GET", "POST"), strict_slashes=False)
@login_required
def teamInfo(id):
    form = teamInfo_Form()
    t = db.session.query(Team).filter_by(id=id).first()

    if form.validate_on_submit():
        t.info = form.info.data
        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            flash(f"An database error occured!", "danger")

    form.info.data = t.info
    return render_template("wklb/teamInfo.html", team=t, form=form)

@bp.route("/info", strict_slashes=False)
def info():
    return render_template("wklb/info.html", registerCode=registerCode)

@bp.route("/submitResult", methods=("GET", "POST"))
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

        return redirect(url_for("wklb.standings"))

    return render_template("wklb/submitResult.html", form=form,
                           home_team=current_user.team.name, text="Submit Game")

