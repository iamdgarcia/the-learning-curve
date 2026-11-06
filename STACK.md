# The Learning Curve AI Stack

Building an AI application is getting easier. Deciding what to use for each part is not.

Where do you run the model? Do you need a GPU? Should you consume a model via API or self-host it? Where do you host the backend? What about the frontend? What happens when that small prototype starts becoming a real application?

The problem is no longer that tools are missing. It's the opposite: there are too many.

This is a selection of the tools I recommend for building AI applications and systems, **organised by the problem they solve**.

Not a popularity ranking. Not an exhaustive list. The stack I would choose today to start building.

> **Disclosure:** some links are affiliate or referral links. If you use one, The Learning Curve may receive a commission at no extra cost to you. Affiliation does not determine which tools appear — they have to make technical sense first.

---

## An AI application is not just a model

It usually has several pieces:

```
┌─────────────────────────────────────────────────────┐
│                  Your AI application                │
├──────────────┬──────────────┬────────────┬──────────┤
│  AI Inference│  GPU Compute │  Backend   │ Frontend │
│  (the model) │  (if you     │  (API,     │ (what    │
│              │  need it)    │  workers,  │ the user │
│              │              │  DB)       │ sees)    │
└──────────────┴──────────────┴────────────┴──────────┘
```

You don't need all of them. A prototype can be a web app connected to a model API. Other projects will need their own GPUs, background workers and a more complete infrastructure.

The goal of this stack is to help you decide what you need based on what you're trying to build.

---

## 1. AI Inference — Novita AI

<table>
<tr>
<td width="72" align="center" valign="top"><br>
  <img src="https://www.google.com/s2/favicons?domain=novita.ai&sz=64" width="40" height="40" alt="Novita AI"/>
</td>
<td valign="top">

### [Novita AI ↗](https://novita.ai/?ref=mzblm2z&utm_source=affiliate)
**I want to use a model without managing all the infrastructure.**

Novita provides APIs for open-source models (DeepSeek, Llama, Qwen and others), plus serverless GPUs and on-demand GPU instances. OpenAI-compatible — works as a drop-in replacement with no SDK changes.

| ✅ Use Novita when… | ❌ Look elsewhere when… |
|--------------------|------------------------|
| Prototyping an AI application | You need full control over the execution environment |
| Quick testing of open-source models | You want to install your own serving stack |
| Consuming a model via API | You need to modify the runtime |
| You don't want to manage model serving | You want to manage the GPU directly |

**Key:** `NOVITA_API_KEY` + `NOVITA_BASE_URL` · **Default model:** `deepseek/deepseek_v3`
</td>
</tr>
</table>

---

## 2. GPU & Compute — RunPod

<table>
<tr>
<td width="72" align="center" valign="top"><br>
  <img src="https://www.google.com/s2/favicons?domain=runpod.io&sz=64" width="40" height="40" alt="RunPod"/>
</td>
<td valign="top">

### [RunPod ↗](https://runpod.io)
**I want to control where and how my model runs.**

There are situations where an API is not enough: maybe you need to deploy your own model, a specific GPU, or control the container and runtime. RunPod offers on-demand GPUs and a serverless platform that can scale to zero when idle.

| ✅ Use RunPod when… | ❌ Look elsewhere when… |
|--------------------|------------------------|
| Running your own models | You just need to consume an existing model API |
| Self-hosted inference | You want to get to something working fast |
| Fine-tuning | The model already exists as a public API |
| Custom containers or runtimes | — |
| Experiments that need environment control | — |

**Novita vs RunPod in one line:**
- *"Give me access to this model and let me start using it"* → **Novita AI**
- *"I want to decide exactly what runs, where it runs, and on what infrastructure"* → **RunPod**

They are not necessarily direct competitors. In many projects they can be two different pieces of the same stack.
</td>
</tr>
</table>

---

## 3. Backend & Infrastructure — Railway

<table>
<tr>
<td width="72" align="center" valign="top"><br>
  <img src="https://cdn.simpleicons.org/railway" width="40" height="40" alt="Railway"/>
</td>
<td valign="top">

### [Railway ↗](https://railway.com?referralCode=6Lguh2)
**The model is not the application.**

This is a very common mistake when you start building with LLMs. You can have a model working perfectly and still not have an application. A real application needs APIs, authentication, databases, workers, webhooks, or scheduled tasks. Railway lets you deploy all these services inside a single project.

