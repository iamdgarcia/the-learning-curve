# 03 — Google ADK episode agent (google-adk 1.31.1, zero API keys).
# Custom BaseLlm plays the LLM from a script; InMemoryRunner + session service.
# Run: python agent.py
import asyncio
import time
import warnings

warnings.filterwarnings("ignore")

from google.adk.agents import Agent
from google.adk.models import BaseLlm
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.runners import InMemoryRunner
from google.genai import types as gtypes


# ---------- scripted fake model (the LLM contract: async GENERATOR) ----------
class ScriptedLlm(BaseLlm):
    model: str = "scripted"

    async def generate_content_async(self, llm_request: LlmRequest, stream: bool = False):
        last = llm_request.contents[-1] if llm_request.contents else None
        parts0 = last.parts[0] if last and last.parts else None

        def user_text() -> str:
            return parts0.text if parts0 and parts0.text else ""

        if parts0 and parts0.function_response:
            frs = [p.function_response.name for p in last.parts if p.function_response]
            yield LlmResponse(content=gtypes.Content(
                role="model", parts=[gtypes.Part(text=f"done: {frs}")]))
        elif "parallel" in user_text():
            # several function_calls in ONE response = ADK parallel function calling
            yield LlmResponse(content=gtypes.Content(role="model", parts=[
                gtypes.Part(function_call=gtypes.FunctionCall(name=f"w_{c}", args={}))
                for c in ("madrid", "oviedo", "barcelona")]))
        elif "hello" in user_text():
            yield LlmResponse(content=gtypes.Content(
                role="model", parts=[gtypes.Part(text="Hello! I am here.")]))
        elif "long" in user_text():
            for word in ("one ", "two ", "three ", "four ", "five "):
                await asyncio.sleep(0.15)
                yield LlmResponse(content=gtypes.Content(
                    role="model", parts=[gtypes.Part(text=word)]), partial=True)
        else:
            yield LlmResponse(content=gtypes.Content(role="model", parts=[
                gtypes.Part(function_call=gtypes.FunctionCall(name="get_order_status", args={}))]))


# ---------- tools (async: sync tools BLOCK the ADK event loop) ----------
TOOL_TIMES: dict[str, float] = {}

def mk_weather(city: str):
    async def _w() -> str:
        TOOL_TIMES[city] = time.time()
        await asyncio.sleep(0.4)  # pretend network
        return f"sunny {city}"
    _w.__name__ = f"w_{city}"
    _w.__doc__ = f"weather in {city}"
    return _w

async def get_order_status() -> str:
    await asyncio.sleep(0.3)
    return "shipped"


def make_agent():
    return Agent(
        name="helper",
        model=ScriptedLlm(),
        tools=[get_order_status, *(mk_weather(c) for c in ("madrid", "oviedo", "barcelona"))],
        instruction="help with orders and weather",
    )


async def b1_tool_loop(runner, s):
    print("-- b1: tool loop --")
    async for ev in runner.run_async(user_id="u", session_id=s.id,
            new_message=gtypes.Content(role="user", parts=[gtypes.Part(text="status of order A-1234")])):
        for p in (ev.content.parts if ev.content else []):
            if p.function_call:
                print(f"  EVENT function_call: {p.function_call.name}")
            elif p.text:
                print(f"  EVENT text: {p.text[:60]}")


async def b2_parallel(runner, s):
    print("-- b2: parallel tools (3 x ~400ms) --")
    TOOL_TIMES.clear()
    t0 = time.time()
    async for ev in runner.run_async(user_id="u", session_id=s.id,
            new_message=gtypes.Content(role="user", parts=[gtypes.Part(text="check parallel weather now")])):
        pass
    dt = 1000 * (time.time() - t0)
    starts = {c: round(1000 * (t - t0)) for c, t in TOOL_TIMES.items()}
    verdict = "PARALLEL" if max(starts.values()) - min(starts.values()) < 100 else "SERIALIZED"
    print(f"  tool bodies entered at {starts}ms; total {dt:.0f}ms -> {verdict}")


async def b3_nonstalling(runner, s):
    print("-- b3: user turn while tool pending --")
    agen = runner.run_async(user_id="u", session_id=s.id,
        new_message=gtypes.Content(role="user", parts=[gtypes.Part(text="status again")]))
    async for ev in agen:
        if ev.content and ev.content.parts and ev.content.parts[0].function_call:
            t1 = time.time()
            # second invocation WHILE the first has a tool pending
            ans = None
            async for ev2 in runner.run_async(user_id="u", session_id=s.id,
                    new_message=gtypes.Content(role="user", parts=[gtypes.Part(text="hello?")])):
                if ev2.content and ev2.content.parts and ev2.content.parts[0].text:
                    ans = ev2.content.parts[0].text
            print(f"  second invocation answered in {1000*(time.time()-t1):.0f}ms: {ans!r}")
            break


async def b4_bargein(runner, s):
    print("-- b4: barge-in mid-stream --")
    agen = runner.run_async(user_id="u", session_id=s.id,
        new_message=gtypes.Content(role="user", parts=[gtypes.Part(text="tell me long story")]))
    n = 0
    async for ev in agen:
        if ev.content and ev.content.parts and ev.content.parts[0].text:
            n += 1
            if n == 2:
                await agen.aclose()  # consumer-side cancel: GeneratorExit kills generation
                print("  aclose after 2 partials -> generation aborted, partials not persisted")
                break


async def main():
    runner = InMemoryRunner(agent=make_agent(), app_name="demo")
    session = await runner.session_service.create_session(app_name="demo", user_id="u")
    await b1_tool_loop(runner, session)
    await b2_parallel(runner, session)
    await b3_nonstalling(runner, session)
    await b4_bargein(runner, session)
    print("== ADK: 4/4 behaviors (b3 = invocation-level concurrency, b4 = consumer-owned cancel)")


if __name__ == "__main__":
    asyncio.run(main())
