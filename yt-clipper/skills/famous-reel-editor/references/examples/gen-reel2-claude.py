#!/usr/bin/env python3
# reel2 v2: feedback Riccardo. Accento ARANCIONE Claude.
import json, re, html, sys
A="#f0813f"; AB="#ffa766"; AD="rgba(240,129,63,0.45)"; GL="rgba(240,129,63,0.16)"
RED="#ff5470"; REDD="rgba(255,84,112,0.5)"; GREY="#8b938e"; WARN="#ffb454"
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
def eb(e): return f'<div class="eyebrow"><span class="ebdot"></span>{esc(e)}</div>' if e else ""
def js_s(s): return json.dumps(s)

def boxline(inner, w=28): return "|"+inner.ljust(w)[:w]+"|"
def hr(w=28,fill="-"): return "+"+fill*w+"+"
ASCII="\n".join([
 hr(),
 boxline(" LOGO     home  prezzi  [=]"),
 hr(),
 boxline(""),
 boxline("     T I T O L O   HERO"),
 boxline("    sottotitolo che vende"),
 boxline("      [   INIZIA ORA   ]"),
 boxline(""),
 "+--------+--------+----------+",
 boxline(" [img]  | [img]  | [img]"),
 boxline(" feature| feature| feature"),
 "+--------+--------+----------+",
 boxline("      footer   .   2026"),
 hr(),
])
CMD_SP="/plugins superpowers"
CMD_SEC="/security-review"
MD=[("h1","# overview.md"),
    ("h2","## Architettura"),
    ("li","src/   core dell'app"),
    ("li","api/   endpoint REST"),
    ("li","db/    schema & migrazioni"),
    ("h2","## Convenzioni"),
    ("tx","naming, pattern, stile del codice"),
    ("h2","## Flussi chiave"),
    ("tx","auth . pagamenti . upload")]

BEATS=[
 ("Smetti","claudehero",{"codeword":"code","princword":"principiante"}),
 ("Dopo","hrgraph",{"eyebrow":"L'HO USATO","num":"1000+","unit":"ORE SU CLAUDE CODE","numword":"mille"}),
 ("questi sono i trucchi","twopill",{"eyebrow":"RISULTATO","p1":"−MILIONI DI TOKEN","w1":"milioni","p2":"2× QUALITÀ","w2":"raddoppiare"}),
 ("Primo","genflow",{"eyebrow":"PRIMA REGOLA","s1":"PRIMA DI GENERARE","s1w":"prima","s2":"GENERA UN DIAGRAMMA ASCII","s2w":"diagramma"}),
 ("così","asciiwin",{"title":"landing.txt"}),
 ("Poi","terminalsp",{"num":"01","name":"SUPERPOWERS","cmdword":"plugin","qword":"giuste","betterword":"meglio"}),
 ("Usa gli hooks","hooksimg",{}),
 ("comandi","hookflow",{"eyebrow":"DOPO OGNI AZIONE","steps":["AZIONE","HOOK","COMANDO AUTO"]}),
 ("Tipo","githubcard",{"num":"02","top":"AD OGNI MODIFICA","chip":"AUTO-PUSH","earlyword":"modifica","logoword":"github"}),
 ("Crea","mdfile",{"num":"03","fileword":"overviewmd"}),
 ("Questo","agents",{"eyebrow":"PIÙ CONTESTO AGLI AGENTI","logoword":"agenti","drawword":"contesto","stampword":"esponenzialmente","stamp":"RISULTATI"}),
 ("e prima","terminalsec",{"num":"04","name":"SECURITY REVIEW","cmdword":"comando","scanword":"trovare","vulnword":"falle","doneword":"sicurezza"}),
 ("questi sono solo","ctacount",{"eyebrow":"SONO SOLO ALCUNI","chip":"+ PROMPT PRONTI","vuoiword":"vuoi","ottoword":"otto","promptword":"prompt"}),
 ("Commenta","ctacomment",{"pre":"COMMENTA: ","acc":"TRUCCHI","sub":"→ TI GIRO LA GUIDA","ctaword":"commenta"}),
]
starts=[find(t) for t,_,_ in BEATS]; ends=[starts[i+1] for i in range(len(starts)-1)]+[TOTAL]

