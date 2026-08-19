#!/usr/bin/env python3
"""comp_2 framing, Miku standing still while the background motif swaps
every 2 beats (0.857 s @ 140 BPM), 8 motifs.
~6.86 s, 12 fps, 16:9.  Output: movie/current/motif_swap.mp4
"""
import os
import json
import math
import random
import subprocess
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "core"))
import pygame

import bg_sketch as B
import design_sketch as DS
import bg_props as P

OUT_DIR = "/Users/arimura/Dropbox/ボカコレ2026S/movie/current"
CHECK_DIR = os.path.join(OUT_DIR, "check")
os.makedirs(CHECK_DIR, exist_ok=True)
W, H = 1280, 720
FPS = 12
MOTIF_SEC = 0.857               # 2 beats @ 140 BPM
TARGET_H = 4.4                  # match the comp_2 house height
MAX_W = 9.0

MIKU_W_POS = (-2.4, 5.05)
MIKU_WORLD_H = 2.3
MIKU_V = {"render": "line", "bg": "black", "mono": True, "line_col": DS.WHITE,
          "scribble": True, "roughness": 2.0, "lw": 2}

SWAP = [
    ("pylon", lambda: P.pylon()),
    ("ferris", lambda: P.ferris_wheel()),
    ("watertower", lambda: P.water_tower()),
    ("bridge", lambda: P.truss_bridge()),
    ("lighthouse", lambda: P.lighthouse()),
    ("crane", lambda: P.crane()),
    ("turbine", lambda: P.wind_turbine()),
    ("drafting", lambda: P.drafting()),
]


def normalize(shape):
    """Scale to the house slot: TARGET_H tall, centred on x=0, on the ground."""
    xs = [v[0] for f in shape["data"] for v in f["vertices"]]
    ys = [v[1] for f in shape["data"] for v in f["vertices"]]
    height = max(0.001, -min(ys))
    width = max(0.001, max(xs) - min(xs))
    sc = min(TARGET_H / height, MAX_W / width)
    cx = (min(xs) + max(xs)) / 2
    for f in shape["data"]:
        for v in f["vertices"]:
            v[0] = (v[0] - cx) * sc + 1.2   # sit in the comp_2 house slot
            v[1] = v[1] * sc
            v[2] = v[2] * sc
    return shape


def main():
    pygame.init()
    pygame.display.set_mode((64, 64))
    with open(os.path.join(os.path.dirname(HERE), "core", "bg_models.json")) as f:
        P.MODELS = json.load(f)
    style = B.STYLES["inverted-soft-jitter"]
    P.setup_view(W, H, 0.58, 0, 20.0)

    fixed_front = [P.tree_2(-2.8, 1.5), P.tree_3(4.6, 1.5)]
    motifs = [normalize(build()) for _, build in SWAP]

    out = os.path.join(OUT_DIR, "motif_swap.mp4")
    frames = int(round(MOTIF_SEC * len(SWAP) * FPS))
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-vcodec", "rawvideo",
         "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", out],
        stdin=subprocess.PIPE)

    for i in range(frames):
        t = i / FPS
        mi = min(int(t / MOTIF_SEC), len(SWAP) - 1)
        surf = pygame.Surface((W, H))
        surf.fill(style["bg"])
        P.stars(surf, hash("comp_2") % 1000, W)
        lrng = random.Random(10500 + i)
        for sh in [P.ground(), motifs[mi]] + fixed_front:
            B.draw_shape(surf, sh, style, P.MODELS["materials"], lrng)
        mx, mz = MIKU_W_POS
        feet = B.project(mx * B.M, 0, mz * B.M)
        head_ref = B.project(mx * B.M, -MIKU_WORLD_H * B.M, mz * B.M)
        mw = (feet[1] - head_ref[1]) / 1.9
        d = DS.D(surf, MIKU_V, seed=600 + i)
        sw = round(math.sin(math.pi * 2 * t / 3.0) * 2) / 2 * 0.03
        DS.draw_miku(d, feet[0], feet[1] - 1.53 * mw, mw,
                     tail_swing=(sw, -sw), tail_swing2=(-sw, sw))
        if i in (5, 25, 66):
            pygame.image.save(surf, os.path.join(CHECK_DIR, f"motif_swap_f{i}.png"))
        ff.stdin.write(pygame.image.tostring(surf, "RGB"))

    ff.stdin.close()
    ff.wait()
    print(f"saved {out}")


if __name__ == "__main__":
    main()
