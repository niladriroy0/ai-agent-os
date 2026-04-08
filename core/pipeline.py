from agents.manager import AgentManager

class Pipeline:

    def __init__(self):
        self.manager = AgentManager()

    def run(self, task):
        try:
            results = self.manager.handle_task(task)

            if not results:
                task.mark_failed()
                return "No valid subtasks generated"

            task.mark_completed()
            return results

        except Exception as e:
            task.mark_failed()
            return str(e)