# 🤖 ai-agent-os

> A distributed, event-driven AI Agent Operating System — powered by Apache Kafka, local LLMs (Ollama), and a modular Python pipeline.

---

## What Is This?

`ai-agent-os` is an **AI agent orchestration framework** that processes tasks asynchronously at scale. It decouples task submission from execution using Apache Kafka as the message bus, and uses a local LLM (Mistral via Ollama) to plan and decompose tasks before execution.

---

## Architecture at a Glance

```
main.py ──► TaskProducer ──► Kafka ──► TaskConsumer ──► Worker
                                                            │
                                                         Pipeline
                                                            │
                                           ┌────────────────┤
                                       Scheduler       AgentManager
                                           │            Planner + Executor
                                    (Priority Queue)        │
                                                     LLM (Ollama/Mistral)
                                                            │
                                                       MathTool / Logger
```

For full details, see [`SYSTEM_ARCHITECTURE.md`](./SYSTEM_ARCHITECTURE.md).

---

## Project Structure

```
ai-agent-os/
├── main.py                  # Entry point: publish tasks to Kafka
├── docker-compose.yml       # Kafka + Zookeeper services
├── agents/
│   ├── manager.py           # Orchestrates planner + executor
│   ├── planner.py           # LLM-based task decomposition
│   └── executor.py          # Runs subtasks via tools
├── brokers/
│   ├── producer.py          # Publishes tasks to Kafka
│   └── consumer.py          # Reads tasks from Kafka
├── config/
│   └── kafka_config.py      # Broker URL and topic name
├── core/
│   ├── pipeline.py          # Main orchestration hub
│   └── state.py             # Tracks task completion/failure
├── llm/
│   ├── client.py            # HTTP interface to Ollama
│   └── prompts.py           # Prompt templates
├── memory/
│   └── memory_store.py      # In-process key-value result store
├── models/
│   └── task.py              # Task dataclass + TaskStatus enum
├── scheduler/
│   └── scheduler.py         # Priority queue + retry + dependency check
├── tools/
│   ├── gateway.py           # Single tool execution entry point
│   ├── registry.py          # Maps tool names to instances
│   ├── math_tool.py         # Evaluates math expressions
│   └── logger.py            # Prints log messages
├── workers/
│   └── worker.py            # Kafka consumer loop + pipeline trigger
└── logs/
    └── system.log           # Runtime scheduler logs
```

---

## Prerequisites

| Requirement | Purpose |
|---|---|
| Python 3.9+ | Runtime |
| Docker + Docker Compose | Kafka + Zookeeper |
| Ollama + Mistral | Local LLM server |
| `kafka-python`, `requests` | Python dependencies |

---

## Quick Start

```bash
# 1. Start Kafka
docker-compose up -d

# 2. Install dependencies
pip install kafka-python requests

# 3. Start Ollama
ollama run mistral

# 4. Start the worker (terminal 1)
python workers/worker.py

# 5. Publish tasks (terminal 2)
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

Scheduler events are written to `logs/system.log`:

```
2026-05-17 01:00:00 | INFO | Task Added: task_1
2026-05-17 01:00:01 | INFO | Running Task: task_1
2026-05-17 01:00:02 | INFO | Completed Task: task_1
```

---

## License

MIT — see [`LICENSE`](./LICENSE).
