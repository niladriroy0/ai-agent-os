from tools.logger import log

class PlannerAgent:

    def plan(self, task):
        payload = task.payload

        # 🔒 Safety check
        if not payload or not isinstance(payload, str):
            log("Planner received invalid payload")
            return []

        # 🧠 Basic decomposition
        if "and" in payload:
            subtasks = [p.strip() for p in payload.split("and")]
        else:
            subtasks = [payload]

        # 📜 Logging
        log(f"Planner created subtasks: {subtasks}")

        return subtasks