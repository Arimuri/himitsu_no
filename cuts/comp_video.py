#!/usr/bin/env python3
"""
comp_2 composition as a living still: locked camera, boiling lines,
Miku idling. 3 s, 12 fps, 16:9.  Output: movie/current/comp_2.mp4
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
W, H = 1280, 720
FPS = 12
DUR = 6.0

MIKU_V = {"render": "line", "bg": "black", "mono": True, "line_col": DS.WHITE,
          "scribble": True, "roughness": 2.0, "lw": 2}


def main():
    pygame.init()
    pygame.display.set_mode((64, 64))
    with open(os.path.join(os.path.dirname(HERE), "core", "bg_models.json")) as f:
        P.MODELS = json.load(f)
    style = B.STYLES["inverted-soft-jitter"]
    P.setup_view(W, H, 0.58, 0, 20.0)
    EYE0, EYE1 = (0.0, -50.0, 500.0), (185.0, -350.0, 545.0)
    C0, C1 = (0.0, -200.0, 0.0), (0.0, -55.0, 20.0)
    MIKU_W_POS = (-2.4, 5.05)          # world anchor (x, z)
    MIKU_WORLD_H = 2.3

    scene = [P.ground(), P.building_5(1.6), P.tree_2(-2.8, 1.5),
             P.tree_3(4.6, 1.5)]

    out = os.path.join(OUT_DIR, "comp_2.mp4")
    frames = int(DUR * FPS)
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-vcodec", "rawvideo",
         "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", out],
        stdin=subprocess.PIPE)

    for i in range(frames):
        t = i / (frames - 1)
        e = t * t * (3 - 2 * t)
        # slow move up-right, easing into a bird's-eye
        B.EYE = tuple(a + (b - a) * e for a, b in zip(EYE0, EYE1))
        B.CENTER = tuple(a + (b - a) * e for a, b in zip(C0, C1))
        B.CAM_X, B.CAM_Y, B.CAM_Z = B._camera_basis()
        surf = pygame.Surface((W, H))
        surf.fill(style["bg"])
        P.stars(surf, hash("comp_2") % 1000, W)
        lrng = random.Random(9500 + i)
        for sh in scene:
            B.draw_shape(surf, sh, style, P.MODELS["materials"], lrng)
        mx, mz = MIKU_W_POS
        feet = B.project(mx * B.M, 0, mz * B.M)
        head_ref = B.project(mx * B.M, -MIKU_WORLD_H * B.M, mz * B.M)
        mw = (feet[1] - head_ref[1]) / 1.9
        d = DS.D(surf, MIKU_V, seed=600 + i)
        ts = i / FPS
        sw = round(math.sin(math.pi * 2 * ts / 3.0) * 2) / 2 * 0.03
        DS.draw_miku(d, feet[0], feet[1] - 1.53 * mw, mw,
                     tail_swing=(sw, -sw), tail_swing2=(-sw, sw))
        ff.stdin.write(pygame.image.tostring(surf, "RGB"))

    ff.stdin.close()
    ff.wait()
    print(f"saved {out}")


if __name__ == "__main__":
    main()
