#!/usr/bin/env python3
# c0886: "bad website -> good website with one Claude prompt". Orange Claude accent.
import json, re, html, sys
A="#f0813f"; AB="#ffa766"; AD="rgba(240,129,63,0.45)"; GL="rgba(240,129,63,0.16)"
RED="#ff5470"; REDD="rgba(255,84,112,0.5)"; GREY="#8b938e"
d=json.load(open(sys.argv[1] if len(sys.argv)>1 else "../edit/tF2/transcripts/cutF2.json"))
WS=[w for w in d["words"] if w.get("type")!="spacing" and w.get("start") is not None]
TOTAL=round(WS[-1]["end"],2)+0.3
def norm(s): return re.sub(r"[^a-z0-9 ]","",s.lower())
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
def eb(e): return f'<div class="eyebrow"><span class="ebdot"></span>{esc(e)}</div>' if e else ""
def js_s(s): return json.dumps(s)

# ---- anchor guard: verify word indices before building ----
EXPECT={8:"this",10:"60",14:"cloud",16:"just",22:"so",24:"slash",33:"redesign",
        41:"nenea",42:"dont",56:"enter",57:"because",70:"redesign",74:"if",
        88:"comment",98:"free"}
for idx,w in EXPECT.items():
    assert norm(WS[idx]["text"])==w, f"anchor mismatch at {idx}: {WS[idx]['text']!r} != {w!r}"

PROMPT_TXT="Redesign my entire frontend in the theme of Linear."

BEATS=[
 ("This is how","hookswap",{}),                       # 0.00
 ("Just","skilltitle",{"name":"FRONTEND DESIGN","chip":"CLAUDE CODE SKILL"}),   # 4.54
 ("so","terminal",{}),                                # 6.68
 ("redesign my","promptcard",{}),                     # 11.14
 ("dont stop","dontstop",{}),                         # 16.42
 ("and then hit","enterkey",{}),                      # 23.02
 ("because","claudecard",{}),                         # 24.00
 ("If","cta",{}),                                     # 30.96
]
starts=[0.0]+[find(t) for t,_,_ in BEATS[1:]]
# fix the 'and then hit' occurrence (first 'and then' is at 8.8)
starts[5]=find_after("and then hit",20.0)
ends=[starts[i+1] for i in range(len(starts)-1)]+[TOTAL]

T_THIS2=WS[8]["start"]        # 1.44 swap bad->good
T_60=WS[10]["start"]          # 2.36
T_CLAUDE=WS[14]["start"]      # 3.82
T_SLASH=WS[24]["start"]       # 7.12
T_WRITE=WS[29]["start"]       # 9.62 "write this exact thing"
T_LINEAR=WS[41]["start"]      # 15.44
T_ENTER=WS[56]["start"]       # 23.68
T_CHIP=find_after("frontend",26.0)   # 26.64
T_REDES2=WS[70]["start"]      # 29.22
T_COMMENT=WS[88]["start"]     # 34.02
T_SKILLS2=WS[89]["start"]     # 34.30
T_FREE=WS[98]["start"]        # 36.18

BAD_SITE=(f'<div class="bframe bad" id="bad0">'
 f'<div class="bbar"><span class="td r"></span><span class="td y"></span><span class="td g"></span>'
 f'<span class="burl">my-website-2009.com</span></div>'
 f'<div class="bbody badbody">'
 f'<div class="badtitle">WELCOME TO MY WEBSITE!!!</div>'
 f'<div class="badrow"><div class="badbtn b1">CLICK HERE</div><div class="badbtn b2">BEST PRICES</div><div class="badbtn b3">!!SALE!!</div></div>'
 f'<div class="badtxt">Lorem ipsum dolor sit amet, we are the best company since 2009, call now...</div>'
 f'<div class="badimg">[ pixelated_photo.jpg ]</div>'
 f'<div class="badfoot">visitor counter: 000412</div>'
 f'</div></div>')
