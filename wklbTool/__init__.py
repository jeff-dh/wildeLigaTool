from datetime import timedelta
from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .config import secretKey

from .auth import init_auth
from .wklb import init_wklb

def create_app():

    app = Flask(__name__, instance_relative_config=True)

    app.secret_key = secretKey
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database.db"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    @app.before_request
    def session_handler():
        session.permanent = True
        app.permanent_session_lifetime = timedelta(minutes=30)

    db.init_app(app)
    init_wklb(app)
    init_auth(app)

    from flask_migrate import Migrate
    migrate = Migrate()
    migrate.init_app(app, db)

    app.add_url_rule("/", "wklb.news")
    return app
