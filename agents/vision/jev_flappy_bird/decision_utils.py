"""
Physics (from flappy_bird_gymnasium/envs/constants.py, screen 288x512):
  PLAYER_MAX_VEL_Y = 10 px/frame  → norm max vel = 1.00
  PLAYER_ACC_Y     =  1 px/frame  → norm gravity  = 0.10/step
  PLAYER_FLAP_ACC  = -9 px/frame  → norm flap vel = -0.90
  PIPE_VEL_X       = -4 px/frame  → PIPE_SPEED = 4/288 ≈ 0.01389/step
  VEL_SCALE        = 10/512       → norm Δy per step per norm vel unit
  bird_x           = 288*0.2 = 57.6 px  (fixed)
  PLAYER_WIDTH     = 34 px
  PIPE_WIDTH       = 52 px
  Collision start: pipe_x < (57.6+34)/288 ≈ 0.318
  Collision end:   pipe_x < (57.6-52)/288 ≈ 0.019
  pipe_gap default = 100 px → gap_half_norm ≈ 100/(2*512) ≈ 0.098
"""

BIRD_X       = 0.20
PIPE_CLEAR_X = 0.019    # pipe has fully passed the bird when pipe_x < this
COLLISION_X  = 0.318    # pipe starts overlapping bird when pipe_x < this
PIPE_SPEED   = 4 / 288
VEL_SCALE    = 10 / 512
GRAVITY      = 1 / 10
FLAP_VEL     = -9 / 10
MAX_VEL      = 10 / 10
MARGIN       = 0.04
MAX_STEPS    = 12        # hard cap on look-ahead steps (beyond this projections are noisy)
GROUND_Y     = 0.73      # normalized safe floor


def _project_minmax(y, vel, steps):
    """Simulate N steps under gravity (no flap). Returns (end_y, min_y, max_y)."""
    min_y = y
    max_y = y
    for _ in range(steps):
        vel = min(vel + GRAVITY, MAX_VEL)
        y  += vel * VEL_SCALE
        if y < min_y: min_y = y
        if y > max_y: max_y = y
    return y, min_y, max_y


def format_state(obs):
    last_x, last_top, last_bot = obs[0], obs[1], obs[2]
    next_x, next_top, next_bot = obs[3], obs[4], obs[5]
    nn_top, nn_bot             = obs[7], obs[8]
    player_y  = obs[9]
    player_vel = obs[10]

    # Active pipe = last (obs[0]) while still physically overlapping the bird,
    # else next pipe (obs[3]).
    if last_x > PIPE_CLEAR_X:
        active_x, active_top, active_bot = last_x, last_top, last_bot
        ahead_top, ahead_bot            = next_top, next_bot
    else:
        active_x, active_top, active_bot = next_x, next_top, next_bot
        ahead_top, ahead_bot            = nn_top, nn_bot

    # Detect off-screen default pipe (no real pipe nearby)
    if active_top < 0.01 and active_bot > 0.98:
        active_top, active_bot = 0.05, GROUND_Y

    gap_center = (active_top + active_bot) / 2.0

    # Steps until pipe fully clears (or capped).  This spans the whole
    # relevant window: from now through the end of the collision.
    steps_ahead = max(1, min(int((active_x - PIPE_CLEAR_X) / PIPE_SPEED), MAX_STEPS))

    # No-flap trajectory: where will the bird be (and what's the range)?
    _, nf_min, nf_max = _project_minmax(player_y, player_vel, steps_ahead)

    top_limit = active_top + MARGIN
    bot_limit = active_bot - MARGIN

    if nf_max > bot_limit:
        # Will hit bottom — only flap if it won't overshoot above top
        _, fl_min, _ = _project_minmax(player_y, FLAP_VEL, steps_ahead)
        if fl_min < top_limit:
            pipe_threat = "approaching bottom pipe"
            advice = (f"DO NOT flap — flapping would send bird to y={fl_min:.3f}, "
                      f"above the gap top at {active_top:.3f}. "
                      f"Stay the course; gravity moves the bird toward the gap.")
        else:
            pipe_threat = "will hit BOTTOM pipe"
            advice = "Flap now to rise into the gap."
    elif nf_min < top_limit:
        pipe_threat = "will hit TOP pipe"
        advice = "Do not flap; let the bird fall into the gap."
    else:
        pipe_threat = "on track through gap"
        advice = "Maintain course; do not flap."

    ahead_center = (ahead_top + ahead_bot) / 2.0
    motion = "falling" if player_vel > 0.05 else ("rising" if player_vel < -0.05 else "level")

    return (
        f"Active pipe: dist={active_x:.2f}, gap=[{active_top:.3f},{active_bot:.3f}] "
        f"(center {gap_center:.3f}). "
        f"Bird: y={player_y:.3f}, {motion} (vel={player_vel:+.2f}). "
        f"No-flap range over {steps_ahead} steps: [{nf_min:.3f},{nf_max:.3f}] — {pipe_threat}. "
        f"{advice} "
        f"Next gap center: {ahead_center:.3f}."
    )


question = "What is the correct action for the bird right now?"

options = {
    "flap": "Flap wings to rise upward.",
    "no_flap": "Do not flap; let the bird fall with gravity.",
}
