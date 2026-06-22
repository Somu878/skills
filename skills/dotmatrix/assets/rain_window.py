"""rain_window.py — reference dot-matrix scene: rain on a window at night.

A different mood from cozy_study: looking out a rain-streaked window at a
distant city. Rain falls, city lights twinkle, and occasional lightning
briefly washes the sky. Seamless loop (all motion is periodic in t).

Demonstrates the same scene_color contract with a completely different
visual vocabulary. See references/writing-a-scene.md.
"""

import math

# --------------------------------------------------------------------------- #
# Scene dimensions + background
# --------------------------------------------------------------------------- #
SCENE_W = 64
SCENE_H = 40
BG = (8, 10, 18)   # deep wet-night blue

# --------------------------------------------------------------------------- #
# Palette
# --------------------------------------------------------------------------- #
WALL       = (22, 20, 26)
FRAME      = (45, 42, 48)
GLASS      = (12, 16, 28)
SKY_TOP    = (8, 12, 24)
SKY_BOT    = (24, 28, 48)
CLOUD      = (30, 34, 50)
RAIN       = (110, 130, 160)
RAIN_BRIGHT= (160, 180, 210)
LIGHT_RED  = (220, 60, 60)
LIGHT_YEL  = (220, 180, 70)
LIGHT_BLU  = (70, 140, 255)
LIGHT_WHT  = (200, 210, 220)
SILLS      = (55, 52, 58)
MUG        = (180, 90, 70)
MUG_STEAM  = (180, 190, 200)

# --------------------------------------------------------------------------- #
# Math helpers
# --------------------------------------------------------------------------- #
def _clamp(v, lo=0, hi=255):
    return max(lo, min(hi, int(v)))


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(_clamp(a[i] + (b[i] - a[i]) * t) for i in range(3))


def smoothstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0 + 1e-9)))
    return t * t * (3 - 2 * t)


def in_rect(x, y, x0, y0, x1, y1):
    return x0 <= x < x1 and y0 <= y < y1


def in_ellipse(x, y, cx, cy, rx, ry):
    dx = (x - cx) / (rx + 1e-9)
    dy = (y - cy) / (ry + 1e-9)
    return dx * dx + dy * dy <= 1.0


def dist(x, y, cx, cy):
    return math.hypot(x - cx, y - cy)


# --------------------------------------------------------------------------- #
# Precomputed city lights: (x, y, color, twinkle frequency, phase)
# --------------------------------------------------------------------------- #
CITY_LIGHTS = [
    (42, 18, LIGHT_RED, 3, 0.0),
    (48, 14, LIGHT_YEL, 2, 0.2),
    (55, 22, LIGHT_BLU, 4, 0.5),
    (38, 24, LIGHT_WHT, 5, 0.1),
    (51, 19, LIGHT_YEL, 2, 0.7),
    (44, 12, LIGHT_RED, 6, 0.3),
    (58, 16, LIGHT_WHT, 3, 0.8),
    (40, 20, LIGHT_BLU, 4, 0.4),
]

# Rain streaks: (x, speed phase, length, brightness phase)
RAINS = [
    (12, 0.0, 6, 0.0),
    (18, 0.15, 8, 0.3),
    (25, 0.35, 5, 0.6),
    (31, 0.55, 9, 0.1),
    (37, 0.72, 7, 0.8),
    (44, 0.45, 6, 0.2),
    (50, 0.88, 8, 0.5),
    (56, 0.22, 5, 0.9),
    (8, 0.62, 7, 0.4),
    (22, 0.05, 6, 0.7),
    (35, 0.78, 9, 0.15),
    (47, 0.92, 7, 0.55),
]


