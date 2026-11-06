#!/usr/bin/env python3
# shortvid: "My 15 favorite Claude skills in 60 seconds" — ORANGE theme
# hook (logo+15+60s stamp) -> 14 rapid skill cards (numbadge+name+15-dot progress)
# -> favorite #15 self-healing -> terminal error->auto-fix -> CTA pills + COMMENT "SKILLS"
import json, re, html, sys

A = "#f0813f"          # accent orange
AB = "#ffa766"         # bright orange
AD = "rgba(240,129,63,0.45)"
GL = "rgba(240,129,63,0.16)"
RED = "#ff5a5a"; REDD = "rgba(255,90,90,0.5)"; GREY = "#8b8f93"

d = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "../edit/tF/transcripts/cutF.json"))
WS = [w for w in d["words"] if w.get("type") != "spacing" and w.get("start") is not None]
TOTAL = round(WS[-1]["end"], 2) + 0.66

# ---- index guard: every anchor verified before building the timeline ----
EXPECT = {1:"15", 3:"Claude", 6:"60", 9:"copywriting", 12:"front-end", 16:"specific",
          21:"N8N", 24:"prompt", 28:"researcher", 31:"compositor", 34:"marketing",
          37:"customer", 41:"know", 47:"trigger.dev", 50:"cost", 54:"scalability",
          57:"security", 61:"favorite", 64:"self-healing", 69:"automatically",
          76:"errors.", 83:"skills", 86:"free,", 88:"come", 90:"skills"}
for idx, txt in EXPECT.items():
    got = WS[idx]["text"]
    assert got == txt, f"anchor mismatch idx {idx}: expected {txt!r} got {got!r}"

def T(i): return round(WS[i]["start"], 2)
def esc(s): return html.escape(s)

N_SKILLS = 15
SKILLS = [  # (num, name, nameword-idx, fontsize-class)
    (1,  "COPYWRITING",        9,  ""),
    (2,  "FRONT-END DESIGN",   12, "md"),
    (3,  "TECH STACK",         16, ""),
    (4,  "N8N",                21, ""),
    (5,  "PROMPT ENGINEERING", 24, "md"),
    (6,  "RESEARCHER",         28, ""),
    (7,  "COMPOSIO",           31, ""),
    (8,  "MARKETING",          34, ""),
    (9,  "CUSTOMER SUPPORT",   37, "md"),
    (10, "KNOW-ME",            41, ""),
    (11, "TRIGGER.DEV",        47, ""),
    (12, "COST REDUCER",       50, ""),
    (13, "SCALABILITY",        54, ""),
    (14, "SECURITY",           57, ""),
]

# beat boundaries (contiguous)
skill_starts = [3.16, 4.62, 6.00, 7.66, 8.78, 10.12, 11.40, 12.76, 14.18, 15.76, 17.68, 19.34, 21.00, 22.56]
FAV_S = 23.78; TERM_S = 26.46; CTA_S = 29.92

beats = []  # (start, end, type, params)
beats.append((0.0, skill_starts[0], "hook", {}))
for k, (num, name, wi, sz) in enumerate(SKILLS):
    e = skill_starts[k + 1] if k + 1 < len(SKILLS) else FAV_S
    beats.append((skill_starts[k], e, "skill", {"num": num, "name": name, "wi": wi, "sz": sz}))
beats.append((FAV_S, TERM_S, "fav", {}))
beats.append((TERM_S, CTA_S, "term", {}))
beats.append((CTA_S, TOTAL, "cta", {}))

def dots(n_on):
    return '<div class="dots">' + "".join(
        f'<span class="dot{" on" if j < n_on else ""}"></span>' for j in range(N_SKILLS)) + "</div>"

