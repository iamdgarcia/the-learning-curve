# 04 — LangChain classic episode agent (langchain 1.4.6, langchain-core 1.6.12, no API keys).
# Scripted BaseChatModel; create_agent (which is a LangGraph internally — see NOTES).
# Run: python agent.py
import asyncio
import time
import warnings

warnings.filterwarnings("ignore")

from langchain.agents import create_agent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import tool


# ---------- scripted fake model ----------
class ScriptedChat(BaseChatModel):
    mode: str = "single"

    def _generate(self, messages, stop=None, run_manager=None, **kw) -> ChatResult:
        has_tool_resp = any(getattr(m, "type", "") == "tool" for m in messages)
        if has_tool_resp:
            names = [getattr(m, "name", "?") for m in messages if getattr(m, "type", "") == "tool"]
            msg = AIMessage(f"Done: {', '.join(names)}")
        elif self.mode == "parallel":
            msg = AIMessage("", tool_calls=[
                {"name": f"w_{c}", "args": {}, "id": f"c{i}"}
                for i, c in enumerate(("madrid", "oviedo", "barcelona"))])
        else:
            last = str(messages[-1].content)
            if "hello" in last:
                msg = AIMessage(f"echo({last})")
            else:
                msg = AIMessage("", tool_calls=[
                    {"name": "get_order_status", "args": {}, "id": "c0"}])
        return ChatResult(generations=[ChatGeneration(message=msg)])

    @property
    def _llm_type(self) -> str:
        return "scripted"

    def bind_tools(self, tools, **kw):  # shipped fakes lack this; scripts must add it
        return self


# ---------- tools ----------
@tool
def get_order_status() -> str:
    """Returns order status."""
    time.sleep(0.8)
    return "shipped"


def mk_weather(city: str):
    async def _w() -> str:
        await asyncio.sleep(0.4)
        return f"sunny {city}"
    _w.__name__ = f"w_{city}"
    _w.__doc__ = f"weather in {city}"
    return tool(_w)


W = {c: mk_weather(c) for c in ("madrid", "oviedo", "barcelona")}


async def b1_tool_loop():
    print("-- b1: tool loop --")
    agent = create_agent(ScriptedChat(), tools=[get_order_status])
    async for ev in agent.astream({"messages": [HumanMessage("status of order A-1234")]},
                                  stream_mode="updates"):
        for k, v in ev.items():
            for m in (v.get("messages", []) if isinstance(v, dict) else []):
                tc = getattr(m, "tool_calls", None)
                print(f"  [{k}] {type(m).__name__}: {str(m.content)[:40]}"
                      + (f" tool_calls={[t['name'] for t in tc]}" if tc else ""))


async def b2_parallel():
    print("-- b2: parallel tools (3 x ~400ms) --")
    agent = create_agent(ScriptedChat(mode="parallel"), tools=list(W.values()))
    t0 = time.time()
    async for ev in agent.astream({"messages": [HumanMessage("parallel weather check")]},
                                  stream_mode="updates"):
        k = list(ev)[0]
        for m in (ev[k].get("messages", []) if isinstance(ev[k], dict) else []):
            print(f"  @{1000*(time.time()-t0):5.0f}ms [{k}] {getattr(m, 'name', '') or type(m).__name__}")
    dt = 1000 * (time.time() - t0)
    print(f"  total {dt:.0f}ms -> {'PARALLEL' if dt < 900 else 'SERIALIZED'}")


async def b3_nonstalling():
    print("-- b3: user turn while tool pending --")
    agent = create_agent(ScriptedChat(), tools=[get_order_status])
    t0 = time.time()
    task = asyncio.create_task(agent.ainvoke({"messages": [HumanMessage("status?")]}))
    await asyncio.sleep(0.05)  # tool pending now
    t1 = time.time()
    r2 = await agent.ainvoke({"messages": [HumanMessage("hello?")]})
    dt = 1000 * (time.time() - t1)
    print(f"  second ainvoke returned @{dt:.0f}ms: {r2['messages'][0].content!r} -> {r2['messages'][-1].content[:30]!r}")
    r1 = await task
    print(f"  first run done @{1000*(time.time()-t0):.0f}ms; its transcript: "
          f"{[str(m.content)[:14] for m in r1['messages']]}")
    print("  => second run is a SEPARATE conversation; 'hello?' never entered run 1")


async def b4_bargein():
    print("-- b4: barge-in at t=100ms (tool sleeps 800ms) --")
    agent = create_agent(ScriptedChat(), tools=[get_order_status])
    t0 = time.time()
    task = asyncio.create_task(agent.ainvoke({"messages": [HumanMessage("status?")]}))
    await asyncio.sleep(0.1)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print(f"  CancelledError @{1000*(time.time()-t0):.0f}ms -> generation AND pending tool cancelled together")


async def main():
    print("=== LangChain classic agent-frameworks-in-action ===")
    await b1_tool_loop()
    await b2_parallel()
    await b3_nonstalling()
    await b4_bargein()
    print("== LangChain: 2/4 behaviors (b3/b4 structural: state per run, no gen/tool separation)")


if __name__ == "__main__":
    asyncio.run(main())
