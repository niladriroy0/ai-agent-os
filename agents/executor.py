from tools.gateway import ToolGateway

class ExecutorAgent:

    def __init__(self):
        self.gateway = ToolGateway()

    def execute(self, task):
        # Log start
        self.gateway.execute("logger", f"Executing Task {task.task_id}")

        # Execute math via gateway
        result = self.gateway.execute("math", task.payload)

        # Log result
        self.gateway.execute("logger", f"Result: {result}")

        return result