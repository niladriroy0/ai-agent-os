# 🏗️ System Architecture — ai-agent-os

> A distributed, event-driven AI agent operating system built on Apache Kafka, Ollama LLMs, and a modular Python pipeline.

---

## 1. Overview

`ai-agent-os` is a **multi-agent orchestration framework** that processes tasks in a distributed manner. Tasks are submitted by producers, transported through Apache Kafka, consumed by workers, and then processed through a layered pipeline of agents, schedulers, tools, and memory — with results persisted and logged at each step.

The system is intentionally architected in two halves:

| Half | Responsibility |
|---|---|
| **Ingestion Layer** | `main.py` → `TaskProducer` → Kafka topic |
| **Execution Layer** | `Worker` → `TaskConsumer` → `Pipeline` → Agents → Tools |

---

## 2. High-Level Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                        PRODUCER SIDE                             │
│                                                                  │
│   main.py                                                        │
│      │                                                           │
│      └──► TaskProducer (brokers/producer.py)                     │
│                │                                                 │
│                └──► Kafka Topic: "agent_tasks"  (localhost:9092) │
└──────────────────────────────────────────────────────────────────┘
                             │
                       [Kafka Broker]
                             │
┌──────────────────────────────────────────────────────────────────┐
│                        WORKER SIDE                               │
│                                                                  │
│   Worker (workers/worker.py)                                     │
│      │                                                           │
│      ├──► TaskConsumer (brokers/consumer.py)                     │
│      │        └── Reads from Kafka topic "agent_tasks"           │
│      │                                                           │
│      └──► Pipeline (core/pipeline.py)                            │
│               │                                                  │
│               ├──► Scheduler (scheduler/scheduler.py)            │
│               │        ├── Priority Queue (heapq)                │
│               │        ├── Dependency Resolution                 │
│               │        └── Retry Logic (max 2 retries)           │
│               │                                                  │
│               ├──► AgentManager (agents/manager.py)              │
│               │        ├──► PlannerAgent (agents/planner.py)     │
│               │        │        ├── LLMClient → Ollama           │
│               │        │        └── Regex + ast subtask parser   │
│               │        └──► ExecutorAgent (agents/executor.py)   │
│               │                 ├── Memory context injection      │
│               │        │        └── ToolGateway → MathTool       │
│               │                                                  │
│               ├──► MemoryStore (memory/memory_store.py)          │
│               │        └── In-process key-value store            │
│               │                                                  │
│               └──► ExecutionState (core/state.py)                │
│                        └── Tracks completed / failed task IDs    │
└──────────────────────────────────────────────────────────────────┘
                             │
                      logs/system.log
```

---

## 3. Component Breakdown

### 3.1 Entry Point — `main.py`

The script that seeds the system with tasks. Creates `Task` objects and calls `TaskProducer.send_task()` for each one. Tasks are plain Python objects serialized to JSON before publishing to Kafka.

**Current demo tasks:**
- `task_1` — payload: `"2+2 and 10*5"`, priority 1
- `task_2` — payload: `"previous + 100"`, priority 2 (depends on `task_1`'s result in memory)

---

### 3.2 Kafka Infrastructure — `brokers/` + `config/`

| File | Class | Role |
|---|---|---|
| `brokers/producer.py` | `TaskProducer` | Serializes `Task` dicts and publishes to `"agent_tasks"` Kafka topic |
| `brokers/consumer.py` | `TaskConsumer` | Subscribes to `"agent_tasks"` topic, yields raw message dicts |
| `config/kafka_config.py` | — | Constants: `KAFKA_BROKER = "localhost:9092"`, `TASK_TOPIC = "agent_tasks"` |

The Kafka broker + Zookeeper are managed via `docker-compose.yml` using Confluent's official images (`cp-kafka:7.5.0`, `cp-zookeeper:7.5.0`).

---

### 3.3 Worker — `workers/worker.py`

`Worker` is the long-running process on the consumer side. It:
1. Instantiates `TaskConsumer` and `Pipeline`.
2. Enters an infinite loop, yielding messages from Kafka.
3. Reconstructs full `Task` objects from the raw JSON dict.
4. Calls `Pipeline.process_task(task)` and prints results.
5. Handles graceful shutdown on `KeyboardInterrupt`.

This file is also the `__main__` entry point for the worker process.

---

### 3.4 Core Pipeline — `core/pipeline.py`

`Pipeline` is the orchestration hub on the worker side. It owns:
- A `MemoryStore` instance (shared across all task executions)
- An `AgentManager` instance (handles planner + executor agents)
- A `Scheduler` instance (manages queue + retry logic)

**`process_task(task)`** — runs the agent manager on a single task, saves results to memory, updates task status, returns a result dict.

**`run(task)`** — adds task to scheduler queue, then calls `scheduler.run(self.process_task)`.

---

### 3.5 Scheduler — `scheduler/scheduler.py`

The scheduler is a **synchronous priority-queue executor** using Python's `heapq`. Key design decisions made during development:

| Feature | Implementation |
|---|---|
| Priority Queue | `heapq` — lower `priority` integer = higher urgency |
| Dependency Checking | Loops through `task.dependencies` list, checks `ExecutionState` |
| Retry Logic | Up to `max_retries=2` automatic retries on exception |
| Task Re-queuing | Failed/waiting tasks pushed back into heap |
| Execution | Direct synchronous call (no `ThreadPoolExecutor` — removed to fix Windows deadlock) |
| Logging | Writes to `logs/system.log` via Python `logging` module |

**Scheduler flow:**
```
heapq.heappop() → dependency check → mark_running() → execute_task() → mark_completed() / retry / mark_failed()
```

---

### 3.6 Agent Layer — `agents/`

#### `AgentManager` (`agents/manager.py`)
Orchestrates the two-agent workflow for each task:
1. Calls `PlannerAgent.plan(task)` to decompose the task into subtasks.
2. Iterates over subtasks, creates child `Task` objects, calls `ExecutorAgent.execute()` on each.
3. Returns a list of results.

#### `PlannerAgent` (`agents/planner.py`)
- Accepts a `Task`, extracts the `payload` string.
- Builds a prompt using `planner_prompt()` from `llm/prompts.py`.
- Calls `LLMClient.generate()` to get a plan from the local Mistral model.
- Uses `re.search(r"\[.*\]", response)` + `ast.literal_eval()` to parse a Python list of subtask strings from the LLM's response.
- Falls back gracefully if parsing fails; logs via `LoggerTool`.

#### `ExecutorAgent` (`agents/executor.py`)
- Takes a single subtask `Task`.
- If the payload contains the keyword `"previous"`, looks up the last entry in `MemoryStore` and substitutes it into the expression.
- Executes the final expression via `ToolGateway → MathTool`.
- Logs execution and result.

---

### 3.7 LLM Layer — `llm/`

| File | Class / Function | Role |
|---|---|---|
| `llm/client.py` | `LLMClient` | HTTP POST to Ollama `/api/generate`, model: `mistral:latest`, timeout: 120s, graceful fallback on error |
| `llm/prompts.py` | `planner_prompt(task)` | Returns the system prompt instructing the LLM to output only a Python list of math expressions |

The LLM is a **local Ollama instance** running on `http://localhost:11434`. No cloud API calls are made.

