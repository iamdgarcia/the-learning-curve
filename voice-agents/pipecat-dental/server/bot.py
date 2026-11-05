"""pipecat-dental - Dental Clinic Voice Assistant (PoC)

Pipeline: ElevenLabs STT → NovitaAI LLM → ElevenLabs TTS

Demo flows:
  1. New appointment: caller gives DNI → patient profile + pending check-up
                      → calendar search → propose slot → patient asks for another
                      → confirm alternative slot
  2. Appointment inquiry: caller gives DNI → upcoming appointments listed

Required env vars:
  ELEVENLABS_API_KEY
  ELEVENLABS_VOICE_ID  (default: Aria multilingual)
  NOVITA_API_KEY
  NOVITA_MODEL         (default: deepseek/deepseek-v4.1-flash-1017)
"""

import asyncio
import json
import os
import random
from datetime import datetime, timedelta

import aiohttp
from dotenv import load_dotenv
from loguru import logger
from pipecat.adapters.llm.schemas.function_schema import FunctionSchema
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import (
    BotBackchannelFrame,
    BotStartedSpeakingFrame,
    BotStoppedSpeakingFrame,
    EndFrame,
    LLMFullResponseEndFrame,
    LLMFullResponseStartFrame,
    LLMRunFrame,
    TextFrame,
    TranscriptionFrame,
    UserStartedSpeakingFrame,
    UserStoppedSpeakingFrame,
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.worker import PipelineParams, PipelineWorker
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.runner.types import RunnerArguments
from pipecat.runner.utils import create_transport
from pipecat.services.elevenlabs.stt import ElevenLabsSTTService
from pipecat.services.elevenlabs.dialogue.tts import ElevenLabsDialogueTTSService
from pipecat.services.elevenlabs.tts import TextAggregationMode
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.transcriptions.language import Language
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.daily.transport import DailyParams
from pipecat.transports.websocket.fastapi import FastAPIWebsocketParams
from pipecat.workers.runner import WorkerRunner
from pipecat_backchannel import Backchannel, BackchannelParams
from pipecat_backchannel.processor import BackchannelProcessor
from pipecat_backchannel.player import ClipPlayer
from pipecat_backchannel.frames import PlayCachedClipFrame

# Live demo broadcaster — registers /events WebSocket on the Pipecat FastAPI app
from pipecat.runner.run import app as _pipecat_app
import broadcaster
broadcaster.register_route(_pipecat_app)

load_dotenv(override=True)

SYSTEM_PROMPT = """Eres Sofía, la asistente de la Clínica Dental Sonrisa. Hablas por teléfono: respuestas cortas, directas y naturales. Sin listas, sin emojis, sin formatos visuales.

Al inicio de cada llamada saluda exactamente así: "Buenos días, le atiende Sofía de la Clínica Dental Sonrisa, ¿en qué le puedo ayudar?"

Flujo:
1. Escucha lo que necesita el paciente.
2. Pide el DNI solo cuando el paciente haya dicho qué quiere. El DNI tiene 8 dígitos y una letra (ej. 12345678A). El paciente puede darlo en partes o usando el alfabeto fonético ("D de Dinamarca" = D, "A de Asturias" = A). Ensambla los fragmentos hasta tener el DNI completo. Antes de llamar a buscar_paciente, repítelo siempre para confirmación: "¿Su DNI es 12345678A, correcto?" Si el paciente corrige algo, actualiza y confirma de nuevo.
3. Solo cuando el paciente confirme el DNI, llama a buscar_paciente. Si hay revisión pendiente, coméntalo en una frase.
4. Para nueva cita: pregunta preferencia de horario, llama a buscar_huecos y propón una opción concreta. Si el paciente pide otra hora, propón la siguiente disponible.
5. Al confirmar, llama a confirmar_cita.
6. Para consultar citas: llama a buscar_paciente y lee las citas futuras.
7. Cuando la llamada haya terminado, despídete en una frase y acto seguido llama a colgar_llamada. No digas nada más después de llamarla.

Normas: español peninsular. Respuestas de máximo 2 frases. No inventes datos. Cuando menciones una hora, usa siempre el campo hora_natural (p.ej. "las 4 de la tarde"), nunca el formato HH:MM. Si el historial ya contiene una frase tuya justo antes de tu respuesta, no la repitas ni la parafrasees; continúa desde donde quedaste."""

# In-memory store for confirmed appointments (persists within a single run)
_CITAS_CONFIRMADAS: dict[str, list[dict]] = {}

_PACIENTES: dict[str, dict] = {
    "12345678A": {
        "nombre": "Daniel García Peña",
        "dni": "12345678A",
        "telefono": "+34 600 123 456",
        "ultima_visita": "2025-11-20",
        "tipo_ultima_visita": "Revisión anual y limpieza",
        "revision_pendiente": True,
        "historial": [
            "2025-11-20 — Revisión anual y limpieza",
            "2024-11-18 — Revisión anual y limpieza",
            "2024-03-05 — Empaste molar 36",
        ],
    }
}


def _generar_huecos() -> list[dict]:
    hoy = datetime.now()
    huecos = []
    horarios = ["09:00", "09:30", "10:00", "10:30", "11:00", "12:00", "16:00", "16:30", "17:00", "17:30"]
    ocupados = {
        (1, "09:00"), (1, "10:00"), (1, "17:00"),
        (2, "09:30"), (2, "11:00"),
        (3, "10:00"), (3, "16:30"),
        (4, "09:00"), (4, "12:00"),
        (5, "11:00"), (5, "17:30"),
    }
    for dia_offset in range(1, 14):
        fecha = hoy + timedelta(days=dia_offset)
        if fecha.weekday() >= 5:
            continue
        nombre_dia = ["lunes", "martes", "miércoles", "jueves", "viernes"][fecha.weekday()]
        for hora in horarios:
            disponible = (dia_offset, hora) not in ocupados
            huecos.append({
                "fecha": fecha.strftime("%d/%m/%Y"),
                "dia_semana": nombre_dia,
                "hora": hora,
                "disponible": disponible,
            })
    return huecos


_HUECOS = _generar_huecos()


def _buscar_paciente(dni: str) -> dict:
    dni_norm = dni.upper().strip()
    paciente = _PACIENTES.get(dni_norm)
    if not paciente:
        return {
            "encontrado": False,
            "mensaje": f"No se encontró ningún paciente con DNI {dni}.",
        }
    citas_futuras = _CITAS_CONFIRMADAS.get(dni_norm, [])
    aviso_revision = (
        f"Tiene una revisión pendiente (última visita: {paciente['ultima_visita']}). "
        if paciente.get("revision_pendiente")
        else ""
    )
    return {
        "encontrado": True,
        "nombre": paciente["nombre"],
        "dni": paciente["dni"],
        "ultima_visita": paciente["ultima_visita"],
        "tipo_ultima_visita": paciente["tipo_ultima_visita"],
        "revision_pendiente": paciente["revision_pendiente"],
        "historial": paciente["historial"],
        "citas_futuras": citas_futuras,
        "mensaje": (
            f"Paciente encontrado: {paciente['nombre']}. "
            + aviso_revision
            + (
                f"Tiene {len(citas_futuras)} cita(s) próxima(s): "
                + ", ".join(f"{c['fecha']} a las {c['hora']} ({c['tipo']})" for c in citas_futuras)
                + "."
                if citas_futuras
                else "No tiene citas futuras registradas."
            )
        ),
    }


def _hora_natural(hora: str) -> str:
    h, m = map(int, hora.split(":"))
    h12 = h if h <= 12 else h - 12
    minutos = " y media" if m == 30 else ""
    if h < 12:
        periodo = "de la mañana"
    elif h == 12:
        return f"las 12{minutos} del mediodía"
    elif h < 21:
        periodo = "de la tarde"
    else:
        periodo = "de la noche"
    return f"las {h12}{minutos} {periodo}"


def _buscar_huecos(hora_preferida: str = "", tarde: bool = False) -> dict:
    disponibles = [h for h in _HUECOS if h["disponible"]]
    if tarde:
        disponibles = [h for h in disponibles if h["hora"] >= "14:00"]
    elif hora_preferida:
        disponibles = [h for h in disponibles if h["hora"] >= hora_preferida]
    primeros = disponibles[:6]
    if not primeros:
        return {"huecos": [], "mensaje": "No hay huecos disponibles con esos criterios. Prueba con otros horarios."}
    for h in primeros:
        h["hora_natural"] = _hora_natural(h["hora"])
    return {
        "huecos": primeros,
        "mensaje": "Huecos disponibles: "
        + ", ".join(f"{h['dia_semana']} {h['fecha']} a {h['hora_natural']}" for h in primeros)
        + ".",
    }


def _confirmar_cita(dni: str, fecha: str, hora: str, tipo: str = "Revisión anual") -> dict:
    dni_norm = dni.upper().strip()
    paciente = _PACIENTES.get(dni_norm)
    if not paciente:
        return {"confirmado": False, "mensaje": f"No se encontró el paciente con DNI {dni}."}
    cita = {"fecha": fecha, "hora": hora, "tipo": tipo, "paciente": paciente["nombre"]}
    _CITAS_CONFIRMADAS.setdefault(dni_norm, []).append(cita)
    _PACIENTES[dni_norm]["revision_pendiente"] = False
    return {
        "confirmado": True,
        "cita": cita,
        "mensaje": f"Cita confirmada para {paciente['nombre']} el {fecha} a {_hora_natural(hora)}.",
    }


# Backchannel: pre-renders Spanish clips from TTS, plays from memory while user speaks
_ES_CLIPS = {
    "continue": ["Sí.", "Sí,", "Ajá.", "Ajá,", "Mmm.", "Mmm,", "Entiendo."],
    "affirm":   ["Claro.", "Claro,", "Sí, entiendo.", "De acuerdo.", "Correcto."],
    "empathy":  ["Entiendo...", "Sí...", "Ya veo.", "Ya veo,"],
    # Tool thinking phrases — triggered directly from handlers, bypass speculation gate
    "tool":     ["Déjeme buscar su ficha...", "Déjeme consultar la agenda...", "Perfecto, un momento..."],
}

backchannel = Backchannel(
    volume=0.7,
    clip_groups=_ES_CLIPS,
    params=BackchannelParams(
        min_speech_before_eligible_s=0.7,
        fire_probability=0.7,
        cooldown_s=5,
    ),
)

class DemoEventProcessor(FrameProcessor):
    """Intercepts TranscriptionFrame (user) and bot text chunks → broadcasts to demo UI."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._bot_text: list[str] = []

    async def process_frame(self, frame, direction: FrameDirection):
        await self.push_frame(frame, direction)

        # User speech — final transcription only
        if isinstance(frame, TranscriptionFrame) and frame.finalized and frame.text.strip():
            await broadcaster.broadcast({"type": "transcript", "speaker": "user", "text": frame.text.strip()})

        # Bot text — accumulate chunks, emit on response end
        elif isinstance(frame, TextFrame) and direction == FrameDirection.DOWNSTREAM and frame.text:
            self._bot_text.append(frame.text)

        elif isinstance(frame, LLMFullResponseEndFrame):
            text = "".join(self._bot_text).strip()
            self._bot_text.clear()
            if text:
                await broadcaster.broadcast({"type": "transcript", "speaker": "bot", "text": text})




async def run_bot(transport: BaseTransport, runner_args: RunnerArguments) -> None:
    logger.info("Starting dental bot")

    elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY") or ""

    async with aiohttp.ClientSession() as aiohttp_session:
        stt = ElevenLabsSTTService(
            api_key=elevenlabs_api_key,
            aiohttp_session=aiohttp_session,
            settings=ElevenLabsSTTService.Settings(language=Language.ES),
        )

        tts = ElevenLabsDialogueTTSService(
            api_key=elevenlabs_api_key,
            settings=ElevenLabsDialogueTTSService.Settings(
                model="eleven_v4_turbo",
                voice=os.getenv("ELEVENLABS_VOICE_ID", "1eHrpOW5l98cxiSRjbzJ"),
                language=Language.ES,
                stability=0.4,
            ),
            text_aggregation_mode=TextAggregationMode.SENTENCE,
        )

        llm = OpenAILLMService(
            api_key=os.getenv("NOVITA_API_KEY") or "",
            base_url="https://api.novita.ai/openai",
            settings=OpenAILLMService.Settings(
                model=os.getenv("NOVITA_MODEL", "deepseek/deepseek-v4.1-flash-1017"),
                system_instruction=SYSTEM_PROMPT,
            ),
        )

        async def handle_buscar_paciente(params):
            logger.info(f"Tool: {params.function_name} args={params.arguments}")
            await broadcaster.broadcast({"type": "tool_call", "tool": "buscar_paciente", "args": params.arguments})
            await clip_player.push_frame(PlayCachedClipFrame(text="Déjeme buscar su ficha..."))
            result = _buscar_paciente(**params.arguments)
            await broadcaster.broadcast({"type": "tool_result", "tool": "buscar_paciente", "result": result})
            await params.result_callback(json.dumps(result, ensure_ascii=False))

        async def handle_buscar_huecos(params):
            logger.info(f"Tool: {params.function_name} args={params.arguments}")
            await broadcaster.broadcast({"type": "tool_call", "tool": "buscar_huecos", "args": params.arguments})
            await clip_player.push_frame(PlayCachedClipFrame(text="Déjeme consultar la agenda..."))
            result = _buscar_huecos(**params.arguments)
            await broadcaster.broadcast({"type": "tool_result", "tool": "buscar_huecos", "result": result})
            await params.result_callback(json.dumps(result, ensure_ascii=False))

        async def handle_confirmar_cita(params):
            logger.info(f"Tool: {params.function_name} args={params.arguments}")
            await broadcaster.broadcast({"type": "tool_call", "tool": "confirmar_cita", "args": params.arguments})
            await clip_player.push_frame(PlayCachedClipFrame(text="Perfecto, un momento..."))
            result = _confirmar_cita(**params.arguments)
            await broadcaster.broadcast({"type": "tool_result", "tool": "confirmar_cita", "result": result})
            await params.result_callback(json.dumps(result, ensure_ascii=False))

        async def handle_colgar(params):
            logger.info("Tool: colgar_llamada — scheduling shutdown")
            await broadcaster.broadcast({"type": "call_end"})
            await params.result_callback("")

            async def _shutdown():
                await asyncio.sleep(6)
                await worker.queue_frames([EndFrame()])

            asyncio.create_task(_shutdown())

        tools = [
            FunctionSchema(
                name="buscar_paciente",
                description="Carga la ficha del paciente por DNI. Devuelve nombre, historial dental, si tiene revisión pendiente y citas futuras.",
                properties={
                    "dni": {"type": "string", "description": "DNI del paciente (p.ej. '12345678A')"},
                },
                required=["dni"],
                handler=handle_buscar_paciente,
            ),
            FunctionSchema(
                name="buscar_huecos",
                description="Busca huecos disponibles en el calendario de la clínica.",
                properties={
                    "hora_preferida": {
                        "type": "string",
                        "description": "Hora mínima en formato HH:MM si el paciente prefiere a partir de cierta hora.",
                    },
                    "tarde": {
                        "type": "boolean",
                        "description": "True si el paciente prefiere horario de tarde (a partir de las 14:00).",
                    },
                },
                required=[],
                handler=handle_buscar_huecos,
            ),
            FunctionSchema(
                name="confirmar_cita",
                description="Confirma y registra una nueva cita para el paciente.",
                properties={
                    "dni": {"type": "string", "description": "DNI del paciente"},
                    "fecha": {"type": "string", "description": "Fecha en formato DD/MM/YYYY"},
                    "hora": {"type": "string", "description": "Hora en formato HH:MM"},
                    "tipo": {"type": "string", "description": "Tipo de visita, p.ej. 'Revisión anual' o 'Limpieza'."},
                },
                required=["dni", "fecha", "hora"],
                handler=handle_confirmar_cita,
            ),
            FunctionSchema(
                name="colgar_llamada",
                description="Finaliza la llamada. Llámala después de despedirte. No generes ningún texto adicional tras llamarla.",
                properties={},
                required=[],
                handler=handle_colgar,
            ),
        ]

        context = LLMContext(tools=tools)  # type: ignore[arg-type]
        user_aggregator, assistant_aggregator = LLMContextAggregatorPair(
            context,
            user_params=LLMUserAggregatorParams(vad_analyzer=SileroVADAnalyzer()),
        )

        # Manual placement: keep reference to clip_player so tool handlers
        # can push PlayCachedClipFrame directly, bypassing the LLM speculation gate
        bc_listener = BackchannelProcessor(
            params=backchannel._params,
            clips=backchannel._library,
            selector=backchannel._selector,
            turn_analyzer=backchannel._turn_factory(),
        )
        clip_player = ClipPlayer(clips=backchannel._library, volume=backchannel._volume)

        pipeline = Pipeline([
            transport.input(),
            stt,
            bc_listener,      # listener backchannel: after STT
            user_aggregator,
            llm,
            tts,
            clip_player,      # plays cached clips: after TTS, before output
            transport.output(),
            assistant_aggregator,
        ])

        worker = PipelineWorker(
            pipeline,
            params=PipelineParams(enable_metrics=True, enable_usage_metrics=True),
        )

        runner = WorkerRunner(handle_sigint=runner_args.handle_sigint)
        await runner.add_workers(worker)

        @user_aggregator.event_handler("on_user_backchannel")
        async def on_user_backchannel(_aggregator, message):
            logger.debug(f"User backchannel detected: '{message.content}' — no LLM turn triggered")

        @worker.rtvi.event_handler("on_client_ready")
        async def on_client_ready(_rtvi):
            context.add_message({"role": "user", "content": "Hola."})
            await worker.queue_frames([LLMRunFrame()])

        @transport.event_handler("on_client_connected")
        async def on_client_connected(_transport, _client):
            logger.info("Client connected")
            await broadcaster.broadcast({"type": "call_start"})

        @transport.event_handler("on_client_disconnected")
        async def on_client_disconnected(_transport, _client):
            logger.info("Client disconnected")
            await runner.cancel()

        await runner.run()


async def bot(runner_args: RunnerArguments):
    transport_params = {
        "daily": lambda: DailyParams(audio_in_enabled=True, audio_out_enabled=True),
        "webrtc": lambda: TransportParams(audio_in_enabled=True, audio_out_enabled=True),
        "twilio": lambda: FastAPIWebsocketParams(audio_in_enabled=True, audio_out_enabled=True),
        "telnyx": lambda: FastAPIWebsocketParams(audio_in_enabled=True, audio_out_enabled=True),
        "plivo": lambda: FastAPIWebsocketParams(audio_in_enabled=True, audio_out_enabled=True),
    }
    transport = await create_transport(runner_args, transport_params)
    await run_bot(transport, runner_args)


if __name__ == "__main__":
    from pipecat.runner.run import main

    # Pre-render backchannel clips before accepting connections
    async def _prewarm():
        prewarm_tts = ElevenLabsDialogueTTSService(
            api_key=os.getenv("ELEVENLABS_API_KEY", ""),
            settings=ElevenLabsDialogueTTSService.Settings(
                model="eleven_v4_turbo",
                voice=os.getenv("ELEVENLABS_VOICE_ID", "1eHrpOW5l98cxiSRjbzJ"),
                language=Language.ES,
            ),
        )
        await backchannel.prewarm(tts=prewarm_tts)

    import asyncio as _asyncio
    _asyncio.run(_prewarm())
    main()
