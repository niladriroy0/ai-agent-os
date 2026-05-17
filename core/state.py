class ExecutionState:

    def __init__(self):

        self.completed_tasks = set()

        self.failed_tasks = set()

    def mark_completed(self, task_id):

        self.completed_tasks.add(task_id)

    def mark_failed(self, task_id):

        self.failed_tasks.add(task_id)

    def is_completed(self, task_id):

        return task_id in self.completed_tasks

    def is_failed(self, task_id):

        return task_id in self.failed_tasks