---

### 3.8 Tools Layer — `tools/`

| File | Class | Role |
|---|---|---|
| `tools/registry.py` | `ToolRegistry` | Dictionary of registered tools, indexed by `tool.name` |
| `tools/gateway.py` | `ToolGateway` | Single entry point for tool execution; looks up tool in registry and calls `tool.execute()` |
| `tools/math_tool.py` | `MathTool` | `name="math"` — evaluates arbitrary math expressions using Python `eval()` |
| `tools/logger.py` | `LoggerTool` | `name="logger"` — prints a `[LOG]:` prefixed message to stdout |

> **Future extension points noted in `gateway.py`:** permission checks, rate limiting, and logging middleware are scaffolded as comments.

---

### 3.9 Data Models — `models/`

#### `Task` (`models/task.py`)

| Attribute | Type | Description |
|---|---|---|
| `task_id` | `str` | Unique identifier |
| `payload` | `str` | The raw task instruction / expression |
| `priority` | `int` | Lower = higher priority in heap (default: 5) |
| `dependencies` | `list[str]` | Task IDs that must complete first |
| `timeout` | `int` | Max seconds allowed (default: 10, not enforced in current scheduler) |
| `status` | `TaskStatus` | Enum: `PENDING`, `RUNNING`, `COMPLETED`, `FAILED` |
| `created_at` | `datetime` | UTC timestamp at creation |
| `retries` | `int` | Retry count used by scheduler |
| `result` | `any` | Final result stored after execution |

`Task.__lt__` is implemented so `heapq` can compare tasks by priority.

---

### 3.10 Memory — `memory/memory_store.py`

`MemoryStore` is a **simple in-process key-value store** (`dict`). It provides:
- `save(key, value)` — stores a result
- `get(key)` — retrieves by key
- `get_all()` — returns entire store (used by `ExecutorAgent` to find `"previous"`)

> ⚠️ **Current limitation:** Memory is not persisted across worker restarts. It lives for the lifetime of the `Pipeline` object.

---

### 3.11 State Tracking — `core/state.py`

`ExecutionState` tracks which task IDs have been completed or failed using Python `set`s. It is used by the `Scheduler` for dependency resolution.

---

## 4. Data Flow — End to End

```
1. main.py creates Task objects
2. TaskProducer serializes them to JSON and publishes to Kafka "agent_tasks" topic
3. Worker's TaskConsumer picks up the message
4. Worker reconstructs Task and calls Pipeline.process_task()
5. Pipeline passes task to AgentManager.handle_task()
6. AgentManager calls PlannerAgent.plan() → LLM returns subtask list
7. AgentManager iterates subtasks → ExecutorAgent.execute() for each
8. ExecutorAgent resolves "previous" from MemoryStore (if needed)
9. ExecutorAgent calls ToolGateway → MathTool.execute() → eval()
10. Results stored in MemoryStore, task marked COMPLETED
11. Pipeline returns result dict → Worker prints it
12. Scheduler logs final state to logs/system.log
```

---

## 5. Infrastructure — `docker-compose.yml`

| Service | Image | Port | Role |
|---|---|---|---|
| `zookeeper` | `confluentinc/cp-zookeeper:7.5.0` | `2181` | Kafka coordination / leader election |
| `kafka` | `confluentinc/cp-kafka:7.5.0` | `9092` | Message broker |

Start with:
```bash
docker-compose up -d
```

---

## 6. Known Limitations & Future Work

| Area | Current State | Future Direction |
|---|---|---|
| Memory | In-process dict | Redis / persistent vector store |
| LLM | Local Ollama only | Cloud LLM support (OpenAI, Anthropic) |
| Tools | MathTool + LoggerTool only | Plugin-based dynamic tool registry |
| Scheduler | Synchronous direct execution | Async task execution with proper timeout |
| Worker | Single worker process | Horizontal scaling via Kafka consumer groups |
| Security | No auth/authz on tool execution | Permission model in ToolGateway |
| Monitoring | File-based log only | Metrics dashboard (Prometheus/Grafana) |
