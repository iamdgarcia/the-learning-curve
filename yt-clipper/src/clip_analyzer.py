"""
Two-agent clip pipeline:
  Agent 1 (Finder)   — scans transcript, proposes candidate clips with rationale
  Agent 2 (Reviewer) — scores each candidate, rejects weak ones, refines timestamps,
                        writes final titles/descriptions/tags
"""
import logging
from enum import Enum
from openai import OpenAI
from pydantic import BaseModel, Field
from src.config import settings

log = logging.getLogger(__name__)

# ── Clip modes ─────────────────────────────────────────────────────────────────

class ClipMode(str, Enum):
    shorts   = "shorts"    # 30–90 s, vertical energy, hook in first 3 s
    standard = "standard"  # 2–8 min, educational/narrative arc
    emotion  = "emotion"   # 30–90 s, prioritises emotional peaks & reactions
    topic    = "topic"     # 30–90 s, filtered to a specific topic/keyword


CLIP_MODE_CONFIG = {
    ClipMode.shorts:   {"min": 30,  "max": 90,  "label": "YouTube Short (30–90 s)"},
    ClipMode.standard: {"min": 120, "max": 480, "label": "Standard clip (2–8 min)"},
    ClipMode.emotion:  {"min": 30,  "max": 90,  "label": "Emotional moment (30–90 s)"},
    ClipMode.topic:    {"min": 30,  "max": 90,  "label": "Topic clip (30–90 s)"},
}

# ── Pydantic schemas ───────────────────────────────────────────────────────────

class CandidateClip(BaseModel):
    clip_id: int
    start_seconds: int
    end_seconds: int
    start_time: str          # HH:MM:SS
    end_time: str
    rationale: str           # why this moment is worth clipping
    hook: str                # the opening line / strongest sentence


class CandidatesResponse(BaseModel):
    candidates: list[CandidateClip]


class ReviewedClip(BaseModel):
    clip_id: int
    start_seconds: int       # reviewer may adjust ±5 s for cleaner cut
    end_seconds: int
    start_time: str
    end_time: str
    score: int = Field(..., ge=1, le=10, description="Virality / retention score")
    approved: bool
    rejection_reason: str = ""
    title: str               # ≤100 chars, hook-first
    description: str         # ≤500 chars with hashtags
    tags: list[str]
    hook: str                # refined opening line


class ReviewResponse(BaseModel):
    reviewed: list[ReviewedClip]


# Final public model (only approved clips, stripped of internal fields)
class Clip(BaseModel):
    clip_id: int
    start_seconds: int
    end_seconds: int
    start_time: str
    end_time: str
    title: str
    description: str
    tags: list[str]
    hook: str
    score: int
    mode: str


class ClipsResponse(BaseModel):
    clips: list[Clip]


# ── LLM client ────────────────────────────────────────────────────────────────

def _client() -> OpenAI:
    if not settings.novita_api_key:
        raise RuntimeError("NOVITA_API_KEY not set in .env")
    return OpenAI(api_key=settings.novita_api_key, base_url=settings.novita_base_url)


def _chat(client: OpenAI, system: str, user: str, schema: type) -> object:
    """Call LLM and parse into Pydantic schema. Strips markdown fences if present."""
    response = client.chat.completions.create(
        model=settings.novita_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.3,
    )
    raw = response.choices[0].message.content.strip()
    # Strip markdown code fences if model wraps JSON
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    return schema.model_validate_json(raw)


# ── Agent 1: Finder ───────────────────────────────────────────────────────────

FINDER_SYSTEM = """\
You are a senior YouTube content strategist specializing in clipping live streams \
and long-form videos into high-retention short clips.

Your job: scan the timestamped transcript and identify the BEST candidate moments. \
Be generous — propose more candidates than needed; a reviewer will filter them.

Rules:
- Each clip must be self-contained (viewer needs no prior context).
- Prioritize: strong hooks, surprising facts, emotional peaks, actionable tips, \
  controversial takes, story climaxes.
- Avoid: intros/outros, sponsor reads, dead air, incomplete thoughts.
- Times must align EXACTLY with transcript timestamps — never interpolate.
- IMPORTANT: The metadata language is {language}. Write rationale and hook in {language}.

Return ONLY valid JSON. No markdown. No commentary.
"""

FINDER_USER = """\
Channel context: {channel_context}
Clip mode: {mode_label}
Clip duration: {min_dur}–{max_dur} seconds
Max candidates to propose: {max_candidates}
Metadata language: {language} — write all text fields in this language.

Transcript:
{transcript}

Return JSON:
{{
  "candidates": [
    {{
      "clip_id": <int starting at 1>,
      "start_seconds": <int>,
      "end_seconds": <int>,
      "start_time": "<HH:MM:SS>",
      "end_time": "<HH:MM:SS>",
      "rationale": "<why this moment pops>",
      "hook": "<the strongest opening sentence verbatim from transcript>"
    }}
  ]
}}
"""

# ── Agent 2: Reviewer ─────────────────────────────────────────────────────────

REVIEWER_SYSTEM = """\
You are a harsh but fair YouTube clip curator. You receive candidate clips and \
decide which ones are worth publishing.

Your job:
1. Score each clip 1–10 for virality + retention potential.
2. Approve clips scoring ≥ 7. Reject the rest with a brief reason.
3. Fine-tune start/end by ±10 s if it gives a cleaner cut (cold open, clean ending).
4. Write a punchy title (hook-first, ≤100 chars), description (≤500 chars, hashtags), \
   tags, and refine the hook line.
5. IMPORTANT: Write ALL text (title, description, rejection_reason, hook, tags) in {language}. \
   Do NOT translate into English or any other language.

For {mode_label}:
{mode_instructions}

Return ONLY valid JSON. No markdown.
"""