def inner(i, t, p):
    if t == "hook":
        return (f'<div class="hookwrap">'
                f'<img src="assets/logos/claude.svg" class="clogo" id="hl{i}"/>'
                f'<div class="hookbig" id="hb{i}">15</div>'
                f'<div class="hooksub" id="hs{i}">CLAUDE SKILLS</div>'
                f'<div class="stamp" id="hst{i}">IN 60 SECONDS</div></div>')
    if t == "skill":
        return (f'<div class="skrow"><div class="numbadge" id="nb{i}">{p["num"]:02d}</div>'
                f'<div class="skname {p["sz"]}" id="sk{i}">{esc(p["name"])}</div></div>'
                f'{dots(p["num"])}')
    if t == "fav":
        return (f'<div class="favtag" id="fv{i}">★ MY FAVORITE</div>'
                f'<div class="skrow"><div class="numbadge big" id="nb{i}">15</div>'
                f'<div class="skname" id="sk{i}">SELF-HEALING</div></div>'
                f'{dots(15)}')
    if t == "term":
        return (f'<div class="term"><div class="tbar"><span class="td r"></span><span class="td y"></span>'
                f'<span class="td g"></span><span class="ttitle">claude</span></div>'
                f'<div class="tbody">'
                f'<div class="tln red" id="t1{i}">✗ Error: build failed</div>'
                f'<div class="tln grey" id="t2{i}">⟳ Claude fixing itself…</div>'
                f'<div class="tln acc" id="t3{i}">✓ Fixed automatically</div>'
                f'</div></div>')
    if t == "cta":
        pills = "".join(f'<span class="pill" id="p{i}x{j}">{esc(n)}</span>'
                        for j, n in enumerate(["COPYWRITING", "N8N", "SECURITY", "SELF-HEALING", "+11 MORE"]))
        return (f'<div class="eyebrow"><span class="ebdot"></span>ALL 15 SKILLS — FREE</div>'
                f'<div class="pills" id="pw{i}">{pills}</div>'
                f'<div class="kw" id="ck{i}">COMMENT<br/><span class="acc">"SKILLS"</span></div>')
    return ""

clips = []; tw = []
for i, (s, e, t, p) in enumerate(beats):
    dur = max(0.6, e - s)
    clips.append(f'<div class="beat" id="beat{i}" data-start="{s}" data-duration="{dur:.2f}" '
                 f'data-track-index="{i+2}"><div class="inner {t}" id="in{i}">{inner(i, t, p)}</div></div>')
    js = [f'tl.fromTo("#beat{i}",{{opacity:0,y:26,scale:0.98}},{{opacity:1,y:0,scale:1,duration:0.18,ease:"power3.out"}},{s:.2f});']
    if t == "hook":
        # logo visible from frame 1; 15 pops on '15', sub on 'Claude', stamp on '60'
        js.append(f'tl.fromTo("#hl{i}",{{opacity:0,scale:0.7}},{{opacity:1,scale:1,duration:0.28,ease:"back.out(1.8)"}},0.02);')
        js.append(f'tl.fromTo("#hb{i}",{{opacity:0,scale:1.9}},{{opacity:1,scale:1,duration:0.3,ease:"back.out(2.2)"}},{T(1):.2f});')
        js.append(f'tl.fromTo("#hs{i}",{{opacity:0,y:26}},{{opacity:1,y:0,duration:0.28,ease:"power3.out"}},{T(3):.2f});')
        js.append(f'tl.fromTo("#hst{i}",{{opacity:0,scale:1.7,rotate:-9}},{{opacity:1,scale:1,rotate:-5,duration:0.28,ease:"back.out(2)"}},{T(6):.2f});')
    if t == "skill":
        js.append(f'tl.fromTo("#nb{i}",{{opacity:0,scale:0.55}},{{opacity:1,scale:1,duration:0.24,ease:"back.out(2.2)"}},{s+0.04:.2f});')
        js.append(f'tl.fromTo("#sk{i}",{{opacity:0,x:-44}},{{opacity:1,x:0,duration:0.26,ease:"power3.out"}},{max(s+0.06, T(p["wi"])-0.05):.2f});')
    if t == "fav":
        js.append(f'tl.fromTo("#fv{i}",{{opacity:0,scale:1.5}},{{opacity:1,scale:1,duration:0.26,ease:"back.out(2)"}},{T(61):.2f});')
        js.append(f'tl.fromTo("#nb{i}",{{opacity:0,scale:0.55}},{{opacity:1,scale:1,duration:0.26,ease:"back.out(2.2)"}},{s+0.05:.2f});')
        js.append(f'tl.fromTo("#sk{i}",{{opacity:0,x:-44}},{{opacity:1,x:0,duration:0.3,ease:"power3.out"}},{T(64):.2f});')
    if t == "term":
        js.append(f'tl.fromTo("#t1{i}",{{opacity:0,y:12}},{{opacity:1,y:0,duration:0.2,ease:"power3.out"}},{s+0.15:.2f});')
        js.append(f'tl.fromTo("#t2{i}",{{opacity:0,y:12}},{{opacity:1,y:0,duration:0.2,ease:"power3.out"}},{T(69):.2f});')
        js.append(f'tl.fromTo("#t3{i}",{{opacity:0,y:12,scale:0.94}},{{opacity:1,y:0,scale:1,duration:0.24,ease:"back.out(1.8)"}},{T(76)-0.25:.2f});')
    if t == "cta":
        for j in range(5):
            js.append(f'tl.fromTo("#p{i}x{j}",{{opacity:0,y:18,scale:0.85}},{{opacity:1,y:0,scale:1,duration:0.2,ease:"back.out(1.9)"}},{s+0.15+j*0.18:.2f});')
        js.append(f'tl.to("#pw{i}",{{opacity:0.35,duration:0.25}},{T(88):.2f});')
        js.append(f'tl.fromTo("#ck{i}",{{opacity:0,scale:1.4}},{{opacity:1,scale:1,duration:0.28,ease:"back.out(2)"}},{T(88):.2f});')
    if i < len(beats) - 1:
        js.append(f'tl.to("#beat{i}",{{opacity:0,duration:0.14,ease:"power2.in"}},{e-0.14:.2f});')
    tw.append("\n      ".join(js))

