from clickhouse_driver import Client
from .config import CLICKHOUSE_HOST, CLICKHOUSE_PORT, CLICKHOUSE_DB

def get_client():
    return Client(host=CLICKHOUSE_HOST, port=CLICKHOUSE_PORT, database=CLICKHOUSE_DB)

def ensure_tables():
    client = get_client()

    client.execute('''
    CREATE TABLE IF NOT EXISTS actions (
        user_id String,
        entity_id String,    -- post_id
        action_type String,  -- view|like|comment
        timestamp DateTime
    ) ENGINE = MergeTree() ORDER BY (entity_id, timestamp)
    ''')

    client.execute('''
    CREATE TABLE IF NOT EXISTS user_registrations (
        user_id String,
        timestamp DateTime
    ) ENGINE = MergeTree() ORDER BY (user_id, timestamp)
    ''')
