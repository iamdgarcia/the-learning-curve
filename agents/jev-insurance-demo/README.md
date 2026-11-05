# 🚗 Insurance Claim Triage with JEV-27B-VL

> A zero-training-data demo that evaluates car damage claims using Novita AI's **JEV-27B-VL** — a decision model that returns probabilities, not text.

**[▶ Live Demo](https://your-demo-url.com)** · **[Try the model free for 15 days →](https://your-affiliate-link.com)**

![Demo screenshot](docs/demo.png)

---

## What is JEV-27B-VL?

Most LLMs generate text. JEV-27B-VL does something different: it takes a piece of content and a question, and returns the **probability of each possible answer**.

Three question types:
| Kind | Output | Example |
|------|--------|---------|
| `noul` | Yes / No | "Does this image show a damaged vehicle?" |
| `score` | 0 – 5 rating | "How severe is the damage?" |
| `choice` | Pick one from a list | "Which department should handle this?" |

No fine-tuning. No training data. No prompt engineering. Just a question and a confidence score.

---

## What this demo does

Given a car photo (and an optional claim description), the app fires **3 parallel decisions** in under 2 seconds:

1. **Damage detected?** → yes/no with confidence
2. **Zone** → Frontal or Rear
3. **Severity** → 0 (no damage) to 5 (total loss)

---

## Benchmark results

Evaluated on 48 images from the [`SaiVaibhavS/comprehensive-car-damage`](https://huggingface.co/datasets/SaiVaibhavS/comprehensive-car-damage) dataset (HuggingFace). **Zero fine-tuning, zero labeled training data.**

| Metric | Accuracy |
|--------|----------|
| 🔍 Damage detection | **83.3%** |
| 📍 Zone (Front / Rear) | **100.0%** |
| ⚡ Severity bucket | 50.0% |

- **Avg latency:** ~1.5s per claim (3 decisions in parallel)
- **Avg cost:** ~$0.00003 per claim
- **Dataset:** 6 classes × 8 images (F_Breakage, F_Crushed, F_Normal, R_Breakage, R_Crushed, R_Normal)

The 100% zone accuracy is remarkable — the model distinguishes front vs. rear damage perfectly with no training.

The severity score shows the model's own calibration: it tends to give conservative scores (3–4) even for heavily crushed vehicles. For production use, calibrate the buckets to your own labeled data.

---

## Run it yourself

**Requirements:** [Bun](https://bun.sh) · Python 3 · [Novita AI API key](https://your-affiliate-link.com)

```bash
git clone https://github.com/your-org/jev-insurance-demo
cd jev-insurance-demo

# 1. Download dataset images (from HuggingFace parquet, no login needed)
pip install pyarrow
python3 src/download_dataset.py 8   # 8 images per class = 48 total

# 2. Run benchmark (evaluates all 48 images, saves results.json)
NOVITA_API_KEY=sk_... bun run src/benchmark.ts

# 3. Start the demo
NOVITA_API_KEY=sk_... bun run src/server.ts
# → http://localhost:3456
```

---

## Project structure

```
jev-insurance-demo/
├── src/
│   ├── api.ts                  # JEV-27B-VL wrapper
│   ├── dataset.ts              # Dataset loader
│   ├── benchmark.ts            # Benchmark runner → data/results.json
│   ├── download_dataset.py     # Downloads images from HuggingFace parquet
│   └── server.ts               # Bun HTTP server (serves demo + proxies API)
├── demo/
│   └── index.html              # Single-page UI
└── data/
    ├── cases.json              # 48 cases with metadata + LLM descriptions
    ├── results.json            # Benchmark results
    └── images/                 # Downloaded car damage photos
```

---

## API usage

```typescript
const res = await fetch("https://api.novita.ai/v3/autotrust/v1/decide", {
  method: "POST",
  headers: { Authorization: `Bearer ${API_KEY}`, "Content-Type": "application/json" },
  body: JSON.stringify({
    model: "autotrust/jev-27b-vl",
    kind: "noul",
    state: [{ image: "data:image/jpeg;base64,..." }],
    question: "Does this image show a damaged vehicle?"
  })
});

const { choice, probabilities } = await res.json();
// choice: "true" | "false"
// probabilities: [0.008, 0.992]
```

**[Get your free API key →](https://your-affiliate-link.com)**

---

## Other use cases

The same pattern works for any industry where you need fast, structured decisions:

- **Content moderation** — is this comment toxic? what category?
- **Support routing** — which team handles this ticket?
- **HR screening** — does this CV meet minimum requirements?
- **Real estate** — does this photo match the listing description?

---

## License

MIT · Built by [The Learning Curve AI](https://your-site.com)

> **Disclosure:** The Novita AI links in this README are affiliate links.