GOOD_SITE=(f'<div class="bframe good" id="good0">'
 f'<div class="bbar dark"><span class="td r"></span><span class="td y"></span><span class="td g"></span>'
 f'<span class="burl">yoursite.com</span></div>'
 f'<div class="bbody goodbody">'
 f'<div class="gnav"><span class="glogo">◆</span><span class="gnavl">Product</span><span class="gnavl">Pricing</span><span class="gnavl">Docs</span><span class="gcta-s">Sign in</span></div>'
 f'<div class="ghero">Build software<br/>that feels effortless</div>'
 f'<div class="gsub">The modern toolkit for teams that ship.</div>'
 f'<div class="gbtn">Get started →</div>'
 f'</div></div>')

def inner(i,t,p):
    if t=="hookswap":
        return (f'<div class="swapwrap">{BAD_SITE}{GOOD_SITE}</div>'
                f'<div class="stamp60" id="st{i}">60 SECONDS</div>'
                f'<div class="cpill" id="cp{i}"><img src="assets/logos/claude.svg" class="cpimg"/>ONE CLAUDE PROMPT</div>')
    if t=="skilltitle":
        return (f'{eb("THE SKILL")}<div class="skwrap">'
                f'<div class="skname" id="sk{i}">FRONTEND<br/>DESIGN</div>'
                f'<div class="skchip" id="sc{i}">{esc(p["chip"])}</div></div>')
    if t=="terminal":
        return (f'<div class="win"><div class="wbar"><span class="td r"></span><span class="td y"></span><span class="td g"></span><span class="wtitle">claude</span></div>'
                f'<div class="wbody term">'
                f'<div class="tprompt">›&nbsp;<span class="tcmd" id="cmd{i}"></span><span class="cur">▋</span></div>'
                f'<div class="qhead" id="qh{i}">then write this exact thing ↓</div>'
                f'</div></div>')
    if t=="promptcard":
        return (f'{eb("THE PROMPT")}'
                f'<div class="pmsg"><pre class="ptext"><span id="px{i}"></span><span class="cur">▋</span></pre></div>'
                f'<div class="lbadge" id="lb{i}"><span class="ldot"></span>LINEAR</div>')
    if t=="dontstop":
        return (f'{eb("AND ADD")}'
                f'<div class="kw dsbig" id="ds{i}">DON\'T<br/>STOP</div>'
                f'<div class="dssub" id="du{i}">UNTIL THE ENTIRE SOFTWARE HAS A MAKEOVER</div>')
    if t=="enterkey":
        return (f'<div class="keywrap"><div class="key" id="ky{i}">ENTER<span class="karr">⏎</span></div></div>')
    if t=="claudecard":
        return (f'<div class="chwrap">'
                f'<img src="assets/logos/claude.svg" class="cclogo" id="cl{i}"/>'
                f'<div class="ccname" id="cn{i}">CLAUDE</div>'
                f'<div class="ghchip" id="gc{i}">FRONTEND DESIGN SKILL</div>'
                f'<div class="rgstamp" id="rs{i}">FULL REDESIGN</div></div>')
    if t=="cta":
        return (f'<div class="ctapills"><div class="pillrow">'
                f'<div class="spill" id="sp{i}_0">/frontend-design</div>'
                f'<div class="spill" id="sp{i}_1">+ ALL MY CLAUDE SKILLS</div></div></div>'
                f'<div class="kw ctak" id="ck{i}">COMMENT<br/>"<span class="acc">SKILLS</span>"</div>'
                f'<div class="ctasub" id="cu{i}">→ I\'LL SEND IT 100% FREE</div>'
                f'<div class="meter"><span id="mt{i}"></span></div>')
    return ""

