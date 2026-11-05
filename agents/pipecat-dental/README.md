# Agente de voz conversacional con Pipecat

Pipeline en tiempo real: **ElevenLabs STT → DeepSeek LLM → ElevenLabs TTS v4**  
Demo con React + WebRTC que visualiza transcripciones, tool calls y latencia por etapa.

**[Guía completa en The Learning Curve →](https://iamdgarcia.substack.com)**

---

## Qué hace

**Sofía**, la asistente de IA de la Clínica Dental Sonrisa, atiende llamadas desde el navegador:

| Flujo | Descripción |
|-------|-------------|
| 🦷 Pedir cita | Pide DNI → carga ficha → busca huecos → confirma cita |
| 📋 Consultar citas | Pide DNI → lista las citas futuras registradas |

Características del pipeline:
- **VAD + interrupciones** — el usuario puede cortar al agente en cualquier momento
- **Backchannels** — el agente emite "Sí...", "Entiendo..." mientras escucha
- **Function calling** — el LLM llama herramientas reales para gestionar la agenda

---

## Stack

| Capa | Servicio | Notas |
|------|----------|-------|
| STT | [ElevenLabs](https://try.elevenlabs.io/5rwirobe89kq) | Streaming WebSocket, baja latencia |
| LLM | [Novita AI](https://novita.ai) — DeepSeek v4.1 Flash | OpenAI-compatible, muy económico |
| TTS | [ElevenLabs Dialogue v4 Turbo](https://try.elevenlabs.io/5rwirobe89kq) | Expresividad natural, streaming por frases |
| Framework | [Pipecat](https://pipecat.ai) | Orquesta STT→LLM→TTS, VAD, backchannels |
| Transport | SmallWebRTC | Audio directo desde el navegador, sin instalación |
| Frontend | React + Vite + Tailwind | Visualizador de conversación y latencias |

---

## Setup

### Requisitos

- Python ≥ 3.11 con [`uv`](https://docs.astral.sh/uv/) (`pip install uv`)
- Node.js ≥ 18

### 1. Dependencias del servidor

```bash
cd server
uv sync
```

### 2. Variables de entorno

```bash
cp server/.env.example server/.env
```

Edita `server/.env`:

```env
ELEVENLABS_API_KEY=...     # https://try.elevenlabs.io/5rwirobe89kq
ELEVENLABS_VOICE_ID=...    # opcional, por defecto Aria multilingual
NOVITA_API_KEY=...         # https://novita.ai
NOVITA_MODEL=deepseek/deepseek-v4.1-flash-1017  # opcional
```

### 3. Dependencias del frontend

```bash
cd frontend
npm install
```

### 4. Arrancar

En dos terminales:

```bash
# Terminal 1 — bot
cd server && uv run bot.py

# Terminal 2 — UI
cd frontend && npm run dev
```

Abre [http://localhost:5173](http://localhost:5173), pulsa **Iniciar llamada** y habla.

> **Nota:** WebRTC requiere contexto seguro. Usa `localhost`, no la IP de red local.

---

## Arquitectura

```
Micrófono (WebRTC)
    │
    ▼
ElevenLabs STT ──► DeepSeek LLM ──► ElevenLabs TTS v4 ──► Altavoces
                        │
                 Function calling
        (buscar_paciente · buscar_huecos · confirmar_cita · colgar_llamada)
                        │
                   WebSocket /events
                        │
                        ▼
              React UI — timeline + tool calls + latency panel
```

### Herramientas del agente

| Tool | Qué hace |
|------|----------|
| `buscar_paciente(dni)` | Carga ficha: historial, revisiones pendientes, citas futuras |
| `buscar_huecos(hora_preferida?, tarde?)` | Huecos disponibles en el calendario |
| `confirmar_cita(dni, fecha, hora, tipo?)` | Registra la cita |
| `colgar_llamada()` | Finaliza la llamada |

---

## Demo UI

La interfaz React conecta por WebSocket a `/events` y muestra en tiempo real:

- **DuplexTimeline** — ondas de audio del agente y el usuario, con marcadores de turno, interrupciones y backchannels
- **Latency panel** — desglose STT / LLM / TTS por turno
- **Agenda** — panel derecho con tool calls y resultados

---

## Flujo de la demo

1. **Primera llamada**: di `12345678A` cuando Sofía pida el DNI, pide una revisión → ella busca huecos y confirma.
2. **Segunda llamada**: llama de nuevo con el mismo DNI → Sofía lista la cita recién creada.

---

## Estructura del proyecto

```
pipecat-quickstart/
├── server/
│   ├── bot.py            ← pipeline principal (STT + LLM + TTS + tools + backchannels)
│   ├── broadcaster.py    ← WebSocket hub para la demo UI
│   ├── pyproject.toml    ← dependencias Python (uv)
│   └── .env.example      ← plantilla de variables de entorno
└── frontend/
    ├── src/
    │   ├── App.jsx                         ← layout principal
    │   ├── components/
    │   │   ├── AgendaPanel.jsx             ← panel de tool calls
    │   │   └── pipecat/
    │   │       ├── duplex-timeline.jsx     ← visualizador de conversación
    │   │       ├── latency-panel.jsx       ← desglose de latencias
    │   │       └── ...
    │   └── ...
    └── package.json
```

---

## Recursos

- [Pipecat Documentation](https://docs.pipecat.ai/)
- [ElevenLabs STT](https://elevenlabs.io/speech-to-text)
- [Novita AI](https://novita.ai) — modelos LLM OpenAI-compatible
- [The Learning Curve](https://iamdgarcia.substack.com) — newsletter de IA aplicada en español
