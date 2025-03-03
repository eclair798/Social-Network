import time
from flask import Flask
from sqlalchemy.exc import OperationalError
from app.database import db
from app.config import DATABASE_URI, JWT_SECRET_KEY
from app.routes import bp
from app.schemas import ma

from flask_jwt_extended import JWTManager

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY

db.init_app(app)
ma.init_app(app)
app.register_blueprint(bp, url_prefix='/user')



jwt = JWTManager(app)

def create_db_with_retries(retries=5, delay=3):
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

if __name__ == "__main__":
    create_db_with_retries()
    app.run(host='0.0.0.0', port=5000, debug=True)