clips=[];tw=[]
for i,((trig,t,p),s,e) in enumerate(zip(BEATS,starts,ends)):
    dur=max(0.6,e-s)
    clips.append(f'<div class="beat" id="beat{i}" data-start="{s}" data-duration="{dur:.2f}" data-track-index="{i+2}"><div class="inner {t}" id="in{i}">{inner(i,t,p)}</div></div>')
    if t=="hookswap":
        js=[f'tl.set("#beat{i}",{{opacity:1}},0);']
        # bad site visible from FRAME 1, small punch on first "this"(0.58)
        js.append(f'tl.set("#bad0",{{opacity:1}},0);tl.set("#good0",{{opacity:0}},0);')
        js.append(f'tl.fromTo("#bad0",{{scale:1}},{{scale:1.04,duration:0.14,yoyo:true,repeat:1,ease:"power2.out"}},0.58);')
        # sequential swap on second "this": bad exits fully, then good pops
        js.append(f'tl.to("#bad0",{{opacity:0,x:-90,scale:0.92,duration:0.16,ease:"power2.in"}},{T_THIS2-0.16:.2f});')
        js.append(f'tl.fromTo("#good0",{{opacity:0,x:70,scale:0.94}},{{opacity:1,x:0,scale:1,duration:0.3,ease:"back.out(1.7)"}},{T_THIS2:.2f});')
        js.append(f'tl.fromTo("#st{i}",{{opacity:0,scale:1.6,rotate:6}},{{opacity:1,scale:1,rotate:-4,duration:0.3,ease:"back.out(2.2)"}},{T_60:.2f});')
        js.append(f'tl.fromTo("#cp{i}",{{opacity:0,y:26,scale:0.85}},{{opacity:1,y:0,scale:1,duration:0.3,ease:"back.out(2)"}},{T_CLAUDE:.2f});')
    else:
        js=[f'tl.fromTo("#beat{i}",{{opacity:0,y:30,scale:0.97}},{{opacity:1,y:0,scale:1,duration:0.2,ease:"power3.out"}},{s:.2f});']
    if t=="skilltitle":
        js.append(f'tl.fromTo("#sk{i}",{{opacity:0,y:26,scale:0.9}},{{opacity:1,y:0,scale:1,duration:0.32,ease:"back.out(1.8)"}},{s+0.08:.2f});')
        js.append(f'tl.fromTo("#sc{i}",{{opacity:0,scale:0.8}},{{opacity:1,scale:1,duration:0.28,ease:"back.out(2)"}},{s+0.45:.2f});')
    if t=="terminal":
        cmd="/frontend-design"
        js.append(f'var cv{i}={js_s(cmd)};tl.to({{n:0}},{{n:cv{i}.length,duration:1.2,ease:"none",onUpdate:function(){{document.getElementById("cmd{i}").textContent=cv{i}.slice(0,Math.round(this.targets()[0].n));}}}},{T_SLASH-0.1:.2f});')
        js.append(f'tl.fromTo("#qh{i}",{{opacity:0,y:12}},{{opacity:1,y:0,duration:0.26,ease:"power3.out"}},{T_WRITE:.2f});')
    if t=="promptcard":
        js.append(f'var pv{i}={js_s(PROMPT_TXT)};tl.to({{n:0}},{{n:pv{i}.length,duration:3.6,ease:"none",onUpdate:function(){{document.getElementById("px{i}").textContent=pv{i}.slice(0,Math.round(this.targets()[0].n));}}}},{s+0.15:.2f});')
        js.append(f'tl.fromTo("#lb{i}",{{opacity:0,scale:0.7,y:16}},{{opacity:1,scale:1,y:0,duration:0.3,ease:"back.out(2)"}},{T_LINEAR:.2f});')
    if t=="dontstop":
        js.append(f'tl.fromTo("#ds{i}",{{opacity:0,scale:1.35}},{{opacity:1,scale:1,duration:0.3,ease:"back.out(2)"}},{s+0.15:.2f});')
        js.append(f'tl.fromTo("#du{i}",{{opacity:0,y:18}},{{opacity:1,y:0,duration:0.28,ease:"power3.out"}},{s+0.65:.2f});')
    if t=="enterkey":
        js.append(f'tl.fromTo("#ky{i}",{{opacity:0,scale:0.55,y:30}},{{opacity:1,scale:1,y:0,duration:0.26,ease:"back.out(2.2)"}},{s+0.06:.2f});')
        js.append(f'tl.to("#ky{i}",{{y:14,duration:0.1,yoyo:true,repeat:1,ease:"power2.in"}},{T_ENTER:.2f});')
    if t=="claudecard":
        js.append(f'tl.fromTo("#cl{i}",{{opacity:0,scale:0.6,rotate:-12}},{{opacity:1,scale:1,rotate:0,duration:0.4,ease:"back.out(1.8)"}},{s+0.3:.2f});')
        js.append(f'tl.fromTo("#cn{i}",{{opacity:0,y:18}},{{opacity:1,y:0,duration:0.3,ease:"power3.out"}},{s+0.5:.2f});')
        js.append(f'tl.fromTo("#gc{i}",{{opacity:0,scale:0.8}},{{opacity:1,scale:1,duration:0.3,ease:"back.out(2)"}},{T_CHIP-0.2:.2f});')
        js.append(f'tl.fromTo("#rs{i}",{{opacity:0,scale:1.5,rotate:-7}},{{opacity:1,scale:1,rotate:-4,duration:0.32,ease:"back.out(2)"}},{T_REDES2:.2f});')
    if t=="cta":
        js.append(f'tl.fromTo("#sp{i}_0",{{opacity:0,x:-40}},{{opacity:1,x:0,duration:0.28,ease:"back.out(1.8)"}},{s+0.25:.2f});')
        js.append(f'tl.fromTo("#sp{i}_1",{{opacity:0,x:-40}},{{opacity:1,x:0,duration:0.28,ease:"back.out(1.8)"}},{s+1.9:.2f});')
        js.append(f'tl.to("#sp{i}_0,#sp{i}_1",{{opacity:0.35,duration:0.25}},{T_COMMENT-0.1:.2f});')
        js.append(f'tl.fromTo("#ck{i}",{{opacity:0,scale:1.3}},{{opacity:1,scale:1,duration:0.3,ease:"back.out(2)"}},{T_COMMENT:.2f});')
        js.append(f'tl.fromTo("#ck{i} .acc",{{scale:1.5}},{{scale:1,duration:0.28,ease:"back.out(2.4)"}},{T_SKILLS2:.2f});')
        js.append(f'tl.fromTo("#cu{i}",{{opacity:0,y:16}},{{opacity:1,y:0,duration:0.28,ease:"power3.out"}},{T_FREE-0.9:.2f});')
        js.append(f'tl.fromTo("#mt{i}",{{scaleX:0}},{{scaleX:1,duration:1.2,ease:"power2.out"}},{s+0.4:.2f});')
    if i<len(BEATS)-1:
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

