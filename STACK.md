# Recommended Stack

Tools used across every project in this repo. Organised by what you need, not by what they sell.

Links marked with ↗ are affiliate or referral links — they help keep this content free at no extra cost to you.

---

## AI Voice & Audio

### Need a realistic AI voice?
**[ElevenLabs ↗](https://try.elevenlabs.io/5rwirobe89kq)**

The best text-to-speech for Spanish and English. Used in every pipeline that generates audio (yt-clipper, voice agents). Multilingual v2 model sounds genuinely human. Word-level timestamps for tight subtitle sync.

- Free tier: 10K characters/month
- Used for: TTS in Pipelines B/C/D, transcription in Pipeline D
- Key: `ELEVENLABS_API_KEY`

---

## LLM Inference

### Need affordable, fast LLM calls?
**[Novita AI ↗](https://novita.ai/?ref=mzblm2z&utm_source=affiliate)**

OpenAI-compatible API with access to DeepSeek, Llama, Qwen and others. Significantly cheaper than OpenAI for the same output quality. Used as the default LLM provider across all pipelines.

- Used for: script writing, clip analysis, trend discovery, visual planning
- Key: `NOVITA_API_KEY` + `NOVITA_BASE_URL`
- Default model: `deepseek/deepseek_v3`

### Need fast inference for transcription?
**[Groq](https://console.groq.com)** — free tier, Whisper large-v3, near-instant.

- Used for: Pipeline D transcription (`--transcriber groq`)
- Key: `GROQ_API_KEY`

---

## Deployment

### Need to deploy a frontend or serverless function?
**[Netlify ↗](https://join.netlify.com/uk2itht31g7b)**

Every agent blueprint in this repo has a one-click Netlify deploy. Free tier covers all demos and personal projects.

- Used for: agent blueprints, web UIs
- Free tier: 100GB bandwidth, 300 build minutes/month

### Need to deploy a backend, database, or long-running agent?
**[Railway ↗](https://railway.com?referralCode=6Lguh2)**

The simplest way to run a persistent Python service, Postgres, Redis, or a Docker container. No YAML config files. Used for backend APIs and self-hosted services.

- Used for: voice agent servers, APIs, databases
- Free tier: $5 credit/month (usually enough for a side project)

---

## Stock Footage

### Need B-roll for your videos?
**[Pexels](https://www.pexels.com/api/)** — free, no attribution required in most cases.

- Used for: Pipeline A B-roll overlay
- Key: `PEXELS_API_KEY`
- Free tier: 200 requests/hour

---

## Quick reference

| I need… | Tool | Free tier | Link |
|---------|------|-----------|------|
| AI voice (TTS) | ElevenLabs | 10K chars/mo | [↗](https://try.elevenlabs.io/5rwirobe89kq) |
| Fast transcription | ElevenLabs Scribe / Groq | ✅ | [↗](https://try.elevenlabs.io/5rwirobe89kq) |
| LLM inference (cheap) | Novita AI | Pay-per-use | [↗](https://novita.ai/?ref=mzblm2z&utm_source=affiliate) |
| Deploy a frontend | Netlify | Generous free | [↗](https://join.netlify.com/uk2itht31g7b) |
| Deploy a backend | Railway | $5 credit/mo | [↗](https://railway.com?referralCode=6Lguh2) |
| Stock footage | Pexels | 200 req/hr | [pexels.com/api](https://www.pexels.com/api/) |
