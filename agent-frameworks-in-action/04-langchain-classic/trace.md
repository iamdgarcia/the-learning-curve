# 04 — LangChain classic: real trace

Output of `python agent.py` (langchain 1.4.6, langchain-core 1.6.12, no API keys,
scripted model).

```
=== LangChain classic agent-frameworks-in-action ===
-- b1: tool loop --
  [model] AIMessage:  tool_calls=['get_order_status']
  [tools] ToolMessage: shipped
  [model] AIMessage: Done: get_order_status
-- b2: parallel tools (3 x ~400ms) --
  @    5ms [model] AIMessage
  @  424ms [tools] w_madrid
  @  424ms [tools] w_oviedo
  @  424ms [tools] w_barcelona
  @  428ms [model] AIMessage
  total 428ms -> PARALLEL
-- b3: user turn while tool pending --
  second ainvoke returned @3ms: 'hello?' -> 'echo(hello?)'
  first run done @808ms; its transcript: ['status?', '', 'shipped', 'Done: get_orde']
  => second run is a SEPARATE conversation; 'hello?' never entered run 1
-- b4: barge-in at t=100ms (tool sleeps 800ms) --
  CancelledError @106ms -> generation AND pending tool cancelled together
== LangChain: 2/4 behaviors (b3/b4 structural: state per run, no gen/tool separation)
```

Key numbers: parallel tools 418ms total (vs ~1200ms serialized); second invocation
during a pending tool = independent conversation (3ms ack because the fake model is
instant, but it never touches run 1's state); barge-in cancels the pending 800ms tool
with the run.
