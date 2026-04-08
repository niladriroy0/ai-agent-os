from tools.math_tool import execute_math
from tools.logger import log

class ExecutorAgent:

    def execute(self, task):
        log(f"Executing Task {task.task_id}")

        result = execute_math(task.payload)

        log(f"Result: {result}")

        return result