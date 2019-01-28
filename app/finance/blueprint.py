from flask import Blueprint

# Define blueprint: 'finance', set its url prefix: app.url/finance
finance = Blueprint('finance', __name__, url_prefix='/finance', template_folder='templates', static_folder='static')
