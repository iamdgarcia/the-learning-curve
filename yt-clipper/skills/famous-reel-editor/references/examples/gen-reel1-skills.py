#!/usr/bin/env python3
# reel1 v3: hook (4 SKILL -> LOGO CLAUDE grande -> ILLEGALE sotto), count centrato + 4
# blocchi verdi, Humanizer pill con emoji 📄/✍🏻/📧 + risultato centrato senza emoji,
# Prompt Master TERMINALE con typing (TextPlugin), Find Skills no chip, CTA SKILL verde.
import json, re, html, sys
A="#2fe081"; AD="rgba(47,224,129,0.45)"; GL="rgba(47,224,129,0.16)"; RED="#ff5470"; REDD="rgba(255,84,112,0.5)"; GREY="#8b938e"
d=json.load(open(sys.argv[1] if len(sys.argv)>1 else "cut_transcript.json"))
WS=[w for w in d["words"] if w.get("type")!="spacing" and w.get("start") is not None]
TOTAL=round(WS[-1]["end"],2)+0.3
def norm(s): return re.sub(r"[^a-z0-9àèéìòù ]","",s.lower())
TOK=[norm(w["text"]) for w in WS]
def find(trig):
    tt=norm(trig).split()
    for i in range(len(TOK)-len(tt)+1):
        if TOK[i:i+len(tt)]==tt: return round(WS[i]["start"],2)
    for i,t in enumerate(TOK):
        if tt and t==tt[0]: return round(WS[i]["start"],2)
    return 0.0
def find_after(trig, after):
    tt=norm(trig).split()
    for i in range(len(TOK)-len(tt)+1):
        if TOK[i:i+len(tt)]==tt and WS[i]["start"]>=after-0.01: return round(WS[i]["start"],2)
    return after
def esc(s): return html.escape(s)
def eb(e,red=False): return f'<div class="eyebrow{" red" if red else ""}"><span class="ebdot{" red" if red else ""}"></span>{esc(e)}</div>' if e else ""

CONF="scrivimi una mail per un cliente"
PERF="> claude\\n  <role> copywriter B2B </role>\\n  <obiettivo> email di follow-up </obiettivo>\\n  <tono> diretto, pro </tono>"

BEATS=[
 ("Queste quattro","hook",{"quatword":"quattro","claudeword":"rendono Claude","stampword":"illegale"}),
 ("Ne ho costruite","count",{"eyebrow":"NE HO COSTRUITE","count":60,"suffix":"+","unit":"SKILL","countword":"sessanta","blkanchor":"queste quattro"}),
 ("La prima","skilltitle",{"num":"01","name":"FRONTEND SLIDES","chips":["PRESENTAZIONI","REPORT","SITI WEB"],"nameword":"frontend"}),
 ("Humanizer","humanizer",{"num":"02","name":"HUMANIZER","words":[("📄","OUTPUT","output"),("✍🏻","TESTO","testo"),("📧","EMAIL","email")],"fixword":"riscrive","result":"COME LO SCRIVI TU"}),
 ("Prompt Master","terminal",{"num":"03","name":"PROMPT MASTER","confword":"richieste","perfword":"perfetto"}),
 ("Find Skills","skilltitle",{"num":"04","name":"FIND SKILLS","chips":[],"nameword":"find skills"}),
 ("Pesca fra","bigstat",{"eyebrow":"PESCA TRA","count":91000,"unit":"SKILL DISPONIBILI","countword":"novantunomila"}),
 ("Vuoi queste","cta",{"eyebrow":"VUOI LE 4 SKILL?","pre":"COMMENTA: ","acc":"SKILL","ctaword":"commenta"}),
]
starts=[find(t) for t,_,_ in BEATS]; ends=[starts[i+1] for i in range(len(starts)-1)]+[TOTAL]