REVIEWER_USER = """\
Candidates to review (clip mode: {mode_label}, metadata language: {language}):
{candidates_json}

Return JSON:
{{
  "reviewed": [
    {{
      "clip_id": <int>,
      "start_seconds": <int>,
      "end_seconds": <int>,
      "start_time": "<HH:MM:SS>",
      "end_time": "<HH:MM:SS>",
      "score": <1–10>,
      "approved": <true|false>,
      "rejection_reason": "<empty string if approved>",
      "title": "<hook-first title>",
      "description": "<description with hashtags>",
      "tags": ["tag1", "tag2", ...],
      "hook": "<refined opening line>"
    }}
  ]
}}
"""

MODE_INSTRUCTIONS = {
    ClipMode.shorts: (
        "Shorts need a HOOK in the first 3 seconds — viewer must be grabbed instantly. "
        "Prefer tight, punchy moments. Penalize clips that open with a slow buildup. "
        "Title should read like a scroll-stopper."
    ),
    ClipMode.standard: (
        "Standard clips should have a clear 3-part arc: setup → insight → payoff. "
        "Prefer educational depth over pure virality. "
        "Title should promise clear value (what the viewer will learn/gain)."
    ),
    ClipMode.emotion: (
        "Prioritise moments of strong emotion: surprise, laughter, frustration → resolution, "
        "genuine excitement, vulnerability, or a clear \u2018aha\u2019 moment. "
        "The emotional beat must be visible within the first 5 seconds. "
        "Score highly: audible reactions, unexpected turns, relatable human moments. "
        "Score low: dry technical explanations with no emotional colour."
    ),
    ClipMode.topic: (
        "Select only clips that are directly about the topic: {topic}. "
        "Reject any clip where the topic is only mentioned in passing. "
        "Prefer self-contained explanations a viewer can understand without prior context. "
        "Title should name the topic explicitly."
    ),
}


def _seconds_to_ts(s: int) -> str:
    return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"


# ── Public API ────────────────────────────────────────────────────────────────

def analyze(
    transcript_text: str,
    max_clips: int = 5,
    mode: ClipMode = ClipMode.shorts,
    channel_context: str = "",
    language: str = "Spanish",
    topic: str = "",   # used when mode=topic
) -> ClipsResponse:
    """
    Run the two-agent pipeline.
    Returns only approved clips, sorted by score descending, capped at max_clips.
    """
    cfg = CLIP_MODE_CONFIG[mode]
    client = _client()

    # Build system prompts upfront
    finder_system = FINDER_SYSTEM.format(language=language)

    mode_instructions = MODE_INSTRUCTIONS[mode]
    if mode == ClipMode.topic:
        mode_instructions = mode_instructions.format(topic=topic or "the main subject")

    reviewer_system = REVIEWER_SYSTEM.format(
        mode_label=cfg["label"],
        mode_instructions=mode_instructions,
        language=language,
    )

    # ── Agent 1: find candidates (ask for 2× to give reviewer room to filter)
    log.info(f"[Agent 1] Finding candidates ({mode.value} mode)...")
    finder_prompt = FINDER_USER.format(
        channel_context=channel_context,
        mode_label=cfg["label"],
        min_dur=cfg["min"],
        max_dur=cfg["max"],
        max_candidates=max_clips * 2,
        transcript=transcript_text,
        language=language,
    )
    candidates: CandidatesResponse = _chat(client, finder_system, finder_prompt, CandidatesResponse)
    log.info(f"[Agent 1] Proposed {len(candidates.candidates)} candidates.")

    # ── Agent 2: review & filter
    log.info("[Agent 2] Reviewing candidates...")
    import json
    candidates_json = json.dumps(
        [c.model_dump() for c in candidates.candidates], indent=2
    )
    reviewer_prompt = REVIEWER_USER.format(
        mode_label=cfg["label"],
        candidates_json=candidates_json,
        language=language,
    )
    mode_instructions = MODE_INSTRUCTIONS[mode]
    if mode == ClipMode.topic:
        mode_instructions = mode_instructions.format(topic=topic or "the main subject")

    finder_system  = FINDER_SYSTEM.format(language=language)
    reviewer_system = REVIEWER_SYSTEM.format(
        mode_label=cfg["label"],
        mode_instructions=mode_instructions,
        language=language,
    )
    reviewed: ReviewResponse = _chat(client, reviewer_system, reviewer_prompt, ReviewResponse)

    approved = [r for r in reviewed.reviewed if r.approved]
    rejected = [r for r in reviewed.reviewed if not r.approved]
    log.info(f"[Agent 2] Approved {len(approved)}, rejected {len(rejected)}.")
    for r in rejected:
        log.info(f"  ✗ clip_{r.clip_id}: {r.rejection_reason}")

    # Sort by score, cap at max_clips
    approved.sort(key=lambda r: r.score, reverse=True)
    approved = approved[:max_clips]

    clips = [
        Clip(
            clip_id=r.clip_id,
            start_seconds=r.start_seconds,
            end_seconds=r.end_seconds,
            start_time=r.start_time or _seconds_to_ts(r.start_seconds),
            end_time=r.end_time or _seconds_to_ts(r.end_seconds),
            title=r.title,
            description=r.description,
            tags=r.tags,
            hook=r.hook,
            score=r.score,
            mode=mode.value,
        )
        for r in approved
    ]

    return ClipsResponse(clips=clips)
