# Dot Matrix

Generate ambient, lo-fi dot-matrix scene videos — cozy dioramas, rainy windows, cityscapes, and more. Inspired by the Claude FM aesthetic.

Renders a grid of glowing dots pixel-by-pixel from a Python scene module, then encodes a seamless-loop MP4 with bloom and oversampling.

## Demo

![Demo](demo.gif)

[Download full video (mp4)](https://github.com/Somu878/skills/raw/main/dotmatrix/demo.mp4)

## Requirements

- Python 3
- [Pillow](https://pypi.org/project/Pillow/) (`pip install pillow`)
- [ffmpeg](https://ffmpeg.org/) (on PATH)

## Quick Start

```bash
# Resolve the skill directory
DOTMATRIX_SKILL_DIR="$(dirname "$(readlink -f SKILL.md)")"

# Render the cozy study scene (24s loop)
python3 "$DOTMATRIX_SKILL_DIR/scripts/render_scene.py" \
  --scene "$DOTMATRIX_SKILL_DIR/assets/cozy_study.py" \
  --duration 24 --output cozy_study.mp4 --self-check
```

## Bundled Scenes

| Scene | File | Mood |
|-------|------|------|
| Cozy Study | `assets/cozy_study.py` | Warm study with bookshelf, fireplace, lamp, reader, plant |
| Rain Window | `assets/rain_window.py` | Rainy night window with city lights and lightning |

## Usage

```
python3 scripts/render_scene.py \
  --scene <path/to/scene.py>   # scene module path
  --output out.mp4              # output .mp4 path (required)
  --duration 24                 # loop length in seconds (default 24)
  --fps 24                      # frames per second (default 24)
  --dot-size 14                 # rendered dot diameter in px (default 14)
  --gap 4                       # px gap between dots (default 4)
  --scale 2                     # internal overscale for anti-aliasing (default 2)
  --bloom 0.18                  # glow blend 0..1 (default 0.18; 0 = off)
  --self-check                  # verify output after writing
```

## Authoring a Scene

Create a Python module with:

```python
SCENE_W = 64
SCENE_H = 40
BG = (r, g, b)

def scene_color(gx, gy, t, W, H):
    # return (r, g, b) for cell (gx, gy) at normalized time t in [0, 1)
    ...
```

The loop is seamless when `scene_color(..., t=0)` equals `scene_color(..., t→1)`. Use sines/cosines of `t * 2π * k` or phase wrapping with `% 1.0`.

See `references/writing-a-scene.md` for the full contract and `references/palettes.md` for color palettes.

## License

MIT
