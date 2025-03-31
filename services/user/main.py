from app.database import db

from app import create_app, create_db_with_retries

if __name__ == "__main__":
    app = create_app()
    create_db_with_retries(app, db)
    app.run(host='0.0.0.0', port=5000, debug=True)
