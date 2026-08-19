#!/usr/bin/env python3
"""radiowaves cut: a 3D lattice radio mast pulsing billboard arcs; the camera
orbits while tilting up into a sky holding several constellations.
8 s, 12 fps, 16:9.  Output: movie/current/radio_sky.mp4
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
from scribble import jitter_line

OUT_DIR = "/Users/arimura/Dropbox/ボカコレ2026S/movie/current"
CHECK_DIR = os.path.join(OUT_DIR, "check")
os.makedirs(CHECK_DIR, exist_ok=True)
W, H = 1280, 720
FPS = 12
DUR = 8.0

MAST_H = 3.6
TIP = (0.0, -MAST_H - 0.35, 0.0)
T_HOLD, T_PAN = 0.8, 4.5        # then ~2.7 s drifting across the sky
R_ORBIT, EYE_H = 7.0, -1.2

# (x, y, scale, z, yaw) — two layers scattered across the whole end-of-tilt
# sky: three far ones around the zenith (5.0, -4.9), two low near-overhead
# ones that land big toward the frame edges.  All stay out of the opening
# horizontal view (checked via elevation/depth against the fisheye FOV).
CONSTELLATIONS = [
    (5.0, -22.0, 3.0, -4.9, 0.0),
    (-8.0, -31.5, 3.2, -12.0, 1.1),
    (16.0, -23.0, 3.0, -9.0, 2.3),
    (1.0, -9.5, 1.8, 6.0, 3.6),
    (10.5, -11.0, 2.0, 3.5, 4.8),
]
FE_C = 0.72                     # fisheye strength: r = f/c * tan(c * theta)


def fe_project(px, py, pz):
    """Fisheye-ish projection (r = f/c * tan(c*theta)) for the sky layer."""
    dx, dy, dz = px * B.M - B.EYE[0], py * B.M - B.EYE[1], pz * B.M - B.EYE[2]
    vx = dx * B.CAM_X[0] + dy * B.CAM_X[1] + dz * B.CAM_X[2]
    vy = dx * B.CAM_Y[0] + dy * B.CAM_Y[1] + dz * B.CAM_Y[2]
    vz = dx * B.CAM_Z[0] + dy * B.CAM_Z[1] + dz * B.CAM_Z[2]
    fwd = -vz
    if fwd <= 1e-6:
        return None
    th = math.atan2(math.hypot(vx, vy), fwd)
    if th > 1.25:
        return None
    focal = (B.VIEW_H / 2) / math.tan(B.FOV / 2)
    r = focal * B.VIEW_ZOOM / FE_C * math.tan(FE_C * th)
    ph = math.atan2(vy, vx)
    return (B.VIEW_W / 2 + B.VIEW_XOFF + r * math.cos(ph),
            B.VIEW_H / 2 + B.VIEW_YOFF + r * math.sin(ph))


def draw_sky(surf, shapes, style, rng):
    """Constellations through the fisheye: subdivide segments so they bend."""
    for sh in shapes:
        for face in sh["data"]:
            vs = face["vertices"]
            for a, b in zip(vs, vs[1:] + [vs[0]]):
                pts = []
                ok = True
                for k in range(7):
                    t = k / 6
                    p = fe_project(a[0] + (b[0] - a[0]) * t,
                                   a[1] + (b[1] - a[1]) * t,
                                   a[2] + (b[2] - a[2]) * t)
                    if p is None:
                        ok = False
                        break
                    pts.append(p)
                if not ok:
                    continue
                for j in range(6):
                    jitter_line(surf, style["line"], style["lw"],
                                pts[j][0], pts[j][1],
                                pts[j + 1][0], pts[j + 1][1], rng)


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


def radio_mast():
    """Four-legged tapering lattice mast with a tip antenna."""
    f = []
    lv = [0.0, -1.1, -2.1, -2.9, -MAST_H]
    wd = [0.6, 0.44, 0.3, 0.19, 0.1]
    for sx, sz in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        for k in range(len(lv) - 1):
            f.append(P.seg((wd[k] * sx, lv[k], wd[k] * sz),
                           (wd[k + 1] * sx, lv[k + 1], wd[k + 1] * sz)))
    # X braces + horizontal frames on all four sides
    for k in range(len(lv) - 1):
        for side in range(4):
            a0 = [(-1, -1), (1, -1), (1, 1), (-1, 1)][side]
            a1 = [(1, -1), (1, 1), (-1, 1), (-1, -1)][side]
            p00 = (wd[k] * a0[0], lv[k], wd[k] * a0[1])
            p01 = (wd[k] * a1[0], lv[k], wd[k] * a1[1])
            p10 = (wd[k + 1] * a0[0], lv[k + 1], wd[k + 1] * a0[1])
            p11 = (wd[k + 1] * a1[0], lv[k + 1], wd[k + 1] * a1[1])
            f.append(P.seg(p00, p11))
            f.append(P.seg(p01, p10))
        for side in range(4):
            a0 = [(-1, -1), (1, -1), (1, 1), (-1, 1)][side]
            a1 = [(1, -1), (1, 1), (-1, 1), (-1, -1)][side]
            f.append(P.seg((wd[k + 1] * a0[0], lv[k + 1], wd[k + 1] * a0[1]),
                           (wd[k + 1] * a1[0], lv[k + 1], wd[k + 1] * a1[1])))
    f.append(P.seg((0, -MAST_H, 0), TIP))
    return {"data": f}


def waves(t):
    """Pulsing billboard arcs either side of the tip (camera-facing)."""
    X, Y = B.CAM_X, B.CAM_Y
    f = [P.q(5, [(TIP[0] + 0.09 * (X[0] * math.cos(a) + Y[0] * math.sin(a)),
                  TIP[1] + 0.09 * (X[1] * math.cos(a) + Y[1] * math.sin(a)),
                  TIP[2] + 0.09 * (X[2] * math.cos(a) + Y[2] * math.sin(a)))
                 for a in [math.pi * 2 * k / 8 for k in range(8)]])]
    for k in range(3):
        r = 0.45 + ((t * 0.55 + k / 3.0) % 1.0) * 1.15
        for sgn in (-1, 1):
            pts = []
            for j in range(6):
                a = math.radians(-28 + 56 * j / 5)
                u = sgn * r * math.cos(a)
                v = -r * math.sin(a)
                pts.append((TIP[0] + X[0] * u + Y[0] * v,
                            TIP[1] + X[1] * u + Y[1] * v,
                            TIP[2] + X[2] * u + Y[2] * v))
            f += P.chain(pts)
    return {"data": f}


def main():
    pygame.init()
    pygame.display.set_mode((64, 64))
    with open(os.path.join(os.path.dirname(HERE), "core", "bg_models.json")) as f:
        P.MODELS = json.load(f)
    style = B.STYLES["inverted-soft-jitter"]
    P.setup_view(W, H, 1.15, 0.0, 30.0)

    # orbit-safe ground: short-segment ring + ticks (a big quad would clip
    # whenever one corner falls behind the orbiting camera)
    # radius stays inside the camera orbit (7.0) so no ring edge ever grazes
    # the near plane and shoots across the sky
    ring = [(5.5 * math.cos(a), 0, 5.5 * math.sin(a))
            for a in [math.pi * 2 * k / 24 for k in range(24)]]
    gnd = {"data": [P.seg(ring[k], ring[(k + 1) % 24]) for k in range(24)]}
    trng = random.Random(77)
    for _ in range(26):
        a = trng.uniform(0, math.pi * 2)
        r = trng.uniform(1.2, 5.0)
        gx, gz = r * math.cos(a), r * math.sin(a)
        gnd["data"].append(P.seg((gx, 0, gz), (gx + 0.22, -0.16, gz)))
    scene = [gnd, radio_mast()]
    sky = [yaw_shape(P.constellation(x, y, s, z), ya)
           for x, y, s, z, ya in CONSTELLATIONS]

    C0, C1 = (0.0, -120.0, 0.0), (0.0, -2200.0, 0.0)
    out = os.path.join(OUT_DIR, "radio_sky.mp4")
    frames = int(DUR * FPS)
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-vcodec", "rawvideo",
         "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", out],
        stdin=subprocess.PIPE)

    for i in range(frames):
        t = i / FPS
        th = 0.15 + 2.2 * (t / DUR)                    # continuous slow orbit
        B.EYE = (R_ORBIT * math.sin(th) * B.M, EYE_H * B.M,
                 R_ORBIT * math.cos(th) * B.M)
        pt_ = max(0.0, min(1.0, (t - T_HOLD) / T_PAN))
        e = pt_ * pt_ * (3 - 2 * pt_)
        B.CENTER = tuple(a + (b - a) * e for a, b in zip(C0, C1))
        B.CAM_X, B.CAM_Y, B.CAM_Z = B._camera_basis()
        surf = pygame.Surface((W, H))
        surf.fill(style["bg"])
        P.stars(surf, hash("radio") % 1000, W)
        lrng = random.Random(11100 + i)
        draw_sky(surf, sky, style, lrng)
        for sh in scene:
            B.draw_shape(surf, sh, style, P.MODELS["materials"], lrng)
        B.draw_shape(surf, waves(t), style, P.MODELS["materials"], lrng)
        if i in (0, 40, 70, 95):
            pygame.image.save(surf, os.path.join(CHECK_DIR, f"radio_sky_f{i}.png"))
        ff.stdin.write(pygame.image.tostring(surf, "RGB"))

    ff.stdin.close()
    ff.wait()
    print(f"saved {out}")


if __name__ == "__main__":
    main()
