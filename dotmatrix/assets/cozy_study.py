"""cozy_study.py — reference dot-matrix scene: a cozy study at night.

Claude-FM-style ambient diorama: warm-lit room, bookshelf (left), fireplace
(right), hanging lamp (center), a character reading in a chair, a plant.
Fire flickers, lamp glows, character breathes, embers rise, plant sways.
Seamless loop (all motion is sine-of-t).

This is the reference scene bundled with the skill. Read it to learn the
scene_color contract, then write your own. See references/writing-a-scene.md.
"""

import math

# --------------------------------------------------------------------------- #
# Scene dimensions + background (required module-level attributes)
# --------------------------------------------------------------------------- #
SCENE_W = 64
SCENE_H = 40
BG = (12, 10, 22)   # deep night blue/black

# --------------------------------------------------------------------------- #
# Palette (cozy study at night)
# --------------------------------------------------------------------------- #
WALL        = (38, 28, 40)
FLOOR       = (26, 18, 14)
SHELF_WOOD  = (62, 40, 26)
BRICK       = (80, 45, 35)
FIREBOX     = (20, 12, 10)
FIRE_WARM   = (255, 150, 50)
FIRE_HOT    = (255, 220, 120)
EMBER       = (255, 180, 80)
LAMP        = (255, 210, 130)
CHAR_BODY   = (210, 160, 140)
CHAR_HAIR   = (60, 40, 30)
BOOK_HELD   = (70, 110, 170)
PLANT       = (60, 120, 60)
POT         = (110, 70, 45)
BOOKS = [(140, 50, 50), (50, 90, 140), (180, 150, 60), (70, 130, 70)]


