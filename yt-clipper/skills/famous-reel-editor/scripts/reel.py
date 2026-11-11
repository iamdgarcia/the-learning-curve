#!/usr/bin/env python3
"""
Pipeline D — famous-reel-editor
Turn a raw vertical talking-head clip into a finished 9:16 reel.

Usage:
  python reel_gen.py --clip path/to/raw.mp4 [--name myname]
                     [--transcriber groq|local|elevenlabs]
                     [--step N]          # resume from step N (1-based)
                     [--upload] [--privacy unlisted|public|private]

Steps (run in order; script pauses at review points):
  1  Transcribe raw clip
  2  Build EDL (auto-cut pauses ≥ 0.20s)   ← REVIEW: edit edl.json before continuing
  3  Silence-trim EDL
  4  Cut & join (render cutF.mp4)
  5  Generate cards HTML  (npx hyperframes render)
  6  Burn karaoke captions
  7  Compose final reel (face + cards + captions + music)
  8  Upload to YouTube  (only if --upload)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
import argparse
import os
import pathlib
import subprocess
import sys

SKILL = pathlib.Path(__file__).parent / "skills" / "famous-reel-editor"
SCRIPTS = SKILL / "scripts"
REELS_DIR = pathlib.Path(__file__).parent / "temp" / "reels"


def run(cmd: str, cwd: pathlib.Path | None = None, check: bool = True) -> int:
    print(f"\n$ {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    if check and result.returncode != 0:
        sys.exit(f"Command failed (exit {result.returncode}): {cmd}")
    return result.returncode


def pause(msg: str) -> None:
    print(f"\n{'='*60}")
    print(f"  REVIEW STEP: {msg}")
    print(f"{'='*60}")
    input("  Press Enter when ready to continue...\n")


def main() -> None:
    ap = argparse.ArgumentParser(description="Pipeline D — famous-reel-editor")
    ap.add_argument("--clip",        required=True, help="Path to raw vertical talking-head clip")
    ap.add_argument("--name",        default="",    help="Project name (default: clip filename stem)")
    ap.add_argument("--transcriber", default="elevenlabs", choices=["elevenlabs", "groq", "local"])
    ap.add_argument("--step",        type=int, default=1, help="Resume from step N")
    ap.add_argument("--upload",      action="store_true")
    ap.add_argument("--privacy",     default="unlisted", choices=["unlisted", "public", "private"])
    args = ap.parse_args()

    clip = pathlib.Path(args.clip).resolve()
    if not clip.exists():
        sys.exit(f"Clip not found: {clip}")

    name = args.name or clip.stem
    proj = REELS_DIR / name
    proj.mkdir(parents=True, exist_ok=True)

    transcriber_script = {
        "elevenlabs": SCRIPTS / "transcribe.py",
        "groq":       SCRIPTS / "transcribe_groq.py",
        "local":      SCRIPTS / "transcribe_local.py",
    }[args.transcriber]

    raw_json   = proj / "raw_transcript.json"
    edl_json   = proj / "edl.json"
    edl2_json  = proj / "edl2.json"   # after silence_keep
    cut_mp4    = proj / "cutF.mp4"
    cap_json   = proj / "cutF_cap.json"
    cards_dir  = proj / "cards"
    cards_mp4  = cards_dir / "cards_all.mp4"
    capt_dir   = proj / "capt"
    final_mp4  = proj / f"{name}-FINAL.mp4"

    step = args.step

    # ── Step 1: Transcribe ────────────────────────────────────────────────
    if step <= 1:
        print("\n[Step 1/7] Transcribing...")
        run(f"python3 {transcriber_script} {clip} {raw_json}")

    # ── Step 2: Build EDL ─────────────────────────────────────────────────
    if step <= 2:
        print("\n[Step 2/7] Building EDL (auto-cut pauses ≥ 0.20s)...")
        run(f"python3 {SCRIPTS / 'make_edl.py'} {raw_json} {clip} {edl_json}")
        pause(
            f"Edit {edl_json} to exclude stumble windows.\n"
            f"  Add exclude ranges like: python3 {SCRIPTS/'make_edl.py'} ... exclude='67.5-83.5'\n"
            f"  Then press Enter."
        )

    # ── Step 3: Silence-trim ──────────────────────────────────────────────
    if step <= 3:
        print("\n[Step 3/7] Silence-trimming EDL...")
        run(f"python3 {SCRIPTS / 'silence_keep.py'} {edl_json} {clip} {edl2_json}")

    # ── Step 4: Cut & join ────────────────────────────────────────────────
    if step <= 4:
        print("\n[Step 4/7] Cutting & joining clip...")
        # cutjoin.py reads edl2.json and writes cutF.mp4
        run(f"python3 {SCRIPTS / 'cutjoin.py'} {edl2_json} {cut_mp4}")
        # Copy transcript for caption patching (user can fix transcriber errors here)
        import shutil
        shutil.copy(edl2_json, cap_json)
        print(f"\n  Caption transcript written to: {cap_json}")
        print(f"  Patch any transcriber errors in that JSON (e.g. 'Cloud' → 'Claude') before continuing.")
        pause("Review/patch cap_json, then press Enter.")

    # ── Step 5: Cards (gen.py + hyperframes) ─────────────────────────────
    if step <= 5:
        print("\n[Step 5/7] Generating cards + rendering with hyperframes...")
        cards_dir.mkdir(exist_ok=True)
        run(f"python3 {SCRIPTS / 'gen.py'} {cap_json}", cwd=cards_dir)
        run(f"npx --yes hyperframes render . -o {cards_mp4}", cwd=cards_dir)

    # ── Step 6: Captions ──────────────────────────────────────────────────
    if step <= 6:
        print("\n[Step 6/7] Burning karaoke captions...")
        capt_dir.mkdir(exist_ok=True)
        run(f"python3 {SCRIPTS / 'captions.py'} {cap_json} {capt_dir} 12 92")

    # ── Step 7: Compose ───────────────────────────────────────────────────
    if step <= 7:
        print("\n[Step 7/7] Composing final reel...")
        print("  Tune crop_y so the face sits in the UPPER part of the lower band.")
        print("  Test a few values:")
        print(f"    ffmpeg -ss 5 -i {cut_mp4} -vf 'scale=1080:-2,crop=1080:1056:0:120' -frames:v 1 /tmp/test_120.jpg")
        print(f"    ffmpeg -ss 5 -i {cut_mp4} -vf 'scale=1080:-2,crop=1080:1056:0:200' -frames:v 1 /tmp/test_200.jpg")
        crop_y = input("\n  Enter crop_y (default 200): ").strip() or "200"
        music  = os.environ.get("MUSIC", str(SKILL / "assets" / "bg-music.m4a"))
        run(
            f"bash {SCRIPTS / 'compose.sh'} "
            f"{cut_mp4} {cards_mp4} {capt_dir} {final_mp4} {crop_y}",
            check=False,  # compose.sh exits 0 even with warnings
        )
        print(f"\n✅ Reel ready: {final_mp4}")

    # ── Step 8: Upload (optional) ─────────────────────────────────────────
    if args.upload:
        print("\n[Step 8] Uploading to YouTube...")
        from src.youtube_uploader import upload_video
        video_id = upload_video(str(final_mp4), title=name, privacy=args.privacy)
        print(f"✅ Uploaded: https://www.youtube.com/watch?v={video_id}")


if __name__ == "__main__":
    main()
