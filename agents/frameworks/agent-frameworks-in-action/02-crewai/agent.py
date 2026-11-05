"""Episode 02 — CrewAI 1.15.28: the canonical agent spec, four behaviors.

Same 4 behaviors: tool loop, parallel tools, non-stalling user turn, barge-in.
ZERO API keys: CrewAI requires an LLM — we give it a scripted fake via the
LLM base class, deterministic, no network.

Run:  python agent.py
"""
from __future__ import annotations

import asyncio
import os
import threading
import time

os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
from concurrent.futures import ThreadPoolExecutor

from crewai import Agent, Crew, Task
from crewai.llms.base_llm import BaseLLM
from crewai.tools import tool

t0 = time.time()


def ts() -> str:
    return f"{(time.time() - t0) * 1000:7.1f}ms"


# ---------------- scripted fake LLM (no API key, no network) ----------------
class ScriptedLLM(BaseLLM):
    """Stands in for the model: answers from the prompt text deterministically."""

    def __init__(self):
        super().__init__(model="scripted/fake")

    def call(self, messages, tools=None, **kwargs) -> str | list:
        text = messages[-1]["content"] if isinstance(messages[-1], dict) else str(messages[-1])
        all_text = " ".join(str(m.get("content", "")) if isinstance(m, dict) else str(m) for m in messages)
        fnames = [t.get("function", {}).get("name") for t in (tools or []) if isinstance(t, dict)]
        print(f"{ts()} [llm] prompt {len(text)} chars; tools offered: {fnames}")
        if tools and "shipped" not in all_text and "sunny" not in all_text and "rain" not in all_text and "humid" not in all_text:
            # CrewAI's executor expects a LIST of OpenAI-style tool calls; fill args
            import json as _json, re as _re
            args = {}
            if fnames[0] == "weather":
                m = _re.search(r"weather in (\w+)", all_text)
                args = {"city": m.group(1) if m else "madrid"}
            return [{"function": {"name": fnames[0], "arguments": _json.dumps(args)}}]
        # tool results already in context -> final answer (breaks the loop)
        return "Hello from the scripted crew!"

    def supports_function_calling(self) -> bool:
        return True

    def supports_stop_words(self) -> bool:
        return False

    def get_context_window_size(self) -> int:
        return 8192


# ---------------- fake tools ----------------
@tool("order_status")
def order_status() -> str:
    """Check order status."""
    time.sleep(0.05)
    print(f"{ts()} [tool] order_status EXECUTED")
    return "shipped"


@tool("weather")
def weather(city: str) -> str:
    """Get weather for a city."""
    time.sleep(0.05)
    print(f"{ts()} [tool] weather({city}) EXECUTED")
    return {"madrid": "sunny 23C", "oviedo": "rain 14C", "barcelona": "humid 25C"}[city]


# ---------------- crew ----------------
llm = ScriptedLLM()

agent = Agent(
    role="support agent",
    goal="answer the user using tools when needed",
    backstory="A deterministic scripted agent used for framework conformance testing.",
    llm=llm,
    tools=[order_status, weather],
    allow_delegation=False,
    verbose=False,
)

task = Task(
    description="{user_request}",
    expected_output="a short answer",
    agent=agent,
)

crew = Crew(agents=[agent], tasks=[task], verbose=False)


def behavior_1_tool_loop():
    print("== behavior 1: tool loop ==")
    crew.kickoff(inputs={"user_request": "status of order A-1234 (use the tool)"})


def behavior_2_parallel_tools():
    print("\n== behavior 2: parallel tools ==")
    # CrewAI tasks are sequential by default (one agent, one task at a time).
    # True parallel fan-out requires a Crew with multiple tasks + async_execution=True,
    # so demonstrate the official mechanism:
    from crewai import Task as T

    a2 = Agent(role="weather agent", goal="report weather", backstory="scripted",
               llm=llm, tools=[weather], allow_delegation=False, verbose=False)
    cities = ["madrid", "oviedo", "barcelona"]
    # NOTE: one agent == one executor; concurrent tasks on the same agent raise
    # "Executor is already running". Parallel fan-out needs one agent per task.
    def mk(city):
        ag = Agent(role=f"weather agent {city}", goal="report weather", backstory="scripted",
                   llm=llm, tools=[weather], allow_delegation=False, verbose=False)
        return T(description=f"weather in {city} (use the tool)", expected_output="short",
                 agent=ag, async_execution=True)
    tasks = [mk(c) for c in cities]
    a_join = Agent(role="summarizer", goal="one-line summary", backstory="scripted",
                   llm=llm, allow_delegation=False, verbose=False)
    tasks.append(T(description="summarize the three weather results in one line",
                   expected_output="one line", agent=a_join, async_execution=False))
    c2 = Crew(agents=[a2], tasks=tasks, verbose=False)
    t1 = time.time()
    result = c2.kickoff()
    print(f"{ts()} [crew] 3 async tasks joined in {(time.time() - t1) * 1000:.0f}ms (parallel gate)")


def behavior_3_nonstalling_turn():
    print("\n== behavior 3: non-stalling user turn ==")
    print("  kickoff() is a blocking call: a user message arriving while the crew")
    print("  runs has nowhere to go (no input queue, no mid-run injection API).")
    print("  Demonstrating the BLOCK: measuring ack latency if we 'answer' the user")
    print("  only after kickoff returns.")
    t1 = time.time()
    crew.kickoff(inputs={"user_request": "long status check (use the tool)"})
    tool_ms = (time.time() - t1) * 1000
    print(f"{ts()} [measured] user ack waited {tool_ms:.0f}ms == full crew duration (stalls)")


def behavior_4_barge_in():
    print("\n== behavior 4: barge-in mid-stream ==")
    print("  No streaming surface: ScriptedLLM.call returns the whole string; there")
    print("  is no token-stream hook to cancel mid-flight. The LLM call itself is")
    print("  opaque to the framework. Demonstrating: nothing to cancel between")
    print("  kickoff start and end except the whole call.")
    t1 = time.time()
    result = crew.kickoff(inputs={"user_request": "tell me a long story"})
    print(f"{ts()} [measured] kickoff ran to completion {(time.time() - t1) * 1000:.0f}ms; no partial output exists")


if __name__ == "__main__":
    behavior_1_tool_loop()
    behavior_2_parallel_tools()
    behavior_3_nonstalling_turn()
    behavior_4_barge_in()