# --------------------------------------------------------------------------- #
# The scene
# --------------------------------------------------------------------------- #
def scene_color(gx, gy, t, W, H):
    # --- wall and window frame ---
    col = WALL

    # window glass area
    wx0, wx1 = int(W * 0.12), int(W * 0.88)
    wy0, wy1 = int(H * 0.10), int(H * 0.78)
    in_window = in_rect(gx, gy, wx0, wy0, wx1, wy1)

    # frame (border around glass)
    on_frame = (
        in_rect(gx, gy, wx0 - 2, wy0 - 2, wx1 + 2, wy0) or   # top
        in_rect(gx, gy, wx0 - 2, wy1, wx1 + 2, wy1 + 2) or   # bottom
        in_rect(gx, gy, wx0 - 2, wy0 - 2, wx0, wy1 + 2) or   # left
        in_rect(gx, gy, wx1, wy0 - 2, wx1 + 2, wy1 + 2)      # right
    )
    if on_frame:
        col = FRAME
        return col

    if in_window:
        # sky gradient
        p = (gy - wy0) / max(1, wy1 - wy0)
        col = mix(SKY_TOP, SKY_BOT, p)

        # clouds
        cloud_y = wy0 + 4 + math.sin(t * math.pi * 2) * 2
        cloud1 = smoothstep(6.0, 0.0, dist(gx, gy, W * 0.55, cloud_y))
        cloud2 = smoothstep(5.0, 0.0, dist(gx, gy, W * 0.75, cloud_y + 5))
        col = mix(col, CLOUD, max(cloud1, cloud2) * 0.4)

        # lightning flash: brief bright wash
        flash = 0.0
        for freq, phase, width in [(2, 0.0, 0.03), (5, 0.4, 0.02)]:
            pulse = math.sin(t * math.pi * 2 * freq + phase)
            flash = max(flash, smoothstep(1.0 - width, 1.0, pulse))
        if flash > 0:
            col = mix(col, (220, 230, 255), flash * 0.55)

        # distant city lights (twinkle)
        for lx, ly, lc, freq, phase in CITY_LIGHTS:
            if wx0 + 2 <= lx < wx1 - 2 and wy0 + 2 <= ly < wy1 - 2:
                twinkle = 0.7 + 0.3 * math.sin(t * math.pi * 2 * freq + phase * 2 * math.pi)
                d = dist(gx, gy, lx, ly)
                glow = smoothstep(2.5, 0.0, d) * twinkle
                if glow > 0:
                    col = mix(col, lc, glow * 0.6)

        # rain streaks on the window
        for rx, rphase, rlen, bphase in RAINS:
            phase = (t + rphase) % 1.0
            ry = wy0 + phase * (wy1 - wy0 - rlen)
            if ry <= gy < ry + rlen and abs(gx - rx) < 0.7:
                fade = 1.0 - abs(gy - (ry + rlen / 2)) / (rlen / 2 + 1e-9)
                fade = max(0.0, min(1.0, fade))
                bright = 0.6 + 0.4 * math.sin(t * math.pi * 2 * 3 + bphase * 2 * math.pi)
                col = mix(col, RAIN_BRIGHT if bright > 0.8 else RAIN, fade * bright * 0.55)

    # --- windowsill ---
    sill_y0, sill_y1 = int(H * 0.78), int(H * 0.86)
    if in_rect(gx, gy, 0, sill_y0, W, sill_y1):
        col = SILLS

    # --- mug on the sill ---
    mug_cx, mug_cy = W * 0.24, (sill_y0 + sill_y1) / 2.0 - 1
    if in_ellipse(gx, gy, mug_cx, mug_cy, 3.5, 3.0):
        col = MUG
    # mug rim
    if in_ellipse(gx, gy, mug_cx, mug_cy - 1.5, 2.8, 1.2):
        col = mix(MUG, (230, 210, 200), 0.4)

    # steam rising from mug
    for i in range(3):
        phase = (t + i / 3.0) % 1.0   # wraps seamlessly at t=1
        sx = mug_cx + math.sin(t * math.pi * 2 * 2 + i) * 1.2
        sy = mug_cy - 3 - phase * 5
        if in_ellipse(gx, gy, sx, sy, 1.0, 1.5):
            fade = 1.0 - phase
            col = mix(col, MUG_STEAM, fade * 0.35)

    return col
