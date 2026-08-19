#!/usr/bin/env python3
"""Miku riding a ferris wheel gondola; the camera slowly zooms in on her
as the wheel turns.  8 s, 12 fps, 16:9.
Output: movie/current/ferris_ride.mp4
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
DUR = 13.0
S = 6.5                         # wheel scale (big gondolas)
GK = 2                          # Miku's gondola index
SPIN = 0.09                     # rad/s
Z0, Z1 = 0.42, 5.0
MIKU_WORLD_H = 2.3
MIKU_V = {"render": "line", "bg": "black", "mono": True, "line_col": DS.WHITE,
          "scribble": True, "roughness": 2.0, "lw": 2}


def scale_shape(shape, sc):
    for face in shape["data"]:
        for v in face["vertices"]:
            v[0] *= sc
            v[1] *= sc
            v[2] *= sc
    return shape


def gondola_pos(ang):
    a = ang + math.pi * 2 * GK / 8
    px = 1.85 * math.cos(a) * S
    py = (-1.85 - 0.6 + 1.85 * math.sin(a)) * S
    return px, py


def gondola_faces(ang, k):
    """Six opaque faces of gondola k (already S-scaled), depth-sorted
    far->near for the current camera and split at the box centre: `far`
    faces sit behind a rider standing inside, `near` faces occlude her."""
    a = ang + math.pi * 2 * k / 8
    gx = 1.85 * math.cos(a) * S
    gy = (-1.85 - 0.6 + 1.85 * math.sin(a)) * S
    w, h, d = 0.26 * S, 0.3 * S, 0.3 * S
    x0, x1 = gx - w / 2, gx + w / 2
    z0, z1 = -d / 2, d / 2
    yb, yt = gy + 0.36 * S, gy + 0.36 * S - h
    faces = [P.q(2, [(x0, yb, z0), (x1, yb, z0), (x1, yt, z0), (x0, yt, z0)]),
             P.q(2, [(x0, yb, z0), (x0, yb, z1), (x0, yt, z1), (x0, yt, z0)]),
             P.q(2, [(x1, yb, z0), (x1, yb, z1), (x1, yt, z1), (x1, yt, z0)]),
             P.q(2, [(x0, yt, z0), (x1, yt, z0), (x1, yt, z1), (x0, yt, z1)]),
             P.q(2, [(x0, yb, z0), (x1, yb, z0), (x1, yb, z1), (x0, yb, z1)]),
             P.q(1, [(x0, yb, z1), (x1, yb, z1), (x1, yt, z1), (x0, yt, z1)])]

    def dist(face):
        vs = face["vertices"]
        return math.hypot(
            sum(v[0] for v in vs) / 4 * B.M - B.EYE[0],
            sum(v[1] for v in vs) / 4 * B.M - B.EYE[1],
            sum(v[2] for v in vs) / 4 * B.M - B.EYE[2])

    cdist = math.hypot(gx * B.M - B.EYE[0], (yb - h / 2) * B.M - B.EYE[1],
                       -B.EYE[2])
    faces.sort(key=dist, reverse=True)
    return ([f for f in faces if dist(f) >= cdist],
            [f for f in faces if dist(f) < cdist])


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
    gnd = ground_lines()

    out = os.path.join(OUT_DIR, "ferris_ride.mp4")
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
        e = u * u * (3 - 2 * u)
        ang = SPIN * t
        wheel = scale_shape(P.ferris_wheel(0.0, 1.85, ang, 0.38,
                                           gondolas=False), S)
        gx, gy = gondola_pos(ang)
        # camera: zoom in while panning the view centre onto the gondola,
        # so the close-up stays on-axis (no skew, no cover-up)
        P.setup_view(W, H, Z0 + (Z1 - Z0) * e, 0.0, 330.0 - 330.0 * e)
        tgt = (gx * B.M, (gy + 0.36 * S - 1.6) * B.M, 0.0)
        CEN0 = (0.0, -200.0, 0.0)
        B.CENTER = tuple(a + (b - a) * e for a, b in zip(CEN0, tgt))
        surf = pygame.Surface((W, H))
        surf.fill(style["bg"])
        P.stars(surf, hash("ferrisride") % 1000, W)
        lrng = random.Random(15900 + i)
        B.draw_shape(surf, gnd, style, P.MODELS["materials"], lrng)
        B.draw_shape(surf, wheel, style, P.MODELS["materials"], lrng)
        for k in range(8):
            if k == GK:
                continue
            far, near = gondola_faces(ang, k)
            B.draw_shape(surf, {"data": far + near}, style,
                         P.MODELS["materials"], lrng)
        gfar, gnear = gondola_faces(ang, GK)
        B.draw_shape(surf, {"data": gfar}, style,
                     P.MODELS["materials"], lrng)
        # Miku in the gondola, then the gondola front wall over her legs
        floor_y = gy + 0.36 * S
        stand_y = floor_y - 1.45            # feet inside: head/chest clear
                                            # the near wall even seen from below
        feet = B.project(gx * B.M, stand_y * B.M, 0)
        head_ref = B.project(gx * B.M, (stand_y - MIKU_WORLD_H) * B.M, 0)
        if feet and head_ref:
            mw = (feet[1] - head_ref[1]) / 1.9
            d = DS.D(surf, MIKU_V, seed=1150 + i)
            sw = round(math.sin(math.pi * 2 * t / 3.2) * 2) / 2 * 0.03
            DS.draw_miku(d, feet[0], feet[1] - 1.53 * mw, mw,
                         tail_swing=(sw, -sw), tail_swing2=(-sw, sw))
        B.draw_shape(surf, {"data": gnear}, style,
                     P.MODELS["materials"], lrng)
        if i in (0, 78, 155):
            pygame.image.save(surf,
                              os.path.join(CHECK_DIR, f"ferrisride_f{i}.png"))
        ff.stdin.write(pygame.image.tostring(surf, "RGB"))

    ff.stdin.close()
    ff.wait()
    print(f"saved {out}")


if __name__ == "__main__":
    main()
