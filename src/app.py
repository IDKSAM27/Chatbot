import os
import secrets

from flask import Flask
from flask_caching import Cache
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from rich.logging import RichHandler

with open("version.txt") as version_file:
    version_txt = version_file.read().strip().splitlines()

VERSION = "-".join(version_txt)

app = Flask(__name__)
app.logger.handlers = [RichHandler()]

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", secrets.token_hex(16))

app.config["CACHE_TYPE"] = "SimpleCache"
app.config["CACHE_DEFAULT_TIMEOUT"] = 300

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///site.db")

cache = Cache(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)

login_manager.login_view = "login"
login_manager.login_message_category = "info"


@login_manager.user_loader
def load_user(user_id: str | int):
    from .models import Users

    return db.session.execute(db.select(Users).filter_by(id=int(user_id))).scalar_one_or_none()


from .models import *  # noqa: E402, F403
from .routes import *  # noqa: E402, F403
from .routes import api_router  # noqa: E402

app.register_blueprint(api_router)
with app.app_context():
    db.create_all()
