#!/usr/bin/env python3
"""String-phone cut: Miku talks into the left cup, the pulse runs down the
string to the right cup — where nobody is waiting.  5 s, 12 fps, 16:9.
Output: movie/current/stringphone_call.mp4
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
from scribble import jitter_line

OUT_DIR = "/Users/arimura/Dropbox/ボカコレ2026S/movie/current"
CHECK_DIR = os.path.join(OUT_DIR, "check")
os.makedirs(CHECK_DIR, exist_ok=True)
W, H = 1280, 720
FPS = 12
DUR = 5.0

CUP_Y = -1.62                   # cup axis height (Miku face height)
BX, MX = 2.15, 2.72             # inner (base) / outer (mouth) cup x
SAG = 0.55
MIKU_POS = (-3.75, 0.0)
MIKU_WORLD_H = 2.3
MIKU_V = {"render": "line", "bg": "black", "mono": True, "line_col": DS.WHITE,
          "scribble": True, "roughness": 2.0, "lw": 2}

# single transmission: (launch time, travel seconds)
PULSES = [(1.4, 1.8)]
SPEAK = [(0.5, 1.6)]                    # Miku-side tick window


def cup(sgn):
    """Paper cup on a slim stand, base inward, mouth outward."""
    f = []
    base = [(BX * sgn, CUP_Y + 0.2 * math.sin(a), 0.2 * math.cos(a))
            for a in [math.pi * 2 * k / 8 for k in range(8)]]
    mouth = [(MX * sgn, CUP_Y + 0.31 * math.sin(a), 0.31 * math.cos(a))
             for a in [math.pi * 2 * k / 8 for k in range(8)]]
    f.append(P.q(0, base))
    f.append(P.q(0, mouth))
    for k in range(0, 8, 2):
        f.append(P.seg(base[k], mouth[k]))
    px = (BX + 0.28) * sgn                 # stand under the cup body
    f.append(P.seg((px - 0.02 * sgn, 0, 0), (px, CUP_Y + 0.3, 0)))
    f.append(P.seg((px - 0.3 * sgn, 0, 0.12), (px, CUP_Y + 0.3, 0)))
    f.append(P.seg((px + 0.24 * sgn, 0, -0.12), (px, CUP_Y + 0.3, 0)))
    return f


def string_line(t):
    """Sagging string with travelling pulses (bumps)."""
    pts = []
    for k in range(29):
        u = k / 28
        x = -BX + 2 * BX * u
        y = CUP_Y + SAG * math.sin(math.pi * u)
        for t0, tr in PULSES:
            p = (t - t0) / tr
            if 0.0 <= p <= 1.0:
                y -= 0.26 * math.exp(-((u - p) / 0.055) ** 2)
        pts.append((x, y, 0))
    return P.chain(pts)


def ticks(sgn, k):
    """Sound arcs at a cup mouth: three short radial strokes."""
    f = []
    ox = (MX + 0.14) * sgn
    for deg in (-30, 0, 30):
        a = math.radians(deg)
        r0, r1 = 0.22 + 0.05 * k, 0.5 + 0.05 * k
        f.append(P.seg((ox + sgn * r0 * math.cos(a), CUP_Y - r0 * math.sin(a), 0),
                       (ox + sgn * r1 * math.cos(a), CUP_Y - r1 * math.sin(a), 0)))
    return f


def ground_lines():
    return {"data": [P.seg((-45, 0, -30), (45, 0, -30)),
                     P.seg((-30, 0, -10), (30, 0, -10))]}


def main():
    pygame.init()
    pygame.display.set_mode((64, 64))
    with open(os.path.join(os.path.dirname(HERE), "core", "bg_models.json")) as f:
        P.MODELS = json.load(f)
    style = B.STYLES["inverted-soft-jitter"]
    P.setup_view(W, H, 1.3, 0.0, 55.0)

    out = os.path.join(OUT_DIR, "stringphone_call.mp4")
    frames = int(DUR * FPS)
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-vcodec", "rawvideo",
         "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", out],
        stdin=subprocess.PIPE)

    for i in range(frames):
        t = i / FPS
        B.VIEW_ZOOM = 1.28 + 0.08 * (i / (frames - 1))
        surf = pygame.Surface((W, H))
        surf.fill(style["bg"])
        lrng = random.Random(11900 + i)
        P.stars(surf, hash("stringphone") % 1000, W)

        f = cup(-1) + cup(1) + string_line(t)
        # Miku-side speech ticks (blinking)
        for t0, t1 in SPEAK:
            if t0 <= t <= t1 and (i // 3) % 2 == 0:
                f += ticks(-1, 0)
        # arrivals at the empty right cup
        for t0, tr in PULSES:
            ta = t0 + tr
            if ta <= t <= ta + 0.45:
                f += ticks(1, int((t - ta) * FPS) // 2)
        B.draw_shape(surf, ground_lines(), style, P.MODELS["materials"], lrng)
        B.draw_shape(surf, {"data": f}, style, P.MODELS["materials"], lrng)

        mx, mz = MIKU_POS
        feet = B.project(mx * B.M, 0, mz * B.M)
        head_ref = B.project(mx * B.M, -MIKU_WORLD_H * B.M, mz * B.M)
        if feet and head_ref:
            mw = (feet[1] - head_ref[1]) / 1.9
            d = DS.D(surf, MIKU_V, seed=950 + i)
            sw = round(math.sin(math.pi * 2 * t / 3.2) * 2) / 2 * 0.03
            DS.draw_miku(d, feet[0], feet[1] - 1.53 * mw, mw,
                         tail_swing=(sw, -sw), tail_swing2=(-sw, sw))
        if i in (10, 34, 50):
            pygame.image.save(surf,
                              os.path.join(CHECK_DIR, f"stringphone_f{i}.png"))
        ff.stdin.write(pygame.image.tostring(surf, "RGB"))

    ff.stdin.close()
    ff.wait()
    print(f"saved {out}")


if __name__ == "__main__":
    main()
