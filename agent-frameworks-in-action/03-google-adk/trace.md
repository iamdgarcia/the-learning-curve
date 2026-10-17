# 03 — Google ADK: real trace

Output of `python agent.py` (google-adk 1.31.1, no API keys, scripted model).
The only cleanup: OpenTelemetry prints harmless context-detach tracebacks when a
stream generator is closed early (ADK bug, reported upstream behavior — see NOTES).

```
-- b1: tool loop --
  EVENT function_call: get_order_status
  EVENT text: done: ['get_order_status']
-- b2: parallel tools (3 x ~400ms) --
  tool bodies entered at {'madrid': 4, 'oviedo': 4, 'barcelona': 4}ms; total 434ms -> PARALLEL
-- b3: user turn while tool pending --
  second invocation answered in 14ms: 'Hello! I am here.'
-- b4: barge-in mid-stream --
  aclose after 2 partials -> generation aborted, partials not persisted
== ADK: 4/4 behaviors (b3 = invocation-level concurrency, b4 = consumer-owned cancel)
```
