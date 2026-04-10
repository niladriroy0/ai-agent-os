import time
from collections import deque

class Scheduler:

    def __init__(self, max_retries=2):
        self.queue = deque()
        self.max_retries = max_retries

    def add_task(self, task, priority=0):
        task.retries = 0

        if priority > 0:
            self.queue.appendleft(task)
        else:
            self.queue.append(task)

    def run(self, handler):
        results = []

        while self.queue:
            task = self.queue.popleft()

            try:
                result = handler(task)
                results.append((task.task_id, result))

            except Exception as e:
                if task.retries < self.max_retries:
                    task.retries += 1
                    print(f"[RETRY] Task {task.task_id} retry {task.retries}")
                    self.queue.append(task)
                else:
                    results.append((task.task_id, f"FAILED: {str(e)}"))

        return results
