#
# SPDX-License-Identifier: MIT
#

"""Speculative KV-cache prefill example — ElevenLabs STT/TTS + local LLM.

While you speak, your partial transcriptions are fed into the local model's
KV cache. When your turn ends, the generation phase starts from a warm cache
instead of a cold one. Watch stdout for a per-turn log line like:

    spec-prefill hit 83% (15/18 tokens) … moved 312ms off the critical path, TTFT 47ms

STT/TTS run in the cloud (ElevenLabs). The LLM runs locally (Qwen2.5-0.5B
by default — small enough to run on CPU, big enough to be useful).

Run:
    uv run bot.py --transport webrtc
    # open http://localhost:7860 in your browser

First run downloads the model (~1 GB for 0.5B, ~15 GB for 7B).
Change it via SPEC_MODEL env var.
"""

import os

from dotenv import load_dotenv
from loguru import logger
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import LLMRunFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.worker import PipelineParams, PipelineWorker, ProcessorUnusablePolicy
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.runner.types import RunnerArguments
from pipecat.runner.utils import create_transport
from pipecat.services.elevenlabs.stt import ElevenLabsRealtimeSTTService
from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
from pipecat.services.settings import LLMSettings
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.workers.runner import WorkerRunner

from pipecat_speculative_prefill import SpeculativeLLMService, TransformersPrefillBackend

load_dotenv()

# ---------------------------------------------------------------------------
# Model — loaded once at process start, shared across all sessions.
# Qwen2.5-0.5B is the smallest useful model (~1 GB). For a smarter bot at
# the cost of more RAM/VRAM, set SPEC_MODEL=Qwen/Qwen2.5-7B-Instruct.
# ---------------------------------------------------------------------------
MODEL = os.environ.get("SPEC_MODEL", "Qwen/Qwen2.5-0.5B-Instruct")

logger.info(f"Loading model {MODEL} …")
backend = TransformersPrefillBackend.from_pretrained(MODEL, dtype=None)
logger.info("Model ready.")


def make_tts() -> ElevenLabsTTSService:
    return ElevenLabsTTSService(
        api_key=os.getenv("ELEVENLABS_API_KEY"),
        settings=ElevenLabsTTSService.Settings(
            voice=os.getenv("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb"),
            model="eleven_flash_v2_5",
        ),
    )


async def run_bot(transport: BaseTransport, runner_args: RunnerArguments) -> None:
    logger.info("Starting bot session")

    stt = ElevenLabsRealtimeSTTService(api_key=os.getenv("ELEVENLABS_API_KEY"))
    tts = make_tts()

    context = LLMContext()
    llm = SpeculativeLLMService(
        backend=backend,
        context=context,
        settings=LLMSettings(
            model=MODEL,
            system_instruction=(
                "You are a helpful assistant in a voice conversation. "
                "Your responses will be spoken aloud, so keep them short and "
                "conversational; avoid emojis, bullet points, or markdown."
            ),
            temperature=0.7,
            max_tokens=256,
        ),
    )

    user_aggregator, assistant_aggregator = LLMContextAggregatorPair(
        context,
        user_params=LLMUserAggregatorParams(vad_analyzer=SileroVADAnalyzer()),
    )

    pipeline = Pipeline(
        [
            transport.input(),
            stt,
            llm.transcription_tap(),  # ← feeds STT partials into the KV cache while the user speaks
            user_aggregator,
            llm,
            tts,
            transport.output(),
            assistant_aggregator,
        ]
    )

    worker = PipelineWorker(
        pipeline,
        params=PipelineParams(enable_metrics=True),
        processor_unusable_policy=ProcessorUnusablePolicy.END,
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
                "content": "Greet the user briefly and ask how you can help.",
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

    main()