# --------------------------------------------------------------------------- #
# Math helpers (the same ones every scene tends to need)
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
# The scene. gx, gy are grid coordinates; t is normalized time in [0,1).
# Returns an (r,g,b) tuple. Must be identical at t=0 and t→1 for a seamless
# loop — so every animated term is sin/cos of t.
# --------------------------------------------------------------------------- #
def scene_color(gx, gy, t, W, H):
    floor_y = H * 0.72

    # --- base: wall + floor ---
    if gy < floor_y:
        col = WALL
        # subtle lamp warmth on the wall
        lamp_cx, lamp_cy = W * 0.5, floor_y * 0.55
        warmth = smoothstep(W * 0.5, W * 0.1, dist(gx, gy, lamp_cx, lamp_cy)) * 0.5
        col = mix(col, LAMP, warmth * 0.15)
    else:
        col = FLOOR
        # floor warmer near the fire (right)
        fire_cx = W * 0.82
        warm = smoothstep(1.0, 0.0, abs(gx - fire_cx) / (W * 0.4)) * 0.25
        col = mix(col, FIRE_WARM, warm)

    # --- bookshelf (left) ---
    sx0, sx1 = int(W * 0.04), int(W * 0.30)
    sy0, sy1 = int(H * 0.08), int(floor_y - 2)
    if in_rect(gx, gy, sx0, sy0, sx1, sy1):
        if gx < sx0 + 1 or gx > sx1 - 2 or gy < sy0 + 1 or gy > sy1 - 2:
            col = SHELF_WOOD
        else:
            shelf_row = (gy - sy0) // 6
            local_y = (gy - sy0) % 6
            if local_y >= 5:
                col = SHELF_WOOD
            else:
                col = BOOKS[(shelf_row * 31 + (gx - sx0)) % len(BOOKS)]
                if (gx - sx0) % 9 == 0:
                    col = WALL

    # --- fireplace (right) ---
    fx0, fx1 = int(W * 0.70), int(W * 0.92)
    fy0, fy1 = int(H * 0.45), floor_y - 1
    on_fire_frame = (gx < fx0 + 1 or gx > fx1 - 2 or
                     gy < fy0 + 1 or gy > fy1 - 2)
    if in_rect(gx, gy, fx0, fy0, fx1, fy1):
        if on_fire_frame:
            col = BRICK
        else:
            flicker = 0.5 + 0.5 * math.sin(t * math.pi * 2 * 7 + gx * 0.7)
            flicker2 = 0.5 + 0.5 * math.sin(t * math.pi * 2 * 11 + gy * 0.5)
            flame_top = fy0 + 2 + flicker * 3
            base_y = fy1 - 2
            vy = max(0.0, min(1.0, (base_y - gy) / max(1, base_y - flame_top)))
            cx = (fx0 + fx1) / 2.0
            half_w = (fx1 - fx0) / 2.0 - 2
            local_w = half_w * (1.0 - vy * 0.5)
            if abs(gx - cx) < local_w and gy > flame_top:
                heat = (1.0 - vy) * (0.7 + 0.3 * flicker2)
                col = mix(FIRE_WARM, FIRE_HOT, heat)
            else:
                col = FIREBOX

    # --- fire glow on surroundings (animated) ---
    fire_c = ((fx0 + fx1) / 2.0, (fy0 + fy1) / 2.0)
    gd = dist(gx, gy, fire_c[0], fire_c[1])
    glow_pulse = 0.85 + 0.15 * math.sin(t * math.pi * 2 * 6)
    glow = smoothstep(W * 0.35, W * 0.05, gd) * 0.35 * glow_pulse
    if glow > 0.01 and not (in_rect(gx, gy, fx0, fy0, fx1, fy1)
                            and not on_fire_frame):
        col = mix(col, FIRE_WARM, glow)

    # --- hanging lamp (center top) + glow cone ---
    lamp_cx = W * 0.5
    lamp_cy = H * 0.10
    if abs(gx - lamp_cx) < 1 and gy < lamp_cy:
        col = (50, 45, 40)
    if in_ellipse(gx, gy, lamp_cx, lamp_cy, 3, 2):
        col = mix(LAMP, (200, 160, 90), 0.4)
    if lamp_cy < gy < floor_y:
        cone_dy = (gy - lamp_cy) / (floor_y - lamp_cy)
        cone_half_w = 3 + cone_dy * 12
        if abs(gx - lamp_cx) < cone_half_w:
            s = (1 - cone_dy) * smoothstep(cone_half_w, 0, abs(gx - lamp_cx)) * 0.18
            col = mix(col, LAMP, s)

    # --- character: seated blob reading, breathing ---
    # integer frequency so the motion repeats at t=0 and t=1 (seamless loop)
    breathe = 1.0 + 0.04 * math.sin(t * math.pi * 2 * 7)
    ccx = W * 0.50
    base_y = floor_y - 1
    body_h = 9 * breathe
    body_w = 6
    bx = (gx - ccx) / body_w
    by = (base_y - gy) / body_h
    if bx * bx + by * by < 1.0 and base_y - body_h - 1 < gy < base_y:
        col = mix(CHAR_BODY, (60, 40, 40), smoothstep(0.0, 1.0, bx) * 0.3)
    head_cy = base_y - body_h - 2
    if in_ellipse(gx, gy, ccx, head_cy, 3.5, 3.5):
        col = CHAR_HAIR if gy < head_cy - 0.5 else CHAR_BODY
    if (dist(gx, gy, ccx - 1.2, head_cy + 0.3) < 0.9 or
        dist(gx, gy, ccx + 1.2, head_cy + 0.3) < 0.9):
        col = (40, 30, 30)
    sway = math.sin(t * math.pi * 2 * 7) * 0.5
    if in_rect(gx, gy, ccx + sway - 2, base_y - body_h * 0.5 - 1.5,
               ccx + sway + 2, base_y - body_h * 0.5 + 1.5):
        col = BOOK_HELD

    # --- plant (floor, left of character) ---
    pcx = W * 0.36
    pcy = floor_y - 1
    if in_rect(gx, gy, pcx - 1.5, pcy - 2, pcx + 1.5, pcy):
        col = POT
    sway2 = math.sin(t * math.pi * 2 * 0.5) * 0.3
    for (lx, ly) in [(0, -3), (-1.5, -2.5), (1.5, -2.5), (-0.5, -4), (0.5, -4)]:
        if in_ellipse(gx, gy, pcx + lx + sway2, pcy + ly, 1.5, 2):
            col = mix(PLANT, (30, 70, 30), abs(lx) * 0.2)

    # --- rising embers ---
    for i in range(5):
        phase = (t + i / 5.0) % 1.0
        ex = fire_c[0] + math.sin(phase * math.pi * 4 + i) * 3
        ey = fy0 - phase * (H * 0.3)
        if dist(gx, gy, ex, ey) < 0.9:
            col = mix(col, EMBER, 1.0 - phase)

    return col
