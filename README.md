# 🤖 ai-agent-os

> A distributed, event-driven AI Agent Operating System — powered by Apache Kafka, local LLMs (Ollama), and a modular Python pipeline.

---

## What Is This?

`ai-agent-os` is an **AI agent orchestration framework** that processes tasks asynchronously at scale. It decouples task submission from execution using Apache Kafka as the message bus, and uses a local LLM (Mistral via Ollama) to plan and decompose tasks before execution. It now includes a full observability layer, control plane, and an interactive dashboard.

---

## Architecture at a Glance

```
main.py ──► TaskProducer ──► Kafka ──► TaskConsumer ──► Worker ◄──► Observability (Metrics, Audit, WS)
                                                            │           │
                                                         Pipeline       │
                                                            │           ▼
                                           ┌────────────────┤      FastAPI Control Plane
                                       Scheduler       AgentManager     ▲
                                           │            Planner + Executor
                                    (Priority Queue)        │           ▼
                                                     LLM (Ollama)   React Dashboard
                                                            │
                                                       Tools / DB
```

For full details, see [`SYSTEM_ARCHITECTURE.md`](./SYSTEM_ARCHITECTURE.md).

---

## Project Structure

```
ai-agent-os/
├── main.py                  # Entry point: publish tasks to Kafka
├── docker-compose.yml       # Kafka + Zookeeper services
├── api/                     # FastAPI Control Plane and Routes
├── dashboard/               # React / Vite Dashboard Frontend
├── observability/           # Metrics, Execution Tracking, WebSockets
├── agents/                  # Planner & Executor Agents
├── brokers/                 # Kafka Producers & Consumers
├── config/                  # Configuration (Kafka, etc.)
├── core/                    # Pipeline & Execution State
├── llm/                     # Ollama Client & Prompts
├── memory/                  # In-process / Persistent memory stores
├── models/                  # Data Models (Tasks, Status)
├── policy/                  # Rate limiting & Permissions Engine
├── registry/                # Agent Registry
├── scheduler/               # Priority Queue Task Scheduler
├── storage/                 # Redis & PostgreSQL Storage Adapters
├── tools/                   # Extensible Tool Gateway & Logic
├── workers/                 # Kafka Consumer Workers
└── logs/                    # System & Audit Logs
```

---

## Prerequisites

| Requirement | Purpose |
|---|---|
| Python 3.9+ | Runtime |
| Node.js / npm | React Dashboard Frontend |
| Docker + Docker Compose | Kafka + Zookeeper |
| Ollama + Mistral | Local LLM server |
| PostgreSQL / Redis | Persistent Storage (Optional depending on config) |

---

## Quick Start

```bash
# 1. Start Kafka
docker-compose up -d

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start Ollama
ollama run mistral

# 4. Start the worker (terminal 1)
python -m workers.worker

# 5. Start the FastAPI Control Plane (terminal 2)
uvicorn api.server:app --reload

# 6. Start the React Dashboard (terminal 3)
cd dashboard/frontend
npm install
npm run dev

# 7. Publish tasks (terminal 4)
python main.py
```

---

## The `"previous"` Keyword

Tasks can reference prior results using the keyword `previous` in their payload. The `ExecutorAgent` automatically substitutes the last value stored in `MemoryStore`.

```python
Task(task_id="task_2", payload="previous + 100")
# → runs as: "<last result> + 100"
```

---

## Adding a New Tool

1. Create `tools/my_tool.py` with a `name` attribute and `execute(input_data)` method.
2. Register it in `tools/registry.py` inside `ToolRegistry.__init__()`.
3. Call it via `self.gateway.execute("my_tool", data)`.

---

## Logs

Scheduler events are written to `logs/system.log` and `logs/audit.log`:

```
2026-05-17 01:00:00 | INFO | Task Added: task_1
2026-05-17 01:00:01 | INFO | Running Task: task_1
2026-05-17 01:00:02 | INFO | Completed Task: task_1
```

---

## License

MIT — see [`LICENSE`](./LICENSE).
