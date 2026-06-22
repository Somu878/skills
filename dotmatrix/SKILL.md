---
name: dotmatrix
description: Create Claude-FM-style ambient dot-matrix scene videos. Renders cozy dioramas, rainy windows, cityscapes, and other looping pixel-art scenes onto a glowing dot grid. Use when the user wants an ambient dot-matrix animation, a lofi scene video, a dot-matrix background, a cozy study animation, or any "Claude FM" / "dot-matrix diorama" look. Output is a seamless-loop MP4.
disable-model-invocation: true
---

# Dot Matrix

Produce ambient, Claude-FM-style dot-matrix scene videos by invoking the bundled renderer with a scene module. A scene is a small Python file that decides the color of every dot in a grid for every frame. The renderer draws the dots, applies a soft bloom, and encodes a seamless-loop MP4.

## Setup

Resolve the skill directory once. All script calls must use this absolute prefix:

```bash
DOTMATRIX_SKILL_DIR="<skill_directory>"   # parent directory of this SKILL.md
```

**Never call bare `python3 scripts/render_scene.py ...`** — it only works if cwd happens to be the skill directory, which it almost never is. Always use `"$DOTMATRIX_SKILL_DIR/scripts/render_scene.py"`.

Requires Python 3 + Pillow. MP4 output also needs **ffmpeg** on PATH. If Pillow is missing the renderer prints an install hint and exits non-zero; tell the user to run `pip install pillow`. If ffmpeg is missing, suggest installing ffmpeg.

## The renderer

```bash
python3 "$DOTMATRIX_SKILL_DIR/scripts/render_scene.py" \
  --scene $DOTMATRIX_SKILL_DIR/assets/cozy_study.py   # path to a scene module
  --output out.mp4          # REQUIRED: output .mp4 path
  --duration 24             # loop length in seconds (default 24)
  --fps 24                  # frames per second (default 24)
  --dot-size 14             # rendered dot diameter in px (default 14)
  --gap 4                   # px gap between dots (default 4)
  --scale 2                 # internal overscale for anti-aliasing (default 2)
  --bloom 0.18              # glow blend 0..1 (default 0.18; 0 = off)
  --self-check              # verify output after writing; print PASS/FAIL
```

**Always pass `--self-check`** until you've shipped a working video. It catches the common "saved one frame by mistake" bug for free.

## Two workflows

### 1. Use a bundled scene

The skill ships with two ready-made scenes:

- `assets/cozy_study.py` — warm study with bookshelf, fireplace, lamp, reader, plant.
- `assets/rain_window.py` — rainy window at night with city lights and lightning.

```bash
python3 "$DOTMATRIX_SKILL_DIR/scripts/render_scene.py" \
  --scene "$DOTMATRIX_SKILL_DIR/assets/cozy_study.py" \
  --duration 24 --output cozy_study.mp4 --self-check
```

### 2. Author a new scene

Read `references/writing-a-scene.md`, then write a Python module that exposes:

```python
SCENE_W = 64
SCENE_H = 40
BG = (r, g, b)

def scene_color(gx, gy, t, W, H):
    # return an (r, g, b) tuple for cell (gx, gy) at normalized time t in [0, 1)
    ...
```

The loop is seamless only if `scene_color(..., t=0, ...)` equals `scene_color(..., t→1, ...)`. Use sines/cosines of `t * 2π * integer_frequency` or phase variables wrapped with `% 1.0`. See the guide for the full contract, helper functions, and examples.

Use `references/palettes.md` for copy-pasteable color sets.

## How to choose a bundled scene

- **"cozy study / Claude FM / reading by the fire / warm room"** → `cozy_study.py`.
- **"rain on window / rainy night / city lights / storm"** → `rain_window.py`.
- **Vague "ambient dot-matrix scene" with no specific mood** → default to `cozy_study.py`.

## Delivery

- Write the MP4 to the user's working directory (or wherever they asked), **not** inside the skill directory.
- Report back: file path, file size, dimensions (`SCENE_W×SCENE_H` dots and pixel size), duration, frame count, and which scene was used.
- If the user asks for something no bundled scene covers, offer to author a new scene module and render it.

## Error handling

The renderer exits non-zero with a clear stderr message on bad input (missing Pillow/ffmpeg, unloadable scene, missing contract attributes, unwritable output). Read the error, fix the flag or scene, retry.
