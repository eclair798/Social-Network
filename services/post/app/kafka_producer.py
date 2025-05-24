import os
import json
from kafka import KafkaProducer
from datetime import datetime

class PostKafkaProducer:
    _producer = None

    @staticmethod
    def get_producer():
        if PostKafkaProducer._producer is None:
            bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
            PostKafkaProducer._producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
        return PostKafkaProducer._producer

def produce_event(topic: str, user_id: str, entity_id: str, action_type: str):
    producer = PostKafkaProducer.get_producer()
    event_data = {
        "user_id": user_id,
        "entity_id": entity_id,
        "action_type": action_type,
        "timestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    }
    print(f"Producing event: {event_data} to topic {topic}")
    producer.send(topic, event_data)
    producer.flush()

