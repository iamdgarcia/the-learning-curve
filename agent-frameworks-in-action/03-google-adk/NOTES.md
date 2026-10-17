# 03 — Google ADK (google-adk 1.31.1)

The most "managed" of the four: you declare an `Agent` (model + tools + instruction),
wrap it in a `Runner`, and consume an event stream from `run_async()`. Sessions,
state, and artifacts live in injected services (here: all in-memory).

## Run

```bash
pip install google-adk   # 1.31.1 used here
python agent.py
```

No API keys: the model is a custom `BaseLlm` subclass that plays an LLM from a script
(yield `LlmResponse`s — async generator, that's the contract; a plain coroutine breaks
ADK's tracing wrapper).

## Behaviors

### 1. Tool loop — PASS, and observable

The model yields a `function_call` part; ADK executes the Python function, appends a
`function_response` to the session, and re-invokes the model. Every hop surfaces as an
`Event` on the run stream — the whole loop is legible from the outside.

### 2. Parallel tools — PASS (verified by timing)

One `LlmResponse` can carry several `function_call` parts. ADK runs them concurrently
(all three tool bodies entered within 1ms of each other; total wall time ~= one tool
duration, not three). This is ADK's "parallel function calling" — it's real.

### 3. Non-stalling user turn — PASS with an asterisk

You can open a second `run_async()` on the same session while the first invocation has
a tool pending. It completed in ~2ms with its own answer (fake model latency), and the
session transcript shows both interleaved correctly:

```
[user] go
[model] CALL aslow
[user] hello?            <- arrived while the tool was pending
[model] Hello! I am here.
[user] RESP aslow
[model] tool done
```

The asterisk: this is *invocation-level* concurrency, not turn-level. Each
`run_async()` call is one invocation with its own event stream; the "ack" you get is
your own stream, not a guarantee from ADK. If your tool blocks the event loop (sync
`time.sleep` in a tool function), the WHOLE runner stalls — ADK does not threadify
your tools for you. Make tools `async def`.

### 4. Barge-in — PASS, but it's consumer-side

There is no `runner.cancel()`. You stop the run by closing the generator
(`await agen.aclose()`), which fires `GeneratorExit` up through the model stream and
kills generation in place. Verified: after aclose at partial 2, the session records
only the user text — partials are NOT persisted, the answer simply stops existing.

That's honest cancellation semantics: clean, but *you* own it. An ADK-based voice
agent must wrap `run_async()` consumption in a task it can cancel — exactly the
"delivery lifecycle is separate from generation" insight our voice orchestrator
teaches.

## Trace (real output, `python agent.py`)

```
=== ADK agent-frameworks-in-action ===
-- b1: tool loop --
  EVENT function_call: get_order_status
  EVENT text: Done: order is shipped
-- b2: parallel tools (3 x ~400ms) --
  tool bodies entered at: madrid=8ms oviedo=8ms barcelona=9ms
  EVENT text: done ['w_madrid', 'w_oviedo', 'w_barcelona']
  total: 419ms -> PARALLEL
-- b3: user turn while tool pending --
  second invocation answered in 2ms: 'Hello! I am here.'
  transcript shows both interleaved (see NOTES)
-- b4: barge-in mid-stream --
  partial 1 'one ' partial 2 'two ' ... aclose
  session after: only user text recorded (partials dropped)
== 4/4 behaviors work (b3 = invocation-level concurrency, b4 = consumer-owned)
```

## NOTES — what ADK does for you / hides / makes hard

**Does for you:** session + state services with real APIs (`session_service`),
telemetry (OpenTelemetry spans on every LLM call — we saw them in stderr), parallel
function calling, structured events for everything (the run stream IS a trace).

**Hides from you:** the tool-execution scheduling (sync tools block the loop — silent
footgun), the distinction between invocation and turn (there is no turn concept; you
build "user said something while busy" yourself via concurrent invocations).

**Makes hard:** barge-in is consumer-side cancellation with no helper; multiple
invocations on one session are allowed but their ordering guarantees are yours to
reason about; noisy OTel context-detach tracebacks on generator close (harmless, but
scary in logs).
