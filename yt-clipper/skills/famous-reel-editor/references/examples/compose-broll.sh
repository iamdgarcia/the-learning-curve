#!/bin/bash
# Compose reel1: talking-head (basso) + card verdi (fascia alta) + 3 B-roll (sopra la faccia,
# coprono la card nelle loro finestre) + sottotitoli karaoke + musica.
set -e
CUT="edit/cutF.mp4"; CARDS="cards/cards_all.mp4"; CAPT="edit/capt"; OUT="renders/reel1-FINAL.mp4"; CY="${1:-120}"
SKILL_DIR="$HOME/.claude/skills/reel-editor"
MUSIC="${MUSIC:-$SKILL_DIR/assets/bg-music.m4a}"
MUSIC_VOL="${MUSIC_VOL:-0.06}"
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$CUT")
FOUT=$(python3 -c "print(max(0,$DUR-2))")
mkdir -p renders

# B-roll: report 8.85-10.65 (portrait) | website 10.65-13.55 (full-bleed) | skills 28.70-32.30 (full-bleed)
cat > /tmp/reel1_fc.txt <<EOF
[0:v]scale=1080:-2,crop=1080:1056:0:$CY[v];
color=c=black:s=1080x1920[bg];
[bg][v]overlay=0:864:shortest=1[stage];
[1:v]crop=1080:864:0:0[ctop];
[stage][ctop]overlay=0:0[wc];
color=c=black:s=1080x864:r=25[blk];
[wc][blk]overlay=0:0:enable='between(t,8.85,13.68)+between(t,28.70,32.36)'[wcb];
[3:v]trim=0:1.85,setpts=PTS-STARTPTS,fps=25,scale=-2:824,setsar=1,setpts=PTS+8.85/TB[bvr];
[wcb][bvr]overlay=(W-w)/2:20:enable='between(t,8.85,10.65)'[wr];
[4:v]trim=0:2.95,setpts=PTS-STARTPTS,fps=25,scale=-2:864,crop=1080:864,setsar=1,setpts=PTS+10.65/TB[bvw];
[wr][bvw]overlay=0:0:enable='between(t,10.65,13.60)'[ww];
[5:v]trim=0:3.75,setpts=PTS-STARTPTS,fps=25,scale=-2:864,crop=1080:864,setsar=1,setpts=PTS+28.70/TB[bvs];
[ww][bvs]overlay=0:0:enable='between(t,28.70,32.34)'[wb];
[wb][2:v]overlay=0:78[final]
EOF

ffmpeg -y -i "$CUT" -i "$CARDS" -framerate 12 -i "$CAPT/%05d.png" -i broll/report.mov -i broll/website.mov -i broll/skills.mov \
 -filter_complex_script /tmp/reel1_fc.txt \
 -map "[final]" -map 0:a -c:v libx264 -preset medium -crf 21 -pix_fmt yuv420p -c:a aac -b:a 160k -shortest "$OUT.noaudio.mp4"

ffmpeg -y -i "$OUT.noaudio.mp4" -i "$MUSIC" -filter_complex \
"[0:a]loudnorm=I=-16:TP=-1.5:LRA=11[vo];[1:a]atrim=start=4,asetpts=PTS-STARTPTS,volume=$MUSIC_VOL,afade=in:st=0:d=0.5,afade=out:st=$FOUT:d=2[m];[vo][m]amix=inputs=2:duration=first:normalize=0[a]" \
-map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -movflags +faststart "$OUT"
rm -f "$OUT.noaudio.mp4"
echo "FATTO -> $OUT"
