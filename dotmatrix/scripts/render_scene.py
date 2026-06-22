#!/usr/bin/env python3
"""render_scene.py — render a Claude-FM-style ambient dot-matrix scene to MP4.

A scene is a Python module that defines:

    SCENE_W = 64          # grid width in dots
    SCENE_H = 40          # grid height in dots
    BG      = (r, g, b)   # background color (dots equal to BG are skipped)

    def scene_color(gx, gy, t, W, H):
        '''Return an (r, g, b) tuple for grid cell (gx, gy) at normalized
        time t in [0, 1). t=0 and t=1 are identical — the loop is seamless.'''
        ...

The runner imports the scene module, sets up the dot grid, calls scene_color
for every cell of every frame, applies an optional bloom, and encodes to MP4
via ffmpeg. No source image is ever used — the dots ARE the scene.

Usage:
    python3 render_scene.py --scene cozy_study.py --output scene.mp4
    python3 render_scene.py --scene my_scene.py --duration 24 --fps 24 \\
        --dot-size 14 --gap 4 --bloom 0.18 --self-check --output out.mp4

Requires: Python 3 + Pillow. MP4 output needs ffmpeg on PATH.
"""

import argparse
import importlib.util
import math
import os
import shutil
import subprocess
import sys
import tempfile

try:
    from PIL import Image, ImageDraw, ImageFilter
except ImportError:
    sys.stderr.write("ERROR: Pillow is required. Install:  pip install pillow\n")
    sys.exit(2)


def die(msg, code=1):
    sys.stderr.write("ERROR: %s\n" % msg)
    sys.exit(code)


