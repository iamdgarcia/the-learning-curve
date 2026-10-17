# NOTES — LangGraph 1.2.16 vs the canonical spec

## What LangGraph does for you
- **The loop is the graph.** You declare nodes + conditional edges; the run loop
  (super-step execution, state reduction, retries) is the framework's. My agent.py
  has zero while-loops.
- **State reducers** (`Annotated[list, add]`) handle concurrent writes from
  parallel branches — you don't write the merge logic.
- **Conditional edges** make the tool-loop routing declarative: `route()`
  returns the next node name; the graph owns the schedule.

## What it hides
- **Scheduling**: `invoke()` is a synchronous barrier over the whole graph pass.
  Everything between START and END completes before you get control back.
- **Concurrency model**: tools in my fan-out node run in a ThreadPoolExecutor I
  created — LangGraph itself executed the node; the parallelism inside it is mine.
  (LangGraph does support native parallel branches via multiple edges from one
  node + reducer join — that is framework-level, but it is a *graph topology*
  feature, not a per-turn runtime feature.)

## How each behavior fares

### 1. Tool loop — works, implicit
Model node -> tools node -> back. Clean. But notice: the loop is a *graph
cycle*, so "the agent decided to call a tool" is expressed as routing, not as a
runtime event. There is no observable "tool_call started" boundary you can
interpose without adding nodes.

### 2. Parallel tools — works
Fan-out inside one node with a thread pool, or native parallel branches at the
topology level. Both work; both are batch-oriented: you collect ALL results,
then move on. There is no notion of "some tools still pending while the loop
continues."

### 3. Non-stalling user turn — the framework fights you
This is the structural finding. `invoke()`/`stream()` are barrier semantics:
the graph pass must complete. If a user sends a message while tools are
running, you have exactly three options:
  a. Wait for the pass to finish (what agent.py demonstrates — ack latency =
     full tool duration).
  b. Use `interrupt()` (human-in-the-loop) checkpoints — but those *pause the
     graph for approval*, they do not admit new user input mid-pass.
  c. Run the graph as a long-lived service and push user messages through
     `add_item`-style input queues — LangGraph (server) has this, the library
     does not; and even then, the state checkpoint model (Pregel supersteps)
     means the new input lands at the next superstep boundary, not "now".
The plain-Python baseline answers this for free: the user turn is just another
event on the queue. In LangGraph it is an architectural outcast.

### 4. Barge-in — works only because I faked it
The stream cancel is a `threading.Event` I check inside my own node. LangGraph
never cancelled anything; my node cooperatively yielded. A real streaming LLM
call inside a node would need task-level cancellation, which for `invoke()`
means throwing away the whole pass (state up to that point is lost unless
checkpointed). So: barge-in possible, but it is *your* code, not the
framework's, and the state-loss question is yours too.

## Honest verdict
LangGraph excels at *durable, resumable, auditable* agent runs (checkpoints,
time travel, branch ops). The canonical spec's behaviors 3 and 4 — the
realtime, event-driven ones — are outside its center of gravity. Not bugs:
different design target. If your agent talks with a human in real time, you
will be building an event layer NEXT TO the graph (which is exactly what
production teams end up doing).
