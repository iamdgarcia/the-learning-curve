"""Episode 01 — LangGraph 1.2.16: the canonical agent spec, four behaviors.

Same 4 behaviors as 00-plain-python:
  1. tool loop          2. parallel tools
  3. non-stalling user turn (while tools pending)
  4. barge-in mid-stream (tools keep running)

ZERO API keys: the "LLM" is a scripted fake that decides from the message log.
Run:  python agent.py
"""
from __future__ import annotations

import asyncio
import threading
import time
from typing import Annotated, Any, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command


# ---------------- fake scripted model (no API key) ----------------
def scripted_decide(msgs: list[dict], tool_results: dict[str, str]) -> dict:
    """Deterministic policy standing in for the LLM."""
    last = msgs[-1]
    if tool_results:
        return {"kind": "answer", "text": "Done: " + "; ".join(f"{k}={v}" for k, v in tool_results.items())}
    if last["role"] == "tool_user":  # a user turn injected mid-pending
        return {"kind": "answer", "text": f"(ack) {last['text']}"}
    if last["role"] == "user":
        t = last["text"]
        if "parallel" in t:
            return {"kind": "tools", "calls": [("w_madrid", {}), ("w_oviedo", {}), ("w_barcelona", {})]}
        if "status" in t:
            return {"kind": "tools", "calls": [("order_status", {})]}
        if "long story" in t:
            return {"kind": "stream", "text": "Once upon a time a voice agent learned to yield. " * 8}
    return {"kind": "answer", "text": "Hello!"}


TOOLS = {
    "order_status": lambda a: "shipped",
    "w_madrid": lambda a: "sunny 23C",
    "w_oviedo": lambda a: "rain 14C",
    "w_barcelona": lambda a: "humid 25C",
}


# ---------------- graph state ----------------
class State(TypedDict):
    msgs: Annotated[list[dict], lambda a, b: a + b]  # reducer: append
    pending: dict[str, str]  # call_id -> tool name
    results: dict[str, str]
    stream: str


# ---------------- nodes ----------------
t0 = time.time()


def ts() -> str:
    return f"{(time.time() - t0) * 1000:7.1f}ms"


def model_node(state: State) -> dict:
    tool_results = state["results"] if state["results"] else {}
    d = scripted_decide(state["msgs"], tool_results)
    print(f"{ts()} [model] -> {d['kind']}")
    if d["kind"] == "tools":
        calls = {name: args for name, args in d["calls"]}  # name -> args
        return {"pending": calls, "msgs": [{"role": "tool", "text": f"dispatch {len(calls)}"}]}
    if d["kind"] == "stream":
        # simulate token streaming; global CANCEL_EVENT flips on barge-in
        out = []
        for word in d["text"].split(" "):
            if CANCEL_EVENT.is_set():
                print(f"{ts()} [model] stream CANCELLED (barge-in)")
                break
            out.append(word)
            time.sleep(0.01)
        text = " ".join(out)
        return {"msgs": [{"role": "assistant", "text": text}], "stream": text}
    return {"msgs": [{"role": "assistant", "text": d["text"]}]}


def tools_node(state: State) -> dict:
    """Fan-out: run pending tools in parallel threads (behavior 2)."""
    pending = state["pending"]
    if not pending:
        return {}
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(len(pending)) as ex:
        futs = {tname: ex.submit(TOOLS[tname], args) for tname, args in pending.items()}
        results = {tname: f.result() for tname, f in futs.items()}
    for tname, r in results.items():
        print(f"{ts()} [tool] {tname} -> {r}")
    return {"results": results, "pending": {}, "msgs": [{"role": "tool", "text": "results"}]}


def route(state: State) -> str:
    if state["pending"]:
        return "tools"
    if state["results"] and state["msgs"][-1]["role"] == "tool":
        return "model"
    return END


CANCEL_EVENT = threading.Event()

# ---------------- build ----------------
g = StateGraph(State)
g.add_node("model", model_node)
g.add_node("tools", tools_node)
g.add_edge(START, "model")
g.add_conditional_edges("model", route, {"tools": "tools", "model": "model", END: END})
g.add_conditional_edges("tools", route, {"tools": "tools", "model": "model", END: END})
app = g.compile()


# ---------------- driving the four behaviors ----------------
async def main() -> None:
    print("== behavior 1: tool loop ==")
    app.invoke({"msgs": [{"role": "user", "text": "status of order A-1234"}],
                "pending": {}, "results": {}, "stream": ""})

    print("\n== behavior 2: parallel tools (3 weather) ==")
    app.invoke({"msgs": [{"role": "user", "text": "parallel: weather now"}],
                "pending": {}, "results": {}, "stream": ""})

    print("\n== behavior 3: non-stalling user turn ==")
    print("  NOTE: invoke() is synchronous end-to-end; a user turn sent while")
    print("  tools run must wait for the WHOLE graph pass to finish (see NOTES).")
    # demonstrate: send second user message only after invoke returns
    app.invoke({"msgs": [{"role": "user", "text": "hello?"}], "pending": {}, "results": {}, "stream": ""})

    print("\n== behavior 4: barge-in mid-stream ==")
    CANCEL_EVENT.clear()
    t = threading.Thread(target=lambda: (time.sleep(0.08), CANCEL_EVENT.set()), daemon=True)
    t.start()
    app.invoke({"msgs": [{"role": "user", "text": "tell me a long story"}],
                "pending": {}, "results": {}, "stream": ""})
    t.join()
    print(f"{ts()} [app] invoke returned after cancel")


if __name__ == "__main__":
    asyncio.run(main())
