from tools.gateway import ToolGateway
from llm.client import LLMClient
from llm.prompts import planner_prompt
import ast
import re

class PlannerAgent:

    def __init__(self):
        self.gateway = ToolGateway()
        self.llm = LLMClient()

    def plan(self, task):
        payload = task.payload

        if not payload or not isinstance(payload, str):
            self.gateway.execute("logger", "Invalid payload")
            return []

        # 🧠 LLM call
        prompt = planner_prompt(payload)
        response = self.llm.generate(prompt)

        match = re.search(r"\[.*\]", response)

        if match:
            try:
                subtasks = ast.literal_eval(match.group())
            except:
                subtasks = []
        else:
            subtasks = []

        if not subtasks:
            self.gateway.execute("logger", f"LLM parsing failed: {response}")
            return []

        self.gateway.execute("logger", f"LLM planned: {subtasks}")

        return subtasks