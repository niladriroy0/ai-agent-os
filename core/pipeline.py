from agents.manager import AgentManager
from memory.memory_store import MemoryStore
from scheduler.scheduler import Scheduler

class Pipeline:

    def __init__(self):
        self.memory = MemoryStore()
        self.manager = AgentManager(self.memory)
        self.scheduler = Scheduler()

    def process_task(self, task):
        results = self.manager.handle_task(task)

        if not results:
            task.mark_failed()
            return "No valid subtasks generated"

        # save memory
        for idx, res in enumerate(results):
            key = f"{task.task_id}_{idx}"
            self.memory.save(key, res)

        task.mark_completed()
        return results

    def run(self, task):
        self.scheduler.add_task(task)
        results = self.scheduler.run(self.process_task)

        return results