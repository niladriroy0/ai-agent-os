from tools.gateway import ToolGateway

class PlannerAgent:

    def __init__(self):
        self.gateway = ToolGateway()

    def plan(self, task):
        payload = task.payload

        # 🔒 Safety check
        if not payload or not isinstance(payload, str):
            self.gateway.execute("logger", "Planner received invalid payload")
            return []

        # 🧠 Decomposition
        if "and" in payload:
            subtasks = [p.strip() for p in payload.split("and")]
        else:
            subtasks = [payload]

        # 📜 Logging via gateway
        self.gateway.execute("logger", f"Planner created subtasks: {subtasks}")

        return subtasks