NP = 22
parts_html = "".join(
    f'<span class="pt" id="pt{k}" style="left:{(k*131+40)%1040}px;top:{(k*97+30)%760}px;'
    f'width:{5+(k%3)*3}px;height:{5+(k%3)*3}px;opacity:{0.12+0.2*((k*7)%5)/5:.2f}"></span>' for k in range(NP))
streaks_html = "".join(f'<span class="stk" id="stk{k}" style="top:{120+k*230}px"></span>' for k in range(3))
bg = ['tl.to("#glow",{x:120,y:30,scale:1.15,duration:6,yoyo:true,repeat:9,ease:"sine.inOut"},0);',
      'tl.to("#grid",{backgroundPosition:"0px 110px",duration:6,ease:"none",repeat:9},0);']
for k in range(NP):
    du = 4 + (k % 5)
    bg.append(f'tl.to("#pt{k}",{{y:-{120+(k%4)*60},duration:{du},ease:"none",repeat:{int(60/du)+1}}},0);')
    bg.append(f'tl.to("#pt{k}",{{opacity:0,duration:{du},yoyo:true,repeat:{int(60/du)+1},ease:"sine.inOut"}},0);')
for k in range(3):
    bg.append(f'tl.fromTo("#stk{k}",{{x:-1200}},{{x:1200,duration:{5+k*2},ease:"none",repeat:9}},{k*1.5});')

