#!/usr/bin/env python3
"""Convenience-store cut (busstop_wait sibling): road in front, Miku standing
by the entrance.  Camera trucks sideways while gradually rising.
8 s, 12 fps, 16:9.  Output: movie/current/konbini_wait.mp4
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

MIKU_POS = (-2.3, 0.9)          # on the sidewalk by the windows, door clear
MIKU_WORLD_H = 2.3
MIKU_V = {"render": "line", "bg": "black", "mono": True, "line_col": DS.WHITE,
          "scribble": True, "roughness": 2.0, "lw": 2}

CAM_X0, CAM_X1 = -2.2, 2.2
EYE_Y0, EYE_Y1 = -0.9, -3.6


def konbini():
    """Flat-roofed store with the full roadside kit: stocked windows, poster
    glass, striped fascia, pole sign, nobori flags, parking stalls, bins."""
    f = P.box(0.0, -1.5, 7.5, 2.6, 3.0)
    zf = 0.01
    # glass band: three window panes, shelves + goods visible inside
    for k in range(3):
        x0 = -3.3 + k * 1.25
        f.append(P.q(5, [(x0, -0.55, zf), (x0 + 1.05, -0.55, zf),
                         (x0 + 1.05, -1.7, zf), (x0, -1.7, zf)]))
        for r in range(3):
            sy = -0.75 - r * 0.34
            f.append(P.seg((x0 + 0.06, sy, zf), (x0 + 0.99, sy, zf)))
            for g in range(4):
                gx = x0 + 0.16 + g * 0.22
                f.append(P.seg((gx, sy, zf), (gx, sy - 0.16, zf)))
    # posters taped on the glass
    f.append(P.q(2, [(-3.1, -1.05, zf), (-2.72, -1.05, zf),
                     (-2.72, -1.5, zf), (-3.1, -1.5, zf)]))
    f.append(P.q(2, [(-0.9, -0.95, zf), (-0.5, -0.95, zf),
                     (-0.5, -1.42, zf), (-0.9, -1.42, zf)]))
    f.append(P.seg((-3.03, -1.2, zf + 0.001), (-2.79, -1.2, zf + 0.001)))
    f.append(P.seg((-0.83, -1.1, zf + 0.001), (-0.57, -1.1, zf + 0.001)))
    # sliding door: two panes + centre split + mat
    f.append(P.q(5, [(0.8, -0.15, zf), (2.2, -0.15, zf),
                     (2.2, -1.85, zf), (0.8, -1.85, zf)]))
    f.append(P.seg((1.5, -0.15, zf), (1.5, -1.85, zf)))
    f.append(P.seg((0.8, -0.15, zf), (2.2, -0.15, zf)))
    f.append(P.q(0, [(0.85, -0.01, 0.15), (2.15, -0.01, 0.15),
                     (2.15, -0.01, 0.62), (0.85, -0.01, 0.62)]))
    # sign fascia with the double stripe + name ticks
    f.append(P.q(2, [(-3.75, -1.95, zf), (3.75, -1.95, zf),
                     (3.75, -2.45, zf), (-3.75, -2.45, zf)]))
    for yy in (-2.07, -2.16):
        f.append(P.seg((-3.75, yy, zf), (3.75, yy, zf)))
    for k in range(4):
        xx = -2.6 + k * 0.5
        f.append(P.seg((xx, -2.25, zf), (xx + 0.28, -2.38, zf)))
    # rooftop units + antenna
    f += P.box(-1.6, -2.0, 0.95, 0.45, 0.8, 2, 2, y0=-2.6)
    f += P.box(1.9, -2.3, 0.7, 0.35, 0.6, 2, 2, y0=-2.6)
    f.append(P.seg((3.1, -2.6, -2.2), (3.1, -3.5, -2.2)))
    f.append(P.seg((2.9, -3.3, -2.2), (3.3, -3.3, -2.2)))
    # drainpipe + meter box on the left corner
    f.append(P.seg((-3.7, 0, 0.04), (-3.72, -2.55, 0.02)))
    f += P.box(-3.55, 0.15, 0.3, 0.35, 0.18, 2, 2, y0=-1.15)
    # A-board by the door
    f.append(P.seg((2.9, 0, 0.65), (3.05, -0.75, 0.5)))
    f.append(P.seg((3.2, 0, 0.35), (3.05, -0.75, 0.5)))
    f.append(P.seg((2.93, -0.25, 0.6), (3.17, -0.25, 0.4)))
    # bins beside the door
    f += P.box(2.65, 0.35, 0.4, 0.75, 0.4, 2, 2)
    f += P.box(3.15, 0.35, 0.4, 0.75, 0.4, 2, 2)
    f.append(P.seg((2.52, -0.75, 0.35), (3.35, -0.75, 0.35)))
    # vending machine at the left end
    f += P.box(-3.3, 0.4, 0.75, 1.7, 0.6, 5, 2)
    for k in range(3):
        f.append(P.seg((-3.55, -1.35 + k * 0.18, 0.71),
                       (-3.05, -1.35 + k * 0.18, 0.71)))
    # tall pole sign out by the road
    f.append(P.seg((-5.6, 0, 0.8), (-5.62, -3.9, 0.8)))
    f.append(P.seg((-5.52, 0, 0.84), (-5.56, -3.9, 0.82)))
    f += [P.q(2, [(-6.25, -3.9, 0.8), (-4.95, -3.9, 0.8),
                  (-4.95, -3.05, 0.8), (-6.25, -3.05, 0.8)])]
    for yy in (-3.62, -3.5):
        f.append(P.seg((-6.25, yy, 0.8), (-4.95, yy, 0.8)))
    for k in range(2):
        f.append(P.seg((-5.85 + k * 0.45, -3.32, 0.8),
                       (-5.62 + k * 0.45, -3.18, 0.8)))
    # nobori flags flanking the entrance
    for fx in (4.3, 5.1):
        f.append(P.seg((fx, 0, 0.9), (fx - 0.02, -2.3, 0.9)))
        f.append(P.seg((fx - 0.02, -2.3, 0.9), (fx + 0.42, -2.28, 0.9)))
        f.append(P.q(2, [(fx + 0.02, -2.26, 0.9), (fx + 0.4, -2.26, 0.9),
                         (fx + 0.4, -0.9, 0.9), (fx + 0.02, -0.9, 0.9)]))
        for k in range(3):
            f.append(P.seg((fx + 0.21, -2.05 + k * 0.33, 0.9),
                           (fx + 0.21, -1.9 + k * 0.33, 0.9)))
    return {"data": f}


def road():
    f = [P.seg((-34, 0, 1.6), (34, 0, 1.6)),
         P.seg((-34, 0, 4.0), (34, 0, 4.0)),
         P.seg((-34, 0, 1.15), (34, 0, 1.15))]
    x = -33.0
    while x < 33.0:
        f.append(P.seg((x, 0, 2.8), (x + 1.4, 0, 2.8)))
        x += 3.0
    return {"data": f}


def main():
    pygame.init()
    pygame.display.set_mode((64, 64))
    with open(os.path.join(os.path.dirname(HERE), "core", "bg_models.json")) as f:
        P.MODELS = json.load(f)
    style = B.STYLES["inverted-soft-jitter"]
    P.setup_view(W, H, 1.15, 0.0, 30.0)

    scene = [P.ground(hx=20, zf=1.1, zb=-12), road(), konbini()]

    out = os.path.join(OUT_DIR, "konbini_wait.mp4")
    frames = int(DUR * FPS)
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-vcodec", "rawvideo",
         "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", out],
        stdin=subprocess.PIPE)

    for i in range(frames):
        t = i / (frames - 1)
        e = t * t * (3 - 2 * t)
        cx = (CAM_X0 + (CAM_X1 - CAM_X0) * e) * B.M
        B.EYE = (cx, (EYE_Y0 + (EYE_Y1 - EYE_Y0) * e) * B.M, 500.0)
        B.CENTER = (cx, -1.3 * B.M, 0.0)
        B.CAM_X, B.CAM_Y, B.CAM_Z = B._camera_basis()
        surf = pygame.Surface((W, H))
        surf.fill(style["bg"])
        P.stars(surf, hash("konbini") % 1000, W)
        lrng = random.Random(12500 + i)
        for sh in scene:
            B.draw_shape(surf, sh, style, P.MODELS["materials"], lrng)
        mx, mz = MIKU_POS
        feet = B.project(mx * B.M, 0, mz * B.M)
        head_ref = B.project(mx * B.M, -MIKU_WORLD_H * B.M, mz * B.M)
        if feet and head_ref:
            mw = (feet[1] - head_ref[1]) / 1.9
            d = DS.D(surf, MIKU_V, seed=990 + i)
            sw = round(math.sin(math.pi * 2 * (i / FPS) / 3.4) * 2) / 2 * 0.03
            DS.draw_miku(d, feet[0], feet[1] - 1.53 * mw, mw,
                         tail_swing=(sw, -sw), tail_swing2=(-sw, sw))
        if i in (0, 48, 95):
            pygame.image.save(surf,
                              os.path.join(CHECK_DIR, f"konbini_f{i}.png"))
        ff.stdin.write(pygame.image.tostring(surf, "RGB"))

    ff.stdin.close()
    ff.wait()
    print(f"saved {out}")


if __name__ == "__main__":
    main()
