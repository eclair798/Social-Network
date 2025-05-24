from app.clickhouse import ensure_tables
from app.kafka_consumer import start_consumer_thread
from app.routes import serve_grpc_server

if __name__ == "__main__":
    ensure_tables()
    start_consumer_thread()
    serve_grpc_server(port=7000)