def inner(i,t,p):
    if t=="hook":
        return (f'<div class="hookwrap">'
                f'<div class="hooks1" id="h1{i}"><div class="hooktop">QUESTE</div><div class="hookbig">4 SKILL</div></div>'
                f'<img src="assets/logos/claude.svg" class="clogobig" id="h2{i}"/>'
                f'<div class="stamp" id="h3{i}">ILLEGALE</div></div>')
    if t=="count":
        blk="".join(f'<span class="cblk" id="b{i}k{j}"><b>{j+1}</b></span>' for j in range(4))
        return (f'{eb(p["eyebrow"])}<div class="statrow ctr"><div class="big" id="big{i}">0</div>'
                f'<div class="unit">{esc(p["unit"])}</div></div>'
                f'<div class="cblocks" id="cb{i}">{blk}</div>')
    if t=="bigstat":
        num=f'{p["count"]:,}'.replace(",",".")+"+"
        return (f'{eb(p["eyebrow"])}<div class="big xl" id="big{i}">{num}</div>'
                f'<div class="unit big2">{esc(p["unit"])}</div>')
    if t=="skilltitle":
        chips="".join(f'<span class="chip" id="b{i}h{j}">{esc(c)}</span>' for j,c in enumerate(p["chips"]))
        cd=f'<div class="chips">{chips}</div>' if p["chips"] else ""
        return (f'<div class="numbadge" id="nb{i}">{esc(p["num"])}</div>'
                f'<div class="skname" id="sk{i}">{esc(p["name"])}</div>{cd}')
    if t=="humanizer":
        pills="".join(f'<span class="hpill" id="b{i}w{j}">{em} {esc(lbl)}</span>' for j,(em,lbl,_) in enumerate(p["words"]))
        return (f'<div class="numbadge" id="nb{i}">{esc(p["num"])}</div>'
                f'<div class="skname" id="sk{i}">{esc(p["name"])}</div>'
                f'<div class="hpills" id="hp{i}">{pills}</div>'
                f'<div class="swaparr" id="ha{i}">↓</div>'
                f'<div class="hres" id="hr{i}">{esc(p["result"])}</div>')
    if t=="terminal":
        return (f'<div class="numbadge sm" id="nb{i}">{esc(p["num"])}</div>'
                f'<div class="skname sm" id="sk{i}">{esc(p["name"])}</div>'
                f'<div class="term">'
                f'<div class="tbar"><span class="td r"></span><span class="td y"></span><span class="td g"></span><span class="ttitle">claude</span></div>'
                f'<div class="tbody">'
                f'<div class="tbad" id="tb{i}"><span class="tlabel bad">CONFUSO</span><div class="tline grey"><span id="tbx{i}"></span><span class="cur">▋</span></div></div>'
                f'<div class="tgood" id="tg{i}"><span class="tlabel good">PERFETTO</span><div class="tline acc"><span id="tgx{i}"></span><span class="cur">▋</span></div></div>'
                f'</div></div>')
    if t=="cta":
        return (f'{eb(p["eyebrow"])}<div class="kw" id="ck{i}">{esc(p["pre"])}<span class="acc">{esc(p["acc"])}</span></div>'
                f'<div class="meter"><span id="mt{i}"></span></div>')
    return ""

