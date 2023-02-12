from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object(Config)
#Database object
db = SQLAlchemy(app)
#migration engine object
migrate = Migrate(app, db)

from app import routes, models #model for database structure

