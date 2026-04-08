from models.task import Task
from core.pipeline import Pipeline

if __name__ == "__main__":
    
    task = Task(task_id=1, payload="2+2 and 10*5 and 100/4")

    pipeline = Pipeline()

    result = pipeline.run(task)

    print(f"\nFinal Output: {result}")
    print(f"Task Status: {task.status}")