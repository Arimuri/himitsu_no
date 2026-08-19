#!/usr/bin/env python3
"""Miku at the crane game: the claw slides, dives, grabs — and the prize
slips out.  5 s, 12 fps, 16:9.  Output: movie/current/claw_play.mp4
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
SC = 1.25
MIKU_POS = (2.2, 0.6)
MIKU_WORLD_H = 2.3
MIKU_V = {"render": "line", "bg": "black", "mono": True, "line_col": DS.WHITE,
          "scribble": True, "roughness": 2.0, "lw": 2}

# claw timeline: slide left, dive, grab, lift (prize slips), return
T_SLIDE, T_DIVE, T_GRAB, T_LIFT, T_BACK = 0.4, 1.5, 2.3, 2.7, 3.6
PRIZE = (-0.45, -1.62)          # the target prize (scaled units applied later)


def cabinet():
    """Machine body without the claw (animated separately)."""
    f = P.box(0, 0, 1.7 * SC, 2.9 * SC, 1.0 * SC, 1, 2)
    zf = 0.51 * SC
    f.append(P.q(5, [(-0.72 * SC, -1.5 * SC, zf), (0.72 * SC, -1.5 * SC, zf),
                     (0.72 * SC, -2.75 * SC, zf), (-0.72 * SC, -2.75 * SC, zf)]))
    for px, py, r in ((-0.45, -1.68, 0.17), (-0.05, -1.63, 0.15),
                      (0.38, -1.7, 0.18)):
        f.append(P.q(0, [(px * SC + r * SC * math.cos(a),
                          py * SC + r * SC * math.sin(a), zf - 0.25 * SC)
                         for a in [math.pi * 2 * k / 8 for k in range(8)]]))
    f.append(P.q(2, [(-0.85 * SC, -1.45 * SC, zf), (0.85 * SC, -1.45 * SC, zf),
                     (0.85 * SC, -1.25 * SC, zf + 0.3 * SC),
                     (-0.85 * SC, -1.25 * SC, zf + 0.3 * SC)]))
    f.append(P.seg((-0.3 * SC, -1.35 * SC, zf + 0.16 * SC),
                   (-0.3 * SC, -1.55 * SC, zf + 0.2 * SC)))
    for bx in (0.15, 0.4):
        f.append(P.seg(((bx - 0.04) * SC, -1.36 * SC, zf + 0.16 * SC),
                       ((bx + 0.04) * SC, -1.36 * SC, zf + 0.16 * SC)))
    return {"data": f}


def claw(cx, cy, spread):
    zc = 0.31 * SC
    f = [P.seg((cx, -2.75 * SC, zc), (cx, cy, zc))]
    for da in (-0.55 - spread, 0.0, 0.55 + spread):
        f.append(P.seg((cx, cy, zc),
                       (cx + 0.2 * math.sin(da), cy + 0.26, zc)))
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
    P.setup_view(W, H, 1.35, 0.0, 80.0)
    body = cabinet()
    gnd = ground_lines()
    px, py = PRIZE[0] * SC, PRIZE[1] * SC
    x_home, x_tgt = 0.45 * SC, px
    y_top, y_dip = -2.45 * SC, py - 0.28

    out = os.path.join(OUT_DIR, "claw_play.mp4")
    frames = int(DUR * FPS)
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-vcodec", "rawvideo",
         "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", out],
        stdin=subprocess.PIPE)

    for i in range(frames):
        t = i / FPS

        def qz(v):
            return round(v * 5) / 5
        # claw state
        if t < T_SLIDE:
            cx, cy, sp = x_home, y_top, 0.0
        elif t < T_DIVE:
            u = qz((t - T_SLIDE) / (T_DIVE - T_SLIDE))
            cx, cy, sp = x_home + (x_tgt - x_home) * u, y_top, 0.0
        elif t < T_GRAB:
            u = qz((t - T_DIVE) / (T_GRAB - T_DIVE))
            cx, cy, sp = x_tgt, y_top + (y_dip - y_top) * u, 0.35 * u
        elif t < T_LIFT:
            cx, cy, sp = x_tgt, y_dip, 0.35 - 0.35 * qz(
                (t - T_GRAB) / (T_LIFT - T_GRAB))
        elif t < T_BACK:
            u = qz((t - T_LIFT) / (T_BACK - T_LIFT))
            cx, cy, sp = x_tgt, y_dip + (y_top - y_dip) * u, 0.0
        else:
            u = qz(min(1.0, (t - T_BACK) / 0.9))
            cx, cy, sp = x_tgt + (x_home - x_tgt) * u, y_top, 0.0
        fx = claw(cx, cy, sp)
        # the prize rises with the claw a touch, slips and bounces back
        if T_LIFT <= t < T_BACK:
            u = (t - T_LIFT) / (T_BACK - T_LIFT)
            if u < 0.4:
                dy = -0.3 * (u / 0.4)
            elif u < 0.7:
                dy = -0.3 + 0.3 * ((u - 0.4) / 0.3)
            else:
                dy = -0.07 * math.sin(math.pi * (u - 0.7) / 0.3)
            fx.append(P.q(0, [(px + 0.17 * SC * math.cos(a),
                               py + dy + 0.17 * SC * math.sin(a),
                               0.26 * SC)
                              for a in [math.pi * 2 * k / 8 for k in range(8)]]))
            if 0.65 < u < 0.9:
                for deg in (60, 120):
                    a = math.radians(deg)
                    fx.append(P.seg((px + 0.22 * math.cos(a),
                                     py + 0.1 - 0.22 * math.sin(a), 0.3),
                                    (px + 0.36 * math.cos(a),
                                     py + 0.1 - 0.36 * math.sin(a), 0.3)))
        surf = pygame.Surface((W, H))
        surf.fill(style["bg"])
        P.stars(surf, hash("claw") % 1000, W)
        lrng = random.Random(15100 + i)
        B.draw_shape(surf, gnd, style, P.MODELS["materials"], lrng)
        B.draw_shape(surf, body, style, P.MODELS["materials"], lrng)
        B.draw_shape(surf, {"data": fx}, style, P.MODELS["materials"], lrng)
        # Miku at the controls; a sag of disappointment at the slip
        mx, mz = MIKU_POS
        feet = B.project(mx * B.M, 0, mz * B.M)
        head_ref = B.project(mx * B.M, -MIKU_WORLD_H * B.M, mz * B.M)
        mw = (feet[1] - head_ref[1]) / 1.9
        d = DS.D(surf, MIKU_V, seed=1090 + i)
        droop = 0.0
        if 3.3 <= t < 4.2:
            droop = mw * 0.05 * math.sin(math.pi * (t - 3.3) / 0.9)
        sw = round(math.sin(math.pi * 2 * t / 3.0) * 2) / 2 * 0.03
        DS.draw_miku(d, feet[0], feet[1] - 1.53 * mw + droop, mw,
                     tail_swing=(sw, -sw), tail_swing2=(-sw, sw))
        if i in (18, 34, 48):
            pygame.image.save(surf,
                              os.path.join(CHECK_DIR, f"clawplay_f{i}.png"))
        ff.stdin.write(pygame.image.tostring(surf, "RGB"))

    ff.stdin.close()
    ff.wait()
    print(f"saved {out}")


if __name__ == "__main__":
    main()
