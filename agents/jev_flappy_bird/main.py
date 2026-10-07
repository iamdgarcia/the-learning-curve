import time
import pygame
import flappy_bird_gymnasium
import gymnasium
from concurrent.futures import ThreadPoolExecutor
from engine import LayaJevEngine
from decision_utils import format_state, options, question

env    = gymnasium.make("FlappyBird-v0", render_mode="human", use_lidar=False)
engine = LayaJevEngine(repo_id="inferenceprince/laya-onnx-int8")

obs, _ = env.reset()

# ── FPS overlay ──────────────────────────────────────────────────────────────
pygame.font.init()
_font       = pygame.font.SysFont("monospace", 22, bold=True)
_font_big   = pygame.font.SysFont("monospace", 28, bold=True)
_times = []

def _overlay(fps: float, score: int, probs: dict, action: int) -> None:
    surf = pygame.display.get_surface()
    if surf is None:
        return
    h = surf.get_height()

    # Top: FPS / Score
    txt = _font.render(f" FPS {fps:4.1f}  Score {score} ", True, (255, 255, 0), (0, 0, 0))
    surf.blit(txt, (4, 4))

    # Bottom: decision label + probability bars
    bar_h   = 18
    bar_gap = 4
    bar_w   = 100
    items   = [("flap", (0, 255, 128)), ("no_flap", (255, 80, 80))]
    n       = len(items)
    block_h = n * (bar_h + bar_gap) - bar_gap
    label_h = 24
    total_h = label_h + bar_gap + block_h
    base_y  = h - total_h - 4

    label     = "FLAP" if action else "FALL"
    label_col = (0, 255, 128) if action else (255, 80, 80)
    dec_txt   = _font_big.render(f" {label} ", True, label_col, (0, 0, 0))
    surf.blit(dec_txt, (4, base_y))

    bar_y0 = base_y + label_h + bar_gap
    for i, (key, col) in enumerate(items):
        p    = probs.get(key, 0.0)
        fill = int(bar_w * p)
        y    = bar_y0 + i * (bar_h + bar_gap)
        pygame.draw.rect(surf, (40, 40, 40), (4, y, bar_w, bar_h))
        pygame.draw.rect(surf, col,          (4, y, fill,  bar_h))
        lbl = _font.render(f" {key}: {p*100:4.1f}% ", True, (255, 255, 255), (0, 0, 0))
        surf.blit(lbl, (4 + bar_w + 2, y))

    pygame.display.flip()

# ── Main loop with pipelined inference ───────────────────────────────────────
with ThreadPoolExecutor(max_workers=1) as pool:
    # Start first inference before entering the loop
    fut = pool.submit(engine.predict_choice,
                      state_text=format_state(obs),
                      question=question,
                      options=options)

    step, score = 0, 0
    while True:
        t0 = time.perf_counter()

        # While inference runs in background (ONNX releases GIL), keep the
        # pygame event queue drained so the window stays responsive.
        while not fut.done():
            pygame.event.pump()
            time.sleep(0.005)

        probs  = fut.result()
        action = 1 if probs["flap"] > probs["no_flap"] else 0

        obs, reward, terminated, _, info = env.step(action)
        score = info.get("score", 0)

        # Kick off next inference immediately so it overlaps with bookkeeping
        if not terminated:
            fut = pool.submit(engine.predict_choice,
                              state_text=format_state(obs),
                              question=question,
                              options=options)

        # FPS (rolling average over last 20 steps)
        _times.append(time.perf_counter() - t0)
        if len(_times) > 20:
            _times.pop(0)
        fps = 1.0 / (sum(_times) / len(_times))

        _overlay(fps, score, probs, action)

        # Single-line log instead of multi-line print
        print(f"step={step:4d}  score={score:3d}  {'FLAP' if action else 'fall'}  "
              f"p={probs['flap']:.2f}  fps={fps:.1f}", flush=False)

        step += 1
        if terminated:
            break

print(f"\nGame Over!  Final score: {score}")
env.close()
