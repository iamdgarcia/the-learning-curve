# 00 — Plain Python: the baseline agent

Before a framework earns its abstraction, here is what an agent actually is. ~90 lines,
no dependencies, no API keys (scripted fake model — deterministic, CI-friendly).

The canonical agent has 4 behaviors (see the [series README](../README.md)):
tool loop, parallel tools, non-stalling user turn, barge-in.

## Run

```bash
python agent.py
```

## The whole thing

```python
import asyncio, json

# ---------- fake scripted model: deterministic, no API key ----------
class ScriptedModel:
    """Plays the LLM: reads the message log, emits decisions."""

    def __init__(self):
        self.turn = 0

    async def decide(self, messages, pending_results):
        self.turn += 1
        if pending_results:                       # tool results just arrived
            names = [r["name"] for r in pending_results]
            return {"type": "answer",
                    "text": f"Done: {', '.join(names)} -> " +
                            ", ".join(r["result"] for r in pending_results)}
        if any(m["role"] == "user" for m in messages[-1:]):   # fresh user msg
            if "parallel" in messages[-1]["text"]:
                return {"type": "tools", "calls": [
                    {"id": f"c{i}", "name": f"get_weather_{city}", "args": {}}
                    for i, city in enumerate(["madrid", "oviedo", "barcelona"])]}
            if "status" in messages[-1]["text"]:
                return {"type": "tools", "calls": [
                    {"id": "c0", "name": "get_order_status", "args": {}}]}
            return {"type": "answer", "text": "Hello! How can I help?"}
        return {"type": "answer", "text": "..."}

# ---------- ports ----------
TOOLS = {
    "get_order_status": lambda: "shipped",
    **{f"get_weather_{c}": (lambda cc=c: f"sunny in {cc}")
       for c in ["madrid", "oviedo", "barcelona"]},
}

class EventLoop:
    """The agent: one queue, user turns and tool completions are just events."""

    def __init__(self):
        self.messages = []          # canonical state
        self.pending: dict[str, str] = {}   # call_id -> task name
        self.model = ScriptedModel()
        self.user_queue: asyncio.Queue = asyncio.Queue()
        self.wake = asyncio.Event()

    # -- transports call these; they NEVER block on tools (behavior 3) --
    async def user_text(self, text: str):
        self.messages.append({"role": "user", "text": text})
        self.wake.set()

    async def interrupt(self):                       # behavior 4: barge-in
        self._gen_task.cancel()

    # -- the loop --
    async def run(self):
        gen_task = None
        while True:
            await self.wake.wait(); self.wake.clear()
            if gen_task and not gen_task.done():
                await asyncio.sleep(0)  # still streaming; events queued
            # model sees state, decides
            pending_results = [{"name": n, "result": TOOLS[n]()}
                               for n in self.pending.values()]
            decision = await self.model.decide(self.messages, pending_results)
            if decision["type"] == "tools":
                self.pending = {c["id"]: c["name"] for c in decision["calls"]}
                for c in decision["calls"]:       # behavior 2: parallel dispatch
                    asyncio.create_task(self._tool(c["id"], c["name"]))
                self.messages.append({"role": "tool", "text": f"dispatched {len(self.pending)}"})
            else:
                gen_task = asyncio.create_task(self._stream(decision["text"]))
            self.wake.clear()

    async def _tool(self, call_id, name):
        await asyncio.sleep(0.05)                 # pretend network
        self.wake.set()

    async def _stream(self, text):
        for ch in text: print(ch, end="", flush=True)
        print()
```

*(simplified; the runnable file has the scheduler details and prints the event trace)*

## Trace of one run

```
$ python agent.py
user: status of order A-1234
  [model] -> tools: get_order_status
  [loop]  dispatch 1 tool (background), ack immediate
user: hello? you there?            <-- sent 10ms later, NOT blocked by tool
  [loop]  answer: Hello! How can I help?      <-- instant ack (behavior 3)
  [tool]  get_order_status -> shipped (50ms)
  [model] -> answer: Done: get_order_status -> shipped
```

## What you learn from having this baseline

- **An agent loop is small.** The framework's first job is convenience, not magic.
- **Behaviors 3 and 4 are structural**, not features: they fall out of "canonical state +
  event queue" for free. When a framework makes them hard, it's because its abstraction
  (graph nodes, crew steps, checkpointed state) fights the event nature of conversations.
- Every following episode measures the framework against this ruler.
