from app import db
from datetime import datetime

#flask db migrate -m "'table_name' table"
    #creates migration script
#flask db upgrade
    #applies changes to database
#flask db downgrade
    #undos last migration

class User(db.Model):
    #Column instances as class variables
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    #One-to-many relationship defined on the one side, 
    #First argument is model class, backref is name of field added, lazy comes later
    posts = db.relationship('Post', backref='author', lazy='dynamic')

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