import json

from kafka import KafkaProducer

from config.kafka_config import (
    KAFKA_BROKER,
    TASK_TOPIC
)


class TaskProducer:

    def __init__(self):

        self.producer = KafkaProducer(

            bootstrap_servers=KAFKA_BROKER,

            value_serializer=lambda v:
            json.dumps(v).encode("utf-8")
        )

    def send_task(self, task):

        payload = {

            "task_id": task.task_id,

            "payload": task.payload,

            "priority": task.priority,

            "dependencies": task.dependencies
        }

        self.producer.send(
            TASK_TOPIC,
            payload
        )

        self.producer.flush()

        print(
            f"[KAFKA] Sent Task: {task.task_id}"
        )