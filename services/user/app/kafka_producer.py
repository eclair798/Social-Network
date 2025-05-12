import os
import json
from datetime import datetime

from kafka import KafkaProducer

class UserKafkaProducer:
    _producer = None

    @staticmethod
    def get_producer():
        if UserKafkaProducer._producer is None:
            bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
            UserKafkaProducer._producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers, value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
        return UserKafkaProducer._producer

def produce_user_registered_event(user_id: str):
    producer = UserKafkaProducer.get_producer()
    event_data = {
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat()
    }
    producer.send("user-registration", event_data)
    producer.flush()

