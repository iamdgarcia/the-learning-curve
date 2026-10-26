# Pipecat Quickstart — Agente de voz conversacional

Un agente de voz construido con Pipecat usando un pipeline cascade (STT -> LLM -> TTS).

**[Post completo en The Learning Curve](https://iamdgarcia.substack.com)**

## Setup

### 1. Instalar dependencias

```bash
cd server
uv sync
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con tus API keys
```

### 3. Arrancar el bot

```bash
uv run bot.py
```

Abre `http://localhost:7860` en el navegador y habla con tu microfono.

## Arquitectura

```
Microfono -> FunASR (STT) -> OLLama (LLM) -> Kokoro (TTS) -> Altavoces
```

- **STT**: FunASR (local, CPU)
- **LLM**: OLLama (local)
- **TTS**: Kokoro (local, CPU)
- **Transport**: SmallWebRTC (navegador)

Todo corre localmente sin GPU ni API keys.

## Servicios para produccion

| Componente | Local (dev) | Produccion |
|-----------|-------------|------------|
| STT | FunASR (CPU) | Deepgram |
| LLM | OLLama | OpenAI / Novita AI |
| TTS | Kokoro (CPU) | Cartesia |
| Transport | SmallWebRTC | Daily.co / Twilio |

## Codigo de produccion

El codigo completo con herramientas (function calling), conversaciones estructuradas (Flows), deploy a produccion y evaluacion esta disponible para suscriptores de [The Learning Curve](https://iamdgarcia.substack.com/subscribe).

## Learn More

- [Pipecat Documentation](https://docs.pipecat.ai/)
- [Pipecat GitHub](https://github.com/pipecat-ai/pipecat)
- [Pipecat Examples](https://github.com/pipecat-ai/pipecat-examples)
