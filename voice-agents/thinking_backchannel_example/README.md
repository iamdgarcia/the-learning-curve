# Thinking Backchannel Example

> A minimal [Pipecat](https://github.com/pipecat-ai/pipecat) bot that says **"hmm"**, **"one sec"**, and **"let me check"** while it works — powered by ElevenLabs STT/TTS and NovitaAI.

Built on top of [pipecat-thinking-backchannel](https://github.com/iamdgarcia/pipecat-thinking-backchannel): a community integration that fills the silence an agentic pipeline leaves while waiting for the LLM's first token or for a tool call to finish.

---

## Why this matters

A multi-tool voice agent goes silent for 2–5 seconds every time it thinks or calls an API. That silence sounds like a hang. `ThinkingBackchannel` fixes it by playing short audio clips — recorded in the bot's own voice — into those gaps. No VAD, no turn model, no extra latency: just a frame state machine that watches LLM and tool events.

```
user speaks → STT → LLM (silent gap → "hmm") → tool (silent gap → "one sec") → TTS → user hears answer
```

---

## Stack

| Layer | Provider |
|---|---|
| STT | ElevenLabs Realtime (WebSocket, ultra-low latency) |
| LLM | NovitaAI — `deepseek/deepseek-v3-0324` (OpenAI-compatible) |
| TTS | ElevenLabs `eleven_flash_v2_5` (lowest latency model) |
| Backchannel | [`pipecat-thinking-backchannel`](https://github.com/iamdgarcia/pipecat-thinking-backchannel) |
| Transport | SmallWebRTC (browser tab, no account needed) |

---

## Quickstart

**1. Clone and enter the folder**

```bash
git clone https://github.com/iamdgarcia/the-learning-curve.git
cd the-learning-curve/voice-agents/thinking_backchannel_example
```

**2. Set your API keys**

```bash
cp .env.example .env
# edit .env and fill in ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, NOVITA_API_KEY
```

Get your keys:
- **ElevenLabs** → [elevenlabs.io](https://elevenlabs.io) (free tier works; voice ID from [your voices page](https://elevenlabs.io/app/voice-lab))
- **NovitaAI** → [novita.ai](https://novita.ai/?ref=mzblm2z&utm_source=affiliate) (pay-per-token, no subscription)

**3. Run**

```bash
uv run bot.py --transport webrtc
```

Open **http://localhost:7860** in your browser and start talking. Ask something that needs both tools, e.g.:

> *"What's the weather in Madrid? And find me a ramen place there."*

You'll hear a filler clip fire while the LLM decides, and another while each tool runs.

> **First run:** `prewarm()` records the filler clips through your ElevenLabs voice before accepting any connection. This takes ~10 seconds and is cached in `.clip_cache/`. Subsequent runs skip it.

---

## How it works

### 1. The gate watches LLM and tool frames

`ThinkingBackchannel` wraps your processor list and inserts three processors after the TTS service: a `ClipRecorder` (records clips on first run), a `ThinkingBackchannelProcessor` (the frame state machine / gate), and a `ClipPlayer` (plays cached audio).

The gate has two timers:
- **`llm_delay_s`** — fires a `thinking` clip if the LLM hasn't produced its first token within this window
- **`tool_delay_s`** — fires a `working` clip if a tool hasn't returned within this window
- **`cooldown_s`** — minimum gap between clips so they don't pile up on chained tool calls

### 2. Clip groups

Two groups, each with its own phrase pool. The gate picks randomly within a group (never the same clip twice in a row):

```python
THINKING_CLIPS = {
    # Fires while waiting for the LLM's first token
    "thinking": ["Hmm.", "Let me think.", "Good question.", "Right, so...", "Okay...", "Interesting."],
    # Fires while a tool call is running
    "working":  ["One sec.", "Let me check that for you.", "Just a moment.",
                 "I'll look that up.", "Give me a second.", "Let me find that."],
}
```

Clips are recorded **once** in the bot's own TTS voice and cached in `.clip_cache/`. Change the voice or the phrases → delete the cache.

### 3. Pipeline wiring

The only change to a standard Pipecat pipeline is wrapping the processor list with `thinking(...)`:

```python
thinking = ThinkingBackchannel(
    params=ThinkingParams(llm_delay_s=1.2, tool_delay_s=1.0, cooldown_s=5.0),
    clip_groups=THINKING_CLIPS,
)

pipeline = Pipeline(
    thinking([          # ← wrap, don't rebuild
        transport.input(),
        stt,
        user_aggregator,
        llm,
        tts,
        transport.output(),
        assistant_aggregator,
    ])
)
```

That's it. The library figures out where to insert itself (after `tts`).

---

## Customisation

### Change the filler phrases

Edit `THINKING_CLIPS` in `bot.py`, then delete `.clip_cache/` so the new clips are recorded:

```bash
rm -rf .clip_cache/
uv run bot.py --transport webrtc
```

Give each group **at least 2 clips** or it will repeat itself.

### Change the voice

Set `ELEVENLABS_VOICE_ID` in `.env` to any voice ID from your ElevenLabs account, then delete the cache:

```bash
rm -rf .clip_cache/
```

### Tune the timing

```python
ThinkingParams(
    llm_delay_s=1.2,   # wait this long before firing a "thinking" clip
    tool_delay_s=1.0,  # wait this long before firing a "working" clip
    cooldown_s=5.0,    # minimum gap between any two clips
)
```

Lower `llm_delay_s` / `tool_delay_s` → clips fire sooner (more active-sounding).  
Raise `cooldown_s` → fewer clips on long multi-tool chains.

### Swap the LLM

`NovitaLLMService` is OpenAI-compatible. Set `NOVITA_MODEL` in `.env`:

```
NOVITA_MODEL=meta-llama/llama-3.3-70b-instruct
NOVITA_MODEL=qwen/qwen2.5-72b-instruct
```

---

## Project structure

```
thinking_backchannel_example/
├── bot.py           # the full bot (~130 lines)
├── pyproject.toml   # dependencies
├── .env.example     # keys template
└── README.md
```

---

## Related

- [`pipecat-thinking-backchannel`](https://github.com/iamdgarcia/pipecat-thinking-backchannel) — the library this example uses
- [`pipecat-backchannel`](https://github.com/maisterr/pipecat-backchannel) — the companion (backchannels while the *user* speaks: "uh-huh", "sure")
- [The Learning Curve](https://iamdgarcia.substack.com) — more voice-agent examples and guides
