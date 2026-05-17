from brokers.consumer import TaskConsumer

from core.pipeline import Pipeline

from models.task import Task


class Worker:

    def __init__(self):

        self.consumer = TaskConsumer()

        self.pipeline = Pipeline()

    def start(self):

        print("[WORKER] Listening for tasks...\n")

        try:

            for message in self.consumer.listen():

                print(
                    f"[WORKER] Received: {message}"
                )

                task = Task(

                    task_id=message["task_id"],

                    payload=message["payload"],

                    priority=message["priority"],

                    dependencies=message["dependencies"]
                )

                result = self.pipeline.process_task(
                    task
                )

                print(
                    f"[WORKER RESULT] {result}\n"
                )

        except KeyboardInterrupt:

            print("\n[WORKER] Shutdown requested")


if __name__ == "__main__":

    worker = Worker()

    worker.start()