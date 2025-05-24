import threading
import json
from kafka import KafkaConsumer
from .config import KAFKA_BOOTSTRAP_SERVERS, ACTION_TOPICS
from .clickhouse import get_client

def consume_and_store():
    consumer = KafkaConsumer(
        *ACTION_TOPICS,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        group_id="stat-service"
    )

    ch = get_client()
    for msg in consumer:
        topic = msg.topic
        data = msg.value
        print(f"Stat-consumer got message from {topic}: {data}")
        try:
            if topic == "user-registration":
                ch.execute('INSERT INTO user_registrations (user_id, timestamp) VALUES',
                    [(data['user_id'], data['timestamp'])]
                )
            else:
                ch.execute(
                    'INSERT INTO actions (user_id, entity_id, action_type, timestamp) VALUES',
                    [(data['user_id'], data['entity_id'], data['action_type'], data['timestamp'])]
                )
        except Exception as e:
            print(f"Could NOT insert stat data: {data}, error: {e}")

def start_consumer_thread():
    t = threading.Thread(target=consume_and_store, daemon=True)
    t.start()
