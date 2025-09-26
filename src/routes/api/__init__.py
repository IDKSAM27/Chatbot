from flask.blueprints import Blueprint

__all__ = ("api_router",)

v1_router = Blueprint("v1", __name__, url_prefix="/v1")

from .v1 import read_root  # noqa

api_router = Blueprint("api", __name__, url_prefix="/api")
api_router.register_blueprint(v1_router)
