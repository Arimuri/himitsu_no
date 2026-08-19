#!/usr/bin/env python3
"""Telescope cut: the telescope waits on the plain, then the camera pans up
into the sky with a slow zoom until the fisheye constellations it was aimed
at fill the view.  15 s, 12 fps, 16:9.
Output: movie/current/telescope_sky.mp4
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
DUR = 15.0
T_HOLD, T_PAN = 2.5, 9.0        # hold, tilt, then ~3.5 s resting on the sky
C0, C1 = (0.0, -170.0, 0.0), (0.0, -2000.0, 0.0)
Z0, Z1 = 0.85, 1.35             # slow push while tilting
FE_C = 0.72                     # fisheye strength

# (x, y, scale, z, yaw) — a wide ring around the static-camera zenith
# (0, 7.1): two near the centre, five spread far out in varied directions.
# Everything with z >= ~9.5 (or high enough) stays out of the opening view.
CONSTELLATIONS = [
    (0.0, -19.0, 2.0, 7.0, 0.0),
    (-2.5, -26.0, 1.8, 6.5, 2.0),
    (-13.0, -24.0, 2.2, 9.5, 1.1),
    (13.5, -22.0, 2.2, 10.5, 2.3),
    (-9.0, -12.5, 1.6, 12.0, 3.6),
    (9.5, -13.0, 1.6, 12.5, 4.8),
    (0.5, -11.0, 1.4, 14.5, 0.7),
]


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


def fe_project(px, py, pz):
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


def main():
    pygame.init()
    pygame.display.set_mode((64, 64))
    with open(os.path.join(os.path.dirname(HERE), "core", "bg_models.json")) as f:
        P.MODELS = json.load(f)
    style = B.STYLES["inverted-soft-jitter"]
    P.setup_view(W, H, Z0, 0.0, 30.0)
    scene = [plain_ground(), place(P.telescope(), 0.6, 0.0, 1.35)]
    sky = [yaw_shape(P.constellation(x, y, s, z), ya)
           for x, y, s, z, ya in CONSTELLATIONS]

    out = os.path.join(OUT_DIR, "telescope_sky.mp4")
    frames = int(DUR * FPS)
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-vcodec", "rawvideo",
         "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", out],
        stdin=subprocess.PIPE)

    for i in range(frames):
        t = i / FPS
        pt = max(0.0, min(1.0, (t - T_HOLD) / T_PAN))
        e = pt * pt * (3 - 2 * pt)
        B.CENTER = tuple(a + (b - a) * e for a, b in zip(C0, C1))
        B.CAM_X, B.CAM_Y, B.CAM_Z = B._camera_basis()
        # camera roll: eases in mid-tilt, still accelerating at the end
        ru = max(0.0, min(1.0, (t - 6.5) / 8.5))
        roll = 0.65 * ru * ru
        cr, sr = math.cos(roll), math.sin(roll)
        cx_, cy_ = B.CAM_X, B.CAM_Y
        B.CAM_X = tuple(cr * cx_[k] + sr * cy_[k] for k in range(3))
        B.CAM_Y = tuple(-sr * cx_[k] + cr * cy_[k] for k in range(3))
        B.VIEW_ZOOM = Z0 + (Z1 - Z0) * e
        surf = pygame.Surface((W, H))
        surf.fill(style["bg"])
        P.stars(surf, hash("telescope") % 1000, W)
        lrng = random.Random(13300 + i)
        draw_sky(surf, sky, style, lrng)
        for sh in scene:
            B.draw_shape(surf, sh, style, P.MODELS["materials"], lrng)
        if i in (0, 90, 150, 179):
            pygame.image.save(surf,
                              os.path.join(CHECK_DIR, f"telsky_f{i}.png"))
        ff.stdin.write(pygame.image.tostring(surf, "RGB"))

    ff.stdin.close()
    ff.wait()
    print(f"saved {out}")


if __name__ == "__main__":
    main()
