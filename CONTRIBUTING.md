# Contributing to The Learning Curve

Thanks for wanting to contribute. This repo grows through community projects — if you've built something with these blueprints or want to add a standalone AI project, this is the place.

## What we accept

- **Agent blueprints** — deployable, self-contained agents with a web UI
- **Standalone projects** — real-world implementations (RAG, fine-tuning, multi-modal, etc.)
- **Fixes and improvements** to existing projects (bugs, updated deps, better docs)

We don't accept: promotional content, projects without working code, or anything that requires paid APIs with no free tier option.

## How to submit a project

### 1. Fork and clone

```bash
git clone https://github.com/iamdgarcia/the-learning-curve.git
cd the-learning-curve
```

### 2. Create your project folder

Use kebab-case. Put it in the right category:

```
your-project-name/
├── README.md          ← required (see template below)
├── requirements.txt   ← required (or pyproject.toml / package.json)
├── .env.example       ← required — list every env var, no real values
├── netlify.toml       ← if it's a deployable blueprint
└── src/ or notebooks/ ← your code
```

### 3. README template

Every project needs at minimum:

```markdown
# Project Name

One-sentence description of what it does.

## What it does

3–5 bullet points.

## Quick start

\`\`\`bash
cp .env.example .env
# fill in your keys
pip install -r requirements.txt
python main.py
\`\`\`

## Stack

- Python 3.11+
- [list key deps]

## Related course content

Link to the relevant TLC article or course module.
```

### 4. .env.example format

```bash
# Required
OPENAI_API_KEY=your_openai_key_here

# Optional — for inference via Novita AI (cheaper alternative)
# https://novita.ai/?ref=mzblm2z&utm_source=affiliate
NOVITA_API_KEY=your_novita_key_here
```

### 5. Open a PR

- Title: `feat: add [your-project-name]`
- Description: what it does, what stack it uses, link to any related article
- One project per PR

## Code style

- Python: follow what's already in the repo (no strict linter enforced, just be readable)
- Notebooks: clear outputs before committing
- No hardcoded API keys — ever

## Questions?

Open a [Discussion](https://github.com/iamdgarcia/the-learning-curve/discussions) before building something big. Saves everyone time.