| ✅ Use Railway for… |
|--------------------|
| AI application backends |
| REST and streaming APIs |
| Background workers and scheduled jobs |
| Databases (Postgres, Redis) |
| Moving quickly from local to production |

**Free tier:** $5 credit/month
</td>
</tr>
</table>

---

## 4. Frontend & Deployment — Netlify

<table>
<tr>
<td width="72" align="center" valign="top"><br>
  <img src="https://cdn.simpleicons.org/netlify/00C7B7" width="40" height="40" alt="Netlify"/>
</td>
<td valign="top">

### [Netlify ↗](https://join.netlify.com/uk2itht31g7b)
**The user doesn't see your model. They see your application.**

You can have the best model in the world and a perfectly designed API. But the user interacts with an interface. Netlify solves that part of the stack: getting the web application in front of the user.

| ✅ Use Netlify for… |
|--------------------|
| Frontends and AI application UIs |
| Landing pages and demos |
| Prototypes that need to be online fast |
| Lightweight serverless functions |

**Railway + Netlify together:** Railway for the backend, Netlify for the frontend. Two tools, two distinct problems — easier to reason about than putting everything on a single platform.

**Free tier:** 100GB bandwidth, 300 build minutes/month
</td>
</tr>
</table>

---

## 5. AI Voice — ElevenLabs

<table>
<tr>
<td width="72" align="center" valign="top"><br>
  <img src="https://cdn.simpleicons.org/elevenlabs" width="40" height="40" alt="ElevenLabs"/>
</td>
<td valign="top">

### [ElevenLabs ↗](https://try.elevenlabs.io/5rwirobe89kq)
**I need a realistic AI voice or high-quality transcription.**

The most natural TTS for Spanish and English. Multilingual v2 model sounds genuinely human. Word-level timestamps for tight subtitle sync. Also offers Scribe — the transcription API with the tightest word-boundary alignment for voice and video applications.

| ✅ Use ElevenLabs for… |
|------------------------|
| TTS in Shorts and video content |
| Voice in conversational agents |
| Transcription with precise timestamps |
| Voice cloning |

**Free tier:** 10K characters/month · **Key:** `ELEVENLABS_API_KEY`
</td>
</tr>
</table>

---

## What stack should you choose?

### I want to build an MVP quickly
```
Novita AI  →  model via API
Railway    →  backend
Netlify    →  frontend
```
Starting point for most applications. No GPUs to manage. Focus on the product.

### I want to run my own model
```
RunPod     →  GPU + serving
Railway    →  backend
Netlify    →  frontend
```
The inference infrastructure is under your control.

### I want to experiment with open-source models
```
Novita AI  →  quick prototype via API
RunPod     →  when you need environment control
```

---

## Quick reference

| | Tool | For | Free tier | Link |
|-|------|-----|-----------|------|
| <img src="https://www.google.com/s2/favicons?domain=novita.ai&sz=32" width="20"> | Novita AI | Cheap LLM inference | Pay-per-use | [↗](https://novita.ai/?ref=mzblm2z&utm_source=affiliate) |
| <img src="https://www.google.com/s2/favicons?domain=runpod.io&sz=32" width="20"> | RunPod | GPU & own compute | — | [↗](https://runpod.io) |
| <img src="https://cdn.simpleicons.org/railway" width="20"> | Railway | Backend, DB, workers | $5 credit/mo | [↗](https://railway.com?referralCode=6Lguh2) |
| <img src="https://cdn.simpleicons.org/netlify/00C7B7" width="20"> | Netlify | Frontend & deploy | 100GB bw/mo | [↗](https://join.netlify.com/uk2itht31g7b) |
| <img src="https://cdn.simpleicons.org/elevenlabs" width="20"> | ElevenLabs | TTS & transcription | 10K chars/mo | [↗](https://try.elevenlabs.io/5rwirobe89kq) |
| <img src="https://www.google.com/s2/favicons?domain=groq.com&sz=32" width="20"> | Groq | Fast transcription | Generous | [groq.com](https://console.groq.com) |
| <img src="https://cdn.simpleicons.org/pexels/05A081" width="20"> | Pexels | Stock footage | 200 req/hr | [pexels.com](https://www.pexels.com/api/) |

---

## What's next

The stack will grow as new tools are tested. The rule stays the same: a tool enters the stack because I would recommend it technically, not because it has an affiliate programme. And when a better tool appears for a given problem, the stack changes.

**Areas coming next:** observability · vector databases · model gateways · model evaluation · AI coding tools · MLOps · security
