from sqlalchemy import Boolean, Column, ForeignKey, Integer, Text, Date
from sqlalchemy.orm import Mapped, relationship
from flask_login import UserMixin

from . import db

class User(UserMixin, db.Model): #type: ignore
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(Text, nullable=False)
    password = Column(Text, nullable=False)

    team : Mapped["Team"] = \
            relationship("Team", back_populates="user", uselist=False)

class Season(db.Model): #type: ignore
    __tablename__ = "seasons"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)

class Team(db.Model): #type: ignore
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)
    info = Column(Text, nullable=False, default="")
    user_id = Column(ForeignKey(User.id), nullable=False)

    user : Mapped["User"] = \
            relationship("User", back_populates="team", uselist=False)

class Game(db.Model): #type: ignore
    __tablename__ = "games"

    id = Column(Integer, primary_key=True)
    home_team_id = Column(ForeignKey(Team.id), nullable=False)
    visiting_team_id = Column(ForeignKey(Team.id), nullable=False)
    home_team_pts = Column(Integer, nullable=False)
    visiting_team_pts = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)
    season_id = Column(ForeignKey(Season.id), nullable=False)

    home_team : Mapped["Team"] = \
            relationship("Team", foreign_keys=home_team_id, uselist=False)
    visiting_team : Mapped["Team"] = \
            relationship("Team", foreign_keys=visiting_team_id, uselist=False)

