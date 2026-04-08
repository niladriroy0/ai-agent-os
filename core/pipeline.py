from agents.manager import AgentManager
from memory.memory_store import MemoryStore

class Pipeline:

    def __init__(self):
        self.memory = MemoryStore()
        self.manager = AgentManager(self.memory)

    def run(self, task):
        try:
            results = self.manager.handle_task(task)

            if not results:
                task.mark_failed()
                return "No valid subtasks generated"

            # Save results
            for idx, res in enumerate(results):
                key = f"{task.task_id}_{idx}"
                self.memory.save(key, res)

            task.mark_completed()
            return results

        except Exception as e:
            task.mark_failed()
            return str(e)