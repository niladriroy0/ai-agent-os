# 🎤 Interview Guide — ai-agent-os

> A comprehensive Q&A guide covering the architecture, design decisions, and tradeoffs of the `ai-agent-os` project. Use this to prepare for technical discussions or system design interviews.

---

## Table of Contents

1. [System Design Overview](#1-system-design-overview)
2. [Kafka & Message Queue](#2-kafka--message-queue)
3. [Agent Architecture](#3-agent-architecture)
4. [Scheduler Design](#4-scheduler-design)
5. [LLM Integration](#5-llm-integration)
6. [Memory & State](#6-memory--state)
7. [Tool System & Policy](#7-tool-system--policy)
8. [Observability & Control Plane](#8-observability--control-plane)
9. [Fault Tolerance & Reliability](#9-fault-tolerance--reliability)
10. [Scalability & Production Readiness](#10-scalability--production-readiness)
11. [Code Quality & Tradeoffs](#11-code-quality--tradeoffs)

---

## 1. System Design Overview

---

**Q: Describe the overall architecture of ai-agent-os in one paragraph.**

> `ai-agent-os` is a distributed, event-driven AI agent orchestration system. Tasks are submitted via `main.py` which publishes them as JSON messages to an Apache Kafka topic (`agent_tasks`). A separate `Worker` process consumes from that topic, reconstructing `Task` objects, and feeds them into a `Pipeline`. The pipeline uses a priority-queue `Scheduler` to manage execution order and retries. An `AgentManager` wires together a `PlannerAgent` (which calls a local Ollama LLM to decompose tasks) and an `ExecutorAgent` (which runs subtasks through a registered tool gateway protected by a policy engine). All state and task execution metrics are captured by an `Observability` layer, which streams events over WebSockets to a `FastAPI Control Plane` and an interactive `React Dashboard`. Results and state are persisted in PostgreSQL or Redis.

---

**Q: Walk me through a task's full lifecycle from `main.py` to final result.**

> 1. `main.py` creates a `Task` object.
> 2. `TaskProducer` serializes it and publishes to the `agent_tasks` Kafka topic.
> 3. The `Worker` picks up the message and emits a `task_started` WebSocket event.
> 4. `Pipeline` delegates to `AgentManager.handle_task(task)`.
> 5. `PlannerAgent` decomposition happens via LLM.
> 6. Subtasks are executed by `ExecutorAgent`, passing through the `ToolGateway`.
> 7. The `PolicyEngine` validates permissions and rate limits.
> 8. The task completes; `Observability` layer collects metrics and broadcasts completion.
> 9. Results are stored in PostgreSQL/Redis.
> 10. The `React Dashboard` updates its UI instantly.

---

## 2. Kafka & Message Queue

---

**Q: Why was Kafka chosen as the message bus instead of something simpler like a REST endpoint or a shared queue?**

> Kafka provides decoupling, horizontal scalability, durability, and backpressure. A REST endpoint would couple producer and consumer availability.

---

## 3. Agent Architecture

---

**Q: Explain the roles of `PlannerAgent` and `ExecutorAgent`. Why are they separate?**

> `PlannerAgent` focuses on understanding and decomposing tasks via the LLM. `ExecutorAgent` focuses on running deterministic tools. This separation of planning vs. execution allows independent optimization.

---

## 4. Scheduler Design

---

**Q: How does dependency resolution work in the scheduler?**

> When a task is popped from the `heapq`, `dependencies_completed(task)` checks if all task IDs in `task.dependencies` exist in `ExecutionState`. Unmet dependencies cause the task to be re-queued.

---

## 5. LLM Integration

---

**Q: How does the system interact with the LLM? What model is used?**

> `LLMClient` sends HTTP POST requests to `http://localhost:11434/api/generate` (Ollama REST API). The default model is `mistral:latest`.

---

## 6. Memory & State

---

**Q: Is memory shared between tasks? What are the implications?**

> Yes. Previously it was in-process, but now with `storage/postgres_store.py` and `redis_store.py`, memory persists across workers and restarts. Task results can be securely chained via the `"previous"` keyword.

---

## 7. Tool System & Policy

---

**Q: How is the tool registry pattern implemented?**

> `ToolRegistry` maintains mapping of tools. `ToolGateway` routes execution. Furthermore, `policy/engine.py` applies `permissions.py` and `rate_limiter.py` before any tool runs to ensure safety and prevent abuse.

---

## 8. Observability & Control Plane

---

**Q: Explain the Observability Layer. How does the dashboard stay up to date?**

> The `observability/` module includes `metrics_collector.py`, `audit_logger.py`, and `worker_monitor.py`. Real-time updates use `websocket_manager.py`, which is exposed by the FastAPI `Control Plane`. The React dashboard uses a custom `useWebSocket.ts` hook to listen to these events, eliminating the need to poll for status.

---

## 9. Fault Tolerance & Reliability

---

**Q: What failure modes does the system handle?**

> It handles LLM unreachability with fallbacks, tool failures via retries, rate limits via the policy engine, and worker failures by distributing tasks in Kafka. With persistent Postgres/Redis storage, state survives process crashes.

---

## 10. Scalability & Production Readiness

---

**Q: How would you scale this system to handle 10,000 tasks/minute?**

> 1. Run multiple `worker.py` instances.
> 2. Increase Kafka partitions.
> 3. Use async LLM clients and potentially deploy GPU endpoints instead of local CPU Ollama.
> 4. Ensure Redis is used for fast, high-throughput caching and rate limiting.

---

## 11. Code Quality & Tradeoffs

---

**Q: What are the most significant technical debts in this codebase?**

> 1. **`eval()` in `MathTool`** — security risk; must be sandboxed before production.
> 2. **Infinite dependency loop** — no cycle detection or timeout in the scheduler.
> 3. **`auto_offset_reset="latest"`** — tasks can be lost if the worker is down when they're published.

---

*Last updated: May 2026*
