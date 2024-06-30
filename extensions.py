from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_ckeditor import CKEditor
from flask_bootstrap import Bootstrap5
from flask_gravatar import Gravatar
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
login_manager = LoginManager()
ckeditor = CKEditor()
bootstrap = Bootstrap5()
gravatar = Gravatar(size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address,
                  default_limits=["200 per day", "50 per hour"])
