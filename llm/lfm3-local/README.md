# LFM3 Local Playground

Run [Liquid AI's LFM3](https://huggingface.co/collections/LiquidAI/lfm3) on your laptop in three commands. No API key. No cloud. No transformer.

> Companion repo for the Medium article **"How to Run the AI Model That Killed the Transformer on Your Laptop (for Free)"**

---

## What is LFM3?

LFM3 (Liquid Foundation Models 3) is a family of small language models from [Liquid AI](https://liquid.ai) — an MIT spinout — built on a **hybrid SSM architecture**, not a Transformer. Despite having only 1.7B parameters, it matches or beats models twice its size on reasoning and coding benchmarks.

Available formats: GGUF · ONNX · MLX · FP8 · NVFP4

| Model | Size | Quantization | RAM needed |
|---|---|---|---|
| LFM3-1.7B Q4_K_M | 1.1 GB | 4-bit | ~2 GB |
| LFM3-1.7B Q5_K_M | 1.26 GB | 5-bit | ~2.5 GB |
| LFM3-1.7B Q8_0 | 1.85 GB | 8-bit | ~3.5 GB |
| LFM3-VL-2B (vision) | ~1.1 GB | 4-bit | ~2 GB |

---

## Option A — llama.cpp (fastest, no Python)

```bash
# 1. Build llama.cpp (one-time)
git clone https://github.com/ggml-org/llama.cpp && cd llama.cpp
cmake -B build && cmake --build build --config Release -j$(nproc)

# 2. Chat
./build/bin/llama-cli -hf LiquidAI/LFM3-1.7B-GGUF:Q4_K_M \
  --temp 0.1 --top-k 50 --repeat-penalty 1.1 -cnv
```

---

## Option B — Python (llama-cpp-python)

```bash
pip install llama-cpp-python huggingface_hub
python lfm3_chat.py
```

The script auto-downloads the GGUF from Hugging Face on first run (~1.1 GB).

---

## Option C — Ollama (easiest, one line)

```bash
ollama run hf.co/LiquidAI/LFM3-1.7B-GGUF:Q4_K_M
```

> Requires [Ollama](https://ollama.ai) installed and LFM3 support merged (check `ollama list` after pulling).

---

## Connect to a private AI dashboard

Want a ChatGPT-style UI for LFM3 (and 100+ other models)?  
Deploy [Private AI Dashboard](https://github.com/iamdgarcia/the-learning-curve/tree/main/products/private-ai-dashboard) — Open WebUI + LiteLLM on Railway, one click.

Or if you prefer cloud inference without local setup:  
→ [Novita AI](https://novita.ai/?ref=mzblm2z&utm_source=affiliate) runs LFM3 and 200+ open-source models via an OpenAI-compatible API.

---

## Tips

- **Math/science tasks**: use `--temp 1.0 --top-p 0.95 --top-k 20` instead
- **Vision tasks**: swap to `LiquidAI/LFM3-VL-2B-GGUF`
- **Max quality on laptop**: Q5_K_M is the sweet spot (barely noticeable vs Q8_0)

---

Part of [The Learning Curve](https://iamdgarcia.substack.com) — hands-on AI engineering. No hype, just working code.
