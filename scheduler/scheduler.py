import heapq
import logging



from core.state import ExecutionState


# ==========================================
# LOGGER CONFIG
# ==========================================

logging.basicConfig(
    filename="logs/system.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


class Scheduler:

    def __init__(self, max_retries=2):

        self.queue = []

        self.max_retries = max_retries

        self.state = ExecutionState()

    # ==========================================
    # ADD TASK
    # ==========================================

    def add_task(self, task):

        heapq.heappush(
            self.queue,
            (task.priority, task)
        )

        logging.info(
            f"Task Added: {task.task_id}"
        )

    # ==========================================
    # DEPENDENCY CHECK
    # ==========================================

    def dependencies_completed(self, task):

        return all(
            self.state.is_completed(dep)
            for dep in task.dependencies
        )

    # ==========================================
    # EXECUTE TASK
    # ==========================================

    def execute_task(self, handler, task):

        return handler(task)

    # ==========================================
    # MAIN LOOP
    # ==========================================

    def run(self, handler):

        results = []

        while self.queue:

            _, task = heapq.heappop(self.queue)

            # ==========================================
            # DEPENDENCY CHECK
            # ==========================================

            if not self.dependencies_completed(task):

                logging.info(
                    f"Task {task.task_id} waiting for dependencies"
                )

                heapq.heappush(
                    self.queue,
                    (task.priority, task)
                )

                continue

            try:

                task.mark_running()

                logging.info(
                    f"Running Task: {task.task_id}"
                )

                # ==========================================
                # EXECUTION
                # ==========================================

                result = self.execute_task(
                    handler,
                    task
                )

                # ==========================================
                # STORE RESULT
                # ==========================================

                task.result = result

                task.mark_completed()

                self.state.mark_completed(
                    task.task_id
                )

                logging.info(
                    f"Completed Task: {task.task_id}"
                )

                results.append(result)

            # ==========================================
            # GENERAL FAILURE
            # ==========================================

            except Exception as e:

                logging.error(
                    f"Task Failed: "
                    f"{task.task_id} | {str(e)}"
                )

                if task.retries < self.max_retries:

                    task.retries += 1

                    logging.warning(
                        f"Retrying Task "
                        f"{task.task_id} "
                        f"Attempt {task.retries}"
                    )

                    heapq.heappush(
                        self.queue,
                        (task.priority, task)
                    )

                else:

                    task.mark_failed()

                    self.state.mark_failed(
                        task.task_id
                    )

                    results.append({
                        "task_id": task.task_id,
                        "status": "FAILED",
                        "reason": str(e)
                    })

        return results