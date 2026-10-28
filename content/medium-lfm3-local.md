# How to Run LFM3 Locally: The Non-Transformer Model That Fits in 1.1 GB

*LFM3 is 1.7B parameters, fits in 1.1 GB of RAM, and it's not a Transformer. Here's how to run it in three commands.*

---

Last week Liquid AI dropped something that quietly broke the internet in the ML community: **LFM3**, a family of small language models built on a completely different architecture than every model you've heard of.

Not GPT. Not Llama. Not Mistral. None of them are Transformers either — oh wait, they are. LFM3 is not.

And it fits on your laptop.

Let me show you how to run it right now, then explain why this matters more than the usual "new model Tuesday" noise.

---

## Why LFM3 is different

Since 2017, every serious language model has been a Transformer. Attention mechanisms, quadratic complexity on long sequences, the whole package. We've gotten very good at scaling Transformers, but their fundamental limitations haven't gone away: they're memory-hungry, slow on long contexts, and architecturally frozen.

Liquid AI is an MIT spinout, and their bet is that **State Space Models (SSMs)** — specifically their hybrid "Liquid Foundation Model" architecture — can match Transformers at a fraction of the compute and memory cost.

LFM3 is their third generation. The numbers are interesting:

- **LFM3-1.7B** beats Llama 3.2-1B and Gemma 3-1T on standard reasoning and coding benchmarks
- It fits in **1.1 GB** with 4-bit quantization (Q4_K_M)
- It runs at full speed on CPU — no GPU required
- It supports **GGUF, ONNX, MLX, FP8, and NVFP4** formats out of the box

There's also a **vision model** (LFM3-VL-2B) and an **any-to-any model** (LFM3-Omni-2B) that handles audio, text, and images. All under 2B parameters. All free.

---

## Run it in three commands

### Option 1 — Ollama (easiest)

If you have [Ollama](https://ollama.ai) installed:

```bash
ollama run hf.co/LiquidAI/LFM3-1.7B-GGUF:Q4_K_M
```

That's it. Ollama downloads the model and drops you into a chat session. The Q4_K_M quantization is 1.1 GB and runs on any machine made after 2015.

---

### Option 2 — llama.cpp (fastest inference)

LFM3 requires a recent llama.cpp build with SSM/LFM3 architecture support:

```bash
# Build (one-time, ~3 minutes)
git clone https://github.com/ggml-org/llama.cpp && cd llama.cpp
cmake -B build && cmake --build build --config Release -j$(nproc)

# Run
./build/bin/llama-cli -hf LiquidAI/LFM3-1.7B-GGUF:Q4_K_M \
  --temp 0.1 --top-k 50 --repeat-penalty 1.1 -cnv
```

For math and science, tweak the sampling params:

```bash
./build/bin/llama-cli -hf LiquidAI/LFM3-1.7B-GGUF:Q4_K_M \
  --temp 1.0 --top-p 0.95 --top-k 20 -cnv
```

The model downloads automatically from Hugging Face on first run.

---

### Option 3 — Python (for developers)

```bash
pip install llama-cpp-python huggingface_hub
python lfm3_chat.py
```

I wrote a minimal chat script that auto-downloads the GGUF and runs a conversation loop. No framework. No LangChain. Just the model and your messages.

→ [GitHub: lfm3-local playground](https://github.com/iamdgarcia/the-learning-curve/tree/main/llm/lfm3-local)

---

## Which quantization should you pick?

The GGUF page lists several options. Here's the practical answer:

| Quantization | File size | RAM needed | Quality loss |
|---|---|---|---|
| **Q4_K_M** | 1.1 GB | ~2 GB | Negligible |
| Q5_K_M | 1.26 GB | ~2.5 GB | None |
| Q8_0 | 1.85 GB | ~3.5 GB | None |
| BF16 | 3.47 GB | ~6 GB | None (reference) |

**Use Q4_K_M.** Liquid AI trained a QAD (Quantization-Aware Distillation) checkpoint specifically for Q4_0 — meaning the quality loss from quantization is baked back in during training. It's not a naive rounding operation. The 1.1 GB version is legitimately good.

---

## What about the vision model?

Swap `LFM3-1.7B-GGUF` for `LFM3-VL-2B-GGUF`:

```bash
ollama run hf.co/LiquidAI/LFM3-VL-2B-GGUF:Q4_K_M
```

Or with llama.cpp:

```bash
./build/bin/llama-cli -hf LiquidAI/LFM3-VL-2B-GGUF:Q4_K_M \
  --temp 0.1 --top-k 50 --repeat-penalty 1.1 -cnv
```

Send it an image path and ask questions. It runs locally, no API call goes anywhere.

---

## Add a proper UI in one click

Command-line chat is fine for testing. If you want something that actually looks like ChatGPT — with model switching, conversation history, and team access — you need Open WebUI.

The easiest path I've found: deploy the [Private AI Dashboard](https://github.com/iamdgarcia/the-learning-curve/tree/main/products/private-ai-dashboard) template to Railway. It spins up Open WebUI backed by a LiteLLM proxy in about 4 minutes, and you can point it at your local Ollama instance or any OpenAI-compatible endpoint.

It's what I use for all my local model experiments, including LFM3.

---

## Don't want to run it locally?

If your laptop is older or you just want to test without a build step, [Novita AI](https://novita.ai/?ref=mzblm2z&utm_source=affiliate) runs LFM3 and 200+ other open-source models through an OpenAI-compatible API. You pay per token, prices are among the cheapest in the market, and you can switch between LFM3, Llama, DeepSeek, and Qwen in the same API call.

Useful for comparing LFM3 against a baseline without maintaining separate local installs.

---

## The bigger picture

Here's what I think is actually happening with LFM3:

The Transformer is not going away. But the assumption that every useful model has to be a Transformer is cracking. SSMs like Mamba, RWKV, and now LFM3 are proving that you can build models with linear (not quadratic) complexity on long sequences, lower memory footprint, and competitive performance — especially at small parameter counts where Transformers have always been weakest.

LFM3 at 1.7B is probably the most capable truly-laptop-sized model available right now. It's not going to replace GPT-4o for complex reasoning, but for code completion, document summarization, and tool-augmented agents where you care about latency and privacy, it's a serious option.

And it runs in 1.1 GB.

---

## Resources

- [LFM3 collection on Hugging Face](https://huggingface.co/collections/LiquidAI/lfm3) — all models, all formats
- [LFM3-1.7B-GGUF](https://huggingface.co/LiquidAI/LFM3-1.7B-GGUF) — direct GGUF download page
- [lfm3-local playground](https://github.com/iamdgarcia/the-learning-curve/tree/main/llm/lfm3-local) — the Python chat script from this article
- [llama.cpp](https://github.com/ggml-org/llama.cpp) — required for llama-cli
- [Private AI Dashboard](https://github.com/iamdgarcia/the-learning-curve/tree/main/products/private-ai-dashboard) — Open WebUI + LiteLLM, one-click Railway deploy
- [Novita AI](https://novita.ai/?ref=mzblm2z&utm_source=affiliate) — cloud inference if local isn't an option

---

*I write about AI engineering weekly at [The Learning Curve](https://iamdgarcia.substack.com). Working code, no hype.*
