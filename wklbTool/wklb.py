from datetime import date
from flask import Blueprint, render_template, redirect, flash, request, url_for

from sqlalchemy import asc, desc, func
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
    def home(): return Game.home_team_id == Team.id
    def visit(): return Game.visiting_team_id == Team.id
    def homePtsDiff(): return Game.home_team_pts - Game.visiting_team_pts
    def visitPtsDiff(): return Game.visiting_team_pts - Game.home_team_pts

    numberOfResults = db.select(func.count(Game.id)).\
                        filter(home() | visit()).\
                        label("numberOfResults")

    gamesWon = db.select(func.count(Game.id)).\
                filter((home() & (homePtsDiff() > 1)) |
                       (visit() & (visitPtsDiff() > 1))).\
                label("wins")

    gamesLost = db.select(func.count(Game.id)).\
                filter((home() & (homePtsDiff() < -1)) |
                       (visit() & (visitPtsDiff() < -1))).\
                label("loses")


    drawWon = db.select(func.count(Game.id)).\
                filter((home() & (homePtsDiff() == 1)) |
                       (visit() & (visitPtsDiff() == 1))).\
                label("drawWins")

    drawLost = db.select(func.count(Game.id)).\
                filter((home() & (homePtsDiff() == -1)) |
                       (visit() & (visitPtsDiff() == -1))).\
                label("drawLoses")

    pts = (gamesLost * 1 + drawLost * 2 + drawWon * 3 + gamesWon * 4).label("pts")

    homeWonSets = db.select(func.sum(Game.home_team_pts)).\
                    filter(home()).label("hws")
    homeLostSets = db.select(func.sum(Game.visiting_team_pts)).\
                    filter(home()).label("hls")
    visitWonSets = db.select(func.sum(Game.visiting_team_pts)).\
                    filter(visit()).label("vws")
    visitLostSets = db.select(func.sum(Game.home_team_pts)).\
                    filter(visit()).label("vls")

    wonSets = (homeWonSets + visitWonSets).label("wonSets")
    lostSets = (homeLostSets + visitLostSets).label("lostSets")

    tableStmt = db.select(Team.id, Team.name, numberOfResults, gamesWon,
                          drawWon, drawLost, gamesLost, wonSets, lostSets, pts)\
                                  .order_by(desc("pts"))

    table = db.session.execute(tableStmt).all()

    return render_template("wklb/standings.html", table=table)


@bp.route("/deleteResult/<id>", methods=("GET", "POST"), strict_slashes=False)
def deleteResult(id):
    if request.method == "POST":
        try:
            stmt = db.delete(Game)\
                       .where(Game.id==id)
            db.session.execute(stmt)
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            flash(f"An database error occured!", "danger")
        return redirect(url_for("wklb.results"))
    else:
        g = db.session.get(Game, id)

        if not current_user.is_authenticated or g.home_team != current_user.team:
            return redirect(url_for("wklb.results"))

        return render_template("wklb/deleteResult.html",
                               team1_name=g.home_team.name,
                               team2_name=g.visiting_team.name,
                               id=g.id)

@bp.route("/results", methods=("GET", "POST"), strict_slashes=False)
def results():
    stmt = db.select(Game)\
               .order_by(desc("date"))
    res = db.session.execute(stmt).scalars().all()

    return render_template("wklb/results.html", rows=res)

@bp.route("/teamInfo/<id>", methods=("GET", "POST"), strict_slashes=False)
@login_required
def teamInfo(id):
    form = teamInfo_Form()
    t = db.session.get(Team, id)

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

    played_teams = db.select(Game.visiting_team_id)\
                        .where(Game.home_team_id == current_user.team.id)

    stmt = db.select(Team)\
                .where(Team.id != current_user.team.id)\
                .where(Team.id.not_in(played_teams))\
                .order_by(asc("name"))
    teams = db.session.execute(stmt).scalars().all()

    visiting_teams = [(t.id, t.name) for t in teams]
    form.visiting_team.choices = visiting_teams

    if form.validate_on_submit():
        g = Game(home_team_id=current_user.team.id,
                 visiting_team_id=form.visiting_team.data,
                 home_team_pts=form.home_team_pts.data,
                 visiting_team_pts=form.visiting_team_pts.data,
                 date = date.today())

        try:
            db.session.add(g)
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            flash(f"An database error occured!", "danger")

        return redirect(url_for("wklb.standings"))

    return render_template("wklb/submitResult.html", form=form,
                           home_team=current_user.team.name, text="Submit Game")

