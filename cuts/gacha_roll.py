#!/usr/bin/env python3
"""Gacha machine: the crank turns, the machine jiggles, one capsule drops
out, bounces and rolls to rest.  5 s, 12 fps, 16:9.
Output: movie/current/gacha_roll.mp4
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
DUR = 5.0
T_CRANK0, T_CRANK1 = 0.5, 2.2   # two crank turns
T_DROP = 2.45                    # capsule leaves the flap
ZF = 0.36


def machine(jig, crank_a):
    f = P.box(0, 0, 1.15, 1.5, 0.7, 1, 2)
    f.append(P.q(0, [(0.62 * math.cos(a), -2.12 + jig + 0.62 * math.sin(a), 0)
                     for a in [math.pi * 2 * k / 14 for k in range(14)]]))
    for cx, cy, r in ((-0.25, -1.85, 0.16), (0.1, -1.75, 0.15),
                      (0.33, -1.95, 0.14), (-0.02, -2.05, 0.15)):
        f.append(P.q(0, [(cx + r * math.cos(a),
                          cy + jig * 1.4 + r * math.sin(a), 0.01)
                         for a in [math.pi * 2 * k / 8 for k in range(8)]]))
    f.append(P.seg((-0.62, -1.5, 0), (0.62, -1.5, 0)))
    f.append(P.q(0, [(0.2 * math.cos(a), -1.05 + 0.2 * math.sin(a), ZF)
                     for a in [math.pi * 2 * k / 8 for k in range(8)]]))
    f.append(P.seg((0, -1.05, ZF),
                   (0.2 * math.cos(crank_a), -1.05 + 0.2 * math.sin(crank_a),
                    ZF + 0.05)))
    f.append(P.q(5, [(-0.2, -0.42, ZF), (0.2, -0.42, ZF),
                     (0.2, -0.18, ZF), (-0.2, -0.18, ZF)]))
    return {"data": f}


def capsule(cx, cy, rot):
    f = [P.q(5, [(cx + 0.17 * math.cos(a), cy + 0.17 * math.sin(a), ZF + 0.1)
                 for a in [math.pi * 2 * k / 10 for k in range(10)]])]
    f.append(P.seg((cx - 0.17 * math.cos(rot), cy - 0.17 * math.sin(rot),
                    ZF + 0.11),
                   (cx + 0.17 * math.cos(rot), cy + 0.17 * math.sin(rot),
                    ZF + 0.11)))
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
    P.setup_view(W, H, 1.9, 0.0, -15.0)
    gnd = ground_lines()

    out = os.path.join(OUT_DIR, "gacha_roll.mp4")
    frames = int(DUR * FPS)
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-vcodec", "rawvideo",
         "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", out],
        stdin=subprocess.PIPE)

    for i in range(frames):
        t = i / FPS
        if T_CRANK0 <= t < T_CRANK1:
            u = (t - T_CRANK0) / (T_CRANK1 - T_CRANK0)
            crank = -math.pi * 4 * round(u * 10) / 10
            jig = 0.03 * ((i % 2) * 2 - 1)
        else:
            crank = 0.0
            jig = 0.0
        fx = machine(jig, crank)
        # capsule: pokes out of the flap, drops, bounces, rolls right
        if t >= T_DROP:
            s = t - T_DROP
            if s < 0.35:
                u = s / 0.35
                cx, cy = 0.1 + 0.3 * u, -0.3 + 0.13 * u * u
                rot = 0.6 * u
            elif s < 0.85:
                u = (s - 0.35) / 0.5
                cx = 0.4 + 1.1 * u
                cy = -0.17 - 0.55 * abs(math.sin(math.pi * u * 1.5)) * (1 - u)
                rot = 0.6 + 2.6 * u
            else:
                u = min(1.0, (s - 0.85) / 1.3)
                ue = 1 - (1 - u) ** 2
                cx = 1.5 + 1.3 * ue
                cy = -0.17
                rot = 3.2 + 3.4 * ue
            fx["data"] += capsule(cx, cy, rot)
            if T_DROP + 0.32 <= t < T_DROP + 0.55:
                for deg in (60, 120):
                    a = math.radians(deg)
                    fx["data"].append(P.seg(
                        (0.4 + 0.2 * math.cos(a), -0.05 - 0.2 * math.sin(a),
                         ZF), (0.4 + 0.34 * math.cos(a),
                               -0.05 - 0.34 * math.sin(a), ZF)))
        surf = pygame.Surface((W, H))
        surf.fill(style["bg"])
        P.stars(surf, hash("gacha") % 1000, W)
        lrng = random.Random(15300 + i)
        B.draw_shape(surf, gnd, style, P.MODELS["materials"], lrng)
        B.draw_shape(surf, fx, style, P.MODELS["materials"], lrng)
        if i in (14, 32, 55):
            pygame.image.save(surf,
                              os.path.join(CHECK_DIR, f"gacha_f{i}.png"))
        ff.stdin.write(pygame.image.tostring(surf, "RGB"))

    ff.stdin.close()
    ff.wait()
    print(f"saved {out}")


if __name__ == "__main__":
    main()
