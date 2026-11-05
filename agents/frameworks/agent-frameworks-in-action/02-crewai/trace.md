# Trace — actual output of python agent.py

```
== behavior 1: tool loop ==
  156.2ms [llm] prompt 201 chars; tools offered: ['order_status', 'weather']
  208.0ms [tool] order_status EXECUTED
  213.5ms [llm] prompt 7 chars; tools offered: ['order_status', 'weather']

== behavior 2: parallel tools ==
  418.4ms [llm] prompt 187 chars; tools offered: ['weather']
  434.4ms [llm] prompt 187 chars; tools offered: ['weather']
  443.9ms [llm] prompt 190 chars; tools offered: ['weather']
  470.0ms [tool] weather(madrid) EXECUTED
  476.5ms [llm] prompt 9 chars; tools offered: ['weather']
  486.5ms [tool] weather(oviedo) EXECUTED
  492.0ms [llm] prompt 8 chars; tools offered: ['weather']
  496.0ms [tool] weather(barcelona) EXECUTED
  504.5ms [llm] prompt 9 chars; tools offered: ['weather']
  603.1ms [llm] prompt 396 chars; tools offered: []
  660.9ms [crew] 3 async tasks joined in 391ms (parallel gate)

== behavior 3: non-stalling user turn ==
  kickoff() is a blocking call: a user message arriving while the crew
  runs has nowhere to go (no input queue, no mid-run injection API).
  Demonstrating the BLOCK: measuring ack latency if we 'answer' the user
  only after kickoff returns.
  739.2ms [llm] prompt 196 chars; tools offered: ['order_status', 'weather']
  792.2ms [tool] order_status EXECUTED
  803.7ms [llm] prompt 7 chars; tools offered: ['order_status', 'weather']
  877.3ms [measured] user ack waited 216ms == full crew duration (stalls)

== behavior 4: barge-in mid-stream ==
  No streaming surface: ScriptedLLM.call returns the whole string; there
  is no token-stream hook to cancel mid-flight. The LLM call itself is
  opaque to the framework. Demonstrating: nothing to cancel between
  kickoff start and end except the whole call.
  946.8ms [llm] prompt 184 chars; tools offered: ['order_status', 'weather']
  999.9ms [tool] order_status EXECUTED
 1008.1ms [llm] prompt 7 chars; tools offered: ['order_status', 'weather']
 1084.5ms [measured] kickoff ran to completion 207ms; no partial output exists

```
