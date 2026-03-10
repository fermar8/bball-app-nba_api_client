from flask import Flask

from app.routes.api_routes import api_blueprint
from app.services.config import load_environment


def create_app() -> Flask:
    load_environment()
    app = Flask(__name__)
    app.register_blueprint(api_blueprint)
    return app
