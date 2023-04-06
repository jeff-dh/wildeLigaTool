from datetime import timedelta
from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData

naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

db = SQLAlchemy(metadata=MetaData(naming_convention=naming_convention))


from . import config

from .auth import init_auth
from .wklb import init_wklb

def create_app():

    app = Flask(__name__, instance_relative_config=True)

    app.secret_key = config.secretKey
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database.db"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    @app.before_request
    def _():
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
