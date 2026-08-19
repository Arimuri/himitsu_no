#!/usr/bin/env python3
"""Space finale: the floating house (Miku on the roof) has drifted into
space.  Start close, then pull back through a cosmic tableau — the full
solar system, the moon, five constellations, comets, a cruising UFO and
the rocket climbing past.  8 s, 12 fps, 16:9.
Output: movie/current/space_finale.mp4
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
DUR = 8.0
T_HOLD, T_PULL = 1.2, 6.0
RIDGE_Y = -2.5
MIKU_WORLD_H = 2.3
MIKU_V = {"render": "line", "bg": "black", "mono": True, "line_col": DS.WHITE,
          "scribble": True, "roughness": 2.0, "lw": 2}

EYE0, EYE1 = (0.0, -120.0, 400.0), (-380.0, -310.0, 1010.0)
CEN0, CEN1 = (0.0, -175.0, 0.0), (70.0, -600.0, -1150.0)
# solar system layout
SSC = (13.0, -10.0, -16.0)
SS = 1.8
TILT = 0.5
PLANETS = [(1.05, 0.10, 0.50, 0.3), (1.55, 0.16, 0.35, 2.1),
           (2.10, 0.17, 0.25, 4.4), (2.65, 0.13, 0.18, 1.2),
           (3.45, 0.30, 0.12, 5.3), (4.30, 0.26, 0.08, 3.7)]
CONSTELLATIONS = [(-6.0, -15.0, 1.9, -22.0, 0.8),
                  (14.0, -4.0, 2.0, -24.0, 2.0),
                  (-18.0, -2.0, 1.8, -20.0, 3.2),
                  (5.0, -18.0, 1.8, -18.0, 4.4),
                  (22.0, -12.0, 1.7, -20.0, 5.6)]


def yaw_shape(shape, ang):
    xs = [v[0] for f in shape["data"] for v in f["vertices"]]
    zs = [v[2] for f in shape["data"] for v in f["vertices"]]
    cx, cz = (min(xs) + max(xs)) / 2, (min(zs) + max(zs)) / 2
    ca, sa = math.cos(ang), math.sin(ang)
    for f in shape["data"]:
        for v in f["vertices"]:
            dx, dz = v[0] - cx, v[2] - cz
            v[0] = cx + dx * ca + dz * sa
            v[2] = cz - dx * sa + dz * ca
    return shape


def house(dy):
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
            v[1] += dy
    return {"data": f}


def solar_system(t):
    scx, scy, scz = SSC
    X, Y = B.CAM_X, B.CAM_Y
    f = []

    ct, st = math.cos(TILT), math.sin(TILT)

    def orb(dx, dz):
        return (scx + dx, scy + dz * st, scz + dz * ct)

    def disc(cx, cy, cz, r, n=10):
        return P.q(5, [(cx + r * (X[0] * math.cos(a) + Y[0] * math.sin(a)),
                        cy + r * (X[1] * math.cos(a) + Y[1] * math.sin(a)),
                        cz + r * (X[2] * math.cos(a) + Y[2] * math.sin(a)))
                       for a in [math.pi * 2 * k / n for k in range(n)]])

    f.append(disc(scx, scy, scz, 0.55 * SS, 12))
    for k in range(8):
        a = math.pi * 2 * k / 8 + 0.12 * t
        f.append(P.seg(orb(0.78 * SS * math.cos(a), 0.78 * SS * math.sin(a)),
                       orb(1.02 * SS * math.cos(a),
                           1.02 * SS * math.sin(a))))
    for oi, (orad, prad, spd, ph) in enumerate(PLANETS):
        ring = [orb(orad * SS * math.cos(a), orad * SS * math.sin(a))
                for a in [math.pi * 2 * k / 26 for k in range(26)]]
        f += P.chain(ring + [ring[0]])
        a = ph + spd * t
        px, py, pz = orb(orad * SS * math.cos(a), orad * SS * math.sin(a))
        f.append(disc(px, py, pz, prad * SS))
        if oi == 2:
            ma = 1.6 * t
            f.append(disc(px + 0.36 * SS * math.cos(ma), py,
                          pz + 0.36 * SS * math.sin(ma), 0.05 * SS, 8))
        if oi == 5:                          # saturn ring
            f.append(P.q(0, [(px + 0.5 * SS * math.cos(b),
                              py + 0.1 * SS * math.sin(b),
                              pz + 0.22 * SS * math.sin(b))
                             for b in [math.pi * 2 * k / 12
                                       for k in range(12)]]))
    return f


def moon_face():
    mx, my, mz, r = -13.0, -8.0, -19.0, 2.5
    X, Y = B.CAM_X, B.CAM_Y
    return [P.q(5, [(mx + r * (X[0] * math.cos(a) + Y[0] * math.sin(a)),
                     my + r * (X[1] * math.cos(a) + Y[1] * math.sin(a)),
                     mz + r * (X[2] * math.cos(a) + Y[2] * math.sin(a)))
                    for a in [math.pi * 2 * k / 14 for k in range(14)]])]


def comets(t):
    f = []
    for t0, p0, p1 in ((2.2, (24, -18, -22), (-4, -8, -25)),
                       (4.0, (-24, -16, -21), (0, -5, -24))):
        u = (t - t0) / 1.7
        if not 0.0 <= u <= 1.1:
            continue
        hx = p0[0] + (p1[0] - p0[0]) * u
        hy = p0[1] + (p1[1] - p0[1]) * u
        hz = p0[2] + (p1[2] - p0[2]) * u
        dx, dy, dz = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]
        L = math.hypot(dx, dy, dz)
        dx, dy, dz = dx / L, dy / L, dz / L
        f.append(P.seg((hx, hy, hz),
                       (hx - dx * 2.0, hy - dy * 2.0, hz - dz * 2.0)))
        for k in range(3):
            o = 3.0 + k * 1.3
            f.append(P.seg((hx - dx * o, hy - dy * o, hz - dz * o),
                           (hx - dx * (o + 0.65), hy - dy * (o + 0.65),
                            hz - dz * (o + 0.65))))
    return f


def ufo(t):
    if not 2.8 <= t <= 7.6:
        return []
    u = (t - 2.8) / 4.8
    cx = 34 - 62 * u
    cy = -14.5 + 1.0 * math.sin(u * 8)
    cz = -12.0
    f = []
    rim = [(cx + 1.5 * math.cos(a), cy + 0.33 * math.sin(a),
            cz + 0.65 * math.sin(a)) for a in
           [math.pi * 2 * k / 12 for k in range(12)]]
    f.append(P.q(2, rim))
    f += P.chain([(cx + 0.7 * math.cos(a), cy - 0.3 - 0.5 * math.sin(a), cz)
                  for a in [math.pi * k / 6 for k in range(7)]])
    return f


def rocket(t):
    """Climbing steadily up through the tableau."""
    ry = 12.0 - 4.4 * t
    rx, rz = 7.0, -9.0
    n = 6
    f = []
    base = [(rx + 0.42 * math.cos(a), ry + 0.5, rz + 0.42 * math.sin(a))
            for a in [math.pi * 2 * k / n for k in range(n)]]
    top = [(rx + 0.42 * math.cos(a), ry - 1.4, rz + 0.42 * math.sin(a))
           for a in [math.pi * 2 * k / n for k in range(n)]]
    f.append(P.q(0, base))
    f.append(P.q(0, top))
    for k in range(0, n, 2):
        f.append(P.seg(base[k], top[k]))
        f.append(P.seg(top[k], (rx, ry - 2.3, rz)))
    for a in (0.4, 2.5, 4.6):
        dx, dz = math.cos(a), math.sin(a)
        f.append(P.q(2, [(rx + 0.4 * dx, ry, rz + 0.4 * dz),
                         (rx + 0.85 * dx, ry + 0.85, rz + 0.85 * dz),
                         (rx + 0.4 * dx, ry + 0.6, rz + 0.4 * dz)]))
    rng = random.Random(int(t * 12))
    for _ in range(3):
        fx = rng.uniform(-0.2, 0.2)
        l0 = rng.uniform(0.5, 1.0)
        f.append(P.seg((rx + fx, ry + 0.55, rz),
                       (rx + fx * 1.7, ry + 0.55 + l0, rz)))
    for k in range(1, 6):
        ty = ry + 1.4 * k + 0.4
        f.append(P.seg((rx + 0.04, ty, rz), (rx - 0.04, ty + 0.55, rz)))
    return f


def smooth(v):
    return v * v * (3 - 2 * v)


def main():
    pygame.init()
    pygame.display.set_mode((64, 64))
    with open(os.path.join(os.path.dirname(HERE), "core", "bg_models.json")) as f:
        P.MODELS = json.load(f)
    style = B.STYLES["inverted-soft-jitter"]
    P.setup_view(W, H, 0.8, 0.0, 55.0)
    consts = [yaw_shape(P.constellation(x, y, s, z), ya)
              for x, y, s, z, ya in CONSTELLATIONS]

    out = os.path.join(OUT_DIR, "space_finale.mp4")
    frames = int(DUR * FPS)
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-vcodec", "rawvideo",
         "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", out],
        stdin=subprocess.PIPE)

    for i in range(frames):
        t = i / FPS
        e = smooth(max(0.0, min(1.0, (t - T_HOLD) / T_PULL)))
        B.EYE = tuple(a + (b - a) * e for a, b in zip(EYE0, EYE1))
        B.CENTER = tuple(a + (b - a) * e for a, b in zip(CEN0, CEN1))
        B.CAM_X, B.CAM_Y, B.CAM_Z = B._camera_basis()
        surf = pygame.Surface((W, H))
        surf.fill(style["bg"])
        P.stars(surf, hash("spacefinale") % 1000, W)
        lrng = random.Random(16500 + i)
        deep = {"data": moon_face() + solar_system(t) + comets(t)}
        B.draw_shape(surf, deep, style, P.MODELS["materials"], lrng)
        for sh in consts:
            B.draw_shape(surf, sh, style, P.MODELS["materials"], lrng)
        B.draw_shape(surf, {"data": ufo(t) + rocket(t)}, style,
                     P.MODELS["materials"], lrng)
        # the drifting house with Miku on the ridge
        bob = 0.18 * round(math.sin(math.pi * 2 * t / 3.5) * 2) / 2
        B.draw_shape(surf, house(bob), style, P.MODELS["materials"], lrng)
        feet = B.project(0, (RIDGE_Y + bob) * B.M, 0)
        head_ref = B.project(0, (RIDGE_Y + bob - MIKU_WORLD_H) * B.M, 0)
        if feet and head_ref and 0 < feet[1] - head_ref[1] < 700:
            mw = (feet[1] - head_ref[1]) / 1.9
            d = DS.D(surf, MIKU_V, seed=1190 + i)
            sw = round(math.sin(math.pi * 2 * t / 2.8) * 2) / 2 * 0.045
            DS.draw_miku(d, feet[0], feet[1] - 1.53 * mw, mw,
                         tail_swing=(sw, -sw), tail_swing2=(-sw * 1.6,
                                                            sw * 1.6))
        if i in (5, 45, 95):
            pygame.image.save(surf,
                              os.path.join(CHECK_DIR, f"space_f{i}.png"))
        ff.stdin.write(pygame.image.tostring(surf, "RGB"))

    ff.stdin.close()
    ff.wait()
    print(f"saved {out}")


if __name__ == "__main__":
    main()
