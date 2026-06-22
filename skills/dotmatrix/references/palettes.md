# Dot-matrix palettes

Copy-paste color sets for scene authoring. Each palette is a block of Python tuples you can drop into a scene module.

## cozy-night

Warm study at night. Good for rooms, bookshelves, fireplaces, lamps.

```python
BG          = (12, 10, 22)
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
```

## cyberpunk

Neon magenta and cyan on a near-black grid. Good for cityscapes, terminals, arcade vibes.

```python
BG       = (8, 6, 12)
DEEP     = (18, 12, 28)
PANEL    = (30, 22, 42)
NEON_PINK= (255, 40, 160)
NEON_CYAN= (40, 255, 240)
NEON_PURP= (150, 60, 255)
GRID     = (60, 50, 80)
TEXT     = (220, 255, 220)
WARNING  = (255, 200, 40)
```

## forest-dawn

Soft greens and golds. Good for outdoor nature scenes, morning light, trees.

```python
BG        = (18, 24, 28)
SKY_TOP   = (40, 60, 70)
SKY_BOT   = (180, 140, 90)
TREE_DARK = (25, 50, 30)
TREE_MID  = (50, 100, 50)
TREE_LIT  = (90, 160, 70)
GRASS     = (45, 90, 40)
SUN       = (255, 220, 140)
MIST      = (140, 160, 150)
```

## ocean-deep

Blues and teals with bioluminescent accents. Good for underwater, night sea, rain on glass.

```python
BG        = (6, 14, 26)
DEEP      = (10, 30, 50)
MID       = (25, 60, 90)
SURFACE   = (50, 110, 150)
FOAM      = (180, 220, 240)
GLOW      = (60, 220, 200)
BIO       = (120, 255, 220)
DARK_ROCK = (15, 25, 35)
```

## desert-dusk

Warm oranges and purples. Good for sunsets, dunes, campfires.

```python
BG        = (28, 18, 30)
SKY_TOP   = (50, 35, 60)
SKY_BOT   = (220, 110, 70)
DUNE_FAR  = (80, 50, 55)
DUNE_MID  = (130, 80, 60)
DUNE_NEAR = (190, 130, 80)
SUN       = (255, 210, 130)
CAMPFIRE  = (255, 140, 60)
STAR      = (240, 240, 220)
```

## mono-amber

Single-color amber on black. Classic terminal / old hardware look.

```python
BG        = (5, 4, 3)
DIM       = (40, 25, 8)
MID       = (120, 80, 20)
BRIGHT    = (255, 176, 0)
```

## Using a palette

Import colors directly into your scene module:

```python
from palettes import cozy_night   # if you extract one to a file
# or paste the tuples inline

def scene_color(gx, gy, t, W, H):
    col = BG
    if gy < H * 0.7:
        col = WALL
    # ...
    return col
```

No registration step is required — the runner only cares about `SCENE_W`, `SCENE_H`, `BG`, and `scene_color()`.
