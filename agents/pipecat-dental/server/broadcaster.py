"""broadcaster.py — WebSocket event hub for the live demo.

bot.py calls broadcast(event_dict) from tool handlers and frame processors.
demo.html connects to ws://<host>:7860/events and receives JSON events.

Events emitted:
  {"type": "call_start"}
  {"type": "call_end"}
  {"type": "transcript",   "speaker": "user"|"bot", "text": "..."}
  {"type": "tool_call",    "tool": "buscar_paciente"|..., "args": {...}}
  {"type": "tool_result",  "tool": "buscar_paciente"|..., "result": {...}}
"""

import asyncio
import json
from typing import Any

from fastapi import WebSocket
from loguru import logger

_clients: set[WebSocket] = set()


def register_route(app):
    """Call once at import time to mount /events on the Pipecat FastAPI app."""

    @app.websocket("/events")
    async def events_ws(ws: WebSocket):
        await ws.accept()
        _clients.add(ws)
        logger.info(f"Demo client connected ({len(_clients)} total)")
        try:
            while True:
                # keep connection alive; demo only reads, never sends
                await ws.receive_text()
        except Exception:
            pass
        finally:
            _clients.discard(ws)
            logger.info(f"Demo client disconnected ({len(_clients)} total)")


async def broadcast(event: dict[str, Any]) -> None:
    """Fire-and-forget broadcast to all connected demo clients."""
    if not _clients:
        return
    payload = json.dumps(event, ensure_ascii=False)
    dead: set[WebSocket] = set()
    for ws in list(_clients):
        try:
            await ws.send_text(payload)
        except Exception:
            dead.add(ws)
    _clients.difference_update(dead)
