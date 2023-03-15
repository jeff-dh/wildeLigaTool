from datetime import timedelta
from flask import Flask, session

from .config import secretKey

from .auth import init_auth
from .wklb import init_wklb
from .models import init_db

def create_app():

    app = Flask(__name__, instance_relative_config=True)

    app.secret_key = secretKey
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database.db"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    @app.before_request
    def session_handler():
        session.permanent = True
        app.permanent_session_lifetime = timedelta(minutes=30)

    init_db(app)
    init_wklb(app)
    init_auth(app)

    app.add_url_rule("/", "wklb.standings")
    return app
