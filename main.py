from brokers.producer import TaskProducer

from models.task import Task


if __name__ == "__main__":

    producer = TaskProducer()

    # ==========================================
    # TASK 1
    # ==========================================

    task1 = Task(

        task_id="task_1",

        payload="2+2 and 10*5",

        priority=1
    )

    # ==========================================
    # TASK 2
    # ==========================================

    task2 = Task(

        task_id="task_2",

        payload="previous + 100",

        priority=2
    )

    # ==========================================
    # SEND TASKS
    # ==========================================

    producer.send_task(task1)

    producer.send_task(task2)