from app import create_app, create_db_with_retries, db
from app.routes import serve_grpc_server

if __name__ == "main":
    app = create_app()
    create_db_with_retries(app, db)
    serve_grpc_server(port=6000)
