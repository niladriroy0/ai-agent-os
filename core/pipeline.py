from agents.manager import AgentManager

from memory.memory_store import MemoryStore

from scheduler.scheduler import Scheduler


class Pipeline:

    def __init__(self):

        self.memory = MemoryStore()

        self.manager = AgentManager(
            self.memory
        )

        self.scheduler = Scheduler()

    # ==========================================
    # PROCESS TASK
    # ==========================================

    def process_task(self, task):

        results = self.manager.handle_task(task)

        if not results:

            task.mark_failed()

            return {
                "task_id": task.task_id,
                "status": "FAILED",
                "results": []
            }

        # ==========================================
        # SAVE MEMORY
        # ==========================================

        for idx, res in enumerate(results):

            key = f"{task.task_id}_{idx}"

            self.memory.save(
                key,
                res
            )

        task.mark_completed()

        return {
            "task_id": task.task_id,
            "results": results,
            "status": task.status.value
        }

    # ==========================================
    # RUN PIPELINE
    # ==========================================

    def run(self, task):

        self.scheduler.add_task(task)

        return self.scheduler.run(
            self.process_task
        )