def inner(i,t,p):
    if t=="claudehero":
        return (f'<div class="chwrap"><img src="assets/ccode_crop.png" class="cclogo" id="cl{i}"/>'
                f'<div class="princrow" id="pr{i}"><span class="princ" id="pw{i}">PRINCIPIANTE</span>'
                f'<span class="strike" id="ps{i}"></span></div></div>')
    if t=="hrgraph":
        return (f'{eb(p["eyebrow"])}'
                f'<svg class="hrsvg" viewBox="0 0 600 300" preserveAspectRatio="none">'
                f'<defs><linearGradient id="hg{i}" x1="0" y1="0" x2="0" y2="1">'
                f'<stop offset="0" stop-color="{A}" stop-opacity="0.45"/><stop offset="1" stop-color="{A}" stop-opacity="0"/></linearGradient></defs>'
                f'<path id="ha{i}" d="M0,295 C160,285 300,250 410,150 C480,86 540,40 600,14 L600,300 L0,300 Z" fill="url(#hg{i})" opacity="0"/>'
                f'<path id="hl{i}" d="M0,295 C160,285 300,250 410,150 C480,86 540,40 600,14" fill="none" stroke="{A}" stroke-width="8" stroke-linecap="round" '
                f'style="stroke-dasharray:820;filter:drop-shadow(0 0 12px {A})"/></svg>'
                f'<div class="hrlabel"><span class="hrnum" id="hn{i}">{esc(p["num"])}</span><span class="hrunit">{esc(p["unit"])}</span></div>')
    if t=="twopill":
        return (f'{eb(p["eyebrow"])}<div class="pill p1" id="pa{i}">{esc(p["p1"])}</div>'
                f'<div class="pill p2" id="pb{i}">{esc(p["p2"])}</div>')
    if t=="genflow":
        return (f'{eb(p["eyebrow"])}<div class="flow">'
                f'<div class="fstep" id="fs{i}_0">{esc(p["s1"])}</div>'
                f'<div class="farr" id="fa{i}_0">↓</div>'
                f'<div class="fstep last" id="fs{i}_1">{esc(p["s2"])}</div></div>')
    if t=="asciiwin":
        return (f'<div class="win"><div class="wbar"><span class="td r"></span><span class="td y"></span><span class="td g"></span>'
                f'<span class="wtitle">{esc(p["title"])}</span></div>'
                f'<div class="wbody asciibody"><pre class="asciipre"><span id="ax{i}"></span><span class="cur">▋</span></pre></div></div>')
    if t=="terminalsp":
        qs=["Qual è l\'obiettivo finale?","Frontend, backend o entrambi?","Vincoli, stack, deadline?"]
        ql="".join(f'<div class="qline" id="q{i}_{j}">→ {esc(q)}</div>' for j,q in enumerate(qs))
        return (f'<div class="strow"><div class="numbadge sm" id="nb{i}">{esc(p["num"])}</div><div class="skname sm" id="sk{i}">{esc(p["name"])}</div></div>'
                f'<div class="win"><div class="wbar"><span class="td r"></span><span class="td y"></span><span class="td g"></span><span class="wtitle">claude</span></div>'
                f'<div class="wbody term">'
                f'<div class="tprompt">›&nbsp;<span class="tcmd" id="cmd{i}"></span><span class="cur">▋</span></div>'
                f'<div class="qhead" id="qh{i}">Ti fa le giuste domande:</div>'
                f'<div class="qblock">{ql}</div>'
                f'<div class="qbetter" id="qbt{i}">✓ meglio della Plan Mode</div>'
                f'</div></div>')
    if t=="hooksimg":
        hooks=('<svg class="hooksvg" id="hk{i}" viewBox="0 0 260 250">'
               '<g stroke="#f2d23f" stroke-width="11" fill="none" stroke-linecap="round" stroke-linejoin="round">'
               '<circle cx="108" cy="32" r="15"/><path d="M108,47 L108,150 C108,200 58,204 46,162 C42,148 50,138 62,140"/><path d="M62,140 L74,153"/>'
               '<circle cx="152" cy="32" r="15"/><path d="M152,47 L152,150 C152,200 202,204 214,162 C218,148 210,138 198,140"/><path d="M198,140 L186,153"/>'
               '</g></svg>').replace("{i}",str(i))
        return (f'<div class="hkcard">'
                f'<div class="win hkwin" id="hw{i}">'
                f'<div class="wbar"><span class="td r"></span><span class="td y"></span><span class="td g"></span><span class="wtitle">claude code</span></div>'
                f'<div class="wbody hkbody">'
                f'<div class="hkwelcome">✳ Welcome to the Claude Code research preview!</div>'
                f'<div class="hkmid">{hooks}</div>'
                f'<div class="hklogin">✻ Login successful. Press <b>Enter</b> to continue</div>'
                f'</div></div>'
                f'<div class="hkbig" id="hb{i}">HOOKS</div></div>')
    if t=="hookflow":
        parts=[]
        for j,s2 in enumerate(p["steps"]):
            parts.append(f'<div class="fstep{" last" if j==len(p["steps"])-1 else ""}" id="fs{i}_{j}">{esc(s2)}</div>')
            if j<len(p["steps"])-1: parts.append(f'<div class="farr" id="fa{i}_{j}">↓</div>')
        return f'{eb(p["eyebrow"])}<div class="flow">{"".join(parts)}</div>'
    if t=="githubcard":
        return (f'<div class="strow"><div class="numbadge sm" id="nb{i}">{esc(p["num"])}</div><div class="ghtop" id="gt{i}">{esc(p["top"])}</div></div>'
                f'<div class="ghwrap"><img src="assets/logos/github.svg" class="ghlogo" id="gl{i}"/>'
                f'<div class="ghchip" id="gc{i}">{esc(p["chip"])}</div></div>')
    if t=="mdfile":
        rows="".join(f'<div class="md {cls}" id="md{i}_{j}">{esc(txt)}</div>' for j,(cls,txt) in enumerate(MD))
        return (f'<div class="win"><div class="wbar"><span class="td r"></span><span class="td y"></span><span class="td g"></span>'
                f'<span class="wtitle">overview.md</span><span class="wmd">MD</span></div>'
                f'<div class="wbody mdbody" id="mdb{i}">{rows}</div></div>')
    if t=="agents":
        logos="".join(f'<div class="agent" id="ag{i}_{j}"><img src="assets/logos/{l}.svg" class="agimg"/><span class="aglbl">{nm}</span></div>'
                      for j,(l,nm) in enumerate([("claude","Claude"),("gemini","Gemini"),("openai","ChatGPT")]))
        return (f'{eb(p["eyebrow"])}<div class="agentrow">{logos}</div>'
                f'<svg class="agsvg" viewBox="0 0 600 230" preserveAspectRatio="none">'
                f'<defs><linearGradient id="ag{i}g" x1="0" y1="0" x2="0" y2="1">'
                f'<stop offset="0" stop-color="{A}" stop-opacity="0.4"/><stop offset="1" stop-color="{A}" stop-opacity="0"/></linearGradient></defs>'
                f'<path id="aa{i}" d="M0,222 C170,214 300,196 410,140 C485,102 545,46 600,10 L600,230 L0,230 Z" fill="url(#ag{i}g)" opacity="0"/>'
                f'<path id="al{i}" d="M0,222 C170,214 300,196 410,140 C485,102 545,46 600,10" fill="none" stroke="{A}" stroke-width="7" stroke-linecap="round" '
                f'style="stroke-dasharray:780;filter:drop-shadow(0 0 10px {A})"/></svg>'
                f'<div class="rgstamp" id="rs{i}">{esc(p["stamp"])}</div>')
    if t=="terminalsec":
        return (f'<div class="strow"><div class="numbadge sm" id="nb{i}">{esc(p["num"])}</div><div class="skname sm" id="sk{i}">{esc(p["name"])}</div></div>'
                f'<div class="win"><div class="wbar"><span class="td r"></span><span class="td y"></span><span class="td g"></span><span class="wtitle">claude</span></div>'
                f'<div class="wbody term">'
                f'<div class="tprompt">›&nbsp;<span class="tcmd" id="cmd{i}"></span><span class="cur">▋</span></div>'
                f'<div class="scan" id="sc{i}">⟳ scansione di 142 file…</div>'
                f'<div class="vuln" id="v{i}_0">⚠ SQL injection · auth.ts:42</div>'
                f'<div class="vuln" id="v{i}_1">⚠ token esposto · .env</div>'
                f'<div class="vdone" id="vd{i}">✓ 2 falle trovate</div>'
                f'</div></div>')
    if t=="ctacount":
        return (f'{eb(p["eyebrow"])}'
                f'<div class="kw ctaq" id="ck{i}">VUOI TUTTI GLI<br><span class="acc" id="c8{i}">8 TRUCCHI</span>?</div>'
                f'<div class="chip ctr" id="cc{i}">{esc(p["chip"])}</div>')
    if t=="ctacomment":
        return (f'<div class="kw" id="ck{i}">{esc(p["pre"])}<span class="acc">{esc(p["acc"])}</span></div>'
                f'<div class="ctasub" id="cu{i}">{esc(p["sub"])}</div>'
                f'<div class="meter"><span id="mt{i}"></span></div>')
    return ""

