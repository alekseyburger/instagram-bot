from web_app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from web_app import login_manager


@login_manager.user_loader
def load_user(id):
    return AdminPassword.query.get(int(id))

class AdminPassword (UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)  

class Following (db.Model):
    name = db.Column(db.String(64), unique=True, primary_key=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class SpyTrack (db.Model):
        __tablename__ = 'spytrack'
        uname =  db.Column(db.String(30), index=True)
        id =    db.Column(db.String(30), index=True)
        following_name  =    db.Column(db.String(30))
        following_id    =    db.Column(db.String(30))
        following_tag   =    db.Column(db.String(30))
        following_count =    db.Column(db.Integer)
        time            =    db.Column(db.String(30))
        __table_args__ = (db.PrimaryKeyConstraint(uname, following_name,),)