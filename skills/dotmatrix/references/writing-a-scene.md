# Writing a dot-matrix scene

A scene is a plain Python module that describes what color each dot in a dot-matrix grid should be at any moment. The runner (`scripts/render_scene.py`) imports the module, calls the color function for every cell of every frame, draws the dots, and encodes the result to MP4.

## The contract

Your module must define exactly four things:

```python
SCENE_W = 64               # grid width in dots
SCENE_H = 40               # grid height in dots
BG = (r, g, b)             # background color; cells equal to BG are skipped

def scene_color(gx, gy, t, W, H):
    """Return an (r, g, b) tuple for grid cell (gx, gy) at normalized time t.

    gx, gy are integer grid coordinates (0 <= gx < W, 0 <= gy < H).
    t is a float in [0, 1). The video loops, so t=0 and t→1 must look identical.
    """
    return BG
```

That is the entire contract. Everything else is optional helper code.

## The seamless-loop rule

`t` goes from `0` to just under `1`, then jumps back to `0`. For the loop to be invisible, every animated value must be periodic with period `1` in `t`. The easiest way to guarantee that is to animate only with sines/cosines of the form:

```python
math.sin(t * math.pi * 2 * freq)      # freq can be any integer or half-integer
math.cos(t * math.pi * 2 * freq)
```

The runner samples frames so the last frame is rendered at `t=1`, which is the same as `t=0`, so the loop is mathematically seamless.

### Common mistakes that break the loop

- **Linear ramps:** `gy + t * 10` is different at `t=0` and `t=1`. Do not use bare `t` as a position or offset.
- **Non-integer frequencies:** `math.sin(t * 2π * 1.7)` has period `1/1.7`, which does not divide 1, so `f(0) ≠ f(1)`.
- **Time-based phase shifts that don't wrap:** `phase = (t + 0.3)` without `% 1.0` drifts.
- **Random values:** anything non-deterministic makes the loop jump.

### Correct patterns

```python
# One full back-and-forth per loop
breathe = math.sin(t * math.pi * 2)        # freq = 1

# Seven faster oscillations per loop (period ≈ 1/7 of the loop)
flicker = math.sin(t * math.pi * 2 * 7)

# A phase-shifted repeating element, e.g. rain drops or embers
phase = (t + i / 5.0) % 1.0                # wraps back to 0 at t=1
y = gy - phase * fall_distance

# Combine multiple integer frequencies freely
wobble = math.sin(t * 2π * 3) + 0.5 * math.sin(t * 2π * 11)
```

## Layering a scene

Most scenes are built from back to front:

1. **Background** — wall, sky, void.
2. **Large static shapes** — floor, furniture, window frame.
3. **Animated regions** — fire, rain, city lights, breathing character.
4. **Glossy accents** — lamp glow, lightning flash, reflections.

Return the color of the *topmost* thing that covers the cell. A simple pattern is:

```python
def scene_color(gx, gy, t, W, H):
    col = BG

    # background
    if gy < H * 0.7:
        col = WALL
    else:
        col = FLOOR

    # window
    if in_rect(gx, gy, 10, 5, 54, 25):
        col = NIGHT_SKY
        if is_rain(gx, gy, t):
            col = RAIN

    # lamp glow on top
    if near_lamp(gx, gy):
        col = mix(col, LAMP, 0.3)

    return col
```

## Math helpers

Copy these into your scene so you don't reinvent them:

```python
import math

def _clamp(v, lo=0, hi=255):
    return max(lo, min(hi, int(v)))


def mix(a, b, t):
    """Blend two (r,g,b) colors by t in [0,1]."""
    t = max(0.0, min(1.0, t))
    return tuple(_clamp(a[i] + (b[i] - a[i]) * t) for i in range(3))


def smoothstep(e0, e1, x):
    """0 when x <= e0, 1 when x >= e1, smooth S-curve between."""
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
```

## Performance tips

- **Skip the background.** The runner skips any cell whose color equals `BG`. Start each cell at `BG` and only change it when something covers it. This is the biggest speedup.
- **Keep the grid modest.** `64×40` is the default and a good balance. Larger grids render quadratically more cells.
- **Limit animated elements.** Each animated layer adds per-cell work. Aim for roughly 5–8 animated regions.
- **Avoid expensive math per cell.** A few `sin` calls per cell is fine; nested loops or per-cell randomness is not.
- **Prefer shape tests before animation.** Check `if in_rect(...)` first, then compute animation only inside the region.

## Tuning the render

The runner exposes these knobs; the scene author does not hard-code them:

| flag | default | effect |
|---|---|---|
| `--duration` | 24 | loop length in seconds |
| `--fps` | 24 | frames per second |
| `--dot-size` | 14 | dot diameter in px |
| `--gap` | 4 | px gap between dots |
| `--scale` | 2 | internal overscale for anti-aliasing |
| `--bloom` | 0.18 | glow blend (0 = off, 1 = very soft) |

Scenes look best when designed at the default grid size and then rendered with the default dot size. If you design for a different `SCENE_W`/`SCENE_H`, document it in a module docstring.

## A minimal example

```python
"""minimal_sunset.py — a tiny seamless sunset scene."""
import math

SCENE_W = 64
SCENE_H = 40
BG = (10, 10, 30)

SKY_TOP = (10, 10, 40)
SKY_BOT = (200, 80, 60)
SUN = (255, 220, 120)


def mix(a, b, t):
    return tuple(max(0, min(255, int(a[i] + (b[i] - a[i]) * t))) for i in range(3))


def scene_color(gx, gy, t, W, H):
    # sky gradient
    p = gy / H
    col = mix(SKY_TOP, SKY_BOT, p)

    # sun setting and rising in a loop
    sun_y = H * 0.3 + math.sin(t * math.pi * 2) * H * 0.15
    if math.hypot(gx - W * 0.5, gy - sun_y) < 5:
        col = SUN

    return col
```

Render it:

```bash
python3 "$DOTMATRIX_SKILL_DIR/scripts/render_scene.py" \
  --scene minimal_sunset.py --output sunset.mp4 --self-check
```

## Debugging a non-seamless loop

If the rendered loop has a visible hitch at the cut point:

1. Check every `math.sin`/`math.cos` argument. It should be `t * 2π * freq` with an integer or half-integer `freq`.
2. Check every `phase = t + offset` and make sure it is `% 1.0`'d before use.
3. Temporarily render with `--duration 1 --fps 8` and step through the frames. The last frame should match the first.
4. Render frames at `t=0` and `t=1` directly with `render_frame(scene, 0.0, ...)` and `render_frame(scene, 1.0, ...)`. They must be pixel-identical.
