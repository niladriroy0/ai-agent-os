from tools.gateway import ToolGateway

class ExecutorAgent:

    def __init__(self, memory=None):
        self.gateway = ToolGateway()
        self.memory = memory

    def execute(self, task):
        self.gateway.execute("logger", f"Executing Task {task.task_id}")

        expression = task.payload

        # 🧠 Example: use memory keyword
        if "previous" in expression and self.memory:
            all_memory = self.memory.get_all()

            if all_memory:
                last_value = list(all_memory.values())[-1]
                expression = expression.replace("previous", str(last_value))

        result = self.gateway.execute("math", expression)

        self.gateway.execute("logger", f"Result: {result}")

        return result