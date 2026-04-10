from models.task import Task
from core.pipeline import Pipeline

if __name__ == "__main__":

    pipeline = Pipeline()

    task1 = Task(task_id=1, payload="2+2 and 10*5")
    task2 = Task(task_id=2, payload="previous + 10")

    pipeline.scheduler.add_task(task1)
    pipeline.scheduler.add_task(task2)

    results = pipeline.scheduler.run(pipeline.process_task)

    print("\nFinal Results:")
    for task_id, result in results:
        print(f"Task {task_id}: {result}")