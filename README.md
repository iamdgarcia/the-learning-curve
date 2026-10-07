<div align="center">

<img src="https://substackcdn.com/image/fetch/$s_!eWHj!,e_trim:10:white/e_trim:10:transparent/h_72,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F62395659-6555-44b9-9eb3-e4aaa91e7ccd_1584x396.png" alt="The Learning Curve" width="400"/>

# The Learning Curve

**Hands-on AI engineering projects. No hype, just working code.**

[![Substack](https://img.shields.io/badge/Subscribe-The_Learning_Curve-FF6B00?style=for-the-badge&logo=substack&logoColor=white)](https://iamdgarcia.substack.com)
[![GitHub Stars](https://img.shields.io/github/stars/iamdgarcia/the-learning-curve?style=for-the-badge&color=FF6B00)](https://github.com/iamdgarcia/the-learning-curve/stargazers)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)

</div>

---

> *"Learn AI like an engineer, not like a YouTube guru."*

A curated collection of deployable AI projects, agent blueprints, and full courses from **[The Learning Curve](https://iamdgarcia.substack.com)** — the engineering-first AI community by [@iamdgarcia](https://github.com/iamdgarcia).

Each project ships with working code, a web interface, and a one-click deploy button. No cloud PhD required.

---

## ⚡ Agent Blueprints

Deploy a working AI agent in under 60 seconds. Each blueprint is a self-contained project with a web UI, ready to run on Netlify.

> 🆓 **New to Netlify?** [Create your free account here](https://join.netlify.com/uk2itht31g7b) *(referral link — supports the community)*

| Blueprint | What it does | Difficulty | Course Module | Deploy |
|---|---|---|---|---|
| [Simple Agent](./simple-agent-blueprint) | Basic agent loop: perceive → reason → act → remember | ⭐ Beginner | Module 1 | [![Deploy](https://www.netlify.com/img/deploy/button.svg)](https://app.netlify.com/start/deploy?repository=https://github.com/iamdgarcia/simple-agent-blueprint&affiliate=8mntz9z1uxdi-96ld6) |
| [ReAct Agent](./react-agent-blueprint) | Reasoning + Acting loop with tool use | ⭐ Beginner | Module 1.3 | [![Deploy](https://www.netlify.com/img/deploy/button.svg)](https://app.netlify.com/start/deploy?repository=https://github.com/iamdgarcia/react-agent-blueprint&affiliate=8mntz9z1uxdi-96ld6) |
| [Memory Agent](./memory-agent-blueprint) | Short-term + long-term memory across sessions | ⭐⭐ Intermediate | Module 2.1 | [![Deploy](https://www.netlify.com/img/deploy/button.svg)](https://app.netlify.com/start/deploy?repository=https://github.com/iamdgarcia/memory-agent-blueprint&affiliate=8mntz9z1uxdi-96ld6) |
| [RAG Agent](./rag-agent-blueprint) | Chat with your documents (PDF, text) | ⭐⭐ Intermediate | Module 2.2 | [![Deploy](https://www.netlify.com/img/deploy/button.svg)](https://app.netlify.com/start/deploy?repository=https://github.com/iamdgarcia/rag-agent-blueprint&affiliate=8mntz9z1uxdi-96ld6) |
| [Planning Agent](./planning-agent-blueprint) | Hierarchical goal decomposition + execution | ⭐⭐ Intermediate | Module 3.1 | [![Deploy](https://www.netlify.com/img/deploy/button.svg)](https://app.netlify.com/start/deploy?repository=https://github.com/iamdgarcia/planning-agent-blueprint&affiliate=8mntz9z1uxdi-96ld6) |
| [Reflective Agent](./reflective-agent-blueprint) | Self-critique and iterative improvement | ⭐⭐ Intermediate | Module 3.2 | [![Deploy](https://www.netlify.com/img/deploy/button.svg)](https://app.netlify.com/start/deploy?repository=https://github.com/iamdgarcia/reflective-agent-blueprint&affiliate=8mntz9z1uxdi-96ld6) |
| [Router Agent](./router-agent-blueprint) | Smart task routing to specialized sub-agents | ⭐⭐⭐ Advanced | Module 3.3 | [![Deploy](https://www.netlify.com/img/deploy/button.svg)](https://app.netlify.com/start/deploy?repository=https://github.com/iamdgarcia/router-agent-blueprint&affiliate=8mntz9z1uxdi-96ld6) |
| [Research Team](./research-team-blueprint) | Multi-agent collaboration: orchestrator + workers | ⭐⭐⭐ Advanced | Module 4 | [![Deploy](https://www.netlify.com/img/deploy/button.svg)](https://app.netlify.com/start/deploy?repository=https://github.com/iamdgarcia/research-team-blueprint&affiliate=8mntz9z1uxdi-96ld6) |
| [Guardrails Agent](./guardrails-agent-blueprint) | Safety checks, bias detection, ethical constraints | ⭐⭐⭐ Advanced | Module 5 | [![Deploy](https://www.netlify.com/img/deploy/button.svg)](https://app.netlify.com/start/deploy?repository=https://github.com/iamdgarcia/guardrails-agent-blueprint&affiliate=8mntz9z1uxdi-96ld6) |
| [Production Agent](./production-agent-blueprint) | Logging, tracing, health checks, monitoring | ⭐⭐⭐ Advanced | Module 5 | [![Deploy](https://www.netlify.com/img/deploy/button.svg)](https://app.netlify.com/start/deploy?repository=https://github.com/iamdgarcia/production-agent-blueprint&affiliate=8mntz9z1uxdi-96ld6) |
| [Doc Extraction](./doc-extraction-blueprint) | Structured data extraction from PDFs and images | ⭐⭐⭐ Advanced | Bonus | [![Deploy](https://www.netlify.com/img/deploy/button.svg)](https://app.netlify.com/start/deploy?repository=https://github.com/iamdgarcia/doc-extraction-blueprint&affiliate=8mntz9z1uxdi-96ld6) |

---

## 📚 Courses

| Course | Description | Language | Link |
|---|---|---|---|
| **Agentic AI for Beginners** | From chat to autonomous agents — 5 modules, theory + code | EN / ES | [Start →](./tlc_agents_training) |
| **AI Architect Academy** | From software engineer to AI architect — 6 semesters | ES | [Start →](./ai_architect_course) |

---

## 🔬 Projects

Standalone real-world implementations you can study, fork, and adapt.

| Project | Description | Stack |
|---|---|---|
| [Nemotron Banking ASR](./nemotron-banking-es-asr) | Fine-tuned speech recognition for Spanish banking | NVIDIA Nemotron, NeMo |
| [RAG Production System](./rag-production-system) | Production-ready RAG with observability | Python, LangChain |
| [System One Models Tutorial](./system_one_models_tutorial) | Working with System One model endpoints | Python |

---

## 🛍️ Digital Products

Grab-and-use toolkits, OS templates, and blueprints from the store.

**→ [iamdgarcia.gumroad.com](https://iamdgarcia.gumroad.com)**

<details>
<summary>View all products</summary>

| Product | What it is |
|---|---|
| AI Agency Operations Kit | Full operating system for running an AI agency |
| AI Workflow OS | Notion OS for AI-powered workflows |
| Cursor Rules Pack | Battle-tested Cursor rules for AI engineering |
| Data Analyst OS | End-to-end data analyst workspace |
| Founder OS | AI-first founder operating system |
| LangGraph Agent Blueprint | Production LangGraph agent template |
| LiteLLM + Novita Gateway | Self-hosted LLM gateway setup |
| Marketing OS | AI marketing workflow system |
| MCP Server Starter Kit | Build your own MCP server from scratch |
| ML Engineer Second Brain | Knowledge system for ML engineers |
| PM OS | AI product manager operating system |
| Private AI Dashboard | Self-hosted AI dashboard template |
| Prompt Engineering Vault | 500+ curated, tested prompts |
| RAG Pipeline Blueprint | End-to-end RAG system template |
| Research Paper Tracker | AI-assisted research tracking system |
| Free AI Project Tracker | 100% free — track your AI projects | 

</details>

---

## 🛠️ Recommended Stack

The tools we use across every project in this repo. These are genuine picks — links are affiliate/referral and help keep the community free.

| Tool | What for | Link |
|---|---|---|
| **Netlify** | Deploy every blueprint for free | [Free account →](https://join.netlify.com/uk2itht31g7b) |
| **Novita AI** | Affordable, fast LLM inference (OpenAI-compatible API) | [Try Novita →](https://novita.ai/?ref=mzblm2z&utm_source=affiliate) |
| **Railway** | Deploy backends, databases, and agents with one click | [Try Railway →](https://railway.com?referralCode=6Lguh2) |

---

## 🗺️ Learning Path

Not sure where to start? Follow this order:

```
Module 0 — Setup & Foundations
    ↓
Simple Agent Blueprint         ← deploy your first agent
    ↓
ReAct Agent Blueprint          ← add tool use
    ↓
Memory + RAG Agent Blueprints  ← add memory & docs
    ↓
Planning + Reflective           ← advanced reasoning
    ↓
Research Team + Router          ← multi-agent systems
    ↓
Guardrails + Production         ← ship it safely
```

---

## 🤝 Contributing

Pull requests welcome. If you've built something with these blueprints or want to add a project:

1. Fork this repo
2. Create a folder: `your-project-name/`
3. Include: `README.md`, `requirements.txt`, `.env.example`
4. Open a PR — we'll review and feature it

See [CONTRIBUTING.md](./CONTRIBUTING.md) for the full guide.

---

## 📬 Community

- **Newsletter:** [iamdgarcia.substack.com](https://iamdgarcia.substack.com) — weekly AI engineering deep-dives
- **Issues:** Found a bug or have an idea? [Open an issue](https://github.com/iamdgarcia/the-learning-curve/issues)
- **Discussions:** Questions and project showcases → [GitHub Discussions](https://github.com/iamdgarcia/the-learning-curve/discussions)

---

<div align="center">

Built with ❤️ by [@iamdgarcia](https://github.com/iamdgarcia) and the TLC community.

**[⭐ Star this repo](https://github.com/iamdgarcia/the-learning-curve)** to stay updated when new projects drop.

</div>
