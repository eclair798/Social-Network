import time
from flask import Flask
from sqlalchemy.exc import OperationalError
from .database import db
from .config import DATABASE_URI, JWT_SECRET_KEY
from .routes import bp
from .schemas import ma

from flask_jwt_extended import JWTManager


def create_db_with_retries(app, db, retries=5, delay=3):
    for i in range(retries):
        try:
            with app.app_context():
                db.create_all()
                print("Database connected and tables created!")
                return
        except OperationalError as e:
            print(f'Database connection failed ({str(e)}), retrying in {delay} secs...')
            time.sleep(delay)
    print('Could not establish database connection! Exiting.')
    exit(1)

def create_app(testing=False):
    app = Flask(__name__)
    
    if testing:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
    
    app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
    app.config['TESTING'] = testing

    db.init_app(app)
    ma.init_app(app)
    jwt = JWTManager(app)

    app.register_blueprint(bp, url_prefix='/user')

    return app
