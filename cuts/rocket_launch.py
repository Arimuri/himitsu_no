#!/usr/bin/env python3
"""Rocket launch cut: lift-off from a pad, camera tilting up into the sky
exactly like comp_3's second half.  5 s, 12 fps, 16:9.
Output: movie/current/rocket_launch.mp4
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
T_LIFT = 0.9                    # ignition / lift-off
C0, C1 = (0.0, -200.0, 0.0), (0.0, -2000.0, 0.0)   # comp_3 tilt


def rocket(oy, oz):
    """Slim lathe rocket: body, nose, three fins, window, nozzle."""
    f = []
    n = 8

    def ring(y, r):
        return [(r * math.cos(a), y, oz + r * math.sin(a))
                for a in [math.pi * 2 * k / n for k in range(n)]]

    base = ring(oy, 0.28)
    top = ring(oy - 1.45, 0.28)
    f.append(P.q(0, base))
    f.append(P.q(0, top))
    for k in range(0, n, 2):
        f.append(P.seg(base[k], top[k]))
    tip = (0.0, oy - 2.15, oz)
    for k in range(0, n, 2):
        f.append(P.seg(top[k], tip))
    noz = ring(oy + 0.18, 0.17)
    f.append(P.q(0, noz))
    for k in range(0, n, 2):
        f.append(P.seg(base[k], noz[k]))
    # window
    f.append(P.q(5, [(0.13 * math.cos(a), oy - 1.05 + 0.13 * math.sin(a),
                      oz + 0.28)
                     for a in [math.pi * 2 * k / 8 for k in range(8)]]))
    # three fins
    for a in (0.4, 2.5, 4.6):
        dx, dz = math.cos(a), math.sin(a)
        f.append(P.q(2, [(0.26 * dx, oy - 0.4, oz + 0.26 * dz),
                         (0.62 * dx, oy + 0.28, oz + 0.62 * dz),
                         (0.26 * dx, oy + 0.05, oz + 0.26 * dz)]))
    return f


def gantry():
    """Slim service tower beside the pad."""
    f = []
    for zs in (0.18, -0.18):
        f.append(P.seg((-1.35, 0, zs), (-1.2, -2.7, zs * 0.5)))
        f.append(P.seg((-1.05, 0, zs), (-1.1, -2.7, zs * 0.5)))
    for k in range(4):
        y = -0.55 - k * 0.55
        f.append(P.seg((-1.31, y, 0.14), (-1.11, y - 0.35, -0.12)))
        f.append(P.seg((-1.11, y, -0.12), (-1.31, y - 0.35, 0.14)))
        f.append(P.seg((-1.31, y, 0.14), (-1.11, y, -0.12)))
    f.append(P.seg((-1.15, -2.6, 0), (-0.35, -2.35, 0)))
    return {"data": f}


def pad():
    f = [P.q(0, [(1.15 * math.cos(a), -0.01, 0.15 + 0.8 * math.sin(a))
                 for a in [math.pi * 2 * k / 12 for k in range(12)]])]
    for a in (0.5, 1.6, 2.7, 3.8):
        f.append(P.seg((0.45 * math.cos(a), 0, 0.45 * math.sin(a)),
                       (0.32 * math.cos(a), -0.22, 0.32 * math.sin(a))))
    return {"data": f}


def main():
    pygame.init()
    pygame.display.set_mode((64, 64))
    with open(os.path.join(os.path.dirname(HERE), "core", "bg_models.json")) as f:
        P.MODELS = json.load(f)
    style = B.STYLES["inverted-soft-jitter"]
    P.setup_view(W, H, 0.66, 0.0, 20.0)
    gnd = {"data": [P.seg((-30 + k * 1.5, 0, -14), (-28.5 + k * 1.5, 0, -14))
                    for k in range(40)]
           + [P.seg((-24 + k * 1.5, 0, -6), (-22.5 + k * 1.5, 0, -6))
              for k in range(32)]}

    out = os.path.join(OUT_DIR, "rocket_launch.mp4")
    frames = int(DUR * FPS)
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-vcodec", "rawvideo",
         "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", out],
        stdin=subprocess.PIPE)

    for i in range(frames):
        t = i / FPS
        pt = max(0.0, min(1.0, (t - 1.0) / 4.0))
        e = pt * pt * (3 - 2 * pt)
        B.CENTER = tuple(a + (b - a) * e for a, b in zip(C0, C1))
        B.CAM_X, B.CAM_Y, B.CAM_Z = B._camera_basis()
        surf = pygame.Surface((W, H))
        surf.fill(style["bg"])
        P.stars(surf, hash("rocket") % 1000, W)
        lrng = random.Random(13100 + i)
        for sh in (gnd, pad(), gantry()):
            B.draw_shape(surf, sh, style, P.MODELS["materials"], lrng)
        # rocket ascent with a gentle pitch-over toward the tilt axis
        if t < T_LIFT:
            ry, rz = 0.0, 0.0
            burn = t > T_LIFT - 0.35
        else:
            s = t - T_LIFT
            ry = -1.05 * s ** 2.2
            rz = 0.083 * s * s
            burn = True
        f = rocket(ry - 0.25, rz)
        if burn:
            frng = random.Random(400 + i)
            for _ in range(3):
                fx = frng.uniform(-0.14, 0.14)
                l0 = frng.uniform(0.25, 0.55)
                f.append(P.seg((fx, ry - 0.02, rz),
                               (fx * 1.6, ry - 0.02 + l0, rz)))
            if t >= T_LIFT:
                for k in range(1, 6):        # dashed exhaust trail
                    ty = ry + 0.75 * k + 0.2
                    if ty > -0.1:
                        break
                    f.append(P.seg((0.03, ty, rz * 0.7),
                                   (-0.03, ty + 0.3, rz * 0.7)))
            if T_LIFT <= t < T_LIFT + 0.6:   # ignition puffs, brief
                u = (t - T_LIFT) / 0.6
                for sx in (-1, 1):
                    r = 0.28 + 0.35 * u
                    cx = sx * (0.5 + 0.7 * u)
                    f.append(P.q(0, [(cx + r * math.cos(a),
                                      -0.12 - 0.18 * u + 0.5 * r * math.sin(a),
                                      0.3)
                                     for a in [math.pi * 2 * k / 10
                                               for k in range(10)]]))
        B.draw_shape(surf, {"data": f}, style, P.MODELS["materials"], lrng)
        if i in (8, 24, 55):
            pygame.image.save(surf,
                              os.path.join(CHECK_DIR, f"rocket_f{i}.png"))
        ff.stdin.write(pygame.image.tostring(surf, "RGB"))

    ff.stdin.close()
    ff.wait()
    print(f"saved {out}")


if __name__ == "__main__":
    main()
