from datetime import date
from flask import Blueprint, abort, render_template, redirect, flash, request, url_for

from sqlalchemy import asc, desc, func, text
from sqlalchemy.exc import SQLAlchemyError
from flask_login import current_user, login_required

from .models import Team, Game, User
from . import db
from .forms import teamInfo_Form, submitResult_Form

bp = Blueprint("wklb", __name__)

def init_wklb(app):
    app.register_blueprint(bp)

@bp.route("/standings", methods=("GET",), strict_slashes=False)
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
                filter((home() & ((homePtsDiff() == -1) | (homePtsDiff() == 0))) |
                       (visit() & ((visitPtsDiff() == -1) | (visitPtsDiff() == 0)))).\
                label("drawLoses")

    pts = (gamesLost * 1 + drawLost * 2 + drawWon * 3 + gamesWon * 4).label("pts")

    homeWonSets = db.select(func.coalesce(func.sum(Game.home_team_pts), 0)).\
                    filter(home()).label("hws")
    homeLostSets = db.select(func.coalesce(func.sum(Game.visiting_team_pts), 0)).\
                    filter(home()).label("hls")
    visitWonSets = db.select(func.coalesce(func.sum(Game.visiting_team_pts), 0)).\
                    filter(visit()).label("vws")
    visitLostSets = db.select(func.coalesce(func.sum(Game.home_team_pts), 0)).\
                    filter(visit()).label("vls")

    wonSets = (homeWonSets + visitWonSets).label("wonSets")
    lostSets = (homeLostSets + visitLostSets).label("lostSets")

    tableStmt = db.select(Team.id, Team.name, numberOfResults, gamesWon,
                          drawWon, drawLost, gamesLost, wonSets, lostSets, pts)\
                                  .join(User)\
                                  .order_by(desc("pts"))\
                                  .order_by(desc(text("wonSets - lostSets")))\
                                  .order_by(desc("wonSets"))

    table = db.session.execute(tableStmt).all()

    return render_template("wklb/standings.html",
                           table=table)


@bp.route("/deleteResult/<id>", methods=("POST",), strict_slashes=False)
@login_required
def deleteResult(id):
    if request.method == "POST":
        g = db.session.get(Game, id)
        if g.home_team.user_id != current_user.id:
            return abort(403)

        try:
            db.session.delete(g)
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            flash(f"An database error occured!", "danger")
        return redirect(url_for("wklb.results"))

    assert(False)

@bp.route("/results", methods=("GET", "POST"), strict_slashes=False)
def results():
    form = submitResult_Form()

    if current_user.is_authenticated: #type: ignore
        # the possible opposing teams
        played_teams = db.select(Game.visiting_team_id)\
                        .where(Game.home_team_id == current_user.team.id) #type: ignore

        stmt = db.select(Team)\
                    .where(Team.id != current_user.team.id)\
                    .where(Team.id.not_in(played_teams))\
                    .order_by(asc("name"))
        teams = db.session.execute(stmt).scalars().all()

        form.visiting_team.choices = [(t.id, t.name) for t in teams]

        if form.validate_on_submit():
            g = Game(home_team_id=current_user.team.id, #type: ignore
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
            return redirect(url_for("wklb.results"))

    stmt = db.select(Game)\
               .order_by(Game.date.desc())\
               .order_by(Game.id.desc())
    res = db.session.execute(stmt).scalars().all()

    return render_template("wklb/results.html", rows=res, form=form)

@bp.route("/teams", methods=(["GET", "POST"]), strict_slashes=False)
@login_required
def teams():
    teamsStmt = db.select(Team).order_by(asc(Team.name))
    teams = db.session.execute(teamsStmt).scalars().all()

    form = teamInfo_Form()
    t = db.session.get(Team, current_user.team.id) #type: ignore

    if form.validate_on_submit():
        t.info = form.info.data
        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            flash(f"An database error occured!", "danger")

    form.info.data = t.info
    return render_template("wklb/teams.html", form=form, teams=teams)

@bp.route("/newTeam", methods=("GET",))
def newTeam():
    from .config import registerCode as rCode
    return render_template("wklb/newTeam.html", registerCode=rCode)

@bp.route("/manifest", methods=("GET",))
def manifest():
    return render_template("wklb/manifest.html")

@bp.route("/about", methods=("GET",))
def about():
    return render_template("wklb/about.html")