HTML = f'''<!doctype html><html lang="en"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=1080, height=1920"/>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:1080px;height:1920px;overflow:hidden;background:#000;font-family:"Montserrat","Inter",sans-serif}}
#root{{position:relative;width:1080px;height:1920px}}
#bgz{{position:absolute;top:0;left:0;width:1080px;height:864px;overflow:hidden}}
#grid{{position:absolute;inset:-40px;background-image:linear-gradient(rgba(240,129,63,0.05) 1px,transparent 1px),linear-gradient(90deg,rgba(240,129,63,0.05) 1px,transparent 1px);background-size:110px 110px}}
#glow{{position:absolute;top:120px;left:280px;width:520px;height:520px;border-radius:50%;background:radial-gradient(circle,rgba(240,129,63,0.26),transparent 65%);filter:blur(22px)}}
.pt{{position:absolute;border-radius:50%;background:{A};box-shadow:0 0 12px {A}}}
.stk{{position:absolute;left:0;width:520px;height:2px;background:linear-gradient(90deg,transparent,{A},transparent);opacity:0.3}}
.beat{{position:absolute;top:0;left:0;width:1080px;height:864px}}
.inner{{position:absolute;top:55px;left:64px;right:64px;height:700px;display:flex;flex-direction:column;justify-content:center;gap:26px}}
.eyebrow{{color:{A};font-size:32px;font-weight:800;letter-spacing:6px;text-transform:uppercase;display:flex;align-items:center;gap:13px}}
.ebdot{{width:14px;height:14px;border-radius:50%;background:{A};box-shadow:0 0 14px {A}}}
/* hook */
.inner.hook{{align-items:center;justify-content:center}}
.hookwrap{{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px}}
.clogo{{height:170px;width:170px;object-fit:contain;filter:drop-shadow(0 0 34px rgba(240,129,63,0.55))}}
.hookbig{{color:#fff;font-size:230px;font-weight:900;line-height:0.85;letter-spacing:-6px;text-shadow:0 0 44px {GL}}}
.hooksub{{color:{A};font-size:54px;font-weight:900;letter-spacing:10px}}
.stamp{{color:#fff;font-size:52px;font-weight:900;border:5px solid {A};border-radius:16px;padding:8px 30px;box-shadow:0 0 34px {GL};text-shadow:0 0 22px {GL};margin-top:12px}}
/* skill cards */
.inner.skill,.inner.fav{{align-items:flex-start;gap:34px}}
.skrow{{display:flex;align-items:center;gap:32px}}
.numbadge{{flex:0 0 auto;width:128px;height:128px;border-radius:28px;background:{A};color:#140a05;font-size:64px;font-weight:900;display:flex;align-items:center;justify-content:center;box-shadow:0 0 36px {A}}}
.numbadge.big{{background:linear-gradient(135deg,{A},{AB});box-shadow:0 0 48px {A}}}
.skname{{color:#fff;font-size:96px;font-weight:900;line-height:0.95;letter-spacing:-2px;text-shadow:0 0 30px {GL}}}
.skname.md{{font-size:76px}}
.dots{{display:flex;gap:14px;flex-wrap:wrap}}
.dot{{width:48px;height:14px;border-radius:7px;background:rgba(255,255,255,0.1)}}
.dot.on{{background:{A};box-shadow:0 0 12px {A}}}
.favtag{{color:#140a05;background:linear-gradient(90deg,{A},{AB});font-size:40px;font-weight:900;letter-spacing:5px;border-radius:14px;padding:12px 28px;box-shadow:0 0 34px {A}}}
/* terminal */
.term{{background:#0f0d0b;border:2px solid {AD};border-radius:20px;overflow:hidden;box-shadow:0 0 40px {GL}}}
.tbar{{display:flex;align-items:center;gap:12px;background:#1b1613;padding:16px 22px;border-bottom:1px solid rgba(255,255,255,0.06)}}
.td{{width:18px;height:18px;border-radius:50%}}.td.r{{background:#ff5f57}}.td.y{{background:#febc2e}}.td.g{{background:#28c840}}
.ttitle{{color:#8f857f;font-size:26px;font-weight:700;margin-left:10px;font-family:ui-monospace,"SF Mono",Menlo,monospace}}
.tbody{{padding:34px 34px;display:flex;flex-direction:column;gap:26px;font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace}}
.tln{{font-size:44px;font-weight:700;line-height:1.3}}
.tln.red{{color:{RED};text-shadow:0 0 18px {REDD}}}
.tln.grey{{color:{GREY}}}
.tln.acc{{color:{A};text-shadow:0 0 18px {AD}}}
/* cta */
.inner.cta{{background:rgba(20,12,7,0.9);border:2px solid {A};border-radius:26px;padding:46px;box-shadow:0 0 46px {GL};gap:30px}}
.pills{{display:flex;flex-wrap:wrap;gap:16px}}
.pill{{color:{A};font-size:36px;font-weight:800;text-transform:uppercase;border:2px solid {AD};border-radius:40px;padding:12px 26px;background:rgba(26,16,10,0.7);box-shadow:0 0 18px {GL}}}
.kw{{color:#fff;font-size:110px;font-weight:900;line-height:1.02;letter-spacing:-2px;text-shadow:0 0 30px {GL}}}
.kw .acc{{color:{A};text-shadow:0 0 30px {A}}}
</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL:.2f}" data-width="1080" data-height="1920">
  <div id="bgz" data-start="0" data-duration="{TOTAL:.2f}" data-track-index="0"><div id="grid"></div><div id="glow"></div>{streaks_html}{parts_html}</div>
  {"".join(clips)}
</div>
<script>window.__timelines=window.__timelines||{{}};const tl=gsap.timeline({{paused:true}});
      {chr(10).join(bg)}
      {chr(10).join(tw)}
window.__timelines["main"]=tl;</script></body></html>'''
open("index.html", "w").write(HTML)
print(f"shortvid: {len(beats)} beats, total {TOTAL}s")
for i, (s, e, t, p) in enumerate(beats):
    print(f"  {s:5.2f}-{e:5.2f} {t:6s} {p.get('name','')}")