clips=[];tw=[]
for i,((trig,t,p),s,e) in enumerate(zip(BEATS,starts,ends)):
    dur=max(0.6,e-s)
    clips.append(f'<div class="beat" id="beat{i}" data-start="{s}" data-duration="{dur:.2f}" data-track-index="{i+2}"><div class="inner {t}" id="in{i}">{inner(i,t,p)}</div></div>')
    js=[f'tl.fromTo("#beat{i}",{{opacity:0,y:30,scale:0.97}},{{opacity:1,y:0,scale:1,duration:0.2,ease:"power3.out"}},{s:.2f});']
    if t=="claudehero":
        cw=find(p["codeword"]); pw=find(p["princword"])
        js.append(f'tl.fromTo("#cl{i}",{{opacity:0,scale:0.85,y:20}},{{opacity:1,scale:1,y:0,duration:0.45,ease:"back.out(1.6)"}},{s+0.02:.2f});')
        js.append(f'tl.fromTo("#pw{i}",{{opacity:0,scale:1.2}},{{opacity:1,scale:1,duration:0.26,ease:"back.out(2)"}},{max(s+0.3,pw-0.25):.2f});')
        js.append(f'tl.fromTo("#ps{i}",{{scaleX:0}},{{scaleX:1,duration:0.22,ease:"power3.in"}},{pw+0.1:.2f});')
        js.append(f'tl.to("#pw{i}",{{color:"{GREY}",opacity:0.55,duration:0.22}},{pw+0.12:.2f});')
    if t=="hrgraph":
        nw=find(p["numword"])
        js.append(f'tl.fromTo("#hl{i}",{{attr:{{"stroke-dashoffset":820}}}},{{attr:{{"stroke-dashoffset":0}},duration:1.2,ease:"power2.out"}},{s+0.15:.2f});')
        js.append(f'tl.to("#ha{i}",{{opacity:1,duration:0.6,ease:"power1.out"}},{s+0.5:.2f});')
        js.append(f'tl.fromTo("#hn{i}",{{opacity:0,scale:1.5,y:-10}},{{opacity:1,scale:1,y:0,duration:0.34,ease:"back.out(2.2)"}},{max(s+0.3,nw-0.1):.2f});')
    if t=="twopill":
        w1=find(p["w1"]); w2=find(p["w2"])
        js.append(f'tl.fromTo("#pa{i}",{{opacity:0,x:-40,scale:0.9}},{{opacity:1,x:0,scale:1,duration:0.3,ease:"back.out(1.9)"}},{w1:.2f});')
        js.append(f'tl.fromTo("#pb{i}",{{opacity:0,x:-40,scale:0.9}},{{opacity:1,x:0,scale:1,duration:0.3,ease:"back.out(1.9)"}},{w2:.2f});')
    if t=="genflow":
        s1w=find(p["s1w"]); s2w=find(p["s2w"])
        js.append(f'tl.fromTo("#fs{i}_0",{{opacity:0,y:-24,scale:0.9}},{{opacity:1,y:0,scale:1,duration:0.28,ease:"back.out(1.9)"}},{max(s+0.15,s1w-0.1):.2f});')
        js.append(f'tl.fromTo("#fa{i}_0",{{opacity:0}},{{opacity:1,duration:0.2}},{s2w-0.45:.2f});')
        js.append(f'tl.fromTo("#fs{i}_1",{{opacity:0,y:-24,scale:0.9}},{{opacity:1,y:0,scale:1,duration:0.3,ease:"back.out(2)"}},{s2w:.2f});')
    if t=="asciiwin":
        js.append(f'var av{i}={js_s(ASCII)};tl.to({{n:0}},{{n:av{i}.length,duration:3.4,ease:"none",onUpdate:function(){{document.getElementById("ax{i}").textContent=av{i}.slice(0,Math.round(this.targets()[0].n));}}}},{s+0.1:.2f});')
    if t=="terminalsp":
        js.append(f'tl.fromTo("#nb{i}",{{opacity:0,scale:0.6}},{{opacity:1,scale:1,duration:0.28,ease:"back.out(2)"}},{s+0.05:.2f});')
        js.append(f'tl.fromTo("#sk{i}",{{opacity:0,x:-40}},{{opacity:1,x:0,duration:0.3,ease:"power3.out"}},{s+0.12:.2f});')
        cw=find(p["cmdword"]); qw=find(p["qword"]); bw=find(p["betterword"])
        js.append(f'var cv{i}={js_s(CMD_SP)};tl.to({{n:0}},{{n:cv{i}.length,duration:1.1,ease:"none",onUpdate:function(){{document.getElementById("cmd{i}").textContent=cv{i}.slice(0,Math.round(this.targets()[0].n));}}}},{cw-0.2:.2f});')
        js.append(f'tl.fromTo("#qh{i}",{{opacity:0,y:12}},{{opacity:1,y:0,duration:0.24,ease:"power3.out"}},{qw:.2f});')
        for j in range(3): js.append(f'tl.fromTo("#q{i}_{j}",{{opacity:0,x:-30}},{{opacity:1,x:0,duration:0.24,ease:"back.out(1.8)"}},{qw+0.35+j*0.42:.2f});')
        js.append(f'tl.fromTo("#qbt{i}",{{opacity:0,scale:0.85}},{{opacity:1,scale:1,duration:0.3,ease:"back.out(2)"}},{bw:.2f});')
    if t=="hooksimg":
        js.append(f'tl.fromTo("#hw{i}",{{opacity:0,scale:0.9,y:16}},{{opacity:1,scale:1,y:0,duration:0.4,ease:"back.out(1.6)"}},{s+0.05:.2f});')
        js.append(f'tl.fromTo("#hk{i}",{{opacity:0,scale:0.55}},{{opacity:1,scale:1,duration:0.42,ease:"back.out(1.9)"}},{s+0.18:.2f});')
        js.append(f'tl.to("#hk{i}",{{rotation:5,transformOrigin:"50% 16%",duration:0.6,yoyo:true,repeat:5,ease:"sine.inOut"}},{s+0.55:.2f});')
        js.append(f'tl.fromTo("#hb{i}",{{opacity:0,y:22,scale:0.8}},{{opacity:1,y:0,scale:1,duration:0.34,ease:"back.out(2)"}},{s+0.32:.2f});')
    if t=="hookflow":
        ns=len(p["steps"])
        for j in range(ns): js.append(f'tl.fromTo("#fs{i}_{j}",{{opacity:0,y:-24,scale:0.9}},{{opacity:1,y:0,scale:1,duration:0.26,ease:"back.out(1.9)"}},{s+0.2+j*0.5:.2f});')
        for j in range(ns-1): js.append(f'tl.fromTo("#fa{i}_{j}",{{opacity:0}},{{opacity:1,duration:0.2}},{s+0.42+j*0.5:.2f});')
    if t=="githubcard":
        ew=find(p["earlyword"]); gw=find(p["logoword"])
        js.append(f'tl.fromTo("#nb{i}",{{opacity:0,scale:0.6}},{{opacity:1,scale:1,duration:0.28,ease:"back.out(2)"}},{s+0.05:.2f});')
        js.append(f'tl.fromTo("#gt{i}",{{opacity:0,x:-30}},{{opacity:1,x:0,duration:0.3,ease:"power3.out"}},{s+0.15:.2f});')
        js.append(f'tl.fromTo("#gl{i}",{{opacity:0,scale:0.5,rotate:-16}},{{opacity:1,scale:1,rotate:0,duration:0.45,ease:"back.out(1.8)"}},{max(s+0.25,ew-0.1):.2f});')
        js.append(f'tl.fromTo("#gc{i}",{{opacity:0,scale:0.8}},{{opacity:1,scale:1,duration:0.3,ease:"back.out(2)"}},{gw:.2f});')
    if t=="mdfile":
        fw=find(p["fileword"]); base=max(s+0.2,fw-0.6)
        for j in range(len(MD)): js.append(f'tl.fromTo("#md{i}_{j}",{{opacity:0,x:-26}},{{opacity:1,x:0,duration:0.2,ease:"power2.out"}},{base+j*0.32:.2f});')
    if t=="agents":
        lw=find(p["logoword"]); dw=find(p["drawword"]); stw=find(p["stampword"])
        for j in range(3): js.append(f'tl.fromTo("#ag{i}_{j}",{{opacity:0,y:24,scale:0.7}},{{opacity:1,y:0,scale:1,duration:0.3,ease:"back.out(2)"}},{max(s+0.15,lw-0.3)+j*0.22:.2f});')
        js.append(f'tl.fromTo("#al{i}",{{attr:{{"stroke-dashoffset":780}}}},{{attr:{{"stroke-dashoffset":0}},duration:1.5,ease:"power2.inOut"}},{max(s+0.35,dw-0.3):.2f});')
        js.append(f'tl.to("#aa{i}",{{opacity:1,duration:0.7,ease:"power1.out"}},{max(s+0.6,dw):.2f});')
        js.append(f'tl.fromTo("#rs{i}",{{opacity:0,scale:1.5,rotate:-7}},{{opacity:1,scale:1,rotate:-4,duration:0.32,ease:"back.out(2)"}},{stw:.2f});')
    if t=="terminalsec":
        js.append(f'tl.fromTo("#nb{i}",{{opacity:0,scale:0.6}},{{opacity:1,scale:1,duration:0.28,ease:"back.out(2)"}},{s+0.05:.2f});')
        js.append(f'tl.fromTo("#sk{i}",{{opacity:0,x:-40}},{{opacity:1,x:0,duration:0.3,ease:"power3.out"}},{s+0.12:.2f});')
        cw=find(p["cmdword"]); scw=find(p["scanword"]); vw=find(p["vulnword"]); dnw=find(p["doneword"])
        js.append(f'var cv{i}={js_s(CMD_SEC)};tl.to({{n:0}},{{n:cv{i}.length,duration:0.9,ease:"none",onUpdate:function(){{document.getElementById("cmd{i}").textContent=cv{i}.slice(0,Math.round(this.targets()[0].n));}}}},{cw:.2f});')
        js.append(f'tl.fromTo("#sc{i}",{{opacity:0,y:10}},{{opacity:1,y:0,duration:0.24,ease:"power3.out"}},{scw:.2f});')
        js.append(f'tl.fromTo("#v{i}_0",{{opacity:0,x:-26}},{{opacity:1,x:0,duration:0.22,ease:"back.out(1.7)"}},{vw:.2f});')
        js.append(f'tl.fromTo("#v{i}_1",{{opacity:0,x:-26}},{{opacity:1,x:0,duration:0.22,ease:"back.out(1.7)"}},{vw+0.3:.2f});')
        js.append(f'tl.fromTo("#vd{i}",{{opacity:0,scale:0.85}},{{opacity:1,scale:1,duration:0.3,ease:"back.out(2)"}},{dnw:.2f});')
    if t=="ctacount":
        vw=find(p["vuoiword"]); ow=find(p["ottoword"]); pw=find(p["promptword"])
        js.append(f'tl.fromTo("#ck{i}",{{opacity:0,y:22,scale:0.95}},{{opacity:1,y:0,scale:1,duration:0.34,ease:"back.out(1.8)"}},{max(s+0.1,vw-0.15):.2f});')
        js.append(f'tl.fromTo("#c8{i}",{{scale:1.45}},{{scale:1,duration:0.3,ease:"back.out(2.4)"}},{ow:.2f});')
        js.append(f'tl.fromTo("#cc{i}",{{opacity:0,y:18}},{{opacity:1,y:0,duration:0.28,ease:"back.out(1.9)"}},{pw:.2f});')
    if t=="ctacomment":
        js.append(f'tl.fromTo("#ck{i}",{{opacity:0,scale:1.3}},{{opacity:1,scale:1,duration:0.3,ease:"back.out(2)"}},{find(p["ctaword"]):.2f});')
        js.append(f'tl.fromTo("#cu{i}",{{opacity:0,y:16}},{{opacity:1,y:0,duration:0.28,ease:"power3.out"}},{find(p["ctaword"])+0.3:.2f});')
        js.append(f'tl.fromTo("#mt{i}",{{scaleX:0}},{{scaleX:1,duration:1.1,ease:"power2.out"}},{s+0.4:.2f});')
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
#grid{{position:absolute;inset:-40px;background-image:linear-gradient(rgba(240,129,63,0.05) 1px,transparent 1px),linear-gradient(90deg,rgba(240,129,63,0.05) 1px,transparent 1px);background-size:110px 110px}}
#glow{{position:absolute;top:120px;left:280px;width:520px;height:520px;border-radius:50%;background:radial-gradient(circle,rgba(240,129,63,0.24),transparent 65%);filter:blur(22px)}}
.pt{{position:absolute;border-radius:50%;background:{A};box-shadow:0 0 12px {A}}}
.stk{{position:absolute;left:0;width:520px;height:2px;background:linear-gradient(90deg,transparent,{A},transparent);opacity:0.3}}
.beat{{position:absolute;top:0;left:0;width:1080px;height:864px}}
.inner{{position:absolute;top:46px;left:60px;right:60px;height:740px;display:flex;flex-direction:column;justify-content:center;gap:22px}}
.eyebrow{{color:{A};font-size:32px;font-weight:800;letter-spacing:6px;text-transform:uppercase;display:flex;align-items:center;gap:13px}}
.ebdot{{width:14px;height:14px;border-radius:50%;background:{A};box-shadow:0 0 14px {A}}}
/* claudehero */
.inner.claudehero{{align-items:center;justify-content:center}}
.chwrap{{display:flex;flex-direction:column;align-items:center;gap:34px}}
.cclogo{{width:860px;max-width:96%;object-fit:contain;border-radius:16px;border:4px solid {A};box-shadow:0 0 48px rgba(240,129,63,0.5)}}
.princrow{{position:relative;display:inline-block}}
.princ{{color:#fff;font-size:96px;font-weight:900;letter-spacing:-1px;text-transform:uppercase;text-shadow:0 0 26px {GL}}}
.strike{{position:absolute;left:-10px;right:-10px;top:52%;height:12px;background:{RED};border-radius:8px;transform-origin:left center;transform:scaleX(0);box-shadow:0 0 22px {REDD}}}
/* hrgraph */
.inner.hrgraph{{align-items:stretch}}
.hrsvg{{width:100%;height:360px}}
.hrlabel{{display:flex;align-items:baseline;gap:24px;justify-content:center}}
.hrnum{{color:#fff;font-size:170px;font-weight:900;line-height:0.8;letter-spacing:-5px;text-shadow:0 0 38px {GL}}}
.hrunit{{color:{A};font-size:42px;font-weight:900;text-transform:uppercase}}
/* twopill */
.inner.twopill{{align-items:stretch}}
.pill{{font-size:74px;font-weight:900;text-transform:uppercase;border-radius:24px;padding:30px 40px;letter-spacing:-1px;text-align:center}}
.pill.p1{{color:#fff;background:rgba(40,30,24,0.85);border:2px solid {AD};box-shadow:0 0 30px {GL}}}
.pill.p2{{color:#1a0f06;background:{A};box-shadow:0 0 40px {A}}}
/* flow (genflow + hookflow) */
.inner.genflow,.inner.hookflow{{align-items:center}}
.flow{{display:flex;flex-direction:column;align-items:center;gap:16px;width:100%}}
.fstep{{width:88%;text-align:center;color:#fff;font-size:62px;font-weight:900;text-transform:uppercase;background:rgba(40,30,24,0.85);border:2px solid {AD};border-radius:22px;padding:30px;box-shadow:0 0 22px {GL};letter-spacing:-1px}}
.fstep.last{{color:#1a0f06;background:{A};border-color:{A};box-shadow:0 0 40px {A}}}
.farr{{color:{A};font-size:64px;font-weight:900;line-height:0.5}}
/* window */
.win{{background:#0c0f0e;border:2px solid {AD};border-radius:22px;overflow:hidden;box-shadow:0 0 44px {GL}}}
.wbar{{display:flex;align-items:center;gap:12px;background:#161b19;padding:16px 22px;border-bottom:1px solid rgba(255,255,255,0.06)}}
.td{{width:18px;height:18px;border-radius:50%}}.td.r{{background:#ff5f57}}.td.y{{background:#febc2e}}.td.g{{background:#28c840}}
.wtitle{{color:#9aa29a;font-size:27px;font-weight:700;margin-left:10px;font-family:ui-monospace,"SF Mono",Menlo,monospace}}
.wmd{{margin-left:auto;color:#1a0f06;background:{A};font-size:20px;font-weight:900;border-radius:7px;padding:3px 10px}}
.wbody{{padding:26px 30px;font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace}}
.asciibody{{min-height:560px;display:flex;align-items:center;justify-content:center}}
.asciipre{{color:{AB};font-size:30px;line-height:1.18;font-weight:600;white-space:pre;text-shadow:0 0 10px rgba(240,129,63,0.35)}}
.cur{{color:{A};animation:blink 1s steps(1) infinite}}@keyframes blink{{50%{{opacity:0}}}}
.term{{min-height:520px}}
.tprompt{{color:#e7efe9;font-size:38px;font-weight:700;margin-bottom:22px}}
.tcmd{{color:{AB}}}
.qhead{{color:#9aa29a;font-size:30px;font-weight:600;margin-bottom:14px}}
.qblock{{display:flex;flex-direction:column;gap:14px;margin-bottom:22px}}
.qline{{color:{AB};font-size:36px;font-weight:700;line-height:1.25}}
.qbetter{{color:#1a0f06;background:{A};display:inline-block;align-self:flex-start;font-size:32px;font-weight:900;border-radius:12px;padding:12px 22px;font-family:"Montserrat",sans-serif;box-shadow:0 0 26px {A}}}
.scan{{color:#9aa29a;font-size:34px;font-weight:600;margin-bottom:18px}}
.vuln{{color:{WARN};font-size:36px;font-weight:700;line-height:1.3;margin-bottom:12px}}
.vdone{{color:#1a0f06;background:{A};display:inline-block;align-self:flex-start;font-size:34px;font-weight:900;border-radius:12px;padding:12px 24px;margin-top:10px;font-family:"Montserrat",sans-serif;box-shadow:0 0 26px {A}}}
/* hooks card (ricreata) */
.inner.hooksimg{{align-items:center;justify-content:center}}
.hkcard{{display:flex;flex-direction:column;align-items:center;gap:24px;width:100%}}
.hkwin{{width:94%}}
.hkbody{{padding:24px 30px;font-family:ui-monospace,"SF Mono",Menlo,monospace}}
.hkwelcome{{color:{AB};font-size:25px;font-weight:600;border:1px solid {AD};border-radius:10px;padding:12px 16px;margin-bottom:8px}}
.hkmid{{display:flex;align-items:center;justify-content:center;padding:8px 0}}
.hooksvg{{height:240px;width:auto;filter:drop-shadow(0 0 14px rgba(242,210,63,0.5))}}
.hklogin{{color:#9aa29a;font-size:23px;font-weight:600;margin-top:8px}}
.hklogin b{{color:{AB}}}
.hkbig{{color:#fff;font-size:160px;font-weight:900;letter-spacing:-3px;line-height:0.85;text-shadow:0 0 42px {GL}}}
/* githubcard */
.inner.githubcard{{align-items:center}}
.ghtop{{color:#fff;font-size:54px;font-weight:900;text-transform:uppercase;letter-spacing:-1px}}
.ghwrap{{display:flex;flex-direction:column;align-items:center;gap:26px;margin-top:14px}}
.ghlogo{{height:280px;width:280px;object-fit:contain;filter:drop-shadow(0 0 30px rgba(255,255,255,0.25))}}
.ghchip{{color:#1a0f06;background:{A};font-size:46px;font-weight:900;text-transform:uppercase;border-radius:16px;padding:14px 34px;box-shadow:0 0 32px {A}}}
/* mdfile */
.inner.mdfile{{align-items:stretch}}
.mdbody{{min-height:540px;display:flex;flex-direction:column;gap:12px;line-height:1.25}}
.md{{font-size:34px;font-weight:600}}
.md.h1{{color:#fff;font-size:50px;font-weight:900;margin-bottom:4px}}
.md.h2{{color:{A};font-size:40px;font-weight:900;margin-top:10px}}
.md.li{{color:#c9cfca}}.md.tx{{color:#9aa29a}}
/* agents */
.inner.agents{{align-items:flex-start}}
.agentrow{{display:flex;gap:26px;justify-content:center;width:100%;margin-bottom:6px}}
.agent{{display:flex;flex-direction:column;align-items:center;gap:14px;background:rgba(20,14,8,0.7);border:2px solid {AD};border-radius:22px;padding:26px 30px;box-shadow:0 0 22px {GL}}}
.agimg{{height:96px;width:96px;object-fit:contain}}
.aglbl{{color:#fff;font-size:30px;font-weight:800;text-transform:uppercase;letter-spacing:1px}}
.agsvg{{width:100%;height:230px}}
.rgstamp{{align-self:flex-start;color:#1a0f06;background:{A};font-size:58px;font-weight:900;text-transform:uppercase;border-radius:16px;padding:12px 32px;box-shadow:0 0 36px {A}}}
/* count / chip / cta */
.statrow{{display:flex;align-items:flex-end;gap:26px}}.statrow.ctr{{justify-content:center}}
.inner.ctacount{{align-items:center;text-align:center}}
.big{{color:#fff;font-size:230px;font-weight:900;line-height:0.82;letter-spacing:-5px;text-shadow:0 0 38px {GL}}}
.unit{{color:{A};font-size:46px;font-weight:900;text-transform:uppercase;line-height:1.05;padding-bottom:24px}}
.chip{{color:{A};font-size:42px;font-weight:800;text-transform:uppercase;border:2px solid {AD};border-radius:40px;padding:14px 30px;background:rgba(20,14,8,0.7);box-shadow:0 0 18px {GL}}}
.chip.ctr{{align-self:center}}
.inner.ctacount{{align-items:center;text-align:center}}
.inner.ctacomment{{align-items:center;justify-content:center;background:rgba(20,14,8,0.9);border:2px solid {A};border-radius:26px;padding:44px;box-shadow:0 0 46px {GL}}}
.kw{{color:#fff;font-size:96px;font-weight:900;line-height:0.98;letter-spacing:-2px;text-align:center;text-shadow:0 0 30px {GL}}}
.kw.ctaq{{font-size:92px;line-height:1.04}}.kw.ctaq .acc{{display:inline-block}}
.kw .acc{{color:{A};text-shadow:0 0 26px {A}}}
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
print(f"reel2 v2: {len(BEATS)} beat, total {TOTAL}s")
for i,((trig,t,p),s,e) in enumerate(zip(BEATS,starts,ends)): print(f"  {s:5.2f}-{e:5.2f} {t:11s} {trig}")
