from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, relationship
from flask_login import UserMixin

db = SQLAlchemy()

def init_db(app):
    db.init_app(app)

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(Text, nullable=False)
    password = Column(Text)
    team : Mapped["Team"] = relationship("Team", back_populates="user", uselist=False)

    def verify_password(self, password):
        import bcrypt
        return bcrypt.checkpw(password, self.password)


class Team(db.Model):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)
    info = Column(Text, nullable=False)
    user_id = Column(ForeignKey(User.id))

    user : Mapped["User"] = relationship("User", back_populates="team", uselist=False)

class Game(db.Model):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True)
    home_team_id = Column(ForeignKey(Team.id))
    visiting_team_id = Column(ForeignKey(Team.id))
    home_team_pts = Column(Integer)
    visiting_team_pts = Column(Integer)

    home_team : Mapped["Team"] = relationship("Team", foreign_keys=home_team_id, uselist=False)
    visiting_team : Mapped["Team"] = relationship("Team", foreign_keys=visiting_team_id, uselist=False)

if __name__ == "__main__":
	from app import create_app, db

	app = create_app()
	app.app_context().push()
	db.create_all()

