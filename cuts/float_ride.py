#!/usr/bin/env python3
"""Miku rides the roof as the house lifts off — then the camera leaves them
behind, flies up into the sky, arrives near the heart of a solar system and
sweeps around the planets.  15 s, 12 fps, 16:9.
Output: movie/current/float_ride.mp4
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
DUR = 15.0
T_LIFT = 1.2
T_FLY, T_ORBIT = 4.5, 8.5       # ascend into the sky, then sweep around
RIDGE_Y = -2.5
MIKU_WORLD_H = 2.3
MIKU_V = {"render": "line", "bg": "black", "mono": True, "line_col": DS.WHITE,
          "scribble": True, "roughness": 2.0, "lw": 2}

SC = (0.5, -20.5, 5.5)          # solar system centre (world)
SSC = 1.7                       # system scale
ORB_R = 4.5                     # camera sweep radius (world)
ORB_DROP = 1.8                  # camera sits below the system plane
# (orbit radius, planet radius, speed rad/s, phase)
PLANETS = [(1.05, 0.10, 0.50, 0.3), (1.55, 0.16, 0.35, 2.1),
           (2.10, 0.17, 0.25, 4.4), (2.65, 0.13, 0.18, 1.2),
           (3.45, 0.30, 0.12, 5.3), (4.30, 0.26, 0.08, 3.7)]


def house(dx, dy):
    f = P.box(0, 0, 2.3, 1.55, 1.7)
    f.append(P.q(5, [(-0.6, -0.6, 0.86), (-0.15, -0.6, 0.86),
                     (-0.15, -1.15, 0.86), (-0.6, -1.15, 0.86)]))
    f.append(P.q(5, [(0.3, -0.5, 0.86), (0.75, -0.5, 0.86),
                     (0.75, -1.05, 0.86), (0.3, -1.05, 0.86)]))
    for zs in (0.95, -0.95):
        f.append(P.seg((-1.35, -1.5, zs), (0.0, RIDGE_Y, zs * 0.15)))
        f.append(P.seg((1.35, -1.5, zs), (0.0, RIDGE_Y, zs * 0.15)))
    f.append(P.seg((-1.35, -1.5, 0.95), (-1.35, -1.5, -0.95)))
    f.append(P.seg((1.35, -1.5, 0.95), (1.35, -1.5, -0.95)))
    f.append(P.seg((0.0, RIDGE_Y, 0.15), (0.0, RIDGE_Y, -0.15)))
    for face in f:
        for v in face["vertices"]:
            v[0] += dx
            v[1] += dy
    return {"data": f}


def solar_system(t):
    """Sun, six orbit rings (open chains so nearby arcs survive the camera),
    billboard planets, one moon."""
    scx, scy, scz = SC
    X, Y = B.CAM_X, B.CAM_Y
    f = []

    def disc(cx, cy, cz, r):
        pts = []
        for k in range(10):
            a = math.pi * 2 * k / 10
            ca, sa = math.cos(a), math.sin(a)
            pts.append((cx + r * (X[0] * ca + Y[0] * sa),
                        cy + r * (X[1] * ca + Y[1] * sa),
                        cz + r * (X[2] * ca + Y[2] * sa)))
        return P.q(5, pts)

    f.append(disc(scx, scy, scz, 0.55 * SSC))
    for k in range(8):                       # sun rays
        a = math.pi * 2 * k / 8 + 0.15 * t
        f.append(P.seg((scx + 0.75 * SSC * math.cos(a), scy,
                        scz + 0.75 * SSC * math.sin(a)),
                       (scx + 1.0 * SSC * math.cos(a), scy,
                        scz + 1.0 * SSC * math.sin(a))))
    for orad, prad, spd, ph in PLANETS:
        ring = [(scx + orad * SSC * math.cos(a), scy,
                 scz + orad * SSC * math.sin(a))
                for a in [math.pi * 2 * k / 28 for k in range(28)]]
        f += P.chain(ring + [ring[0]])
        a = ph + spd * t
        px = scx + orad * SSC * math.cos(a)
        pz = scz + orad * SSC * math.sin(a)
        f.append(disc(px, scy, pz, prad * SSC))
        if orad == 2.10:                     # a little moon
            ma = 1.8 * t
            f.append(disc(px + 0.34 * SSC * math.cos(ma), scy,
                          pz + 0.34 * SSC * math.sin(ma), 0.05 * SSC))
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


def smooth(v):
    return v * v * (3 - 2 * v)


def main():
    pygame.init()
    pygame.display.set_mode((64, 64))
    with open(os.path.join(os.path.dirname(HERE), "core", "bg_models.json")) as f:
        P.MODELS = json.load(f)
    style = B.STYLES["inverted-soft-jitter"]
    P.setup_view(W, H, 0.82, 0.0, 130.0)
    gnd = ground_lines()
    scx, scy, scz = SC
    C_SC = (scx * B.M, scy * B.M, scz * B.M)
    EYE0 = (0.0, -50.0, 500.0)
    EYE1 = (scx * B.M, (scy + ORB_DROP) * B.M, (scz + ORB_R) * B.M)
    CEN0 = (0.0, -200.0, 0.0)

    out = os.path.join(OUT_DIR, "float_ride.mp4")
    frames = int(DUR * FPS)
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-vcodec", "rawvideo",
         "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", out],
        stdin=subprocess.PIPE)

    for i in range(frames):
        t = i / FPS
        u = max(0.0, min(1.35, (t - T_LIFT) / 3.8))
        lift = 3.4 * u ** 1.7
        dx = 0.16 * math.sin(math.pi * 2 * u * 1.2) * u
        # camera: hold -> fly to the system -> sweep around it
        if t < T_FLY:
            B.EYE, B.CENTER = EYE0, CEN0
        elif t < T_ORBIT:
            e = smooth((t - T_FLY) / (T_ORBIT - T_FLY))
            B.EYE = tuple(a + (b - a) * e for a, b in zip(EYE0, EYE1))
            B.CENTER = tuple(a + (b - a) * e for a, b in zip(CEN0, C_SC))
        else:
            ph = 2.6 * smooth((t - T_ORBIT) / (DUR - T_ORBIT))
            B.EYE = (C_SC[0] + ORB_R * B.M * math.sin(ph),
                     (scy + ORB_DROP) * B.M,
                     C_SC[2] + ORB_R * B.M * math.cos(ph))
            B.CENTER = C_SC
        B.CAM_X, B.CAM_Y, B.CAM_Z = B._camera_basis()
        surf = pygame.Surface((W, H))
        surf.fill(style["bg"])
        P.stars(surf, hash("floatride") % 1000, W)
        lrng = random.Random(14100 + i)
        B.draw_shape(surf, gnd, style, P.MODELS["materials"], lrng)
        B.draw_shape(surf, solar_system(t), style, P.MODELS["materials"],
                     lrng)
        srx = 1.7 * (1.0 - 0.6 * min(1.0, u))
        B.draw_shape(surf, {"data": [P.q(0, [
            (dx + srx * math.cos(a), -0.01, 0.2 + 0.5 * srx * math.sin(a))
            for a in [math.pi * 2 * k / 12 for k in range(12)]])]},
            style, P.MODELS["materials"], lrng)
        if T_LIFT <= t < T_LIFT + 0.5:
            v = (t - T_LIFT) / 0.5
            fd = []
            for sx in (-1, 1):
                fd.append(P.seg((sx * (1.5 + 1.1 * v), -0.05 - 0.15 * v, 0.4),
                                (sx * (1.8 + 1.1 * v), -0.05 - 0.2 * v, 0.4)))
            B.draw_shape(surf, {"data": fd}, style, P.MODELS["materials"],
                         lrng)
        B.draw_shape(surf, house(dx, -lift), style, P.MODELS["materials"],
                     lrng)
        feet = B.project(dx * B.M, (RIDGE_Y - lift) * B.M, 0)
        head_ref = B.project(dx * B.M, (RIDGE_Y - lift - MIKU_WORLD_H) * B.M, 0)
        if feet and head_ref and 0 < feet[1] - head_ref[1] < 600:
            mw = (feet[1] - head_ref[1]) / 1.9
            d = DS.D(surf, MIKU_V, seed=1050 + i)
            sw = round(math.sin(math.pi * 2 * t / 3.0) * 2) / 2 * 0.03
            DS.draw_miku(d, feet[0], feet[1] - 1.53 * mw, mw,
                         tail_swing=(sw, -sw), tail_swing2=(-sw, sw))
        if i in (30, 80, 120, 168):
            pygame.image.save(surf,
                              os.path.join(CHECK_DIR, f"floatride_f{i}.png"))
        ff.stdin.write(pygame.image.tostring(surf, "RGB"))

    ff.stdin.close()
    ff.wait()
    print(f"saved {out}")


if __name__ == "__main__":
    main()
