#!/usr/bin/env python3
"""Miku riding the swing in proper 3D: the frame stands at an angle and the
pendulum swings perpendicular to the bar, so she arcs toward and away from
the camera.  5 s, 12 fps, 16:9 (loopable).
Output: movie/current/swing_ride.mp4
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
YAW = 0.6                       # frame heading
BAR_Y = -4.6
CHAIN = 3.35
PERIOD = 2.5
AMP = 0.42
MIKU_WORLD_H = 2.3
MIKU_V = {"render": "line", "bg": "black", "mono": True, "line_col": DS.WHITE,
          "scribble": True, "roughness": 2.0, "lw": 2}

CY, SY = math.cos(YAW), math.sin(YAW)
FX = (CY, 0.0, -SY)             # frame bar direction
FZ = (SY, 0.0, CY)              # swing direction (toward camera at +)


def L(x, y, z):
    """Local frame coords -> world (bar along FX, swing along FZ)."""
    return (x * FX[0] + z * FZ[0], y, x * FX[2] + z * FZ[2])


def frame_shape():
    f = []
    for sx in (-1, 1):
        for zs in (0.95, -0.95):
            f.append(P.seg(L(sx * 2.2, 0, zs), L(sx * 2.0, BAR_Y, 0)))
    f.append(P.seg(L(-2.0, BAR_Y, 0), L(2.0, BAR_Y, 0)))
    f.append(P.seg(L(-2.05, BAR_Y + 0.35, 0), L(-1.6, BAR_Y, 0)))
    f.append(P.seg(L(2.05, BAR_Y + 0.35, 0), L(1.6, BAR_Y, 0)))
    return {"data": f}


def swing_parts(th):
    """Chains + seat swinging along the frame's depth axis."""
    sz = CHAIN * math.sin(th)
    sy = BAR_Y + CHAIN * math.cos(th)
    tang = (math.sin(th), math.cos(th))          # (dz, dy) along the chain
    f = []
    for cx in (-0.34, 0.34):
        f.append(P.seg(L(cx, BAR_Y, 0), L(cx, sy, sz)))
    corners = []
    for cx, dz in ((-0.42, -0.1), (0.42, -0.1), (0.42, 0.14), (-0.42, 0.14)):
        corners.append(L(cx, sy + dz * tang[0] * -1 + 0.0, sz + dz))
    f.append(P.q(2, corners))
    return {"data": f}, (sz, sy)


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
    P.setup_view(W, H, 1.05, 0.0, 55.0)
    gnd = ground_lines()
    frame_s = frame_shape()

    out = os.path.join(OUT_DIR, "swing_ride.mp4")
    frames = int(DUR * FPS)
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-vcodec", "rawvideo",
         "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", out],
        stdin=subprocess.PIPE)

    for i in range(frames):
        t = i / FPS
        th = AMP * math.sin(math.pi * 2 * t / PERIOD)
        th = round(th * 8) / 8
        surf = pygame.Surface((W, H))
        surf.fill(style["bg"])
        P.stars(surf, hash("swing") % 1000, W)
        lrng = random.Random(15700 + i)
        B.draw_shape(surf, gnd, style, P.MODELS["materials"], lrng)
        parts, (sz, sy) = swing_parts(th)
        seat_w = L(0, sy, sz)
        # travelling contact shadow under the seat
        B.draw_shape(surf, {"data": [P.q(0, [
            (seat_w[0] + 0.62 * math.cos(a), -0.01,
             seat_w[2] + 0.34 * math.sin(a))
            for a in [math.pi * 2 * k / 10 for k in range(10)]])]},
            style, P.MODELS["materials"], lrng)
        B.draw_shape(surf, frame_s, style, P.MODELS["materials"], lrng)
        # Miku on the seat, chains + seat drawn over her
        feet = B.project(seat_w[0] * B.M, sy * B.M, seat_w[2] * B.M)
        head_ref = B.project(seat_w[0] * B.M, (sy - MIKU_WORLD_H) * B.M,
                             seat_w[2] * B.M)
        if feet and head_ref:
            mw = (feet[1] - head_ref[1]) / 1.9
            d = DS.D(surf, MIKU_V, seed=1130 + i)
            sw = -th * 0.3
            sw2 = -th * 0.5
            DS.draw_miku(d, feet[0], feet[1] - 1.53 * mw, mw,
                         tail_swing=(sw, -sw * 0.2),
                         tail_swing2=(sw2, -sw2 * 0.2))
        B.draw_shape(surf, parts, style, P.MODELS["materials"], lrng)
        if i in (7, 15, 22):
            pygame.image.save(surf,
                              os.path.join(CHECK_DIR, f"swing_f{i}.png"))
        ff.stdin.write(pygame.image.tostring(surf, "RGB"))

    ff.stdin.close()
    ff.wait()
    print(f"saved {out}")


if __name__ == "__main__":
    main()
