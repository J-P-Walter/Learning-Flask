from app import db, login
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5

#flask db migrate -m "'table_name' table"
    #creates migration script
#flask db upgrade
    #applies changes to database
#flask db downgrade
    #undos last migration

#UserMixin includes generic implementations that are appropriate for most user model classes
class User(UserMixin, db.Model):
    #Column instances as class variables
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    #One-to-many relationship defined on the one side, 
    #First argument is model class, backref is name of field added, lazy comes later
    posts = db.relationship('Post', backref='author', lazy='dynamic')

    #Set and check password functions using werkzeug
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    #Uses Gravatar to generate random, unique geometric images to be used as avatar image
    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)

    #Print function for debugging
    def __repr__(self):
        return '<User {}>'.format(self.username)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id')) #Foreign key, references id value from user table

    #Print function for debugging
    def __repr__(self):
        return '<Post {}>'.format(self.body)

#Flask-Login retrieves id of actice user from session
#from the database
@login.user_loader
def load_user(id):
    return User.query.get(int(id))