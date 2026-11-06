#!/usr/bin/env python3
# Come captions.py ma con OMBRA morbida (no bordo nero duro): la parola bianca resta
# leggibile anche sopra il B-roll bianco del sito. Uso: python captions_shadow.py <json> <out> [fps] [size]
import json, sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

TRANSCRIPT, OUT = sys.argv[1], sys.argv[2]
FPS = int(sys.argv[3]) if len(sys.argv) > 3 else 12
SIZE = int(sys.argv[4]) if len(sys.argv) > 4 else 92
W, H, CY = 1080, 1920, 700
FONT = os.path.expanduser("~/Library/Fonts/Montserrat-VariableFont_wght.ttf")
os.makedirs(OUT, exist_ok=True)
d = json.load(open(TRANSCRIPT))
ws = [w for w in d["words"] if w.get("type") != "spacing" and w.get("start") is not None]
ents = []
for i, w in enumerate(ws):
    a = w["start"]; nxt = ws[i+1]["start"] if i+1 < len(ws) else a+0.4
    b = min(nxt, a+1.0); b = b if b > a else a+0.12
    ents.append((a, b, w["text"].strip().upper()))

def font(sz):
    f = ImageFont.truetype(FONT, sz)
    try: f.set_variation_by_axes([900])
    except Exception: pass
    return f
F = font(SIZE)
total = ws[-1]["end"] + 0.3
n = int(total*FPS)
for i in range(n):
    t = i/FPS; word = next((txt for a, b, txt in ents if a <= t < b), None)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if word:
        dr = ImageDraw.Draw(img); bb = dr.textbbox((0, 0), word, font=F); tw = bb[2]-bb[0]
        x = (W-tw)//2
        # ombra: testo nero su layer separato, sfocato, semi-trasparente -> alone morbido
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ds = ImageDraw.Draw(sh)
        for dx, dy in ((0, 4), (0, 0)):
            ds.text((x+dx, CY+dy), word, font=F, fill=(0, 0, 0, 180))
        sh = sh.filter(ImageFilter.GaussianBlur(9))
        img = Image.alpha_composite(img, sh)
        dr = ImageDraw.Draw(img)
        dr.text((x, CY), word, font=F, fill=(255, 255, 255, 255))
    img.save(f"{OUT}/{i:05d}.png")
print(f"caption frames (shadow): {n} ({len(ents)} parole) -> {OUT}")
