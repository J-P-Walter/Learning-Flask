from app import db, login
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5
from time import time
import jwt
from app import app

#flask db migrate -m "'table_name' table"
    #creates migration script
#flask db upgrade
    #applies changes to database
#flask db downgrade
    #undos last migration

#Auxiliary table, no data other than foreign keys so doesn't need model class
followers = db.Table(
    'followers', 
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')), 
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id')))

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
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    #Many-to-many, 
    followed = db.relationship( 
        'User',                                             #model class that parent class is related to, "right side"
        secondary=followers,                                #configures the association table, found above
        primaryjoin=(followers.c.follower_id == id),        #condition that links the parent class with association table, "left side"
        secondaryjoin=(followers.c.followed_id == id),      #condition that links model class (ie User) with association table, "right side"
        backref=db.backref('followers', lazy='dynamic'),    #define how accessed from right side
        lazy='dynamic')

    #Set and check password functions using werkzeug
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    #Uses Gravatar to generate random, unique geometric images to be used as avatar image
    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)

    #Following logic
    #Can use append and remove due to SQLAlchemy ORM
    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)
    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)
    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):
        # join on followers and Post table by condition where followed_id == user_id
        #filter where only results are where self is following
        #order by timestamp
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
                followers.c.follower_id == self.id)

        #Query for own posts
        own = Post.query.filter_by(user_id=self.id)
        #Union for followed and own posts
        return followed.union(own).order_by(Post.timestamp.desc())
    
    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

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

