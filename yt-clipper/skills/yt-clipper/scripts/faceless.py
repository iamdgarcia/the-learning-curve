"""
Faceless YouTube Short generator — brand-styled, trend-driven, Spanish.

Usage:
  python faceless_gen.py                              # LLM picks trending topic
  python faceless_gen.py --topic "Claude vs GPT-4o"  # custom topic
  python faceless_gen.py --upload                     # upload to YouTube after
  python faceless_gen.py --tiktok                     # copy to temp/tiktok/
  python faceless_gen.py --dry-run                    # script only, no video
  python faceless_gen.py --voice es-ES-ElviraNeural   # female voice
  python faceless_gen.py --brand config/faceless_brand.json  # custom brand file

Brand config: config/faceless_brand.json
  Edit channel_handle, accent_color, channel_niche, tts_voice, etc.
"""
import argparse
import logging
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# Run from project root
# chdir to project root so src/ and config/ are reachable
os.chdir(Path(__file__).resolve().parent.parent.parent)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from src import brand_config as bc
from src.trend_finder import get_trending_topics
from src.script_writer import write_script
from src.visual_planner import plan as plan_visuals
from src.slide_reviewer import review_plan
from src import tts as tts_module
from src.faceless_composer import compose
from src.subtitle_generator import CaptionStyle


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate faceless YouTube Shorts")
    ap.add_argument("--topic",    help="Custom topic (skips trend discovery)")
    ap.add_argument("--hook",     default="", help="Suggested opening hook")
    ap.add_argument("--voice",    help="TTS voice (overrides brand config)")
    ap.add_argument("--duration", type=int, default=55, help="Target seconds (default 55)")
    ap.add_argument("--brand",    default="config/faceless_brand.json", help="Brand config path")
    ap.add_argument("--upload",   action="store_true", help="Upload to YouTube after rendering")
    ap.add_argument("--privacy",  default=None, choices=["public", "unlisted", "private"])
    ap.add_argument("--tiktok",   action="store_true", help="Copy output to temp/tiktok/")
    ap.add_argument("--dry-run",  action="store_true", help="Print script only, no video/audio")
    args = ap.parse_args()

    brand   = bc.load(args.brand)
    voice   = args.voice or brand.tts_voice
    privacy = args.privacy or brand.default_privacy
    out_dir = Path("temp")
    out_dir.mkdir(exist_ok=True)
    ts      = datetime.now().strftime("%Y%m%d_%H%M%S")

    # ── 1. Topic ──────────────────────────────────────────────────────────────
    if args.topic:
        topic = args.topic
        hook  = args.hook
        log.info(f"[1/5] Topic: {topic}")
    else:
        log.info("[1/5] Discovering trending topics...")
        ideas = get_trending_topics(n=5)
        for i, idea in enumerate(ideas, 1):
            log.info(f"  {i}. [{idea.get('score',0)}/10] {idea.get('topic','')} "
                     f"— {idea.get('hook','')[:60]}")
        best  = ideas[0]
        topic = best["topic"]
        hook  = best.get("hook", "")
        log.info(f"  → Selected: {topic}")

    # ── 2. Script ─────────────────────────────────────────────────────────────
    log.info("[2/5] Writing script...")
    data        = write_script(topic, hook=hook, target_duration_s=args.duration)
    script_text = data["script"]
    sections    = data.get("sections", [])   # [{label, title, text}]
    yt_title    = data["title"]
    description = data.get("description", "")
    tags        = data.get("tags", [])

    # topic_label for the top bar: extract from topic string ("X vs Y" → "X · Y")
    topic_label = brand.channel_niche
    import re as _re
    vs_match = _re.split(r'\bvs\.?\b|\bversus\b', topic, flags=_re.IGNORECASE)
    if len(vs_match) >= 2:
        left  = vs_match[0].strip().split()[0].upper()
        right = vs_match[1].strip().split()[0].upper()
        topic_label = f"{left} · {right}"
    elif sections and len(sections) >= 2:
        # fallback: first 2 meaningful words of topic (skip articles)
        _stop = {"el", "la", "los", "las", "un", "una", "de", "del", "en", "por", "que"}
        _words = [w for w in topic.split() if w.lower() not in _stop]
        topic_label = " · ".join(_words[:2]).upper()

    log.info(f"  Title   : {yt_title}")
    log.info(f"  Sections: {[s.get('label','') for s in sections]}")
    log.info(f"  Script  : {len(script_text.split())} words")

    # ── 2b. Visual plan ───────────────────────────────────────────────────────
    visual_plan = None
    if not args.dry_run:
        log.info("[2b/5] Visual planning...")
        visual_plan = plan_visuals(topic, sections)

        log.info("[2c/5] Reviewing slides...")
        visual_plan = review_plan(visual_plan, sections, topic)

    if args.dry_run:
        print("\n── SCRIPT ──────────────────────────────────────────────────")
        print(script_text)
        print("────────────────────────────────────────────────────────────")
        for i, s in enumerate(sections):
            print(f"\n[{i}] {s.get('label','')} — {s.get('title','')}")
            print(s.get("text", "")[:120])
        return

    # Fallback: if LLM didn't return sections, split naively
    if not sections:
        log.warning("No sections returned — using single-section fallback")
        sections = [{"label": "idea", "title": topic.upper()[:30], "text": script_text}]

    # ── 3. TTS ────────────────────────────────────────────────────────────────
    log.info(f"[3/5] TTS ({voice})...")
    audio_path = out_dir / f"faceless_{ts}_audio.mp3"
    _, word_events = tts_module.generate_with_timestamps(
        script_text, str(audio_path), voice=voice, rate=brand.tts_rate
    )

    # ── 4. Compose video ──────────────────────────────────────────────────────
    log.info("[4/5] Composing video...")
    video_path = out_dir / f"faceless_{ts}.mp4"
    compose(
        audio_path   = str(audio_path),
        output_path  = str(video_path),
        sections     = sections,
        visual_plan  = visual_plan,
        topic_label  = topic_label,
        brand        = brand,
        caption_style= CaptionStyle.karaoke,
        word_events  = word_events,
    )
    audio_path.unlink(missing_ok=True)

    # ── 5. TikTok copy ────────────────────────────────────────────────────────
    if args.tiktok or brand.tiktok_enabled:
        tiktok_dir = out_dir / "tiktok"
        tiktok_dir.mkdir(exist_ok=True)
        dst = tiktok_dir / video_path.name
        shutil.copy2(video_path, dst)
        log.info(f"[TikTok] Ready → {dst}")

    # ── 6. Upload ─────────────────────────────────────────────────────────────
    if args.upload:
        log.info("[5/5] Uploading to YouTube...")
        from src import youtube_uploader
        result = youtube_uploader.upload(
            file_path   = str(video_path),
            title       = yt_title,
            description = description,
            tags        = tags,
            privacy     = privacy,
        )
        log.info(f"  ✅ {result['url']}")
    else:
        log.info(f"[5/5] Done — {video_path} (add --upload to publish)")


if __name__ == "__main__":
    main()
