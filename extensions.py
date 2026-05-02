from flask_caching import Cache
from flask_login import LoginManager

cache = Cache()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
