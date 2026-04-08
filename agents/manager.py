from agents.planner import PlannerAgent
from agents.executor import ExecutorAgent
from models.task import Task

class AgentManager:

    def __init__(self, memory=None):
        self.planner = PlannerAgent()
        self.executor = ExecutorAgent(memory)

    def handle_task(self, task):
        subtasks = self.planner.plan(task)

        results = []

        for idx, sub in enumerate(subtasks):
            subtask_id = f"{task.task_id}_{idx}"
            subtask = Task(task_id=subtask_id, payload=sub)

            result = self.executor.execute(subtask)
            results.append(result)

        return results