clips=[];tw=[]
for i,((trig,t,p),s,e) in enumerate(zip(BEATS,starts,ends)):
    dur=max(0.6,e-s)
    clips.append(f'<div class="beat" id="beat{i}" data-start="{s}" data-duration="{dur:.2f}" data-track-index="{i+2}"><div class="inner {t}" id="in{i}">{inner(i,t,p)}</div></div>')
    js=[f'tl.fromTo("#beat{i}",{{opacity:0,y:30,scale:0.97}},{{opacity:1,y:0,scale:1,duration:0.2,ease:"power3.out"}},{s:.2f});']
    if t=="hook":
        js.append(f'tl.fromTo("#h1{i}",{{opacity:0,scale:1.4}},{{opacity:1,scale:1,duration:0.3,ease:"back.out(2)"}},{find(p["quatword"]):.2f});')
        cl=find(p["claudeword"])
        js.append(f'tl.to("#h1{i}",{{opacity:0,scale:0.85,duration:0.22,ease:"power2.in"}},{cl:.2f});')
        js.append(f'tl.fromTo("#h2{i}",{{opacity:0,scale:0.4,rotate:-30}},{{opacity:1,scale:1,rotate:0,duration:0.5,ease:"back.out(1.7)"}},{cl+0.04:.2f});')
        js.append(f'tl.fromTo("#h3{i}",{{opacity:0,scale:1.8,rotate:-10}},{{opacity:1,scale:1,rotate:-7,duration:0.3,ease:"back.out(2)"}},{find(p["stampword"]):.2f});')
    if t=="count":
        cw=find(p["countword"]); cnt=p["count"]
        js.append(f'tl.to({{v:0}},{{v:{cnt},duration:0.85,ease:"power2.out",onUpdate:function(){{document.getElementById("big{i}").textContent=Math.round(this.targets()[0].v)+"{p.get("suffix","")}";}}}},{max(s+0.15,cw-0.2):.2f});')
        blk0=find_after(p["blkanchor"],s)   # i 4 blocchi partono SOLO da quando dice "queste quattro"
        for j in range(4): js.append(f'tl.fromTo("#b{i}k{j}",{{opacity:0,y:24,scale:0.6}},{{opacity:1,y:0,scale:1,duration:0.26,ease:"back.out(2)"}},{blk0+j*0.2:.2f});')
    if t=="bigstat":
        cw=find(p["countword"])
        js.append(f'tl.fromTo("#big{i}",{{opacity:0,scale:1.45}},{{opacity:1,scale:1,duration:0.34,ease:"back.out(2.2)"}},{max(s+0.02,cw-0.12):.2f});')
    if t=="skilltitle":
        js.append(f'tl.fromTo("#nb{i}",{{opacity:0,scale:0.6}},{{opacity:1,scale:1,duration:0.3,ease:"back.out(2)"}},{s+0.05:.2f});')
        js.append(f'tl.fromTo("#sk{i}",{{opacity:0,x:-40}},{{opacity:1,x:0,duration:0.34,ease:"power3.out"}},{find(p["nameword"]):.2f});')
        for j in range(len(p["chips"])): js.append(f'tl.fromTo("#b{i}h{j}",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.24,ease:"back.out(1.8)"}},{s+0.5+j*0.22:.2f});')
    if t=="humanizer":
        js.append(f'tl.fromTo("#nb{i}",{{opacity:0,scale:0.6}},{{opacity:1,scale:1,duration:0.3,ease:"back.out(2)"}},{s+0.05:.2f});')
        js.append(f'tl.fromTo("#sk{i}",{{opacity:0,x:-40}},{{opacity:1,x:0,duration:0.34,ease:"power3.out"}},{s+0.15:.2f});')
        for j,(_,_,wd) in enumerate(p["words"]): js.append(f'tl.fromTo("#b{i}w{j}",{{opacity:0,y:18,scale:0.85}},{{opacity:1,y:0,scale:1,duration:0.26,ease:"back.out(1.9)"}},{find(wd):.2f});')
        js.append(f'tl.to("#hp{i}",{{opacity:0.3,duration:0.3}},{find(p["fixword"]):.2f});')
        js.append(f'tl.fromTo("#ha{i}",{{opacity:0}},{{opacity:1,duration:0.2}},{find(p["fixword"])-0.1:.2f});')
        js.append(f'tl.fromTo("#hr{i}",{{opacity:0,y:18,scale:0.9}},{{opacity:1,y:0,scale:1,duration:0.32,ease:"back.out(1.9)"}},{find(p["fixword"]):.2f});')
    if t=="terminal":
        js.append(f'tl.fromTo("#nb{i}",{{opacity:0,scale:0.6}},{{opacity:1,scale:1,duration:0.28,ease:"back.out(2)"}},{s+0.05:.2f});')
        js.append(f'tl.fromTo("#sk{i}",{{opacity:0,x:-40}},{{opacity:1,x:0,duration:0.3,ease:"power3.out"}},{s+0.12:.2f});')
        cf=find(p["confword"]); pf=find(p["perfword"])
        js.append(f'tl.fromTo("#tb{i}",{{opacity:0,y:14}},{{opacity:1,y:0,duration:0.22,ease:"power3.out"}},{cf-0.1:.2f});')
        # typewriter via textContent (mostra i tag XML letterali, niente parsing HTML)
        js.append(f'var cv{i}="{CONF}";tl.to({{n:0}},{{n:cv{i}.length,duration:0.95,ease:"none",onUpdate:function(){{document.getElementById("tbx{i}").textContent=cv{i}.slice(0,Math.round(this.targets()[0].n));}}}},{cf:.2f});')
        js.append(f'tl.to("#tb{i}",{{opacity:0,height:0,marginBottom:0,duration:0.2,ease:"power2.in"}},{pf-0.02:.2f});')
        js.append(f'tl.fromTo("#tg{i}",{{opacity:0}},{{opacity:1,duration:0.2}},{pf:.2f});')
        js.append(f'var pv{i}="{PERF}";tl.to({{n:0}},{{n:pv{i}.length,duration:1.5,ease:"none",onUpdate:function(){{document.getElementById("tgx{i}").textContent=pv{i}.slice(0,Math.round(this.targets()[0].n));}}}},{pf+0.1:.2f});')
    if t=="cta":
        js.append(f'tl.fromTo("#ck{i}",{{opacity:0,scale:1.3}},{{opacity:1,scale:1,duration:0.3,ease:"back.out(2)"}},{find(p["ctaword"]):.2f});')
        js.append(f'tl.fromTo("#mt{i}",{{scaleX:0}},{{scaleX:1,duration:1.1,ease:"power2.out"}},{s+0.3:.2f});')
    js.append(f'tl.to("#beat{i}",{{opacity:0,duration:0.16,ease:"power2.in"}},{e-0.16:.2f});')
    tw.append("\n      ".join(js))

