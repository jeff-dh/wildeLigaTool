from datetime import date
from flask import Blueprint, abort, render_template, redirect, flash, request, url_for

from sqlalchemy import asc, desc, func, text
from sqlalchemy.exc import SQLAlchemyError
from flask_login import current_user, login_required
from flask_basicauth import BasicAuth

from .models import Team, Game, User, Season
from .forms import adminSeason_form, teamInfo_Form, submitResult_Form

from . import db
from . import config

bp = Blueprint("wklb", __name__)

basic_auth = BasicAuth()

def init_wklb(app):
    app.register_blueprint(bp)
    app.config["BASIC_AUTH_USERNAME"] = "admin"
    app.config["BASIC_AUTH_PASSWORD"] = config.adminPassword
    basic_auth.init_app(app)

def getSeasonId():
    seasonStmt = db.select(func.max(Season.id))
    season_id = db.session.execute(seasonStmt).scalars().one()
    if season_id == None:
        flash("Es wurde noch keine Saison angelegt!", "danger")
    return season_id

@bp.route("/standings", methods=("GET",), strict_slashes=False)
def standings():
    season_id = getSeasonId()

    def home(): return Game.home_team_id == Team.id
    def visit(): return Game.visiting_team_id == Team.id
    def homePtsDiff(): return Game.home_team_pts - Game.visiting_team_pts
    def visitPtsDiff(): return Game.visiting_team_pts - Game.home_team_pts
    def season():
        if season_id == None:
            return False
        return Game.season_id == season_id


    numberOfResults = db.select(func.count(Game.id)).\
                        filter(season()).\
                        filter(home() | visit()).\
                        label("numberOfResults")

    gamesWon = db.select(func.count(Game.id)).\
                filter(season()).\
                filter((home() & (homePtsDiff() > 1)) |
                       (visit() & (visitPtsDiff() > 1))).\
                label("wins")

    gamesLost = db.select(func.count(Game.id)).\
                filter(season()).\
                filter((home() & (homePtsDiff() < -1)) |
                       (visit() & (visitPtsDiff() < -1))).\
                label("loses")

    drawWon = db.select(func.count(Game.id)).\
                filter(season()).\
                filter((home() & (homePtsDiff() == 1)) |
                       (visit() & (visitPtsDiff() == 1))).\
                label("drawWins")

    drawLost = db.select(func.count(Game.id)).\
                filter(season()).\
                filter((home() & ((homePtsDiff() == -1) | (homePtsDiff() == 0))) |
                       (visit() & ((visitPtsDiff() == -1) | (visitPtsDiff() == 0)))).\
                label("drawLoses")

    pts = (gamesLost * 1 + drawLost * 2 + drawWon * 3 + gamesWon * 4).label("pts")

    homeWonSets = db.select(func.coalesce(func.sum(Game.home_team_pts), 0)).\
                    filter(season()).\
                    filter(home()).label("hws")
    homeLostSets = db.select(func.coalesce(func.sum(Game.visiting_team_pts), 0)).\
                    filter(season()).\
                    filter(home()).label("hls")
    visitWonSets = db.select(func.coalesce(func.sum(Game.visiting_team_pts), 0)).\
                    filter(season()).\
                    filter(visit()).label("vws")
    visitLostSets = db.select(func.coalesce(func.sum(Game.home_team_pts), 0)).\
                    filter(season()).\
                    filter(visit()).label("vls")

    wonSets = (homeWonSets + visitWonSets).label("wonSets")
    lostSets = (homeLostSets + visitLostSets).label("lostSets")

    tableStmt = db.select(Team.id, Team.name, numberOfResults, gamesWon,
                          drawWon, drawLost, gamesLost, wonSets, lostSets, pts)\
                                  .join(User)\
                                  .order_by(desc("pts"))\
                                  .order_by(desc(text("wonSets - lostSets")))\
                                  .order_by(desc("wonSets"))\
                                  .filter(text("numberOfResults > 0"))

    table = db.session.execute(tableStmt).all()

    teamsWithoutGamesStmt = db.select(Team.name, numberOfResults).filter(text("numberOfResults == 0"))
    teamsWithoutGames = db.session.execute(teamsWithoutGamesStmt).scalars().all()

    return render_template("wklb/standings.html",
                           table=table, teamsWithoutGames=teamsWithoutGames)


@bp.route("/deleteResult/<id>", methods=("POST",), strict_slashes=False)
@login_required
def deleteResult(id):
    if request.method == "POST":
        g = db.session.get(Game, id)
        if g.home_team.user_id != current_user.id: #type: ignore
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

    season_id = getSeasonId()

    if current_user.is_authenticated: #type: ignore
        # the possible opposing teams
        played_teams = db.select(Game.visiting_team_id)\
                        .filter(Game.season_id == season_id)\
                        .filter(Game.home_team_id == current_user.team.id) #type: ignore

        assert(isinstance(current_user, User))
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
                    date = date.today(),
                    season_id = season_id)

            try:
                db.session.add(g)
                db.session.commit()
            except SQLAlchemyError:
                db.session.rollback()
                flash(f"An database error occured!", "danger")
            return redirect(url_for("wklb.results"))

    stmt = db.select(Game)\
               .order_by(Game.date.desc())\
               .order_by(Game.id.desc())\
               .filter(Game.season_id == season_id)
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

def dynamicContent(url, title):
    return render_template("wklb/dynamicContent.html", url=url, title=title)

@bp.route("/newTeam", methods=("GET",))
def newTeam():
    url = "https://p624608.webspaceconfig.de/wklbBoard/printthread.php?tid=3"
    return dynamicContent(url, "Neues Team anmelden")

@bp.route("/manifest", methods=("GET",))
def manifest():
    url = "https://p624608.webspaceconfig.de/wklbBoard/printthread.php?tid=4"
    return dynamicContent(url, "Manifest / Regeln")

@bp.route("/about", methods=("GET",))
def about():
    url = "https://p624608.webspaceconfig.de/wklbBoard/printthread.php?tid=2"
    return dynamicContent(url, "Über die Liga")

@bp.route("/news", methods=("GET",))
def news():
    url = "https://p624608.webspaceconfig.de/wklbBoard/portal.php"
    return dynamicContent(url, "News")

@bp.route("/admin", methods=["GET", "POST"])
@basic_auth.required
def admin():
    form = adminSeason_form()

    if form.validate_on_submit():
        new_season = Season(name=form.name.data)
        db.session.add(new_season)
        db.session.commit()
        return redirect(url_for("wklb.standings"))

    return render_template("wklb/admin.html", form=form)
