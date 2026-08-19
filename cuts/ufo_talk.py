#!/usr/bin/env python3
"""UFO cut: a saucer descends from above, hovers, and trades words with
Miku (alternating speech ticks / blinking lights), then zips away.
8 s, 12 fps, 16:9.  Output: movie/current/ufo_talk.mp4
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
DUR = 9.2

MIKU_POS = (-2.6, 2.0)
MIKU_WORLD_H = 2.3
MIKU_V = {"render": "line", "bg": "black", "mono": True, "line_col": DS.WHITE,
          "scribble": True, "roughness": 2.0, "lw": 2}

HOVER = (2.0, -4.4)             # UFO hover position (x, y)
T_ARRIVE = 1.5
T_LEAVE = 6.8
MIKU_TURNS = [(1.8, 2.8), (4.1, 5.1)]
UFO_TURNS = [(2.95, 3.95), (5.25, 6.25)]


def ufo(cx, cy, i):
    f = []
    n = 14
    rim = [(cx + 1.35 * math.cos(a), cy + 0.3 * math.sin(a),
            0.5 * math.sin(a)) for a in [math.pi * 2 * k / n for k in range(n)]]
    f.append(P.q(2, rim))
    dome = [(cx + 0.62 * math.cos(a), cy - 0.28 - 0.5 * math.sin(a), 0)
            for a in [math.pi * k / 8 for k in range(9)]]
    f += P.chain(dome)
    f.append(P.seg((cx - 1.35, cy + 0.08, 0), (cx + 1.35, cy + 0.08, 0)))
    # under-lights, blinking in a chase
    for k in range(4):
        lx = cx - 0.9 + k * 0.6
        if (i // 2 + k) % 3 == 0:
            f.append(P.q(5, [(lx + 0.09 * math.cos(a),
                              cy + 0.34 + 0.06 * math.sin(a), 0.1)
                             for a in [math.pi * 2 * j / 8 for j in range(8)]]))
        else:
            f.append(P.seg((lx - 0.07, cy + 0.34, 0.1),
                           (lx + 0.07, cy + 0.34, 0.1)))
    return f


def ticks(cx, cy, toward, k):
    """Three speech strokes radiating toward the other party."""
    f = []
    base = math.atan2(-1.0, toward)
    for da in (-0.45, 0.0, 0.45):
        a = base + da
        r0, r1 = 0.35 + 0.05 * k, 0.7 + 0.05 * k
        f.append(P.seg((cx + r0 * math.cos(a), cy + r0 * math.sin(a), 0),
                       (cx + r1 * math.cos(a), cy + r1 * math.sin(a), 0)))
    return f


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
    P.setup_view(W, H, 0.8, 0.0, 60.0)
    gnd = ground_lines()

    out = os.path.join(OUT_DIR, "ufo_talk.mp4")
    frames = int(DUR * FPS)
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-vcodec", "rawvideo",
         "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", out],
        stdin=subprocess.PIPE)

    for i in range(frames):
        t = i / FPS
        surf = pygame.Surface((W, H))
        surf.fill(style["bg"])
        P.stars(surf, hash("ufo") % 1000, W)
        lrng = random.Random(14300 + i)
        B.draw_shape(surf, gnd, style, P.MODELS["materials"], lrng)
        # UFO position: descend, hover with a bob, then zip away
        hx, hy = HOVER
        if t < T_ARRIVE:
            u = t / T_ARRIVE
            e = 1 - (1 - u) ** 3
            cy = -11.5 + (hy + 11.5) * e
            cx = hx + 1.5 * (1 - e)
        elif t < T_LEAVE:
            cx = hx
            cy = hy + 0.1 * round(math.sin(math.pi * 2 * t / 1.6) * 2) / 2
        else:
            v = (t - T_LEAVE) / (DUR - T_LEAVE)
            cx = hx + 21.0 * v ** 2.2
            cy = hy - 14.0 * v ** 2.2
        f = ufo(cx, cy, i)
        if t >= T_LEAVE + 0.2:
            for k in range(4):
                tb = 0.5 + 0.5 * k
                f.append(P.seg((cx - tb - 0.3, cy + tb * 0.66, 0),
                               (cx - tb, cy + (tb + 0.3) * 0.66 - 0.2, 0)))
        # conversation ticks
        for t0, t1 in MIKU_TURNS:
            if t0 <= t <= t1 and (i // 3) % 2 == 0:
                f += ticks(MIKU_POS[0] + 0.5, -2.6, 1.0, 0)
        for t0, t1 in UFO_TURNS:
            if t0 <= t <= t1 and (i // 3) % 2 == 0:
                f += ticks(cx - 1.2, cy + 0.5, -1.0, 0)
        B.draw_shape(surf, {"data": f}, style, P.MODELS["materials"], lrng)
        # Miku looking up
        mx, mz = MIKU_POS
        feet = B.project(mx * B.M, 0, mz * B.M)
        head_ref = B.project(mx * B.M, -MIKU_WORLD_H * B.M, mz * B.M)
        mw = (feet[1] - head_ref[1]) / 1.9
        d = DS.D(surf, MIKU_V, seed=1070 + i)
        sw = round(math.sin(math.pi * 2 * t / 3.2) * 2) / 2 * 0.03
        DS.draw_miku(d, feet[0], feet[1] - 1.53 * mw, mw,
                     tail_swing=(sw, -sw), tail_swing2=(-sw, sw))
        if i in (14, 40, 108):
            pygame.image.save(surf,
                              os.path.join(CHECK_DIR, f"ufo_f{i}.png"))
        ff.stdin.write(pygame.image.tostring(surf, "RGB"))

    ff.stdin.close()
    ff.wait()
    print(f"saved {out}")


if __name__ == "__main__":
    main()