NP=22
parts_html="".join(f'<span class="pt" id="pt{k}" style="left:{(k*131+40)%1040}px;top:{(k*97+30)%760}px;width:{5+(k%3)*3}px;height:{5+(k%3)*3}px;opacity:{0.12+0.2*((k*7)%5)/5:.2f}"></span>' for k in range(NP))
streaks_html="".join(f'<span class="stk" id="stk{k}" style="top:{120+k*230}px"></span>' for k in range(3))
bg=['tl.to("#glow",{x:120,y:30,scale:1.15,duration:6,yoyo:true,repeat:9,ease:"sine.inOut"},0);',
    'tl.to("#grid",{backgroundPosition:"0px 110px",duration:6,ease:"none",repeat:9},0);']
for k in range(NP):
    dur=4+(k%5)
    bg.append(f'tl.to("#pt{k}",{{y:-{120+(k%4)*60},duration:{dur},ease:"none",repeat:{int(60/dur)+1}}},0);')
    bg.append(f'tl.to("#pt{k}",{{opacity:0,duration:{dur},yoyo:true,repeat:{int(60/dur)+1},ease:"sine.inOut"}},0);')
for k in range(3):
    bg.append(f'tl.fromTo("#stk{k}",{{x:-1200}},{{x:1200,duration:{5+k*2},ease:"none",repeat:9}},{k*1.5});')

