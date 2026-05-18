# 🏗️ System Architecture — ai-agent-os

> A distributed, event-driven AI agent operating system built on Apache Kafka, Ollama LLMs, and a modular Python pipeline.

---

## 1. Overview

`ai-agent-os` is a **multi-agent orchestration framework** that processes tasks in a distributed manner. Tasks are submitted by producers, transported through Apache Kafka, consumed by workers, and then processed through a layered pipeline of agents, schedulers, tools, and memory — with results persisted and logged at each step. The system is monitored via an Observability layer, managed via a FastAPI Control Plane, and visualized in a React Dashboard.

The system is intentionally architected in three main components:

| Component | Responsibility |
|---|---|
| **Ingestion Layer** | `main.py` → `TaskProducer` → Kafka topic |
| **Execution Layer** | `Worker` → `TaskConsumer` → `Pipeline` → Agents → Tools |
| **Control & View** | `FastAPI Control Plane` ↔ `React Dashboard` ↔ `Observability WebSockets` |

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
│               │                                                  │
│               ├──► AgentManager (agents/manager.py)              │
│               │        ├──► PlannerAgent (agents/planner.py)     │
│               │        │        └── LLMClient → Ollama           │
│               │        └──► ExecutorAgent (agents/executor.py)   │
│               │                 ├── ToolGateway → MathTool       │
│               │                                                  │
│               ├──► Storage/Memory (storage/, memory/)            │
│               │        └── Redis / PostgreSQL / In-Memory        │
│               │                                                  │
│               ├──► Policy Engine (policy/)                       │
│               │        └── Rate limiting and Permissions         │
│               │                                                  │
│               └──► Observability (observability/)                │
│                        ├── Metrics Collector                     │
│                        ├── Execution Tracker                     │
│                        └── WebSocket Manager                     │
└──────────────────────────────────────────────────────────────────┘
                             │ (Logs, Metrics, Status)
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                 CONTROL PLANE & FRONTEND                         │
│                                                                  │
│   FastAPI Server (api/server.py)                                 │
│      │                                                           │
│      └──► React/Vite Dashboard (dashboard/)                      │
│               └── Real-time WebSocket Updates                    │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. Component Breakdown

### 3.1 Entry Point — `main.py`

The script that seeds the system with tasks. Creates `Task` objects and calls `TaskProducer.send_task()` for each one. Tasks are plain Python objects serialized to JSON before publishing to Kafka.

---

### 3.2 Kafka Infrastructure — `brokers/` + `config/`

| File | Class | Role |
|---|---|---|
| `brokers/producer.py` | `TaskProducer` | Serializes `Task` dicts and publishes to `"agent_tasks"` Kafka topic |
| `brokers/consumer.py` | `TaskConsumer` | Subscribes to `"agent_tasks"` topic, yields raw message dicts |
| `config/kafka_config.py` | — | Constants: `KAFKA_BROKER = "localhost:9092"`, `TASK_TOPIC = "agent_tasks"` |

---

### 3.3 Worker — `workers/worker.py`

`Worker` is the long-running process on the consumer side. It enters an infinite loop, yielding messages from Kafka, calls `Pipeline.process_task(task)` and updates the Observability layer with its heartbeat via `WorkerMonitor`.

---

### 3.4 Core Pipeline — `core/pipeline.py`

`Pipeline` is the orchestration hub on the worker side. It runs the agent manager on a single task, saves results to memory/storage, updates task status, and orchestrates the dependency and retry logic via `Scheduler`.

---

### 3.5 Scheduler — `scheduler/scheduler.py`

The scheduler is a **synchronous priority-queue executor** using Python's `heapq` and dependency checking logic against the core state.

---

### 3.6 Agent Layer — `agents/`

- **`AgentManager`**: Orchestrates the two-agent workflow.
- **`PlannerAgent`**: Uses LLM client to parse and decompose tasks.
- **`ExecutorAgent`**: Substitutes memory context and calls tools.

---

### 3.7 LLM Layer — `llm/`

Interacts directly with a local **Ollama** instance via `LLMClient`. Uses structured prompts from `prompts.py` to command models like `mistral:latest`.

---

### 3.8 Tools Layer — `tools/`

Contains the `ToolRegistry` and `ToolGateway`. Gateways are extensible to incorporate permissions, rate limits, and custom logic for various tools like `MathTool` and `LoggerTool`.

---

### 3.9 Data Models — `models/`

Contains the definitions for `Task` and `TaskStatus`.

---

### 3.10 Memory — `memory/`

Handles memory resolution, providing the `previous` context to sequential tasks.

---

### 3.11 Observability Layer — `observability/` (New)

The observability layer handles metrics, health tracking, and event emission:
- **`audit_logger.py`**: Logs sensitive and administrative actions to `logs/audit.log`.
- **`execution_tracker.py`**: Tracks active task status and history across all workers.
- **`metrics_collector.py`**: Collects generic metrics.
- **`worker_monitor.py`**: Monitors worker health and heartbeat.
- **`websocket_manager.py`**: Pushes live events directly to connected clients (like the Dashboard).

---

### 3.12 Control Plane / API Layer — `api/` (New)

A **FastAPI** backend that exposes REST endpoints and WebSockets for monitoring and controlling the entire cluster.
- **`server.py`**: Main application setup.
- **`routes/`**: Distinct routers for `tasks.py`, `workers.py`, `metrics.py`, `events.py`, `audit.py`, and `memory.py`.

---

### 3.13 Dashboard Frontend — `dashboard/` (New)

A **React + Vite + Tailwind** frontend that serves as the visual command center.
- Connects to the FastAPI backend via standard HTTP requests and WebSockets (`useWebSocket.ts`).
- Displays live streaming logs, task statuses, worker health, and system metrics.

---

### 3.14 Storage & Policy — `storage/` & `policy/` (New)

- **`storage/`**: Includes modules for `redis_store.py` and `postgres_store.py` to persist data beyond the life of the worker process.
- **`policy/`**: Contains `engine.py`, `permissions.py`, and `rate_limiter.py` to restrict tool access and ensure secure execution within the `ToolGateway`.

---

## 4. Data Flow — End to End

```
1. main.py creates Task objects
2. TaskProducer publishes to Kafka "agent_tasks"
3. Worker picks up the message and emits "task_started" event via WebSocket
4. Pipeline passes task to AgentManager
5. PlannerAgent plans via Ollama LLM
6. ExecutorAgent calls ToolGateway → applies Policy constraints → executes tool
7. Results stored in Storage (Redis/Postgres) and Memory
8. Pipeline returns result dict
9. WebSocket broadcasts "task_completed"
10. Dashboard UI updates instantly with the latest state
```

---

## 5. Infrastructure — `docker-compose.yml`

| Service | Image | Role |
|---|---|---|
| `zookeeper` | `confluentinc/cp-zookeeper:7.5.0` | Kafka coordination / leader election |
| `kafka` | `confluentinc/cp-kafka:7.5.0` | Message broker |

---

## 6. Known Limitations & Future Work

| Area | Current State | Future Direction |
|---|---|---|
| LLM | Local Ollama only | Cloud LLM support (OpenAI, Anthropic) |
| Scheduler | Synchronous direct execution | Async task execution with proper timeout |
| Infrastructure | Minimal compose | Full stack in Docker (Postgres, Redis, Backend, Frontend) |
