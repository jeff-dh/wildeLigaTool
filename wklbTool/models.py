from sqlalchemy import Column, ForeignKey, Integer, Text, Date
from sqlalchemy.orm import Mapped, relationship
from flask_login import UserMixin

from . import db

class User(UserMixin, db.Model): #type: ignore
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(Text, nullable=False)
    password = Column(Text, nullable=False)
    team : Mapped["Team"] = relationship("Team", back_populates="user", uselist=False)

    def verify_password(self, password):
        import bcrypt
        return bcrypt.checkpw(password, self.password)


class Team(db.Model): #type: ignore
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)
    info = Column(Text, nullable=False, default="")
    user_id = Column(ForeignKey(User.id), nullable=False)

    user : Mapped["User"] = relationship("User", back_populates="team", uselist=False)

class Game(db.Model): #type: ignore
    __tablename__ = "games"

    id = Column(Integer, primary_key=True)
    home_team_id = Column(ForeignKey(Team.id), nullable=False)
    visiting_team_id = Column(ForeignKey(Team.id), nullable=False)
    home_team_pts = Column(Integer, nullable=False)
    visiting_team_pts = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)

    home_team : Mapped["Team"] = relationship("Team", foreign_keys=home_team_id, uselist=False)
    visiting_team : Mapped["Team"] = relationship("Team", foreign_keys=visiting_team_id, uselist=False)

if __name__ == "__main__":
	from . import create_app, db

	app = create_app()
	app.app_context().push()
	db.create_all()