HTML=f'''<!doctype html><html lang="en"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=1080, height=1920"/>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:1080px;height:1920px;overflow:hidden;background:#000;font-family:"Montserrat","Inter",sans-serif}}
#root{{position:relative;width:1080px;height:1920px}}
#bgz{{position:absolute;top:0;left:0;width:1080px;height:864px;overflow:hidden}}
#grid{{position:absolute;inset:-40px;background-image:linear-gradient(rgba(240,129,63,0.05) 1px,transparent 1px),linear-gradient(90deg,rgba(240,129,63,0.05) 1px,transparent 1px);background-size:110px 110px}}
#glow{{position:absolute;top:120px;left:280px;width:520px;height:520px;border-radius:50%;background:radial-gradient(circle,rgba(240,129,63,0.24),transparent 65%);filter:blur(22px)}}
.pt{{position:absolute;border-radius:50%;background:{A};box-shadow:0 0 12px {A}}}
.stk{{position:absolute;left:0;width:520px;height:2px;background:linear-gradient(90deg,transparent,{A},transparent);opacity:0.3}}
.beat{{position:absolute;top:0;left:0;width:1080px;height:864px;opacity:0}}
.inner{{position:absolute;top:46px;left:60px;right:60px;height:740px;display:flex;flex-direction:column;justify-content:center;gap:22px}}
.eyebrow{{color:{A};font-size:32px;font-weight:800;letter-spacing:6px;text-transform:uppercase;display:flex;align-items:center;gap:13px}}
.ebdot{{width:14px;height:14px;border-radius:50%;background:{A};box-shadow:0 0 14px {A}}}
/* hookswap */
.inner.hookswap{{align-items:center;justify-content:center;gap:0}}
.swapwrap{{position:relative;width:920px;height:560px}}
.bframe{{position:absolute;inset:0;border-radius:22px;overflow:hidden;opacity:0}}
.bframe.bad{{border:4px solid {RED};box-shadow:0 0 44px {REDD}}}
.bframe.good{{border:4px solid {A};box-shadow:0 0 48px rgba(240,129,63,0.5)}}
.bbar{{display:flex;align-items:center;gap:12px;background:#d6d2c4;padding:14px 20px}}
.bbar.dark{{background:#15161a}}
.td{{width:18px;height:18px;border-radius:50%}}.td.r{{background:#ff5f57}}.td.y{{background:#febc2e}}.td.g{{background:#28c840}}
.burl{{color:#666;font-size:24px;font-weight:600;margin-left:14px;font-family:ui-monospace,Menlo,monospace}}
.bbar.dark .burl{{color:#9aa}}
.bbody{{height:100%}}
.badbody{{background:#fffbe6;padding:28px 34px;display:flex;flex-direction:column;gap:18px}}
.badtitle{{font-family:"Times New Roman",serif;color:#c00;font-size:52px;font-weight:700;text-decoration:underline;text-align:center}}
.badrow{{display:flex;gap:14px;justify-content:center}}
.badbtn{{font-size:26px;font-weight:900;padding:12px 20px;border-radius:6px;border:3px outset #999}}
.badbtn.b1{{background:#00d0ff;color:#900}}.badbtn.b2{{background:#ffe600;color:#0a0}}.badbtn.b3{{background:#f0f;color:#fff}}
.badtxt{{font-family:"Times New Roman",serif;color:#333;font-size:27px;line-height:1.3}}
.badimg{{background:#bbb;color:#666;font-size:26px;font-family:ui-monospace,monospace;text-align:center;padding:34px 0;border:2px dashed #888}}
.badfoot{{color:#090;font-size:23px;font-family:ui-monospace,monospace;text-align:center}}
.goodbody{{background:#0c0d11;padding:30px 40px;display:flex;flex-direction:column;gap:26px}}
.gnav{{display:flex;align-items:center;gap:30px}}
.glogo{{color:{A};font-size:34px}}
.gnavl{{color:#8b90a0;font-size:25px;font-weight:600}}
.gcta-s{{margin-left:auto;color:#fff;font-size:24px;font-weight:700;border:1px solid #333;border-radius:10px;padding:8px 18px}}
.ghero{{color:#fff;font-size:64px;font-weight:800;line-height:1.05;letter-spacing:-2px;margin-top:14px}}
.gsub{{color:#8b90a0;font-size:29px;font-weight:500}}
.gbtn{{align-self:flex-start;color:#1a0f06;background:{A};font-size:30px;font-weight:800;border-radius:14px;padding:16px 34px;box-shadow:0 0 30px rgba(240,129,63,0.55)}}
.stamp60{{position:absolute;top:70px;right:56px;color:#1a0f06;background:{A};font-size:52px;font-weight:900;border-radius:16px;padding:12px 30px;box-shadow:0 0 36px {A};opacity:0}}
.cpill{{position:absolute;bottom:52px;left:50%;transform:translateX(-50%);display:flex;align-items:center;gap:16px;color:#fff;background:rgba(20,14,8,0.92);border:2px solid {A};font-size:40px;font-weight:900;border-radius:60px;padding:16px 38px;box-shadow:0 0 30px {GL};white-space:nowrap;opacity:0}}
.cpimg{{height:52px;width:52px}}
/* skilltitle */
.inner.skilltitle{{align-items:center;text-align:center}}
.skwrap{{display:flex;flex-direction:column;align-items:center;gap:30px}}
.skname{{color:#fff;font-size:150px;font-weight:900;line-height:0.92;letter-spacing:-4px;text-shadow:0 0 38px {GL}}}
.skchip{{color:#1a0f06;background:{A};font-size:42px;font-weight:900;text-transform:uppercase;border-radius:16px;padding:14px 34px;box-shadow:0 0 32px {A}}}
/* window / terminal */
.win{{background:#0c0f0e;border:2px solid {AD};border-radius:22px;overflow:hidden;box-shadow:0 0 44px {GL}}}
.wbar{{display:flex;align-items:center;gap:12px;background:#161b19;padding:16px 22px;border-bottom:1px solid rgba(255,255,255,0.06)}}
.wtitle{{color:#9aa29a;font-size:27px;font-weight:700;margin-left:10px;font-family:ui-monospace,"SF Mono",Menlo,monospace}}
.wbody{{padding:26px 30px;font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace}}
.term{{min-height:420px}}
.tprompt{{color:#e7efe9;font-size:44px;font-weight:700;margin-bottom:30px;margin-top:26px}}
.tcmd{{color:{AB}}}
.cur{{color:{A};animation:blink 1s steps(1) infinite}}@keyframes blink{{50%{{opacity:0}}}}
.qhead{{color:#9aa29a;font-size:36px;font-weight:600}}
/* promptcard */
.inner.promptcard{{align-items:stretch}}
.pmsg{{background:#0c0f0e;border:2px solid {AD};border-radius:22px;padding:40px;box-shadow:0 0 44px {GL};min-height:330px;display:flex;align-items:center}}
.ptext{{color:{AB};font-size:52px;line-height:1.3;font-weight:600;white-space:pre-wrap;font-family:ui-monospace,"SF Mono",Menlo,monospace;text-shadow:0 0 10px rgba(240,129,63,0.35)}}
.lbadge{{align-self:center;display:flex;align-items:center;gap:18px;color:#fff;background:#15161a;border:2px solid #5e6ad2;font-size:54px;font-weight:900;letter-spacing:4px;border-radius:18px;padding:18px 40px;box-shadow:0 0 34px rgba(94,106,210,0.5);opacity:0}}
.ldot{{width:26px;height:26px;border-radius:8px;background:#5e6ad2;box-shadow:0 0 16px #5e6ad2}}
/* dontstop */
.inner.dontstop{{align-items:center;text-align:center}}
.kw{{color:#fff;font-weight:900;letter-spacing:-2px;text-align:center;text-shadow:0 0 30px {GL}}}
.dsbig{{font-size:220px;line-height:0.85;letter-spacing:-6px}}
.dssub{{color:{AB};font-size:44px;font-weight:800;text-transform:uppercase;max-width:90%;line-height:1.2}}
/* enterkey */
.inner.enterkey{{align-items:center;justify-content:center}}
.keywrap{{perspective:600px}}
.key{{display:flex;align-items:center;gap:30px;color:#fff;background:linear-gradient(180deg,#23272b,#101315);border:3px solid {AD};border-bottom:14px solid {A};border-radius:34px;font-size:120px;font-weight:900;letter-spacing:2px;padding:50px 90px;box-shadow:0 0 60px {GL}}}
.karr{{color:{A};text-shadow:0 0 24px {A}}}
/* claudecard */
.inner.claudecard{{align-items:center;justify-content:center}}
.chwrap{{display:flex;flex-direction:column;align-items:center;gap:30px}}
.cclogo{{width:270px;height:270px;object-fit:contain;filter:drop-shadow(0 0 34px rgba(240,129,63,0.55))}}
.ccname{{color:#fff;font-size:96px;font-weight:900;letter-spacing:8px}}
.ghchip{{color:#1a0f06;background:{A};font-size:42px;font-weight:900;text-transform:uppercase;border-radius:16px;padding:14px 34px;box-shadow:0 0 32px {A}}}
.rgstamp{{color:#1a0f06;background:{A};font-size:54px;font-weight:900;text-transform:uppercase;border-radius:16px;padding:12px 32px;box-shadow:0 0 36px {A};transform:rotate(-4deg)}}
/* cta */
.inner.cta{{align-items:center;justify-content:center;background:rgba(20,14,8,0.9);border:2px solid {A};border-radius:26px;padding:44px;box-shadow:0 0 46px {GL}}}
.ctapills{{width:100%}}
.pillrow{{display:flex;flex-direction:column;gap:16px;align-items:center;margin-bottom:10px}}
.spill{{color:{AB};background:#0c0f0e;border:2px solid {AD};font-size:44px;font-weight:800;border-radius:60px;padding:16px 40px;font-family:ui-monospace,Menlo,monospace;box-shadow:0 0 22px {GL};opacity:0}}
.ctak{{font-size:96px;line-height:0.98}}
.kw .acc{{color:{A};text-shadow:0 0 26px {A};display:inline-block}}
.ctasub{{color:{AB};font-size:44px;font-weight:800;text-transform:uppercase;margin-top:6px}}
.meter{{width:100%;height:26px;background:rgba(255,255,255,0.08);border-radius:14px;overflow:hidden;border:1px solid {AD};margin-top:14px}}
.meter span{{display:block;height:100%;width:100%;transform-origin:left;transform:scaleX(0);background:linear-gradient(90deg,{A},{AB});box-shadow:0 0 18px {A}}}
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
print(f"c0886: {len(BEATS)} beats, total {TOTAL}s")
for i,((trig,t,p),s,e) in enumerate(zip(BEATS,starts,ends)): print(f"  {s:5.2f}-{e:5.2f} {t:11s} {trig}")
