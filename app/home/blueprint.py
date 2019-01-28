from flask import Blueprint

# Define blueprint: 'home', set its url prefix: app.url/home
home = Blueprint('home', __name__, url_prefix='/home', template_folder='templates', static_folder='static')
