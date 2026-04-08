from models.task import Task
from core.pipeline import Pipeline

if __name__ == "__main__":

    pipeline = Pipeline()

    # ✅ First task (stores memory)
    task1 = Task(task_id=1, payload="2+2 and 10*5 and 100/4")
    result1 = pipeline.run(task1)

    print(f"\nTask 1 Output: {result1}")

    # ✅ Second task (uses memory)
    task2 = Task(task_id=2, payload="previous + 10")
    result2 = pipeline.run(task2)

    print(f"\nTask 2 Output: {result2}")