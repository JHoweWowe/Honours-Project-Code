from flask_caching import Cache
from flask_compress import Compress
from flask_login import LoginManager

cache = Cache()
compress = Compress()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
