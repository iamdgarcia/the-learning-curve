# Speculative Prefill Example

> A minimal [Pipecat](https://github.com/pipecat-ai/pipecat) bot that **pre-warms the LLM's KV cache while you're still talking** — powered by ElevenLabs STT/TTS and a local model.

Built on top of [pipecat-speculative-prefill](https://github.com/iamdgarcia/pipecat-speculative-prefill): a technique that feeds your partial transcriptions into the model's KV cache as you speak, so when your turn ends the generation phase starts from a warm cache instead of a cold one.

---

## Why this matters

In a voice agent pipeline the LLM can't start until:

1. You finish speaking (VAD detects end of turn)
2. The STT produces the final transcript
3. The LLM prefills the prompt into its KV cache
4. **Then** generation begins

Steps 1–3 are dead time. Speculative prefill attacks step 3: it runs the prefill **during steps 1–2**, overlapping it with the time you'd wait anyway. On a CPU with Qwen2.5-0.5B, that typically moves **200–400 ms off the critical path**:

```
Without: [speaking] → [STT] → [prefill 350ms] → [generate] → [TTS] → voice
With:    [speaking + prefill in parallel] → [STT] →  [generate] → [TTS] → voice
                                                          ↑ cache already warm
```

Each turn logs exactly what it bought:
```
spec-prefill hit 83% (15/18 tokens) … moved 312ms off the critical path, TTFT 47ms
```

---

## Stack

| Layer | Provider |
|---|---|
| STT | ElevenLabs Realtime (WebSocket, ultra-low latency) |
| LLM | Local model via HuggingFace Transformers (`Qwen2.5-0.5B` default) |
| TTS | ElevenLabs `eleven_flash_v2_5` |
| Transport | SmallWebRTC (browser tab, no account needed) |

> **Why local LLM?** Speculative prefill requires direct access to the model's KV cache. That's only possible when the model runs in-process. Cloud LLM APIs (OpenAI, NovitaAI, etc.) don't expose their cache — use the [thinking-backchannel example](../thinking_backchannel_example/) for those.

---

## Quickstart

**1. Clone and enter the folder**

```bash
git clone https://github.com/iamdgarcia/the-learning-curve.git
cd the-learning-curve/voice-agents/speculative_prefill_example
```

**2. Set your API keys**

```bash
cp .env.example .env
# edit .env and fill in ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID
```

Get your keys:
- **ElevenLabs** → [elevenlabs.io](https://elevenlabs.io) (free tier works; voice ID from [your voices page](https://elevenlabs.io/app/voice-lab))

**3. Run**

```bash
uv run bot.py --transport webrtc
```

Open **http://localhost:7860** and start talking. Watch stdout for the per-turn prefill stats.

> **First run** downloads the model weights from HuggingFace (~1 GB for 0.5B). Subsequent runs load from cache instantly.

---

## How it works

### 1. The transcription tap

`llm.transcription_tap()` returns a lightweight frame processor you place **between the STT and the user context aggregator**:

```python
pipeline = Pipeline([
    transport.input(),
    stt,
    llm.transcription_tap(),   # ← the only new processor
    user_aggregator,
    llm,
    tts,
    transport.output(),
    assistant_aggregator,
])
```

Every interim transcription (`InterimTranscriptionFrame`) that arrives while you're still speaking is silently forwarded to the backend, which tokenizes the partial prompt and syncs the KV cache to it. By the time the final transcript arrives, most of the prefill is already done.

### 2. The backend

`TransformersPrefillBackend` owns the model weights and the KV cache. It runs the heavy tokenization and forward pass in a worker thread so it never blocks the async pipeline. The service serializes cache writes and reads with a lock so sync (prefill) and decode (generation) never race.

```python
backend = TransformersPrefillBackend.from_pretrained(
    "Qwen/Qwen2.5-0.5B-Instruct", dtype=None  # dtype=None → auto (bfloat16 on GPU, fp32 on CPU)
)
```

### 3. The hit ratio

At the end of each turn the service logs:

```
spec-prefill hit 83% (15/18 tokens) moved 312ms off the critical path, TTFT 47ms
```

- **hit %** — fraction of the final prompt that was already in cache
- **tokens kept / total** — the raw numbers
- **moved Xms** — estimated latency removed from the critical path
- **TTFT Xms** — actual time-to-first-token for this turn

A hit ratio above ~70% means the technique is working well. Low ratios happen when the user's speech changes significantly from the partial transcriptions (heavy corrections by the STT model).

---

## Customisation

### Change the model

Set `SPEC_MODEL` in `.env`:

```
# CPU-friendly, fast:
SPEC_MODEL=Qwen/Qwen2.5-0.5B-Instruct   # ~1 GB

# Good balance:
SPEC_MODEL=Qwen/Qwen2.5-1.5B-Instruct   # ~3 GB

# Best quality, needs a GPU:
SPEC_MODEL=Qwen/Qwen2.5-7B-Instruct     # ~15 GB
```

Any model with a HuggingFace chat template works. Qwen2.5 is recommended — it has an efficient template and strong instruction-following at small sizes.

### Change the voice

Set `ELEVENLABS_VOICE_ID` in `.env` to any voice ID from your ElevenLabs account.

### Tune generation

```python
LLMSettings(
    temperature=0.7,    # higher = more creative, lower = more predictable
    max_tokens=256,     # keep short for voice; long replies feel awkward
)
```

---

## Hardware requirements

| Model | RAM | GPU VRAM | Speed (CPU) |
|---|---|---|---|
| Qwen2.5-0.5B | ~2 GB | — | Fast (real-time) |
| Qwen2.5-1.5B | ~4 GB | — | Adequate |
| Qwen2.5-7B | ~16 GB | 8 GB+ | Needs GPU |

The 0.5B model runs comfortably on a standard laptop. The prefill trick helps most on CPU (where every ms of prefill is expensive) and is less dramatic on a fast GPU (where prefill is already cheap).

---

## Project structure

```
speculative_prefill_example/
├── bot.py           # the full bot (~130 lines)
├── pyproject.toml   # dependencies
├── .env.example     # keys + model template
└── README.md
```

---

## Related

- [`pipecat-speculative-prefill`](https://github.com/iamdgarcia/pipecat-speculative-prefill) — the library this example uses
- [thinking-backchannel example](../thinking_backchannel_example/) — companion example for cloud LLMs (fills silence with "hmm", "one sec")
- [The Learning Curve](https://iamdgarcia.substack.com) — more voice-agent examples and guides
