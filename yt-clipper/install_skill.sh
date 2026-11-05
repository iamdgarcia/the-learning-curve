#!/usr/bin/env bash
# Install yt-clipper pi skills (yt-clipper + full OpusClip suite).
# Run once from any directory — resolves repo path automatically.

set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
GLOBAL_BASE="$HOME/.pi/agent/skills"

SKILLS=(
    yt-clipper          # Core skill (existing yt-clipper)
    opusclip            # OpusClip orchestrator
    opusclip-extract    # AI clip extraction (emotion, topic, genre)
    opusclip-caption    # Caption styles (karaoke, wordbox, clean, emoji)
    opusclip-reframe    # Aspect ratios + face tracking + zoom
    opusclip-publish    # YouTube upload + channel batch
    youtube-manager     # Upload + schedule + analytics
)

echo "yt-clipper skill installer"
echo "  Repo: $REPO_DIR"
echo "  Skills: ${SKILLS[*]}"
echo ""

install_global() {
    for skill in "${SKILLS[@]}"; do
        src="$REPO_DIR/skills/$skill"
        dest="$GLOBAL_BASE/$skill"
        [ -d "$src" ] || { echo "  ⚠ Skipping $skill (not found in skills/)"; continue; }
        mkdir -p "$dest/references"
        sed "s|__PROJECT_PATH__|$REPO_DIR|g" "$src/SKILL.md" > "$dest/SKILL.md"
        if [ -d "$src/references" ]; then
            for ref in "$src/references/"*.md; do
                [ -f "$ref" ] && sed "s|__PROJECT_PATH__|$REPO_DIR|g" "$ref" \
                    > "$dest/references/$(basename "$ref")"
            done
        fi
        echo "  ✓ $skill → $dest/"
    done
    echo ""
    echo "Global install complete. Active in all pi sessions."
}

install_local() {
    mkdir -p "$REPO_DIR/.pi/skills"
    for skill in "${SKILLS[@]}"; do
        src="$REPO_DIR/skills/$skill"
        link="$REPO_DIR/.pi/skills/$skill"
        [ -d "$src" ] || continue
        # Patch __PROJECT_PATH__ in-place (only in the repo copy)
        sed -i "s|__PROJECT_PATH__|$REPO_DIR|g" "$src/SKILL.md" 2>/dev/null || true
        ln -sfn "$src" "$link"
        echo "  ✓ .pi/skills/$skill → skills/$skill"
    done
    echo ""
    echo "Local install complete. Active when pi runs inside this repo."
}

case "${1:-global}" in
    global) install_global ;;
    local)  install_local  ;;
    both)   install_global; install_local ;;
    *)
        echo "Usage: $0 [global|local|both]"
        echo "  global  Install to ~/.pi/agent/skills/ (default)"
        echo "  local   Symlink into .pi/skills/ (this repo only)"
        echo "  both    Both of the above"
        exit 1
        ;;
esac

echo "Verify: pi skill list"
echo "Force:  /skill:opusclip"
