# 04 — LangChain classic (langchain 1.4.6 / langchain-core 1.6.12)

`create_agent` (the 1.x tool-loop factory — internally a LangGraph, which is itself
a finding) with a scripted fake `BaseChatModel`. The pre-1.0 `create_tool_calling_agent`
path is gone from the docs; this is the current classic API.

## Run

```bash
pip install langchain   # 1.4.6; langchain-core 1.6.12
python agent.py
```

No API keys: the model is a minimal `BaseChatModel` subclass (scripted `_generate`,
plus a no-op `bind_tools` — the fake models shipped with core lack `bind_tools`, which
is itself a finding: "just test with a fake model" is not actually supported).

## Behaviors

### 1. Tool loop — PASS

`create_agent` builds the loop for you; the stream emits per-node updates
(`model` node → `tools` node → `model` node). Clean and legible.

### 2. Parallel tools — PASS (verified by timing)

One `AIMessage` with 3 `tool_calls` → all three tools ran concurrently (all results
landed at ~433ms, total 436ms vs 1200ms serialized). LangChain executes the tool
calls of a single AIMessage concurrently.

### 3. Non-stalling user turn — FAIL (the honest one)

A second `ainvoke()` while the first has a tool pending does NOT fail and does NOT
block — but it is a **completely separate conversation**: its state starts fresh, the
"hello?" never enters the first run, and it takes ~810ms because it replays the whole
loop. There is no way to inject a user message into an in-flight run's state;
checkpointed graph state is per-invocation.

This is the structural difference with ADK (shared session state) and with an
event-loop agent (canonical state + queue): in LangChain/LangGraph the *run* is the
unit of conversation. Multi-turn = state you carry across invocations yourself.

### 4. Barge-in — FAIL (worse: it kills the tool)

`task.cancel()` on the run cancels everything — the in-flight answer AND the pending
tool execution (the 800ms tool was mid-`sleep` at t=100ms; cancellation propagated
into the tool task). Result: partial output lost AND the side effect model never saw
the tool complete. In the plain-Python baseline, cancel = generation only, tools keep
running — that's the contract a voice agent needs ("cancel the answer, keep the
booking"). In LangChain the abstraction does not separate generation from tool
execution, so it can't honor that contract.

## Trace (real output, `python agent.py`)

```
=== LangChain classic agent-frameworks-in-action ===
-- b1: tool loop --
  [model] AIMessage tool_calls=['get_order_status']
  [tools] ToolMessage 'shipped'
  [model] AIMessage 'Done: order is shipped'
-- b2: parallel tools (3 x ~400ms) --
  w_madrid / w_oviedo / w_barcelona results all landed ~433ms; total 436ms -> PARALLEL
-- b3: user turn while tool pending --
  second ainvoke returned in 809ms with its OWN conversation (echo(hello?))
  first run finished at 867ms — 'hello?' never entered it -> SEPARATE STATE
-- b4: barge-in at t=100ms --
  CancelledError at 109ms — pending tool (800ms) cancelled WITH the run
== LangChain: 2/4 behaviors; b3/b4 structural (state per run, no generation/tool separation)
```

## NOTES — what LangChain does for you / hides / makes hard

**Does for you:** the whole tool loop (model → tools → model), parallel execution of
one message's tool calls, streaming updates per graph node, one-line agent factory.

**Hides from you:** that `create_agent` IS a LangGraph (the "classic" wrapper sits on
the graph runtime — its concurrency semantics leak through); that runs are atomic
conversations (nothing in the API surface says "this state is per-run").

**Makes hard:** injecting a user message into a running conversation (no API);
cancelling generation but not tools (no API — cancellation is all-or-nothing);
testing without a real model (shipped fakes lack `bind_tools`; you write your own).

## The voice-agent verdict

Same conformance cells as our voice kit: LangChain classic is a fine *chat* tool
loop, but a voice runtime built on it would stall on pending tools (b3) and cancel
in-flight tool work on barge-in (b4). Both are exactly the failure modes the
event-driven orchestrator exists to remove.
