# 📚 Codebase Overview — ai-agent-os

> A module-by-module reference for every file and class in the project.

---

## Table of Contents

1. [Entry Points](#entry-points)
2. [agents/](#agents)
3. [brokers/](#brokers)
4. [config/](#config)
5. [core/](#core)
6. [llm/](#llm)
7. [memory/](#memory)
8. [models/](#models)
9. [scheduler/](#scheduler)
10. [tools/](#tools)
11. [workers/](#workers)
12. [Infrastructure](#infrastructure)
13. [Dependency Graph](#dependency-graph)

---

## Entry Points

### `main.py`

**Purpose:** Seeds the system with tasks and publishes them to Kafka.

```python
from brokers.producer import TaskProducer
from models.task import Task

producer = TaskProducer()

task1 = Task(task_id="task_1", payload="2+2 and 10*5", priority=1)
task2 = Task(task_id="task_2", payload="previous + 100", priority=2)

producer.send_task(task1)
producer.send_task(task2)
```

**Key design note:** `task2` uses the `"previous"` keyword, meaning it will consume the last result from memory at execution time. There is no explicit dependency declared here — the ordering relies on priority values (1 before 2).

---

## `agents/`

### `agents/__init__.py`
Empty package marker.

---

### `agents/manager.py` — `AgentManager`

**Purpose:** Top-level agent coordinator. Wires `PlannerAgent` and `ExecutorAgent` together.

| Method | Signature | Description |
|---|---|---|
| `__init__` | `(memory=None)` | Instantiates planner and executor; injects memory into executor |
| `handle_task` | `(task: Task) → list` | Plans the task, creates child `Task` objects for each subtask, executes each |

**Subtask ID scheme:** `{task_id}_{idx}` — e.g., `task_1_0`, `task_1_1`.

**Dependencies:**
- `agents.planner.PlannerAgent`
- `agents.executor.ExecutorAgent`
- `models.task.Task`

---

### `agents/planner.py` — `PlannerAgent`

**Purpose:** Uses the local LLM to decompose a task payload into a list of executable subtask strings.

| Method | Signature | Description |
|---|---|---|
| `__init__` | `()` | Creates `ToolGateway` and `LLMClient` |
| `plan` | `(task: Task) → list[str]` | Builds LLM prompt, calls Ollama, parses response with regex + `ast.literal_eval` |

**Parsing pipeline:**
```
payload → planner_prompt(payload) → LLMClient.generate() → re.search(r"\[.*\]") → ast.literal_eval() → list[str]
```

**Fallback behavior:** If the LLM response cannot be parsed, returns `[]` and logs the failure via `LoggerTool`.

**Dependencies:**
- `tools.gateway.ToolGateway`
- `llm.client.LLMClient`
- `llm.prompts.planner_prompt`
- `ast`, `re` (stdlib)

---

### `agents/executor.py` — `ExecutorAgent`

**Purpose:** Executes a single subtask by resolving memory references and delegating to `MathTool`.

| Method | Signature | Description |
|---|---|---|
| `__init__` | `(memory=None)` | Creates `ToolGateway`; stores memory reference |
| `execute` | `(task: Task) → any` | Resolves `"previous"` keyword, executes expression via `math` tool |

**Memory resolution logic:**
```python
if "previous" in expression:
    all_memory = self.memory.get_all()
    last_value = list(all_memory.values())[-1]
    expression = expression.replace("previous", str(last_value))
```

**Error path:** If `"previous"` is in the expression but memory is empty, returns an error string (does not raise).

**Dependencies:**
- `tools.gateway.ToolGateway`

---

## `brokers/`

### `brokers/__init__.py`
Empty package marker.

---

### `brokers/producer.py` — `TaskProducer`

**Purpose:** Serializes `Task` objects to JSON and publishes them to the Kafka `"agent_tasks"` topic.

| Method | Signature | Description |
|---|---|---|
| `__init__` | `()` | Connects to Kafka broker; configures JSON serializer |
| `send_task` | `(task: Task)` | Sends task dict to topic; flushes immediately; prints confirmation |

**Kafka config:** Uses `bootstrap_servers=KAFKA_BROKER`, `value_serializer=lambda v: json.dumps(v).encode("utf-8")`.

**Payload structure sent to Kafka:**
```json
{
  "task_id": "task_1",
  "payload": "2+2 and 10*5",
  "priority": 1,
  "dependencies": []
}
```

**Dependencies:**
- `kafka.KafkaProducer`
- `config.kafka_config` (KAFKA_BROKER, TASK_TOPIC)
- `models.task.Task`

---

### `brokers/consumer.py` — `TaskConsumer`

**Purpose:** Subscribes to the Kafka `"agent_tasks"` topic and yields deserialized task dicts.

| Method | Signature | Description |
|---|---|---|
| `__init__` | `()` | Creates `KafkaConsumer` with `group_id="agent-workers"`, `auto_offset_reset="latest"` |
| `listen` | `() → Generator[dict]` | Infinite loop; yields `message.value` for each incoming Kafka message |

**Note:** `auto_offset_reset="latest"` means the consumer only reads new messages published after it starts. Historical messages are ignored.

**Dependencies:**
- `kafka.KafkaConsumer`
- `config.kafka_config` (KAFKA_BROKER, TASK_TOPIC)

---

## `config/`

### `config/__init__.py`
Empty package marker.

---

### `config/kafka_config.py`

Simple constants file:

```python
KAFKA_BROKER = "localhost:9092"
TASK_TOPIC = "agent_tasks"
```

No classes. Imported directly by `producer.py` and `consumer.py`.

---

## `core/`

### `core/__init__.py`
Empty package marker.

---

### `core/pipeline.py` — `Pipeline`

**Purpose:** The central orchestrator on the worker side. Owns and wires together `MemoryStore`, `AgentManager`, and `Scheduler`.

| Method | Signature | Description |
|---|---|---|
| `__init__` | `()` | Creates memory, manager, and scheduler instances |
| `process_task` | `(task: Task) → dict` | Runs agent manager; saves results to memory; marks task status |
| `run` | `(task: Task) → list` | Adds task to scheduler queue; calls `scheduler.run(self.process_task)` |

**`process_task` result schema:**
```python
# on success:
{"task_id": "task_1", "results": [4, 50], "status": "COMPLETED"}

# on failure:
{"task_id": "task_1", "status": "FAILED", "results": []}
```

**Memory key scheme:** `{task_id}_{idx}` — matches subtask ID scheme used in `AgentManager`.

**Dependencies:**
- `agents.manager.AgentManager`
- `memory.memory_store.MemoryStore`
- `scheduler.scheduler.Scheduler`

---

### `core/state.py` — `ExecutionState`

**Purpose:** Lightweight, in-process task status tracker using Python `set`s.

| Method | Signature | Description |
|---|---|---|
| `__init__` | `()` | Initializes `completed_tasks` and `failed_tasks` sets |
| `mark_completed` | `(task_id: str)` | Adds to `completed_tasks` |
| `mark_failed` | `(task_id: str)` | Adds to `failed_tasks` |
| `is_completed` | `(task_id: str) → bool` | Checks if task ID is in `completed_tasks` |
| `is_failed` | `(task_id: str) → bool` | Checks if task ID is in `failed_tasks` |

**Used by:** `scheduler.scheduler.Scheduler` for dependency gate checking.

---

## `llm/`

### `llm/__init__.py`
Empty package marker.

---

### `llm/client.py` — `LLMClient`

**Purpose:** HTTP client for the local Ollama LLM server.

| Attribute | Value |
|---|---|
| Default model | `"mistral:latest"` |
| Endpoint | `http://localhost:11434/api/generate` |
| Timeout | 120 seconds |
| Streaming | Disabled (`"stream": False`) |

| Method | Signature | Description |
|---|---|---|
| `__init__` | `(model="mistral:latest")` | Stores model name and URL |
| `generate` | `(prompt: str) → str` | POSTs to Ollama; returns `response["response"]`; falls back to `'["2+2"]'` on error |

**Graceful fallback:** On any exception (connection error, timeout, HTTP error), prints `[LLM ERROR]` and returns the hardcoded string `'["2+2"]'` so the pipeline continues.

---

### `llm/prompts.py` — `planner_prompt`

**Purpose:** Generates the system prompt for the `PlannerAgent`.

```python
def planner_prompt(task: str) -> str:
    """
    Returns a prompt instructing the LLM to output ONLY a Python list
    of simple math expressions derived from the task.
    """
```

The prompt is strict: no explanation, no text, only a Python list. This maximizes parse reliability.

---

## `memory/`

### `memory/__init__.py`
Empty package marker.

---

### `memory/memory_store.py` — `MemoryStore`

**Purpose:** Simple in-process key-value store for task results.

| Method | Signature | Description |
|---|---|---|
| `__init__` | `()` | Initializes `self.storage = {}` |
| `save` | `(key: str, value: any)` | Stores `value` under `key` |
| `get` | `(key: str) → any` | Returns value for key, or `None` |
| `get_all` | `() → dict` | Returns entire storage dict |

**Usage in `ExecutorAgent`:** `get_all()` is called and the last value of the returned dict is used as `"previous"`. This relies on Python 3.7+ dict insertion-order guarantee.

> ⚠️ **Not persistent.** Memory is lost when the worker process restarts.

---

## `models/`

### `models/__init__.py`
Empty package marker.

---

### `models/task.py` — `Task` + `TaskStatus`

**Purpose:** Core data model for the system.

#### `TaskStatus` (Enum)

| Value | Meaning |
|---|---|
| `PENDING` | Created, not yet picked up |
| `RUNNING` | Currently being executed by the scheduler |
| `COMPLETED` | Finished successfully |
| `FAILED` | Exhausted retries or raised unrecoverable error |

#### `Task`

| Attribute | Type | Default | Description |
|---|---|---|---|
| `task_id` | `str` | — | Unique task identifier |
| `payload` | `str` | — | Raw task instruction string |
| `priority` | `int` | `5` | Scheduling priority (lower = higher urgency) |
| `dependencies` | `list[str]` | `[]` | Task IDs that must complete first |
| `timeout` | `int` | `10` | Max execution time (reserved, not currently enforced) |
| `status` | `TaskStatus` | `PENDING` | Current state |
| `created_at` | `datetime` | `utcnow()` | Creation timestamp |
| `retries` | `int` | `0` | Retry attempt counter |
| `result` | `any` | `None` | Stored after execution |

**`__lt__`** is implemented for `heapq` compatibility — tasks are compared by `priority`.

---

## `scheduler/`

### `scheduler/__init__.py`
Empty package marker.

---

### `scheduler/scheduler.py` — `Scheduler`

**Purpose:** Priority-queue-based task executor with dependency resolution and retry logic.

**Logging:** Configured at module level to write to `logs/system.log` at `INFO` level.

| Attribute | Type | Description |
|---|---|---|
| `queue` | `list` | `heapq`-managed priority queue of `(priority, task)` tuples |
| `max_retries` | `int` | Default: `2`. Max retry attempts before marking task FAILED |
| `state` | `ExecutionState` | Tracks completed/failed task IDs |

| Method | Signature | Description |
|---|---|---|
| `__init__` | `(max_retries=2)` | Initializes queue and state |
| `add_task` | `(task: Task)` | Pushes `(task.priority, task)` onto heap; logs event |
| `dependencies_completed` | `(task: Task) → bool` | Returns `True` if all dependency IDs are in `state.completed_tasks` |
| `execute_task` | `(handler, task) → any` | Directly calls `handler(task)` — synchronous execution |
| `run` | `(handler: callable) → list` | Main loop: pops tasks, checks deps, executes, retries, or marks failed |

**Retry flow:**
```
exception raised → retries < max_retries → increment retries → push back to heapq
                → retries >= max_retries → mark_failed → append error dict to results
```

**Historical note:** `ThreadPoolExecutor` was removed from `execute_task` to resolve a Windows deadlock caused by blocking Ollama HTTP calls inside threads.

---

## `tools/`

### `tools/__init__.py`
Empty package marker.

---

### `tools/registry.py` — `ToolRegistry`

**Purpose:** Central registry mapping tool names to tool instances.

| Method | Signature | Description |
|---|---|---|
| `__init__` | `()` | Registers `MathTool` and `LoggerTool` by default |
| `register` | `(tool)` | Stores tool in `self.tools[tool.name]` |
| `get_tool` | `(tool_name: str) → tool \| None` | Returns registered tool or `None` |

---

### `tools/gateway.py` — `ToolGateway`

**Purpose:** Single execution entry point for all tool calls. Abstracts tool lookup from callers.

| Method | Signature | Description |
|---|---|---|
| `__init__` | `()` | Creates a `ToolRegistry` instance |
| `execute` | `(tool_name: str, input_data: any) → any` | Looks up tool; returns error string if not found; calls `tool.execute(input_data)` |

**Planned extensions (scaffolded in comments):**
- Permission checking
- Rate limiting
- Execution logging

---

### `tools/math_tool.py` — `MathTool`

| Attribute | Value |
|---|---|
| `name` | `"math"` |

| Method | Signature | Description |
|---|---|---|
| `execute` | `(input_data: str) → any` | Calls `eval(input_data)`; returns exception message string on error |

> ⚠️ **Security note:** `eval()` is used without sandboxing. This is intentional for the current prototype but should be replaced with a safe evaluator (e.g., `numexpr`, `simpleeval`) before production use.

---

### `tools/logger.py` — `LoggerTool`

| Attribute | Value |
|---|---|
| `name` | `"logger"` |

| Method | Signature | Description |
|---|---|---|
| `execute` | `(message: str)` | Prints `[LOG]: {message}` to stdout |

---

## `workers/`

### `workers/__init__.py`
Empty package marker.

---

### `workers/worker.py` — `Worker`

**Purpose:** The long-running consumer process that bridges Kafka and the pipeline.

| Method | Signature | Description |
|---|---|---|
| `__init__` | `()` | Creates `TaskConsumer` and `Pipeline` instances |
| `start` | `()` | Infinite loop: reads from Kafka, reconstructs `Task`, calls `pipeline.process_task()`, prints results |

**`if __name__ == "__main__"`:** Instantiates and starts `Worker` directly. This is the process entry point for the execution side.

**Graceful shutdown:** Catches `KeyboardInterrupt` and exits cleanly.

**Dependencies:**
- `brokers.consumer.TaskConsumer`
- `core.pipeline.Pipeline`
- `models.task.Task`

---

## Infrastructure

### `docker-compose.yml`

Defines two services:

| Service | Image | Port | Config |
|---|---|---|---|
| `zookeeper` | `confluentinc/cp-zookeeper:7.5.0` | `2181` | `ZOOKEEPER_CLIENT_PORT=2181` |
| `kafka` | `confluentinc/cp-kafka:7.5.0` | `9092` | `KAFKA_BROKER_ID=1`, `KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181`, `KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092`, `KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1` |

`kafka` depends on `zookeeper` (Docker Compose `depends_on`).

---

### `logs/system.log`

Written by Python's `logging` module configured in `scheduler/scheduler.py`. Format:

```
%(asctime)s | %(levelname)s | %(message)s
```

> ⚠️ **Note:** This file grows without rotation. The current file is ~1 GB. A log rotation strategy (e.g., `RotatingFileHandler`) should be added to prevent disk exhaustion.

---

### `.gitignore`

Comprehensive ignore file covering:
- Python cache files (`__pycache__/`, `*.pyc`, `*.pyo`)
- Virtual environments (`venv/`, `.venv/`, `env/`)
- IDE files (`.vscode/`, `.idea/`, `*.sublime-*`)
- OS files (`Thumbs.db`, `.DS_Store`)
- Log files (`*.log`, `logs/*.log`)
- Environment/secrets (`.env`, `*.env`)
- Kafka data directories (`kafka-data/`, `zookeeper-data/`)
- Build artifacts (`dist/`, `build/`, `*.egg-info/`)

---

## Dependency Graph

```
main.py
  └── brokers.producer.TaskProducer
        └── config.kafka_config
        └── models.task.Task

workers.worker.Worker
  ├── brokers.consumer.TaskConsumer
  │     └── config.kafka_config
  └── core.pipeline.Pipeline
        ├── memory.memory_store.MemoryStore
        ├── scheduler.scheduler.Scheduler
        │     └── core.state.ExecutionState
        └── agents.manager.AgentManager
              ├── agents.planner.PlannerAgent
              │     ├── llm.client.LLMClient
              │     ├── llm.prompts.planner_prompt
              │     └── tools.gateway.ToolGateway
              │           └── tools.registry.ToolRegistry
              │                 ├── tools.math_tool.MathTool
              │                 └── tools.logger.LoggerTool
              └── agents.executor.ExecutorAgent
                    └── tools.gateway.ToolGateway (same)
```
