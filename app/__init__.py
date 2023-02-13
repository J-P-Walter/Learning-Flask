from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

app = Flask(__name__)
app.config.from_object(Config)
#Database object
db = SQLAlchemy(app)
#migration engine object
migrate = Migrate(app, db)
login = LoginManager(app)
#used to have login-only view, add @login_required
#under @app.route decorators
login.login_view = 'login'

from app import routes, models #model for database structure

