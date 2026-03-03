from flask import Flask
from .services.db import init_db
from .services.config_manager import config

def create_app():
    app = Flask(__name__)
    app.secret_key = 'ksef-panel-local-desktop-app'
    app.config['JSON_AS_ASCII'] = False

    init_db()

    from .routes import register_routes
    register_routes(app)

    return app
