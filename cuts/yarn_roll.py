#!/usr/bin/env python3
"""A ball of yarn rolls along, unwinding a wavy thread behind it, while the
camera pans around in a circle.  4 s, 12 fps, 16:9.
Output: movie/current/yarn_roll.mp4
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
R = 0.62                        # yarn ball radius
X0, X1 = -4.2, 3.4              # roll span

# winding loops: (yaw, pitch) orientations, precomputed unit circles
LOOPS = []
_rng = random.Random(11)
for _ in range(6):
    ya = _rng.uniform(0, math.pi)
    pa = _rng.uniform(-0.9, 0.9)
    cy_, sy_ = math.cos(ya), math.sin(ya)
    cp_, sp_ = math.cos(pa), math.sin(pa)
    pts = []
    for k in range(16):
        a = math.pi * 2 * k / 16
        x, y, z = math.cos(a), math.sin(a), 0.0
        x, z = x * cy_ + z * sy_, -x * sy_ + z * cy_
        y, z = y * cp_ - z * sp_, y * sp_ + z * cp_
        pts.append((x, y, z))
    LOOPS.append(pts)


def ball(bx, roll):
    """Wound ball at (bx, -R) rolled by `roll` radians about z."""
    cr, sr = math.cos(roll), math.sin(roll)
    f = []
    for pts in LOOPS:
        w = []
        for x, y, z in pts:
            rx = x * cr - y * sr
            ry = x * sr + y * cr
            w.append((bx + rx * R * 0.94, -R + ry * R * 0.94, z * R * 0.94))
        f.append(P.q(0, w))
    return {"data": f}


def thread(bx):
    """Unwound thread lying on the ground behind the ball, with one loop."""
    pts = []
    x = -11.0
    while x < bx - 0.1:
        pts.append((x, -0.02, 0.35 + 0.16 * math.sin(x * 2.1)))
        x += 0.35
    pts.append((bx, -0.05, 0.1))
    f = P.chain(pts)
    lx = -7.2
    f.append(P.q(0, [(lx + 0.3 * math.cos(a), -0.02,
                      0.45 + 0.3 * math.sin(a))
                     for a in [math.pi * 2 * k / 10 for k in range(10)]]))
    return {"data": f}


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
    P.setup_view(W, H, 1.55, 0.0, 25.0)
    gnd = ground_lines()

    out = os.path.join(OUT_DIR, "yarn_roll.mp4")
    frames = int(DUR * FPS)
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-vcodec", "rawvideo",
         "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", out],
        stdin=subprocess.PIPE)

    for i in range(frames):
        t = i / FPS
        u = i / (frames - 1)
        bx = X0 + (X1 - X0) * u
        roll = (bx - X0) / R
        # circular pan around the scene, gently following the ball
        ph = -0.55 + 1.1 * u
        B.EYE = (bx * 0.5 * B.M + 7.0 * B.M * math.sin(ph), -2.0 * B.M,
                 7.0 * B.M * math.cos(ph))
        B.CENTER = (bx * 0.5 * B.M, -0.55 * B.M, 0.0)
        B.CAM_X, B.CAM_Y, B.CAM_Z = B._camera_basis()
        surf = pygame.Surface((W, H))
        surf.fill(style["bg"])
        P.stars(surf, hash("yarn") % 1000, W)
        lrng = random.Random(16100 + i)
        B.draw_shape(surf, gnd, style, P.MODELS["materials"], lrng)
        # contact shadow
        B.draw_shape(surf, {"data": [P.q(0, [
            (bx + 0.8 * math.cos(a), -0.01, 0.12 + 0.4 * math.sin(a))
            for a in [math.pi * 2 * k / 10 for k in range(10)]])]},
            style, P.MODELS["materials"], lrng)
        B.draw_shape(surf, thread(bx), style, P.MODELS["materials"], lrng)
        B.draw_shape(surf, ball(bx, roll), style, P.MODELS["materials"], lrng)
        if i in (8, 24, 40):
            pygame.image.save(surf,
                              os.path.join(CHECK_DIR, f"yarn_f{i}.png"))
        ff.stdin.write(pygame.image.tostring(surf, "RGB"))

    ff.stdin.close()
    ff.wait()
    print(f"saved {out}")


if __name__ == "__main__":
    main()
