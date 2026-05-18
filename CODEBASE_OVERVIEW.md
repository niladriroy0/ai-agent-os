# 📚 Codebase Overview — ai-agent-os

> A module-by-module reference for every file and class in the project.

---

## Table of Contents

1. [Entry Points](#entry-points)
2. [agents/](#agents)
3. [api/](#api)
4. [brokers/](#brokers)
5. [config/](#config)
6. [core/](#core)
7. [dashboard/](#dashboard)
8. [llm/](#llm)
9. [memory/](#memory)
10. [models/](#models)
11. [observability/](#observability)
12. [policy/](#policy)
13. [registry/](#registry)
14. [scheduler/](#scheduler)
15. [storage/](#storage)
16. [tools/](#tools)
17. [workers/](#workers)
18. [Infrastructure](#infrastructure)
19. [Dependency Graph](#dependency-graph)

---

## Entry Points

### `main.py`
**Purpose:** Seeds the system with tasks and publishes them to Kafka.

---

## `agents/`

### `agents/manager.py` — `AgentManager`
**Purpose:** Top-level agent coordinator. Wires `PlannerAgent` and `ExecutorAgent` together.

### `agents/planner.py` — `PlannerAgent`
**Purpose:** Uses the local LLM to decompose a task payload into a list of executable subtask strings.

### `agents/executor.py` — `ExecutorAgent`
**Purpose:** Executes a single subtask by resolving memory references and delegating to `ToolGateway`.

---

## `api/` (New Control Plane)

### `api/server.py`
**Purpose:** The main FastAPI application setup, connecting routes, configuring CORS, and managing server lifecycle.

### `api/routes/`
**Purpose:** Specific route controllers for interacting with the backend.
- `tasks.py`: Endpoints to get, create, and list tasks.
- `workers.py`: Endpoints to view worker status.
- `events.py`: Exposes WebSocket connections.
- `audit.py`: Exposes the audit logs.
- `metrics.py`: Exposes system metrics.
- `memory.py`: Exposes the memory store.

---

## `brokers/`

### `brokers/producer.py` — `TaskProducer`
**Purpose:** Serializes `Task` objects to JSON and publishes them to Kafka.

### `brokers/consumer.py` — `TaskConsumer`
**Purpose:** Subscribes to the Kafka topic and yields deserialized task dicts.

---

## `config/`

### `config/kafka_config.py`
**Purpose:** Simple constants for `KAFKA_BROKER` and `TASK_TOPIC`.

---

## `core/`

### `core/pipeline.py` — `Pipeline`
**Purpose:** The central orchestrator on the worker side. Owns and wires together `MemoryStore`, `AgentManager`, and `Scheduler`.

### `core/state.py` — `ExecutionState`
**Purpose:** Lightweight task status tracker for dependency gate checking.

---

## `dashboard/` (New Frontend)

### `dashboard/frontend/`
**Purpose:** A React / Vite / Tailwind UI application.
- `src/App.tsx`: The main dashboard view.
- `src/hooks/useWebSocket.ts`: Hook for streaming real-time status and logs.

---

## `llm/`

### `llm/client.py` — `LLMClient`
**Purpose:** HTTP client for the local Ollama LLM server (`mistral:latest`).

### `llm/prompts.py` — `planner_prompt`
**Purpose:** Generates the system prompt instructing the LLM to output only a Python list.

---

## `memory/`

### `memory/memory_store.py` — `MemoryStore`
**Purpose:** Simple in-process key-value store for cross-task result chaining via `"previous"`.

---

## `models/`

### `models/task.py` — `Task` + `TaskStatus`
**Purpose:** Core data model for the system. `Task` attributes include `task_id`, `payload`, `priority`, `dependencies`, and `status`.

---

## `observability/` (New Layer)

### `observability/audit_logger.py`
**Purpose:** Writes sensitive execution actions to `logs/audit.log`.

### `observability/execution_tracker.py`
**Purpose:** Tracks and persists task history globally across all nodes.

### `observability/metrics_collector.py`
**Purpose:** Aggregates and returns health/execution metrics.

### `observability/websocket_manager.py`
**Purpose:** Pushes live events from the backend to the React dashboard.

### `observability/worker_monitor.py`
**Purpose:** Tracks worker heartbeats and statuses.

---

## `policy/` (New Layer)

### `policy/engine.py`
**Purpose:** The main policy logic combining rate limiters and permission checkers.

### `policy/permissions.py`
**Purpose:** Validates whether specific agents/tasks can execute certain tools.

### `policy/rate_limiter.py`
**Purpose:** Enforces execution frequency limits per tool/user.

---

## `registry/` (New Layer)

### `registry/agent_registry.py`
**Purpose:** Extensible registry mapping names to specific agent configurations.

---

## `scheduler/`

### `scheduler/scheduler.py` — `Scheduler`
**Purpose:** Priority-queue-based task executor with dependency resolution and retry logic.

---

## `storage/` (New Layer)

### `storage/db.py`
**Purpose:** Base abstraction for persistent storage.

### `storage/postgres_store.py`
**Purpose:** Adapter for persisting data to PostgreSQL.

### `storage/redis_store.py`
**Purpose:** Adapter for persisting fast-access data to Redis.

---

## `tools/`

### `tools/registry.py` — `ToolRegistry`
**Purpose:** Central registry mapping tool names to tool instances.

### `tools/gateway.py` — `ToolGateway`
**Purpose:** Single execution entry point for all tool calls. Intercepts calls to enforce `policy/`.

### `tools/math_tool.py` — `MathTool`
**Purpose:** Evaluates arbitrary math expressions.

### `tools/logger.py` — `LoggerTool`
**Purpose:** Prints log messages.

---

## `workers/`

### `workers/worker.py` — `Worker`
**Purpose:** The long-running consumer process that bridges Kafka, Pipeline, and Observability layers.

---

## Infrastructure

### `docker-compose.yml`
Defines `zookeeper` and `kafka`.

### `logs/system.log` & `logs/audit.log`
Written by Python's `logging` module.

### `.gitignore`
Comprehensive ignore file.

---

## Dependency Graph

```
main.py
  └── brokers.producer.TaskProducer

workers.worker.Worker
  ├── brokers.consumer.TaskConsumer
  ├── observability.worker_monitor
  └── core.pipeline.Pipeline
        ├── storage.*
        ├── scheduler.scheduler.Scheduler
        └── agents.manager.AgentManager
              ├── agents.planner.PlannerAgent
              │     └── llm.client.LLMClient
              └── agents.executor.ExecutorAgent
                    └── tools.gateway.ToolGateway
                          ├── tools.registry.ToolRegistry
                          └── policy.engine.PolicyEngine

api.server (FastAPI)
  ├── api.routes.*
  └── observability.websocket_manager

dashboard.frontend (React)
  └── Hooks → WebSocket Manager
```
