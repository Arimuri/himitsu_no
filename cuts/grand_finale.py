#!/usr/bin/env python3
"""The grand finale: start tight on Miku, then rise and pull back until the
whole world we built is in frame — village, industry, ferris wheel, pylons,
bridge, train, playground props — under a sky holding the moon, three
constellations, a mini solar system, comets, a UFO and a distant rocket
launch.  8 s, 12 fps, 16:9.  Output: movie/current/grand_finale.mp4
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
T_HOLD, T_PULL = 1.0, 6.2       # close on Miku, then the long rise
MIKU_POS = (0.0, 4.0)
MIKU_WORLD_H = 2.3
MIKU_V = {"render": "line", "bg": "black", "mono": True, "line_col": DS.WHITE,
          "scribble": True, "roughness": 2.0, "lw": 2}

EYE0, EYE1 = (0.0, -60.0, 430.0), (0.0, -1380.0, 1980.0)
CEN0, CEN1 = (0.0, -110.0, 280.0), (0.0, -280.0, -420.0)


def place(shape, x, z=0.0, sc=1.0):
    for face in shape["data"]:
        for v in face["vertices"]:
            v[0] = v[0] * sc + x
            v[1] = v[1] * sc
            v[2] = v[2] * sc + z
    return shape


def yaw_shape(shape, ang):
    c, s_ = math.cos(ang), math.sin(ang)
    for face in shape["data"]:
        for v in face["vertices"]:
            x, z = v[0], v[2]
            v[0] = x * c + z * s_
            v[2] = -x * s_ + z * c
    return shape


def ground():
    gpts = [(-40, 6.5), (40, 6.5), (40, -42), (-40, -42)]
    f = []
    for k in range(4):
        (x0, z0), (x1, z1) = gpts[k], gpts[(k + 1) % 4]
        n = max(2, int(math.hypot(x1 - x0, z1 - z0) / 1.5))
        for j in range(n):
            t0, t1 = j / n, (j + 1) / n
            f.append(P.seg((x0 + (x1 - x0) * t0, 0, z0 + (z1 - z0) * t0),
                           (x0 + (x1 - x0) * t1, 0, z0 + (z1 - z0) * t1)))
    rng = random.Random(3)
    for _ in range(46):
        x = rng.uniform(-36, 36)
        z = rng.uniform(-38, 5.5)
        a = rng.uniform(0, math.pi)
        l = rng.uniform(0.14, 0.32)
        f.append(P.seg((x, 0, z), (x + math.cos(a) * l, -0.13,
                                   z + math.sin(a) * l * 0.4)))
    return {"data": f}


def build_static():
    """(z_key, shape) list of everything that never moves."""
    s = [(-99, ground())]
    s.append((-26, P.power_line(tuple(range(-33, 34, 9)), 4.4, 0.6, -26.0)))
    s.append((-34, place(P.pylon(0.0, 4.6), 26.0, -34.0, 2.0)))
    s.append((-36, place(P.crane(), -13.0, -36.0, 1.7)))
    s.append((-32, place(P.factory(), 17.0, -32.0, 1.7)))
    s.append((-27, place(P.warehouse(), 31.0, -27.0, 1.5)))
    s.append((-29, place(P.silo(), -24.0, -29.0, 1.5)))
    s.append((-30, place(P.danchi(), -4.0, -30.0, 1.6)))
    s.append((-26, place(P.office(), 8.5, -26.0, 1.4)))
    s.append((-33, place(P.lighthouse(), -33.0, -33.0, 1.6)))
    s.append((-32.5, place(P.rock(0, 1.7, 23), -33.0, -32.0)))
    s.append((-18, place(P.truss_bridge(), 16.0, -18.0, 1.5)))
    s.append((-10, place(P.water_tower(), -31.0, -10.0, 1.4)))
    s.append((-6, place(P.building_1(1.15), -14.0, -6.0)))
    s.append((-8, place(P.building_2(1.15), 11.0, -8.0)))
    s.append((-5, place(P.building_4(1.05), 22.0, -5.0)))
    s.append((-9, place(P.building_5(1.15), -5.0, -9.0)))
    s.append((-2, place(P.bus_stop(), 7.5, -2.0, 1.25)))
    for lx, lz in ((-11.0, 0.0), (-19.0, -2.5), (15.5, -2.5)):
        s.append((lz, place(P.street_lamp(), lx, lz, 1.15)))
    for bld, x, z, sc in ((P.tree_1, -26, -20, 1.6), (P.tree_2, 27, -12, 1.5),
                          (P.tree_3, -9, -14, 1.4), (P.tree_4, 33, -18, 1.5),
                          (P.tree_5, -37, -22, 1.6), (P.tree_2, 2, -16, 1.3)):
        s.append((z, place(bld(0, 1.0), x, z, sc)))
    for x, z, sc, sd in ((-17, 2.5, 1.1, 12), (20, 1.0, 1.3, 34),
                         (31, -3.0, 0.9, 47), (-27, -4.0, 1.2, 5)):
        s.append((z, place(P.rock(0, sc, sd), x, z)))
    # the little yard around Miku
    s.append((2.6, place(P.clothesline(), 5.2, 2.6, 0.9)))
    s.append((4.6, place(P.telescope(), -2.6, 4.6, 0.8)))
    s.append((4.7, place(P.gacha(), 3.1, 4.7, 0.7)))
    # sky layer (far back, drawn first)
    s.append((-60, yaw_shape(P.constellation(13.0, -25.0, 2.4, -46.0), 0.8)))
    s.append((-61, yaw_shape(P.constellation(-28.0, -23.0, 2.2, -44.0), 2.0)))
    s.append((-62, yaw_shape(P.constellation(1.0, -31.0, 2.6, -50.0), 4.0)))
    return s


def solar_mini(t):
    scx, scy, scz, sc = 27.0, -33.0, -52.0, 1.5
    X, Y = B.CAM_X, B.CAM_Y
    f = []

    def disc(cx, cy, cz, r):
        return P.q(5, [(cx + r * (X[0] * math.cos(a) + Y[0] * math.sin(a)),
                        cy + r * (X[1] * math.cos(a) + Y[1] * math.sin(a)),
                        cz + r * (X[2] * math.cos(a) + Y[2] * math.sin(a)))
                       for a in [math.pi * 2 * k / 8 for k in range(8)]])

    f.append(disc(scx, scy, scz, 0.5 * sc))
    for orad, prad, ph in ((1.1, 0.12, 0.5), (1.9, 0.16, 2.4),
                           (2.8, 0.2, 4.2)):
        ring = [(scx + orad * sc * math.cos(a), scy,
                 scz + orad * sc * math.sin(a))
                for a in [math.pi * 2 * k / 20 for k in range(20)]]
        f += P.chain(ring + [ring[0]])
        a = ph + 0.15 * t
        f.append(disc(scx + orad * sc * math.cos(a), scy,
                      scz + orad * sc * math.sin(a), prad * sc))
    return f


def moon_face():
    mx, my, mz, r = -22.0, -28.0, -48.0, 2.4
    X, Y = B.CAM_X, B.CAM_Y
    return [P.q(5, [(mx + r * (X[0] * math.cos(a) + Y[0] * math.sin(a)),
                     my + r * (X[1] * math.cos(a) + Y[1] * math.sin(a)),
                     mz + r * (X[2] * math.cos(a) + Y[2] * math.sin(a)))
                    for a in [math.pi * 2 * k / 14 for k in range(14)]])]


def comets(t):
    f = []
    for t0, p0, p1 in ((2.4, (34, -34, -42), (-6, -25, -46)),
                       (4.2, (-38, -32, -40), (2, -24, -44))):
        u = (t - t0) / 1.7
        if not 0.0 <= u <= 1.1:
            continue
        hx = p0[0] + (p1[0] - p0[0]) * u
        hy = p0[1] + (p1[1] - p0[1]) * u
        hz = p0[2] + (p1[2] - p0[2]) * u
        dx, dy, dz = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]
        L = math.hypot(dx, dy, dz)
        dx, dy, dz = dx / L, dy / L, dz / L
        f.append(P.seg((hx, hy, hz), (hx - dx * 2.2, hy - dy * 2.2,
                                      hz - dz * 2.2)))
        for k in range(3):
            o = 3.2 + k * 1.4
            f.append(P.seg((hx - dx * o, hy - dy * o, hz - dz * o),
                           (hx - dx * (o + 0.7), hy - dy * (o + 0.7),
                            hz - dz * (o + 0.7))))
    return f


def ufo(t):
    if not 3.6 <= t <= 7.4:
        return []
    u = (t - 3.6) / 3.8
    cx = -40 + 80 * u
    cy = -26.5 + 1.2 * math.sin(u * 9)
    cz = -38.0
    f = []
    rim = [(cx + 1.6 * math.cos(a), cy + 0.35 * math.sin(a),
            cz + 0.7 * math.sin(a)) for a in
           [math.pi * 2 * k / 12 for k in range(12)]]
    f.append(P.q(2, rim))
    f += P.chain([(cx + 0.75 * math.cos(a), cy - 0.32 - 0.55 * math.sin(a),
                   cz) for a in [math.pi * k / 6 for k in range(7)]])
    return f


def rocket(t):
    f = [P.seg((-30.6, 0, -30), (-30.5, -2.6, -30)),
         P.seg((-30.2, 0, -30), (-30.3, -2.6, -30))]     # gantry
    ry = 0.0 if t < 3.0 else -1.15 * (t - 3.0) ** 2
    n = 6
    base = [(-29.5 + 0.32 * math.cos(a), ry - 0.4, -30 + 0.32 * math.sin(a))
            for a in [math.pi * 2 * k / n for k in range(n)]]
    top = [(-29.5 + 0.32 * math.cos(a), ry - 1.9, -30 + 0.32 * math.sin(a))
           for a in [math.pi * 2 * k / n for k in range(n)]]
    f.append(P.q(0, base))
    f.append(P.q(0, top))
    for k in range(0, n, 2):
        f.append(P.seg(base[k], top[k]))
        f.append(P.seg(top[k], (-29.5, ry - 2.6, -30)))
    if t >= 2.7:
        rng = random.Random(int(t * 12))
        for _ in range(2):
            fx = rng.uniform(-0.2, 0.2)
            f.append(P.seg((-29.5 + fx, ry - 0.35, -30),
                           (-29.5 + fx * 1.5, ry + rng.uniform(0.4, 0.9),
                            -30)))
    if t >= 3.4:
        for k in range(1, 5):
            ty = ry + 1.0 * k
            if ty > -0.2:
                break
            f.append(P.seg((-29.52, ty, -30), (-29.48, ty + 0.42, -30)))
    return f


def smooth(v):
    return v * v * (3 - 2 * v)


def main():
    pygame.init()
    pygame.display.set_mode((64, 64))
    with open(os.path.join(os.path.dirname(HERE), "core", "bg_models.json")) as f:
        P.MODELS = json.load(f)
    style = B.STYLES["inverted-soft-jitter"]
    P.setup_view(W, H, 0.75, 0.0, 40.0)
    static = sorted(build_static(), key=lambda p: p[0])

    out = os.path.join(OUT_DIR, "grand_finale.mp4")
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
        P.stars(surf, hash("finale") % 1000, W)
        lrng = random.Random(16300 + i)
        # sky first
        sky = {"data": moon_face() + solar_mini(t) + comets(t) + ufo(t)
               + rocket(t)}
        B.draw_shape(surf, sky, style, P.MODELS["materials"], lrng)
        # dynamic ground items merged with statics by depth
        dyn = [(2.6, place(yaw_shape(
                   P.swing_set(0.0, 0.28 * math.sin(math.pi * 2 * t / 2.8)),
                   0.5), -6.5, 2.6, 0.95)),
               (-16, yaw_shape(place(P.ferris_wheel(0.0, 1.85, 0.1 * t, 0.38),
                                     -22.0, -16.0, 2.1), 0.3)),
               (-20, place(P.wind_turbine(0.0, 3.5, 1.4 * t), 30.0, -20.0,
                           1.5)),
               (-12.7, place(P.train(0.0, 2, False), -30.0 + 8.0 * t, -13.0,
                             1.1))]
        for zk, sh in sorted(static + dyn, key=lambda p: p[0]):
            if zk <= MIKU_POS[1]:
                B.draw_shape(surf, sh, style, P.MODELS["materials"], lrng)
        mx, mz = MIKU_POS
        feet = B.project(mx * B.M, 0, mz * B.M)
        head_ref = B.project(mx * B.M, -MIKU_WORLD_H * B.M, mz * B.M)
        if feet and head_ref and 0 < feet[1] - head_ref[1] < 700:
            mw = (feet[1] - head_ref[1]) / 1.9
            d = DS.D(surf, MIKU_V, seed=1170 + i)
            sw = round(math.sin(math.pi * 2 * t / 3.2) * 2) / 2 * 0.03
            DS.draw_miku(d, feet[0], feet[1] - 1.53 * mw, mw,
                         tail_swing=(sw, -sw), tail_swing2=(-sw, sw))
        for zk, sh in sorted(static + dyn, key=lambda p: p[0]):
            if zk > MIKU_POS[1]:
                B.draw_shape(surf, sh, style, P.MODELS["materials"], lrng)
        if i in (4, 40, 70, 95):
            pygame.image.save(surf,
                              os.path.join(CHECK_DIR, f"finale_f{i}.png"))
        ff.stdin.write(pygame.image.tostring(surf, "RGB"))

    ff.stdin.close()
    ff.wait()
    print(f"saved {out}")


if __name__ == "__main__":
    main()
