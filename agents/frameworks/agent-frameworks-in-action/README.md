# Agent Frameworks in Action — same agent, four frameworks

*New TLC series: one agent specification, implemented side by side in LangChain/LangGraph, CrewAI, Google ADK, and plain Python. Every example runs, prints its own trace, and explains what the framework does (and hides) for you.*

---

## Why this series

Every framework demo you find shows a *different* agent doing a *different* task. You learn the framework's API, not the trade-off. This series does the opposite:

**One canonical agent spec** (the same 4 behaviors everywhere):

1. **Tool loop** — call a (fake) weather tool, feed the result back, answer.
2. **Parallel tools** — dispatch 3 independent calls at once, join results.
3. **Non-stalling user turn** — user sends a message while tools are pending; must be acknowledged without waiting for the tools.
4. **Barge-in** — cancel an in-flight answer mid-stream; tools keep running.

These four behaviors are exactly what separates a demo from a production voice/chat agent — and they're the same conformance cells we use to measure voice frameworks (`event-driven-voice-orchestrator` conformance kit). Here we apply them to the agent-framework layer.

**What each episode delivers:**

- `agent.py` — the canonical agent in that framework (~100–200 lines, runnable with zero API keys via a scripted fake model)
- `trace.md` — the actual printed event trace of the run (what the framework emits, in what order)
- `NOTES.md` — what the framework does for you / hides from you / makes hard (the honest part)

## Episodes

| # | Framework | Status | What it teaches |
|---|---|---|---|
| 0 | **Plain Python (no framework)** | ✅ [live](./00-plain-python/) | The baseline: an agent loop is ~80 lines. Everything a framework adds is either convenience or constraint — this is the ruler we measure the rest with. |
| 1 | **LangGraph** | ✅ [live](./01-langgraph/) | Graph-of-nodes mental model; where "parallel" happens (fan-out nodes), why user-turn-during-tools is awkward (state checkpointing) |
| 2 | **CrewAI** | ✅ [live](./02-crewai/) | Role-based crews; great for sequential delegation, weak guarantees on streaming/interruption |
| 3 | **Google ADK** | ✅ [live](./03-google-adk/) | Session/state services; native parallel function calling; the most "managed" of the four |
| 4 | **LangChain (classic)** | ✅ [live](./04-langchain-classic/) | The original tool loop; LCEL streaming; where the newer LangGraph supersedes it |

Each folder: runnable code + trace + notes. Zero API keys needed anywhere (fake scripted models), so every example is CI-friendly and free to run.

## The scoreboard (grows as episodes land)

| Behavior | Plain | LangGraph | CrewAI | ADK | LangChain |
|---|---|---|---|---|---|
| Tool loop | ✅ explicit | ✅ implicit (node cycle) | ✅ implicit (crew step) | ✅ implicit | ✅ explicit |
| Parallel tools | ✅ asyncio.gather | ✅ fan-out | ⚠️ sequential default | ✅ native parallel fns | ⚠️ manual |
| Non-stalling user turn | ✅ queue | ❌ checkpoint blocks | ❌ not modeled | ⚠️ partial | ❌ blocks |
| Barge-in mid-stream | ✅ task.cancel | ⚠️ via node interrupt | ❌ | ⚠️ partial | ⚠️ manual |

*⚠️ = possible but you build it yourself. ❌ = the abstraction fights you. Scores come from the traces, not vibes — each episode shows the repro.*

## Related work in this repo

- [**event-driven-voice-orchestrator**](https://github.com/iamdgarcia/event-driven-voice-orchestrator) — the voice-agent version of the same conformance idea (with a LiveKit adapter)
- [Watch your voice agent think](https://iamdgarcia.medium.com/watching-your-voice-agent-think-three-instruments-you-can-open-in-a-browser-tab-f7ed16ec2a2a) — why observability of the *turn geometry* matters
- [Agentic AI for Beginners](https://github.com/iamdgarcia/tlc_agents_training) — the course this series slots into

## Substack

Each episode gets a companion post in [The Learning Curve](https://iamdgarcia.substack.com) with the trace annotated line by line.
