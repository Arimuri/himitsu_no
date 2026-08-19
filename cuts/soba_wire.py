#!/usr/bin/env python3
"""「そばにいないでも」cut: two far-apart houses joined by one long wire.
A pulse travels over, a beat, and the reply comes back.  4 s, 12 fps, 16:9.
Output: movie/current/soba_wire.mp4
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

HX = 8.5                        # house distance from centre
MAST_Y = -3.7                   # wire endpoint height
SAG = 1.35
# (t0, travel, direction): the call, then the reply
PULSES = [(0.45, 1.45, 1), (2.25, 1.45, -1)]


def place(shape, x, z=0.0, sc=1.0):
    for face in shape["data"]:
        for v in face["vertices"]:
            v[0] = v[0] * sc + x
            v[1] = v[1] * sc
            v[2] = v[2] * sc + z
    return shape


def plain_ground():
    gpts = [(-26, 3.4), (26, 3.4), (26, -24), (-26, -24)]
    f = []
    for k in range(4):
        (x0, z0), (x1, z1) = gpts[k], gpts[(k + 1) % 4]
        n = max(2, int(math.hypot(x1 - x0, z1 - z0) / 1.5))
        for j in range(n):
            t0, t1 = j / n, (j + 1) / n
            f.append(P.seg((x0 + (x1 - x0) * t0, 0, z0 + (z1 - z0) * t0),
                           (x0 + (x1 - x0) * t1, 0, z0 + (z1 - z0) * t1)))
    return {"data": f}


def masts():
    f = []
    for sx in (-1, 1):
        f.append(P.seg((HX * sx - 0.04, -2.4, 0), (HX * sx, MAST_Y, 0)))
        f.append(P.seg((HX * sx - 0.25, -3.0, 0), (HX * sx + 0.25, -3.0, 0)))
    return {"data": f}


def wire(t):
    pts = []
    for k in range(33):
        u = k / 32
        x = -HX + 2 * HX * u
        y = MAST_Y + SAG * math.sin(math.pi * u)
        for t0, tr, dr in PULSES:
            p = (t - t0) / tr
            if 0.0 <= p <= 1.0:
                pu = p if dr > 0 else 1.0 - p
                y -= 0.3 * math.exp(-((u - pu) / 0.045) ** 2)
        pts.append((x, y, 0))
    return {"data": P.chain(pts)}


def glow(sx, k):
    """Arrival flash: rays at the mast tip + a bright window pane."""
    f = []
    for deg in (35, 90, 145):
        a = math.radians(deg)
        r0, r1 = 0.3 + 0.06 * k, 0.62 + 0.06 * k
        f.append(P.seg((HX * sx + r0 * math.cos(a), MAST_Y - r0 * math.sin(a), 0),
                       (HX * sx + r1 * math.cos(a), MAST_Y - r1 * math.sin(a), 0)))
    return f


def main():
    pygame.init()
    pygame.display.set_mode((64, 64))
    with open(os.path.join(os.path.dirname(HERE), "core", "bg_models.json")) as f:
        P.MODELS = json.load(f)
    style = B.STYLES["inverted-soft-jitter"]
    P.setup_view(W, H, 0.62, 0.0, 45.0)
    scene = [plain_ground(),
             place(P.building_1(0.9), -HX, 0.0),
             place(P.building_2(0.9), HX, 0.0),
             masts()]

    out = os.path.join(OUT_DIR, "soba_wire.mp4")
    frames = int(DUR * FPS)
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-vcodec", "rawvideo",
         "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", out],
        stdin=subprocess.PIPE)

    E0, E1 = (0.0, -50.0, 500.0), (0.0, -1300.0, 5800.0)
    for i in range(frames):
        t = i / FPS
        # pull-back: hold flat until 2.3 s, then a hard cubic ramp — all the
        # recession is packed into the last stretch
        v = max(0.0, (t - 2.3) / (DUR - 1 / FPS - 2.3))
        e = min(1.0, v) ** 3
        B.EYE = tuple(a + (b - a) * e for a, b in zip(E0, E1))
        B.CAM_X, B.CAM_Y, B.CAM_Z = B._camera_basis()
        surf = pygame.Surface((W, H))
        surf.fill(style["bg"])
        P.stars(surf, hash("soba") % 1000, W)
        lrng = random.Random(13500 + i)
        for sh in scene:
            B.draw_shape(surf, sh, style, P.MODELS["materials"], lrng)
        fx = wire(t)
        for t0, tr, dr in PULSES:
            ta = t0 + tr
            if ta <= t <= ta + 0.4:
                fx["data"] += glow(dr, int((t - ta) * FPS) // 2)
        B.draw_shape(surf, fx, style, P.MODELS["materials"], lrng)
        if i in (12, 24, 46):
            pygame.image.save(surf,
                              os.path.join(CHECK_DIR, f"soba_f{i}.png"))
        ff.stdin.write(pygame.image.tostring(surf, "RGB"))

    ff.stdin.close()
    ff.wait()
    print(f"saved {out}")


if __name__ == "__main__":
    main()
