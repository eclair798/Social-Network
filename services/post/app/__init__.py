import time
from flask import Flask
from sqlalchemy.exc import OperationalError
from .database import db
from .config import POST_DATABASE_URI

def create_app(testing=False):
    app = Flask(__name__)
    
    if testing:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = POST_DATABASE_URI
    
    db.init_app(app)
    return app

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


