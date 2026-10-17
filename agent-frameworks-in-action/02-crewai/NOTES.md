# NOTES — CrewAI 1.15.28 vs the canonical spec

## What CrewAI does for you
- **Role-first mental model.** You declare agents (role/goal/backstory) + tasks;
  the framework builds the executor loop, tool schemas (OpenAI-style), and the
  inter-task context passing. My `call()` never sees a graph or a scheduler.
- **`async_execution=True` tasks** give you task-level parallelism with an
  automatic join (the framework waits for async tasks before the next sync task).
- **Deterministic harness details** that production wants: rate-limit retries
  wrapped around the LLM call, telemetry, exec-timeout handling.

## What it hides
- **The LLM wire format.** For a custom `BaseLLM` you get OpenAI-style tool
  schemas in, but the *response* contract is undocumented: the executor only
  treats the answer as tool calls if it's a **list** of
  `{"function": {"name", "arguments"}}` dicts (found by reading
  `agent_executor.py` + `is_tool_call_list`). Return a JSON string and it's
  silently the final answer. Return `{"name", "arguments"}` (Bedrock style) and
  it also works — but `{"tool", "args"}` silently doesn't.
- **Where the tool result goes.** It becomes a `role=tool` message with the raw
  string; the next prompt's `text` (last message) is tiny; the result is only in
  the full message list. If your scripted LLM only reads the last message, the
  loop never converges — an easy way to burn an afternoon.
- **Executor identity.** One `Agent` = one executor instance, and the executor
  refuses concurrent invocation ("Executor is already running"). Parallel tasks
  on the SAME agent crash at runtime — parallelism requires one agent per task,
  which is never stated in the docs.

## How each behavior fares

### 1. Tool loop — works, with a wire-format toll
Works once you return the right shape. Two undocumented formats failed silently
before the third worked. With a real provider LLM you'd never see this; with a
custom/proxy LLM (our daily case) it's a wall.

### 2. Parallel tools — works, but it's task-graph parallelism
`async_execution=True` + a sync join task. Costs: one agent instance per
concurrent task (executor exclusivity), and the join task's LLM call pays the
context re-serialization (~90ms for 3 toy results). No in-flight fan-out: the
unit of parallelism is a whole task, not a tool call inside a turn.

### 3. Non-stalling user turn — does not exist
`kickoff()`/`kickoff_async()` are whole-run barriers. There is no input queue,
no mid-run injection API, no way to admit a user message while tasks run. The
measured ack wait = full crew duration. For interactive agents this is
disqualifying, not inconvenient.

### 4. Barge-in — no surface at all
No streaming hook on `BaseLLM.call` (whole-string in, whole-string out), no
cancel token, no partial output concept. The only cancel is abandoning the
entire kickoff (losing everything). Streams exist for OpenAI-compatible
providers internally, but the extension point isn't exposed to custom LLMs.

## Honest verdict
CrewAI optimizes for *delegated batch work by role-playing crews* — research
dossiers, pipelines, reports. Its abstractions (tasks, crews, role context)
assume each unit runs to completion. The canonical spec's realtime behaviors
(3, 4) aren't hard-but-possible here; they're not modeled. If you need them,
you end up writing your own event loop around CrewAI — at which point the
framework is a library of tool-schema builders, not your runtime.
