#
# SPDX-License-Identifier: MIT
#

"""Minimal ThinkingBackchannel example — ElevenLabs STT/TTS + NovitaAI LLM.

The bot says "hmm", "one sec", or "let me check" in the user's own language
while it waits for the LLM's first token or for a tool call to finish.

Run:
    uv run bot.py --transport webrtc
    # then open http://localhost:7860 in your browser
"""

import asyncio
import os

from dotenv import load_dotenv
from loguru import logger
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import LLMRunFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.worker import PipelineParams, PipelineWorker
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.runner.types import RunnerArguments
from pipecat.runner.utils import create_transport
from pipecat.services.elevenlabs.stt import ElevenLabsRealtimeSTTService
from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
from pipecat.services.llm_service import FunctionCallParams
from pipecat.services.novita.llm import NovitaLLMService
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.workers.runner import WorkerRunner

from pipecat_thinking_backchannel import ThinkingBackchannel, ThinkingParams

load_dotenv()


# ---------------------------------------------------------------------------
# Demo tools — sleep long enough that the backchannel has room to fire.
# ---------------------------------------------------------------------------

async def get_weather(params: FunctionCallParams, location: str):
    """Get the current weather for a city.

    Args:
        location: The city, e.g. "San Francisco".
    """
    await asyncio.sleep(4)
    await params.result_callback({"conditions": "sunny", "temperature": "22°C"})


async def find_restaurant(params: FunctionCallParams, location: str, food: str):
    """Find a restaurant serving a kind of food in a city.

    Args:
        location: The city, e.g. "Madrid".
        food: The kind of food, e.g. "ramen".
    """
    await asyncio.sleep(3)
    await params.result_callback({"name": "Ramen House", "rating": 4.6})


# ---------------------------------------------------------------------------
# One ThinkingBackchannel per process — prewarmed before the first session.
# ---------------------------------------------------------------------------

# "thinking" fires while waiting for the LLM's first token — composing-a-thought sounds.
# "working" fires while a tool is running — doing-something-brb sounds.
# ElevenLabs records these in the bot's own voice; delete .clip_cache/ to re-record.
THINKING_CLIPS = {
    "thinking": [
        "Hmm.",
        "Let me think.",
        "Good question.",
        "Right, so...",
        "Okay...",
        "Interesting.",
    ],
    "working": [
        "One sec.",
        "Let me check that for you.",
        "Just a moment.",
        "I'll look that up.",
        "Give me a second.",
        "Let me find that.",
    ],
}

thinking = ThinkingBackchannel(
    params=ThinkingParams(llm_delay_s=0.8, tool_delay_s=0.8, cooldown_s=1.0),
    clip_groups=THINKING_CLIPS,
)


def make_tts() -> ElevenLabsTTSService:
    return ElevenLabsTTSService(
        api_key=os.getenv("ELEVENLABS_API_KEY"),
        settings=ElevenLabsTTSService.Settings(
            voice=os.getenv("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb"),
            model="eleven_flash_v2_5",  # lowest latency model
        ),
    )


async def run_bot(transport: BaseTransport, runner_args: RunnerArguments) -> None:
    logger.info("Starting bot session")

    stt = ElevenLabsRealtimeSTTService(api_key=os.getenv("ELEVENLABS_API_KEY"))
    tts = make_tts()

    llm = NovitaLLMService(
        api_key=os.getenv("NOVITA_API_KEY"),
        settings=NovitaLLMService.Settings(
            model=os.getenv("NOVITA_MODEL", "deepseek/deepseek-v3-0324"),
            system_instruction=(
                "You are a helpful assistant in a voice conversation. "
                "You have tools for weather and restaurants — use them whenever they "
                "would help, and chain them when a request needs both. "
                "Your responses will be spoken aloud, so keep them short and "
                "conversational; avoid emojis, bullet points, or markdown."
            ),
        ),
    )

    context = LLMContext(tools=[get_weather, find_restaurant])
    user_aggregator, assistant_aggregator = LLMContextAggregatorPair(
        context,
        user_params=LLMUserAggregatorParams(vad_analyzer=SileroVADAnalyzer()),
    )

    pipeline = Pipeline(
        thinking(
            [
                transport.input(),
                stt,
                user_aggregator,
                llm,
                tts,
                transport.output(),
                assistant_aggregator,
            ]
        )
    )

    worker = PipelineWorker(
        pipeline,
        params=PipelineParams(enable_metrics=True, enable_usage_metrics=True),
        idle_timeout_secs=runner_args.pipeline_idle_timeout_secs,
    )

    runner = WorkerRunner(handle_sigint=runner_args.handle_sigint)
    await runner.add_workers(worker)

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("Client connected")
        context.add_message(
            {
                "role": "developer",
                "content": (
                    "Introduce yourself briefly, then ask where the user lives "
                    "so you can look up weather or restaurants for them."
                ),
            }
        )
        await worker.queue_frames([LLMRunFrame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Client disconnected")
        await worker.cancel()

    await runner.run()


async def bot(runner_args: RunnerArguments):
    transport_params = {
        "webrtc": lambda: TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
        ),
    }
    transport = await create_transport(runner_args, transport_params)
    await run_bot(transport, runner_args)


if __name__ == "__main__":
    from pipecat.runner.run import main

    # Prewarm: record the filler clips in the bot's own voice before the first
    # caller connects, so no one ever waits for them.
    asyncio.run(thinking.prewarm(tts=make_tts()))

    main()