HTML=f'''<!doctype html><html lang="it"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=1080, height=1920"/>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:1080px;height:1920px;overflow:hidden;background:#000;font-family:"Montserrat","Inter",sans-serif}}
#root{{position:relative;width:1080px;height:1920px}}
#bgz{{position:absolute;top:0;left:0;width:1080px;height:864px;overflow:hidden}}
#grid{{position:absolute;inset:-40px;background-image:linear-gradient(rgba(47,224,129,0.05) 1px,transparent 1px),linear-gradient(90deg,rgba(47,224,129,0.05) 1px,transparent 1px);background-size:110px 110px}}
#glow{{position:absolute;top:120px;left:280px;width:520px;height:520px;border-radius:50%;background:radial-gradient(circle,rgba(47,224,129,0.26),transparent 65%);filter:blur(22px)}}
.pt{{position:absolute;border-radius:50%;background:{A};box-shadow:0 0 12px {A}}}
.stk{{position:absolute;left:0;width:520px;height:2px;background:linear-gradient(90deg,transparent,{A},transparent);opacity:0.3}}
.beat{{position:absolute;top:0;left:0;width:1080px;height:864px}}
.inner{{position:absolute;top:55px;left:64px;right:64px;height:700px;display:flex;flex-direction:column;justify-content:center;gap:22px}}
.eyebrow{{color:{A};font-size:32px;font-weight:800;letter-spacing:6px;text-transform:uppercase;display:flex;align-items:center;gap:13px}}
.ebdot{{width:14px;height:14px;border-radius:50%;background:{A};box-shadow:0 0 14px {A}}}
/* hook (centrato) */
.inner.hook{{align-items:center;justify-content:center}}
.hookwrap{{position:relative;width:100%;height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center}}
.hooks1{{position:absolute;display:flex;flex-direction:column;align-items:center;gap:6px}}
.hooktop{{color:{A};font-size:44px;font-weight:800;letter-spacing:10px}}
.hookbig{{color:#fff;font-size:200px;font-weight:900;line-height:0.82;letter-spacing:-4px;text-shadow:0 0 40px {GL}}}
.clogobig{{height:360px;width:360px;object-fit:contain;margin-bottom:28px;filter:drop-shadow(0 0 40px rgba(217,119,87,0.55))}}
.stamp{{color:{RED};font-size:118px;font-weight:900;border:7px solid {RED};border-radius:20px;padding:6px 40px;text-transform:uppercase;box-shadow:0 0 38px {REDD};text-shadow:0 0 26px {REDD}}}
/* count / bigstat */
.statrow{{display:flex;align-items:flex-end;gap:26px}}
.statrow.ctr{{justify-content:center}}
.inner.count{{align-items:center;text-align:center}}
.big{{color:#fff;font-size:210px;font-weight:900;line-height:0.82;letter-spacing:-4px;text-shadow:0 0 36px {GL}}}
.big.xl{{font-size:188px}}
.unit{{color:{A};font-size:38px;font-weight:900;text-transform:uppercase;line-height:1.05;padding-bottom:22px}}
.unit.big2{{font-size:48px;padding-bottom:0;margin-top:10px}}
.cblocks{{display:flex;gap:22px;justify-content:center;margin-top:14px}}
.cblk{{width:150px;height:180px;border-radius:24px;background:{A};box-shadow:0 0 30px {A};display:flex;align-items:center;justify-content:center}}
.cblk b{{color:#06140d;font-size:80px;font-weight:900}}
/* skilltitle */
.numbadge{{width:118px;height:118px;border-radius:26px;background:{A};color:#06140d;font-size:64px;font-weight:900;display:flex;align-items:center;justify-content:center;box-shadow:0 0 36px {A}}}
.numbadge.sm{{width:88px;height:88px;font-size:48px;border-radius:20px}}
.skname{{color:#fff;font-size:104px;font-weight:900;line-height:0.95;letter-spacing:-2px;text-shadow:0 0 30px {GL}}}
.skname.sm{{font-size:72px}}
.chips{{display:flex;flex-wrap:wrap;gap:16px;margin-top:10px}}
.chip{{color:{A};font-size:40px;font-weight:800;text-transform:uppercase;border:2px solid {AD};border-radius:40px;padding:12px 28px;background:rgba(14,18,16,0.7);box-shadow:0 0 18px {GL}}}
/* humanizer */
.inner.humanizer{{align-items:flex-start}}
.hpills{{display:flex;flex-wrap:wrap;gap:16px;margin-top:6px}}
.hpill{{color:{GREY};font-size:44px;font-weight:800;text-transform:uppercase;border:2px solid rgba(255,255,255,0.1);border-radius:18px;padding:14px 26px;background:rgba(40,44,42,0.7)}}
.hres{{color:#06140d;font-size:58px;font-weight:900;text-transform:uppercase;background:{A};border-radius:18px;padding:18px 34px;align-self:center;box-shadow:0 0 34px {A}}}
.swaparr{{color:{A};font-size:56px;font-weight:900;line-height:0.5;align-self:center}}
/* terminal */
.term{{margin-top:4px;background:#0c0f0e;border:2px solid {AD};border-radius:20px;overflow:hidden;box-shadow:0 0 40px {GL}}}
.tbar{{display:flex;align-items:center;gap:12px;background:#161b19;padding:16px 22px;border-bottom:1px solid rgba(255,255,255,0.06)}}
.td{{width:18px;height:18px;border-radius:50%}}.td.r{{background:#ff5f57}}.td.y{{background:#febc2e}}.td.g{{background:#28c840}}
.ttitle{{color:#7f877f;font-size:26px;font-weight:700;margin-left:10px;font-family:ui-monospace,"SF Mono",Menlo,monospace}}
.tbody{{padding:26px 28px;min-height:240px;font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace}}
.tlabel{{display:inline-block;font-size:24px;font-weight:900;letter-spacing:3px;border-radius:8px;padding:5px 14px;margin-bottom:14px;font-family:"Montserrat",sans-serif}}
.tlabel.bad{{color:{RED};border:2px solid {REDD}}}.tlabel.good{{color:#06140d;background:{A}}}
.tline{{color:#e7efe9;font-size:36px;line-height:1.5;font-weight:600;white-space:pre-wrap;word-break:break-word}}
.tline.grey{{color:{GREY}}}
.tline.acc{{color:{A}}}
.cur{{color:{A};animation:blink 1s steps(1) infinite}}
@keyframes blink{{50%{{opacity:0}}}}
/* cta */
.kw{{color:#fff;font-size:104px;font-weight:900;line-height:0.98;letter-spacing:-2px;text-shadow:0 0 30px {GL}}}
.kw .acc{{color:{A};text-shadow:0 0 26px {A}}}
.meter{{width:100%;height:28px;background:rgba(255,255,255,0.08);border-radius:14px;overflow:hidden;border:1px solid {AD}}}
.meter span{{display:block;height:100%;width:100%;transform-origin:left;transform:scaleX(0);background:linear-gradient(90deg,{A},#7af0b0);box-shadow:0 0 18px {A}}}
.inner.cta{{background:rgba(14,18,16,0.9);border:2px solid {A};border-radius:26px;padding:46px;box-shadow:0 0 46px {GL}}}
</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL:.2f}" data-width="1080" data-height="1920">
  <div id="bgz" data-start="0" data-duration="{TOTAL:.2f}" data-track-index="0"><div id="grid"></div><div id="glow"></div>{streaks_html}{parts_html}</div>
  {"".join(clips)}
</div>
<script>window.__timelines=window.__timelines||{{}};const tl=gsap.timeline({{paused:true}});
      {chr(10).join(bg)}
      {chr(10).join(tw)}
window.__timelines["main"]=tl;</script></body></html>'''
open("index.html","w").write(HTML)
print(f"reel1 v3: {len(BEATS)} beat, total {TOTAL}s")
for i,((trig,t,p),s,e) in enumerate(zip(BEATS,starts,ends)): print(f"  {s:5.2f}-{e:5.2f} {t:11s} {trig}")
