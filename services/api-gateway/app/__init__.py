import time
from flask import Flask
from .config import JWT_SECRET_KEY
from .routes import bp

from flask_jwt_extended import JWTManager


def create_app(testing=False):
    app = Flask(__name__)
    
    app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY

    jwt = JWTManager(app)

    app.register_blueprint(bp)

    return app
