import os

from flask import Flask
from flask_jwt_extended import JWTManager
from datetime import timedelta
from flask_cors import CORS


def create_app(script_info=None):

    # instantiate the app
    app = Flask(
        __name__,
        template_folder="../client/templates",
        static_folder="../client/static",
    )

    # set config
    app_settings = os.getenv("APP_SETTINGS")
    app.config.from_object(app_settings)
    app.config['JWT_SECRET_KEY'] = 'super-secret'
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=12)
    jwt = JWTManager(app)
    cors = CORS(app, resources={r"/*": {"origins": "*"}})

    # register blueprints
    from project.server.main.views import main_blueprint

    app.register_blueprint(main_blueprint)

    # shell context for flask cli
    app.shell_context_processor({"app": app})

    return app
