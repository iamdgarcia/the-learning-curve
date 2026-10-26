"""pipecat-quickstart - Pipecat Voice Agent

This bot uses a cascade pipeline: Speech-to-Text -> LLM -> Text-to-Speech

Required AI services:
- FunASR (Speech-to-Text)
- OLLama (LLM)
- Kokoro (Text-to-Speech)

Run the bot using::

    uv run bot.py
"""

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
from pipecat.services.kokoro.tts import KokoroTTSService
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.daily.transport import DailyParams
from pipecat.workers.runner import WorkerRunner
from pipecat.services.funasr.stt import FunASRSTTService
from pipecat.services.ollama.llm import OLLamaLLMService

load_dotenv(override=True)


async def run_bot(transport: BaseTransport, runner_args: RunnerArguments) -> None:
    """Run the voice bot for this session."""
    logger.info("Starting bot")

    stt = FunASRSTTService(device="cpu")

    tts = KokoroTTSService(
        settings=KokoroTTSService.Settings(voice="af_heart"),
    )
    llm = OLLamaLLMService(
        settings=OLLamaLLMService.Settings(
            model="llama3.1",
            system_instruction=(
                "You are a helpful assistant in a voice conversation. "
                "Your responses will be spoken aloud, so avoid emojis, "
                "bullet points, or other formatting that can't be spoken. "
                "Respond to what the user said in a creative, helpful, and brief way."
            ),
        ),
    )

    context = LLMContext()
    user_aggregator, assistant_aggregator = LLMContextAggregatorPair(
        context,
        user_params=LLMUserAggregatorParams(vad_analyzer=SileroVADAnalyzer()),
    )

    pipeline = Pipeline(
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

    worker = PipelineWorker(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
        observers=[],
    )

    runner = WorkerRunner(handle_sigint=runner_args.handle_sigint)
    await runner.add_workers(worker)

    @worker.rtvi.event_handler("on_client_ready")
    async def on_client_ready(rtvi):
        context.add_message(
            {"role": "developer", "content": "Start by concisely introducing yourself."}
        )
        await worker.queue_frames([LLMRunFrame()])

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("Client connected")

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Client disconnected")
        await runner.cancel()

    await runner.run()


async def bot(runner_args: RunnerArguments):
    """Main bot entry point."""
    transport_params = {
        "daily": lambda: DailyParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
        ),
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
