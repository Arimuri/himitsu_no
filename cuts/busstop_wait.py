#!/usr/bin/env python3
"""Bus stop cut: road in front, Miku waiting beside the bench.  The camera
trucks sideways while gradually rising.  8 s, 12 fps, 16:9.
Output: movie/current/busstop_wait.mp4
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
DUR = 8.0

MIKU_POS = (2.35, 0.2)          # standing beside the bench
MIKU_WORLD_H = 2.3
MIKU_V = {"render": "line", "bg": "black", "mono": True, "line_col": DS.WHITE,
          "scribble": True, "roughness": 2.0, "lw": 2}

CAM_X0, CAM_X1 = -2.2, 2.2      # lateral truck (world units)
EYE_Y0, EYE_Y1 = -0.9, -3.6     # gradual rise


def road():
    f = [P.seg((-34, 0, 1.4), (34, 0, 1.4)),      # near curb
         P.seg((-34, 0, 3.8), (34, 0, 3.8)),      # far edge (closer to camera)
         P.seg((-34, 0, 0.7), (34, 0, 0.7))]      # sidewalk edge
    x = -33.0
    while x < 33.0:
        f.append(P.seg((x, 0, 2.6), (x + 1.4, 0, 2.6)))   # dashed centre line
        x += 3.0
    return {"data": f}


def main():
    pygame.init()
    pygame.display.set_mode((64, 64))
    with open(os.path.join(os.path.dirname(HERE), "core", "bg_models.json")) as f:
        P.MODELS = json.load(f)
    style = B.STYLES["inverted-soft-jitter"]
    P.setup_view(W, H, 1.15, 0.0, 30.0)

    scene = [road(), P.bus_stop(0.0)]

    out = os.path.join(OUT_DIR, "busstop_wait.mp4")
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
        cx = (CAM_X0 + (CAM_X1 - CAM_X0) * e) * B.M
        B.EYE = (cx, (EYE_Y0 + (EYE_Y1 - EYE_Y0) * e) * B.M, 500.0)
        B.CENTER = (cx, -1.3 * B.M, 0.0)
        B.CAM_X, B.CAM_Y, B.CAM_Z = B._camera_basis()
        surf = pygame.Surface((W, H))
        surf.fill(style["bg"])
        P.stars(surf, hash("busstop") % 1000, W)
        lrng = random.Random(11700 + i)
        for sh in scene:
            B.draw_shape(surf, sh, style, P.MODELS["materials"], lrng)
        mx, mz = MIKU_POS
        feet = B.project(mx * B.M, 0, mz * B.M)
        head_ref = B.project(mx * B.M, -MIKU_WORLD_H * B.M, mz * B.M)
        if feet and head_ref:
            mw = (feet[1] - head_ref[1]) / 1.9
            d = DS.D(surf, MIKU_V, seed=900 + i)
            sw = round(math.sin(math.pi * 2 * (i / FPS) / 3.4) * 2) / 2 * 0.03
            DS.draw_miku(d, feet[0], feet[1] - 1.53 * mw, mw,
                         tail_swing=(sw, -sw), tail_swing2=(-sw, sw))
        if i in (0, 48, 95):
            pygame.image.save(surf,
                              os.path.join(CHECK_DIR, f"busstop_f{i}.png"))
        ff.stdin.write(pygame.image.tostring(surf, "RGB"))

    ff.stdin.close()
    ff.wait()
    print(f"saved {out}")


if __name__ == "__main__":
    main()
