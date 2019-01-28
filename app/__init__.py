from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session

app = Flask(__name__)

# Configure application
app.config.from_object('config')
Session(app)

# Change configuration to connect to new database (SQLAchemy)
print("Database used: "+app.config['SQLALCHEMY_DATABASE_URI'])
db = SQLAlchemy(app)

# import the blueprints
from .finance import blueprint, views
app.register_blueprint(blueprint.finance)
from .home import blueprint, views
app.register_blueprint(blueprint.home)

db.create_all()

@app.route("/")
def goingHome():
    return redirect(url_for("home.index"))

from werkzeug.exceptions import default_exceptions
from .finance.views import errorhandler
# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
