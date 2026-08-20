#!/usr/bin/env python3
"""Three metronomes ticking against each other (5:4:3 over the loop).
4 s, 12 fps, 16:9, perfect loop.  Output: movie/current/metronome3.mp4
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
import bg_props as P

OUT_DIR = "/Users/arimura/Dropbox/ボカコレ2026S/movie/current"
CHECK_DIR = os.path.join(OUT_DIR, "check")
os.makedirs(CHECK_DIR, exist_ok=True)
W, H = 1280, 720
FPS = 12
DUR = 4.0
# (x, scale, period s, phase)
UNITS = [(-2.7, 0.95, 0.8, 0.0), (0.0, 1.1, 1.0, 0.35), (2.7, 1.0, 4 / 3, 0.7)]
AMP = 0.5


def metronome(f, ox, sc, arm):
    def S(v):
        return v * sc
    # back face first, then the corner rails, then the filled front face:
    # painted last, its fill hides the back/rail lines = opaque body
    for zs in (S(-0.3),):
        f.append(P.q(0, [(ox - S(0.55), 0, zs), (ox + S(0.55), 0, zs),
                         (ox + S(0.2), S(-1.9), zs), (ox - S(0.2), S(-1.9),
                                                      zs)]))
    for sx in (-1, 1):
        f.append(P.seg((ox + S(0.55) * sx, 0, S(0.3)),
                       (ox + S(0.55) * sx, 0, S(-0.3))))
        f.append(P.seg((ox + S(0.2) * sx, S(-1.9), S(0.3)),
                       (ox + S(0.2) * sx, S(-1.9), S(-0.3))))
    f.append(P.q(2, [(ox - S(0.55), 0, S(0.3)), (ox + S(0.55), 0, S(0.3)),
                     (ox + S(0.2), S(-1.9), S(0.3)), (ox - S(0.2), S(-1.9),
                                                      S(0.3))]))
    zf = S(0.31)
    f.append(P.seg((ox, S(-0.35), zf),
                   (ox + S(1.35) * math.sin(arm),
                    S(-0.35) - S(1.35) * math.cos(arm), zf)))
    wx = ox + S(0.95) * math.sin(arm)
    wy = S(-0.35) - S(0.95) * math.cos(arm)
    f.append(P.q(5, [(wx - S(0.1), wy - S(0.09), zf),
                     (wx + S(0.1), wy - S(0.09), zf),
                     (wx + S(0.07), wy + S(0.09), zf),
                     (wx - S(0.07), wy + S(0.09), zf)]))
    for k in range(3):
        f.append(P.seg((ox - S(0.12) + k * S(0.12), S(-1.75), zf),
                       (ox - S(0.1) + k * S(0.12), S(-1.6), zf)))
    # click ticks at the extremes
    if abs(arm) > AMP * 0.9:
        tx = ox + S(1.42) * math.sin(arm)
        ty = S(-0.35) - S(1.42) * math.cos(arm)
        sgn = 1 if arm > 0 else -1
        for dr in (0.12, 0.24):
            f.append(P.seg((tx + sgn * S(dr), ty - S(0.05), zf),
                           (tx + sgn * S(dr + 0.1), ty - S(0.1), zf)))


def ground_lines():
    gpts = [(-26, 3.4), (26, 3.4), (26, -22), (-26, -22)]
    f = []
    for k in range(4):
        (x0, z0), (x1, z1) = gpts[k], gpts[(k + 1) % 4]
        n = max(2, int(math.hypot(x1 - x0, z1 - z0) / 1.5))
        for j in range(n):
            t0, t1 = j / n, (j + 1) / n
            f.append(P.seg((x0 + (x1 - x0) * t0, 0, z0 + (z1 - z0) * t0),
                           (x0 + (x1 - x0) * t1, 0, z0 + (z1 - z0) * t1)))
    return {"data": f}


def main():
    pygame.init()
    pygame.display.set_mode((64, 64))
    with open(os.path.join(os.path.dirname(HERE), "core", "bg_models.json")) as f:
        P.MODELS = json.load(f)
    style = B.STYLES["inverted-soft-jitter"]
    P.setup_view(W, H, 1.5, 0.0, -85.0)
    gnd = ground_lines()

    out = os.path.join(OUT_DIR, "metronome3.mp4")
    frames = int(DUR * FPS)
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-vcodec", "rawvideo",
         "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", out],
        stdin=subprocess.PIPE)

    for i in range(frames):
        t = i / FPS
        f = []
        for ox, sc, per, ph in UNITS:
            arm = AMP * math.sin(math.pi * 2 * (t / per + ph))
            arm = round(arm * 6) / 6
            metronome(f, ox, sc, arm)
        surf = pygame.Surface((W, H))
        surf.fill(style["bg"])
        P.stars(surf, hash("metro") % 1000, W)
        lrng = random.Random(14900 + i)
        B.draw_shape(surf, gnd, style, P.MODELS["materials"], lrng)
        B.draw_shape(surf, {"data": f}, style, P.MODELS["materials"], lrng)
        if i == 18:
            pygame.image.save(surf,
                              os.path.join(CHECK_DIR, "metro3_f18.png"))
        ff.stdin.write(pygame.image.tostring(surf, "RGB"))

    ff.stdin.close()
    ff.wait()
    print(f"saved {out}")


if __name__ == "__main__":
    main()
