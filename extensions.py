from flask_caching import Cache
from flask_compress import Compress
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager

cache = Cache()
compress = Compress()
limiter = Limiter(key_func=get_remote_address)
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
