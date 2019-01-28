import os

# Statement for enabling the development environment
DEBUG = os.environ['FLASK_DEBUG']

# Define the application directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Define the databse that we are using
SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Ensure that templates are auto-reloaded
TEMPLATES_AUTO_RELOAD = True

# Session configuration to use filesystem (instead of signed cookies)
SESSION_TYPE = "filesystem"
SESSION_PERMANENT = False
SECRET_KEY = '\x9c"U\x17\xbd3\xb5\x92\x1d\x91Fk\x0f\xed\xfec\x0b;\xb5\x9cK\x8e*\xb1'
SESSION_COOKIE_NAME = 'heroku_session'
