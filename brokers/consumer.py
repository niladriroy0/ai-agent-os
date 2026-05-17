import json

from kafka import KafkaConsumer

from config.kafka_config import (
    KAFKA_BROKER,
    TASK_TOPIC
)


class TaskConsumer:

    def __init__(self):

        self.consumer = KafkaConsumer(

            TASK_TOPIC,

            bootstrap_servers=KAFKA_BROKER,

            auto_offset_reset="latest",

            enable_auto_commit=True,

            group_id="agent-workers",

            value_deserializer=lambda x:
            json.loads(x.decode("utf-8"))
        )

    def listen(self):

        for message in self.consumer:

            yield message.value