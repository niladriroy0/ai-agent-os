from tools.math_tool import MathTool
from tools.logger import LoggerTool

class ToolRegistry:

    def __init__(self):
        self.tools = {}

        self.register(MathTool())
        self.register(LoggerTool())

    def register(self, tool):
        self.tools[tool.name] = tool

    def get_tool(self, tool_name):
        return self.tools.get(tool_name)