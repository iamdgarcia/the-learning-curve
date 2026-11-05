import flappy_bird_gymnasium
import gymnasium
from engine import LayaJevEngine
from decision_utils import format_state, options, question

env = gymnasium.make("FlappyBird-v0", render_mode="rgb_array", use_lidar=False)
engine = LayaJevEngine(repo_id="inferenceprince/laya-onnx-int8")

RUNS = 1
MAX_STEPS_PER_RUN = 600
for run in range(RUNS):
    obs, _ = env.reset()
    pipes_passed = 0
    step = 0
    history = []
    prev_score = 0

    while True:
        state_desc = format_state(obs)
        probs = engine.predict_choice(state_text=state_desc, question=question, options=options)
        action = 1 if probs["flap"] > probs["no_flap"] else 0

        snap = {
            "step": step,
            "last_x":  round(obs[0],3),
            "last_top": round(obs[1],3), "last_bot": round(obs[2],3),
            "next_x":  round(obs[3],3),
            "next_top": round(obs[4],3), "next_bot": round(obs[5],3),
            "y": round(obs[9],3), "vel": round(obs[10],3),
            "action": action,
            "flap_p": round(probs["flap"],3),
        }
        history.append(snap)

        obs, reward, terminated, _, info = env.step(action)
        # score in info is the real pipe count
        score = info.get("score", 0)
        if score > prev_score:
            pipes_passed = score
            prev_score = score

        step += 1
        if terminated or step >= MAX_STEPS_PER_RUN:
            break

    print(f"\n=== RUN {run+1}  pipes={pipes_passed}  died step={step} ===")
    for h in history[-15:]:
        gap_c = round((h["next_top"]+h["next_bot"])/2, 3)
        last_c = round((h["last_top"]+h["last_bot"])/2, 3)
        print(f"  step={h['step']:3d} | last_x={h['last_x']:.2f} last_gap={last_c:.3f} | "
              f"next_x={h['next_x']:.2f} next_gap={gap_c:.3f} | "
              f"y={h['y']:.3f} vel={h['vel']:+.2f} | "
              f"{'FLAP' if h['action'] else 'fall'} (p={h['flap_p']:.2f})")

env.close()
