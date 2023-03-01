from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import os
from flask_mail import Mail
from flask_bootstrap import Bootstrap

app = Flask(__name__)
app.config.from_object(Config)

#Flask Extensions:
#Database object, SQLAlchemy database
db = SQLAlchemy(app)

#migration engine object
migrate = Migrate(app, db)

login = LoginManager(app)

#used to have login-only view, add @login_required
#under @app.route decorators
login.login_view = 'login'

#uses flask_mail to email users
mail = Mail(app)

#bootstrap for css
bootstrap = Bootstrap(app)

#Error handling when not in debug, 
#Creates smtphandler, sets level to only report errors
#and attaches it to app.logger
# TO VIEW IN TERMINAL:
# python -m smtpd -n -c DebuggingServer localhost:8025 in separate terminal
# export MAIL_SERVER=localhost
# export MAIL_PORT=8025
# set FLASK_DEBUG to false
# if not app.debug:
#     if app.config['MAIL_SERVER']:
#         auth = None
#         if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
#             auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
#         secure = None
#         if app.config['MAIL_USE_TLS']:
#             secure = ()
#         mail_handler = SMTPHandler(
#             mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
#             fromaddr='no-reply@' + app.config['MAIL_SERVER'],
#             toaddrs=app.config['ADMINS'], subject='Microblog Failure',
#             credentials=auth, secure=secure)
#         mail_handler.setLevel(logging.ERROR)
#         app.logger.addHandler(mail_handler)

#Alternate to email logging errors
#RotatingFileHandler makes sure log files don't get too large
#Formatter provides custom formatting
#
if not app.debug:
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/microblog.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Microblog startup')

#import down here to avoid circular import
from app import routes, models, errors

