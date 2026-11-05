"""
Interview-style animated explainer generator.
Produces dynamic CS/AI videos like KodeKloud / ByteByteGo — in Spanish.

Usage:
  python interview_gen.py --topic "¿Qué es un Bloom Filter?"
  python interview_gen.py                        # LLM picks trending CS/AI topic
  python interview_gen.py --upload --privacy unlisted
  python interview_gen.py --dry-run              # script only

Output: temp/interview_TIMESTAMP.mp4
"""
import argparse, logging, os, sys
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

os.chdir(Path(__file__).parent)
sys.path.insert(0, str(Path(__file__).parent))

from src.interview_writer import write as write_script
from src.animation_renderer import render as render_animation
from src import tts as tts_module
from src.brand_config import load as load_brand


_TOPIC_PROMPT = """
Sugiere UN tema para un YouTube Short educativo sobre IA en español.
Canal: @TheLearningCurveAI (Daniel García) — nicho: LLMs, agentes, RAG, embeddings, transformers, 
modelos de lenguaje, APIs de IA, herramientas como LangChain/MCP/OpenAI.
Elige algo técnico pero accesible, trending en la comunidad IA/dev hispana.
Formato: pregunta de entrevista o concepto clave que un dev de IA debería saber.
Responde SOLO con el tema. Ej: "¿Cómo funciona la atención en un Transformer?"
"""


def _pick_topic() -> str:
    from openai import OpenAI
    from src.config import settings
    client = OpenAI(api_key=settings.novita_api_key, base_url=settings.novita_base_url)
    r = client.chat.completions.create(
        model=settings.novita_model,
        messages=[{"role": "user", "content": _TOPIC_PROMPT}],
        temperature=0.9, max_tokens=30,
    )
    return r.choices[0].message.content.strip().strip('"')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic",   help="CS/AI concept to explain")
    ap.add_argument("--duration", type=int, default=55)
    ap.add_argument("--voice",   default=None)
    ap.add_argument("--upload",  action="store_true")
    ap.add_argument("--privacy", default="unlisted")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--brand",   default="config/faceless_brand.json")
    args = ap.parse_args()

    brand = load_brand(args.brand)
    voice = args.voice or brand.tts_voice
    out_dir = Path("temp"); out_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    # ── 1. Topic ──────────────────────────────────────────────────────────────
    if args.topic:
        topic = args.topic
    else:
        log.info("[1/4] Picking topic...")
        topic = _pick_topic()
    log.info(f"[1/4] Topic: {topic}")

    # ── 2. Script ─────────────────────────────────────────────────────────────
    log.info("[2/4] Writing script...")
    data     = write_script(topic, duration_s=args.duration)
    narration = data["narration"]
    sections  = data["sections"]
    yt_title  = data["yt_title"]
    desc      = data.get("description", "")
    tags      = data.get("tags", [])

    log.info(f"  Title: {yt_title}")
    log.info(f"  Narration: {len(narration.split())} words, {len(sections)} sections")
    for s in sections:
        log.info(f"  [{s['start_s']}s–{s['end_s']}s] {s['title']}")

    if args.dry_run:
        print("\n── NARRATION ───────────────────────────────────────")
        print(narration)
        print("────────────────────────────────────────────────────")
        return

    # ── 3. TTS ────────────────────────────────────────────────────────────────
    log.info(f"[3/4] TTS ({voice})...")
    audio_path = out_dir / f"interview_{ts}_audio.mp3"
    _, word_events = tts_module.generate_with_timestamps(
        narration, str(audio_path), voice=voice, rate=brand.tts_rate
    )

    # Get actual audio duration
    import json, subprocess
    probe = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", str(audio_path)],
        capture_output=True, text=True, check=True,
    )
    audio_duration = float(json.loads(probe.stdout)["streams"][0]["duration"])
    log.info(f"  Audio duration: {audio_duration:.1f}s")

    # Update section end times to match actual audio duration
    # (proportional scale if script ran long/short)
    script_total = sections[-1]["end_s"] if sections else args.duration
    scale = audio_duration / script_total
    for s in sections:
        s["start_s"] = round(s["start_s"] * scale, 1)
        s["end_s"]   = round(s["end_s"]   * scale, 1)

    # ── 4. Render animation ───────────────────────────────────────────────────
    log.info("[4/4] Generating animation (Claude → Playwright)...")
    video_path = out_dir / f"interview_{ts}.mp4"
    work_dir   = out_dir / f"interview_{ts}_work"

    # CTA starts at the last section
    cta_start_s = sections[-1]["start_s"] if sections else None
    log.info(f"  CTA starts at {cta_start_s:.1f}s (fixed slide replaces Claude's CTA)")

    render_animation(
        topic          = topic,
        sections       = sections,
        audio_path     = audio_path,
        audio_duration = audio_duration,
        output_path    = video_path,
        channel_handle = brand.channel_handle,
        work_dir       = work_dir,
        cta_start_s    = cta_start_s,
        word_events    = word_events,
    )

    # audio kept alive through render (Whisper needs it); delete after
    audio_path.unlink(missing_ok=True)

    # ── 5. Upload ─────────────────────────────────────────────────────────────
    if args.upload:
        from src import youtube_uploader
        result = youtube_uploader.upload(
            file_path=str(video_path), title=yt_title,
            description=desc, tags=tags, privacy=args.privacy,
        )
        log.info(f"✅ {result['url']}")
    else:
        log.info(f"Done → {video_path}  (add --upload to publish)")


if __name__ == "__main__":
    main()
