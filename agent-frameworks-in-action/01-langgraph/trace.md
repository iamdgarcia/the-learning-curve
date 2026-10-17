# Trace — actual output of python agent.py

```
== behavior 1: tool loop ==
   25.0ms [model] -> tools
   30.0ms [tool] order_status -> shipped
   31.0ms [model] -> answer

== behavior 2: parallel tools (3 weather) ==
   32.0ms [model] -> tools
   34.0ms [tool] w_madrid -> sunny 23C
   34.0ms [tool] w_oviedo -> rain 14C
   34.0ms [tool] w_barcelona -> humid 25C
   35.0ms [model] -> answer

== behavior 3: non-stalling user turn ==
  NOTE: invoke() is synchronous end-to-end; a user turn sent while
  tools run must wait for the WHOLE graph pass to finish (see NOTES).
   35.0ms [model] -> answer

== behavior 4: barge-in mid-stream ==
   37.0ms [model] -> stream
  120.4ms [model] stream CANCELLED (barge-in)
  120.4ms [app] invoke returned after cancel

```
