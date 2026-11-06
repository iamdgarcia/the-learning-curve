#!/usr/bin/env python3
"""Score a short-form video script: python3 score.py draft.txt

One spoken line per line, the last line is the CTA. Hard fails cost 15, soft flags 5.
The loop in SKILL.md runs until the script scores 90+ with zero hard fails.
"""
import re, sys

HARD = [
    (r'—', 'em dash (nobody speaks one)'),
    (r';', 'semicolon'),
    (r"(?i)\bnot just\b.*\bbut\b", '"not just X but Y"'),
    (r"(?i)\bit'?s not (?:about )?\w+[^.]*?, it'?s\b", '"it\'s not X, it\'s Y"'),
    (r"(?i)here'?s the thing|let that sink in|read the (?:tiny|fine) print|the truth is|in today'?s|buckle up|imagine this|it'?s worth noting|at the end of the day|whether you'?re a", 'stage direction / filler'),
    (r"(?i)\b(spoiler|plot twist)\s*:|here'?s where it gets interesting|the best part\?", 'fake suspense'),
    (r'(?i)\b(delve|unlock|unleash|harness|leverage|seamless|robust|cutting[- ]edge|game[- ]?changer|revolutionary|transformative|landscape|realm|tapestry|elevate|empower|supercharge|deep dive|next level|dive in)\b', 'banned word'),
    (r'(?i)\b(?:brain is (?:trained|wired)|panic button|goldmine|secret sauce)\b', 'metaphor punchline'),
    (r"(?i)\bI tried this and\b", '"I tried this and" (only if it is TRUE, check the facts sheet)'),
]
NUM = r'\d|\b(?:one|two|three|four|five|six|seven|eight|nine|ten|twelve|twenty|fifty|hundred|thousand|million|billion)\b'

def sentences(t): return [s.strip() for s in re.split(r'(?<=[.?!])\s+|\n+', t) if s.strip()]

def score(text):
    hard, soft = [], []
    n = len(text.split()); secs = round(n / 4)
    if not 100 <= n <= 230: soft.append(f'length {n} words ≈ {secs}s (aim 120-200)')
    S = sentences(text); hook = S[0] if S else ''
    if len(hook.split()) > 22: soft.append(f'hook is {len(hook.split())} words (aim 22 or fewer)')
    if not re.search(NUM, hook, re.I) and not re.search(r'\b[A-Z][a-z]+[A-Z]?\w*\b', hook[1:]):
        soft.append('hook has no number and no named thing')
    for rx, why in HARD:
        if re.search(rx, text): hard.append(why)
    one_word = [s for s in S if len(s.split()) == 1]
    if len(one_word) > 1: hard.append(f'{len(one_word)} one-word dramatic sentences: {one_word[:3]}')
    long = [s for s in S if len(s.split()) > 32]
    if long: soft.append(f'{len(long)} sentence(s) over 32 words, e.g. "{long[0][:70]}…"')
    body_q = [s for s in S[1:-1] if s.endswith('?')]
    if len(body_q) > 1: soft.append(f'{len(body_q)} rhetorical questions in the body (only the hook should ask)')
    # a re-hook roughly every 8 s (~32 words): a number, a turn word or a reveal word
    rehook = re.compile(r'(?i)' + NUM + r'|\b(but|and then|turns out|the craziest|here\'s the trick|now|first|second|third|finally|which means)\b')
    gap, worst = 0, 0
    for s in S[1:-1]:
        gap = 0 if rehook.search(s) else gap + len(s.split()); worst = max(worst, gap)
    if worst > 32: soft.append(f'a stretch of {worst} words (≈{round(worst / 4)}s) with no re-hook (number, twist or "first/second…")')
    end = ' '.join(S[-2:]).lower()
    if not re.search(r'\b(comment|follow|link|watch|part)\b', end): soft.append('no clear CTA at the end')
    total = max(0, 100 - 15 * len(hard) - 5 * len(soft))
    return total, hard, soft, n, secs

if __name__ == '__main__':
    if len(sys.argv) < 2: sys.exit('usage: python3 score.py draft.txt')
    total, hard, soft, n, secs = score(open(sys.argv[1]).read())
    print(f'SCORE {total}/100 · {n} words ≈ {secs}s')
    for h in hard: print('  HARD  ', h)
    for s in soft: print('  soft  ', s)
    print('  PASS' if not hard and total >= 90 else '  REWRITE')
