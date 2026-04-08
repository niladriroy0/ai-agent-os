from tools.registry import ToolRegistry

class ToolGateway:

    def __init__(self):
        self.registry = ToolRegistry()

    def execute(self, tool_name, input_data):
        tool = self.registry.get_tool(tool_name)

        if not tool:
            return f"Tool '{tool_name}' not found"

        # 🔒 Future: permission check here
        # 🔒 Future: rate limiting here
        # 🔒 Future: logging here

        return tool.execute(input_data)