# --------------------------------------------------------------------------- #
# Scene loading
# --------------------------------------------------------------------------- #
def load_scene(path):
    """Import a scene module from an arbitrary file path. Returns the module."""
    if not os.path.exists(path):
        die("scene file not found: %s" % path)
    spec = importlib.util.spec_from_file_location("dotmatrix_scene", path)
    if spec is None or spec.loader is None:
        die("cannot import scene module from %s" % path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:  # noqa: BLE001
        die("scene module %s failed to load: %s" % (path, e))
    # Validate the contract.
    for attr in ("SCENE_W", "SCENE_H", "BG", "scene_color"):
        if not hasattr(mod, attr):
            die("scene %s is missing required '%s'. "
                "See references/writing-a-scene.md." % (path, attr))
    if not callable(mod.scene_color):
        die("scene %s: 'scene_color' must be a function" % path)
    try:
        test = mod.scene_color(0, 0, 0.0, mod.SCENE_W, mod.SCENE_H)
        if not (isinstance(test, tuple) and len(test) == 3):
            die("scene %s: scene_color must return an (r,g,b) tuple, got %r"
                % (path, type(test).__name__))
    except Exception as e:  # noqa: BLE001
        die("scene %s: scene_color raised on a probe call: %s" % (path, e))
    return mod


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #
def render_frame(scene, t, dot_size, gap, super_scale, bloom):
    """Render one RGB frame at normalized time t."""
    W, H = scene.SCENE_W, scene.SCENE_H
    cell = dot_size + gap
    img_w = W * cell + gap
    img_h = H * cell + gap
    rw, rh = img_w * super_scale, img_h * super_scale

    img = Image.new("RGB", (rw, rh), scene.BG)
    d = ImageDraw.Draw(img)
    dot_r = (dot_size / 2.0) * super_scale
    bg = scene.BG

    for gy in range(H):
        for gx in range(W):
            col = scene.scene_color(gx, gy, t, W, H)
            # Skip cells equal to background — keeps the "dots on void" look
            # and dramatically speeds up rendering.
            if col == bg:
                continue
            cx = (gap + gx * cell + cell / 2.0) * super_scale
            cy = (gap + gy * cell + cell / 2.0) * super_scale
            d.ellipse([cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r],
                      fill=col)

    # Bloom: blur a copy and blend for a soft cozy glow.
    if bloom > 0:
        blurred = img.filter(ImageFilter.GaussianBlur(radius=6 * super_scale))
        img = Image.blend(img, blurred, alpha=bloom)

    if super_scale > 1:
        img = img.resize((img_w, img_h), Image.LANCZOS)
    return img, (img_w, img_h)


# --------------------------------------------------------------------------- #
# ffmpeg
# --------------------------------------------------------------------------- #
def find_ffmpeg():
    for name in ("ffmpeg", "/opt/homebrew/bin/ffmpeg",
                 "/usr/local/bin/ffmpeg"):
        try:
            r = subprocess.run([name, "-version"],
                               capture_output=True, timeout=5)
            if r.returncode == 0:
                return name
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
    return None


def render_to_mp4(scene, path, fps, duration, dot_size, gap, super_scale,
                  bloom, progress=True):
    ffmpeg = find_ffmpeg()
    if ffmpeg is None:
        die("ffmpeg not found on PATH — cannot write MP4. "
            "Install ffmpeg.", code=2)
    n_frames = max(1, int(fps * duration))
    tmpdir = tempfile.mkdtemp(prefix="dotscene_")
    try:
        first_size = None
        for i in range(n_frames):
            # Sample uniformly over [0, 1] so the last frame lands exactly at
            # t=1, which equals t=0 for a periodic scene -> seamless loop.
            t = (i / max(1, n_frames - 1)) % 1.0
            frame, size = render_frame(scene, t, dot_size, gap, super_scale, bloom)
            if first_size is None:
                first_size = size
            frame.save(os.path.join(tmpdir, "f_%05d.png" % i), format="PNG")
            if progress and (i % max(1, n_frames // 8) == 0):
                sys.stderr.write("  frame %d/%d\n" % (i, n_frames))
        # yuv420p needs even dims — pad up by one px if odd.
        cmd = [
            ffmpeg, "-y",
            "-framerate", str(fps),
            "-i", os.path.join(tmpdir, "f_%05d.png"),
            "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2:color=black",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            path,
        ]
        r = subprocess.run(cmd, capture_output=True, timeout=600)
        if r.returncode != 0:
            die("ffmpeg failed (exit %d): %s"
                % (r.returncode, r.stderr.decode(errors="replace")[-800:]))
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return n_frames, first_size


def self_check(path, expected_frames, expected_size):
    try:
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height,nb_frames",
             "-of", "csv=p=0", path],
            capture_output=True, text=True, timeout=10,
        )
        parts = probe.stdout.strip().split(",")
        w, h = (int(parts[0]), int(parts[1])) if len(parts) >= 2 else (-1, -1)
        n = int(parts[2]) if len(parts) >= 3 else -1
    except Exception as e:  # noqa: BLE001
        sys.stderr.write("SELF-CHECK FAIL: cannot read %r: %s\n" % (path, e))
        return False
    ok = True
    msgs = []
    if n != expected_frames:
        ok = False
        msgs.append("frame count %d != expected %d" % (n, expected_frames))
    if expected_size:
        ew, eh = expected_size
        # padded by at most 1px per axis for even dims
        if not ((w in (ew, ew + 1)) and (h in (eh, eh + 1))):
            ok = False
            msgs.append("size %dx%d != expected %dx%d (±1 padding)" % (w, h, ew, eh))
    status = "PASS" if ok else "FAIL"
    sys.stderr.write("SELF-CHECK %s: %s  frames=%d  size=%dx%d\n"
                     % (status, path, n, w, h))
    for m in msgs:
        sys.stderr.write("  - %s\n" % m)
    return ok


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def parse_args(argv):
    p = argparse.ArgumentParser(
        prog="render_scene.py",
        description="Render a dot-matrix ambient scene to MP4.",
    )
    p.add_argument("--scene", required=True,
                   help="path to a scene module (.py) defining scene_color()")
    p.add_argument("--output", required=True, help="output .mp4 path")
    p.add_argument("--duration", type=float, default=24.0,
                   help="loop length in seconds (default 24)")
    p.add_argument("--fps", type=int, default=24, help="frames per second")
    p.add_argument("--dot-size", type=int, default=14,
                   help="rendered dot diameter in px")
    p.add_argument("--gap", type=int, default=4, help="px gap between dots")
    p.add_argument("--bloom", type=float, default=0.18,
                   help="bloom/glow blend 0..1 (0 = off, 0.18 default)")
    p.add_argument("--scale", type=int, default=2,
                   help="internal render overscale (2 = anti-aliased)")
    p.add_argument("--self-check", action="store_true",
                   help="verify output after writing")
    p.add_argument("--quiet", action="store_true", help="suppress progress")
    args = p.parse_args(argv)
    if args.duration <= 0:
        die("--duration must be > 0")
    if args.fps < 1:
        die("--fps must be >= 1")
    if args.dot_size < 2:
        die("--dot-size must be >= 2")
    if args.gap < 0:
        die("--gap must be >= 0")
    if not (0.0 <= args.bloom <= 1.0):
        die("--bloom must be 0..1")
    if args.scale < 1:
        die("--scale must be >= 1")
    return args


def main(argv=None):
    args = parse_args(argv if argv is not None else sys.argv[1:])
    scene = load_scene(args.scene)
    sys.stderr.write("Rendering %s → %s  (%dx%d dots, %.1fs @ %dfps)\n"
                     % (os.path.basename(args.scene), args.output,
                        scene.SCENE_W, scene.SCENE_H, args.duration, args.fps))
    n_frames, size = render_to_mp4(
        scene, args.output, args.fps, args.duration,
        args.dot_size, args.gap, args.scale, args.bloom,
        progress=not args.quiet,
    )
    if args.self_check:
        if not self_check(args.output, n_frames, size):
            sys.exit(1)
    kb = os.path.getsize(args.output) // 1024
    sys.stderr.write("OK: wrote %s  frames=%d  %dx%d  %dKB\n"
                     % (args.output, n_frames, size[0], size[1], kb))


if __name__ == "__main__":
    main()
