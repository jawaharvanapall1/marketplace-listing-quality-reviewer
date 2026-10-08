from flask import Flask
from flask_cors import CORS

from .config import Config
from .db import DB
from .rag import PolicyIndex


def create_app(overrides=None):
    app = Flask(__name__)

    app.config.from_object(Config)
    app.config.update(overrides or {})

    # Allow the deployed React frontend to access the Flask API
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": "https://marketplace-listing-quality-reviewer-1.onrender.com"
            }
        }
    )

    app.extensions["db"] = DB(app.config["DATABASE_URL"])
    app.extensions["policy"] = PolicyIndex(app.config["DOCS_DIR"])

    from .routes import api
    app.register_blueprint(api, url_prefix="/api")

    return app