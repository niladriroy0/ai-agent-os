from enum import Enum
from datetime import datetime


class TaskStatus(Enum):

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Task:

    def __init__(
        self,
        task_id,
        payload,
        priority=5,
        dependencies=None,
        timeout=10
    ):

        self.task_id = task_id

        self.payload = payload

        self.priority = priority

        self.dependencies = dependencies or []

        self.timeout = timeout

        self.status = TaskStatus.PENDING

        self.created_at = datetime.utcnow()

        self.retries = 0

        self.result = None

    # Needed for heapq
    def __lt__(self, other):

        return self.priority < other.priority

    def mark_running(self):

        self.status = TaskStatus.RUNNING

    def mark_completed(self):

        self.status = TaskStatus.COMPLETED

    def mark_failed(self):

        self.status = TaskStatus.FAILED