#!/usr/bin/env python3
"""Miku hangs a shirt on the clothesline: the shirt floats up from her,
hooks onto the line, two pins snap on, everything sways.
5 s, 12 fps, 16:9.  Output: movie/current/laundry_hang.mp4
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
DUR = 5.0

LX = 2.9                        # pole positions
LINE_Y = -2.9
SAG = 0.4
SHIRT_X = -1.5                  # where the shirt ends up
T_LIFT, T_HANG = 1.2, 2.4
MIKU_POS = (-0.05, 0.25)
MIKU_WORLD_H = 2.3
MIKU_V = {"render": "line", "bg": "black", "mono": True, "line_col": DS.WHITE,
          "scribble": True, "roughness": 2.0, "lw": 2}


def ly(x):
    return LINE_Y + SAG * math.sin(math.pi * (x + LX) / (2 * LX))


def line_scene():
    f = []
    for xs in (-LX, LX):
        f += [P.seg((xs - 0.04, 0, 0), (xs, LINE_Y, 0)),
              P.seg((xs + 0.06, 0, 0.04), (xs + 0.04, LINE_Y, 0.01)),
              P.seg((xs - 0.42, LINE_Y, 0), (xs + 0.42, LINE_Y, 0)),
              P.seg((xs - 0.28, LINE_Y + 0.42, 0), (xs, LINE_Y, 0))]
    f += P.chain([(-LX + 5.8 * k / 16, ly(-LX + 5.8 * k / 16), 0)
                  for k in range(17)])
    # towel + pants already hanging
    tx = 0.9
    f.append(P.q(0, [(tx - 0.36, ly(tx), 0), (tx - 0.36, ly(tx) + 0.85, 0),
                     (tx + 0.36, ly(tx) + 0.85, 0), (tx + 0.36, ly(tx), 0)]))
    f.append(P.seg((tx - 0.36, ly(tx) + 0.28, 0), (tx + 0.36, ly(tx) + 0.28, 0)))
    px = 2.0
    f.append(P.q(0, [(px - 0.3, ly(px), 0), (px - 0.36, ly(px) + 1.0, 0),
                     (px - 0.08, ly(px) + 1.0, 0), (px, ly(px) + 0.42, 0),
                     (px + 0.08, ly(px) + 1.0, 0), (px + 0.36, ly(px) + 1.0, 0),
                     (px + 0.3, ly(px), 0)]))
    for gx in (tx - 0.24, tx + 0.24, px - 0.2, px + 0.2):
        f.append(P.seg((gx, ly(gx) - 0.1, 0), (gx, ly(gx) + 0.1, 0)))
    return {"data": f}


def shirt(cx, top, sway):
    pts = [(cx - 0.45, top + 0.03), (cx - 0.7, top + 0.42),
           (cx - 0.5, top + 0.58), (cx - 0.34, top + 0.36),
           (cx - 0.36 + sway, top + 1.15), (cx + 0.36 + sway, top + 1.15),
           (cx + 0.34, top + 0.36), (cx + 0.5, top + 0.58),
           (cx + 0.7, top + 0.42), (cx + 0.45, top + 0.03)]
    return P.q(0, [(x, y, 0.02) for x, y in pts])


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
    P.setup_view(W, H, 1.05, 0.0, 45.0)
    base = [ground_lines(), line_scene()]

    out = os.path.join(OUT_DIR, "laundry_hang.mp4")
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
        P.stars(surf, hash("laundry") % 1000, W)
        lrng = random.Random(13900 + i)
        for sh in base:
            B.draw_shape(surf, sh, style, P.MODELS["materials"], lrng)
        # the shirt: held, lifted in an arc, then hanging with pins
        f = []
        if t < T_LIFT:
            f.append(shirt(-0.85, -1.35, 0.0))
        elif t < T_HANG:
            u = (t - T_LIFT) / (T_HANG - T_LIFT)
            uq = round(u * 6) / 6
            cx = -0.85 + (SHIRT_X + 0.85) * uq
            top = -1.35 + (ly(SHIRT_X) + 1.35) * uq - 0.3 * math.sin(
                math.pi * uq)
            f.append(shirt(cx, top, 0.0))
        else:
            sway = round(math.sin(math.pi * 2 * (t - T_HANG) / 2.6) * 2) / 2 \
                * 0.06
            f.append(shirt(SHIRT_X, ly(SHIRT_X), sway))
            for k, pxx in enumerate((SHIRT_X - 0.28, SHIRT_X + 0.28)):
                if t >= T_HANG + 0.25 + 0.25 * k:
                    f.append(P.seg((pxx, ly(pxx) - 0.1, 0.03),
                                   (pxx, ly(pxx) + 0.12, 0.03)))
                    if t < T_HANG + 0.45 + 0.25 * k:
                        for deg in (60, 120):
                            a = math.radians(deg)
                            f.append(P.seg(
                                (pxx + 0.14 * math.cos(a),
                                 ly(pxx) - 0.14 * math.sin(a), 0.03),
                                (pxx + 0.26 * math.cos(a),
                                 ly(pxx) - 0.26 * math.sin(a), 0.03)))
        B.draw_shape(surf, {"data": f}, style, P.MODELS["materials"], lrng)
        # Miku by the line; a little hop as she tosses the shirt up
        mx, mz = MIKU_POS
        feet = B.project(mx * B.M, 0, mz * B.M)
        head_ref = B.project(mx * B.M, -MIKU_WORLD_H * B.M, mz * B.M)
        mw = (feet[1] - head_ref[1]) / 1.9
        d = DS.D(surf, MIKU_V, seed=1030 + i)
        hop = 0.0
        if T_LIFT <= t < T_LIFT + 0.3:
            hop = mw * 0.06 * math.sin(math.pi * (t - T_LIFT) / 0.3)
        sw = round(math.sin(math.pi * 2 * t / 3.4) * 2) / 2 * 0.03
        DS.draw_miku(d, feet[0], feet[1] - 1.53 * mw - hop, mw,
                     tail_swing=(sw, -sw), tail_swing2=(-sw, sw))
        if i in (6, 20, 40):
            pygame.image.save(surf,
                              os.path.join(CHECK_DIR, f"laundry_f{i}.png"))
        ff.stdin.write(pygame.image.tostring(surf, "RGB"))

    ff.stdin.close()
    ff.wait()
    print(f"saved {out}")


if __name__ == "__main__":
    main()
