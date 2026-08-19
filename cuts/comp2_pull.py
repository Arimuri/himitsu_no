#!/usr/bin/env python3
"""comp_2 scene, camera reversed: starts tight on Miku, pulls back and up-right
until the little world sits far away.  9 s, 12 fps, 16:9.
Output: movie/current/comp_2_pull.mp4
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
DUR = 11.0

MIKU_W_POS = (-2.4, 5.05)
MIKU_WORLD_H = 2.3
MIKU_V = {"render": "line", "bg": "black", "mono": True, "line_col": DS.WHITE,
          "scribble": True, "roughness": 2.0, "lw": 2}

EYE0, EYE1 = (0.0, -58.0, 398.0), (5300.0, -8800.0, 15200.0)
C0, C1 = (-150.0, -135.0, 335.0), (0.0, -130.0, 0.0)
T_IN, T_PULL = 0.7, 9.6         # hold, then pull all the way out to a dot


def main():
    pygame.init()
    pygame.display.set_mode((64, 64))
    with open(os.path.join(os.path.dirname(HERE), "core", "bg_models.json")) as f:
        P.MODELS = json.load(f)
    style = B.STYLES["inverted-soft-jitter"]
    P.setup_view(W, H, 0.58, 0, 20.0)

    def place(shape, x, z, sc=1.0):
        for face in shape["data"]:
            for v in face["vertices"]:
                v[0] = v[0] * sc + x
                v[1] = v[1] * sc
                v[2] = v[2] * sc + z
        return shape

    # comp_2 core stays put; the surroundings only come into view as the
    # camera pulls away (kept out of the |x|<6, z>-4 opening frustum)
    # ground as short segments: a single quad's front corners sit beside the
    # opening camera (culled whole -> ground popped in mid-shot)
    gpts = [(-26, 4.2), (26, 4.2), (26, -24), (-26, -24)]
    gseg = []
    for k in range(4):
        (x0, z0), (x1, z1) = gpts[k], gpts[(k + 1) % 4]
        n = max(2, int(math.hypot(x1 - x0, z1 - z0) / 1.5))
        for j in range(n):
            t0, t1 = j / n, (j + 1) / n
            gseg.append(P.seg((x0 + (x1 - x0) * t0, 0, z0 + (z1 - z0) * t0),
                              (x0 + (x1 - x0) * t1, 0, z0 + (z1 - z0) * t1)))

    # left side only far away (the opening camera looks left); right cluster
    # pushed back so its glancing edges stay out of the opening frame
    scene = [{"data": gseg},
             P.power_line(tuple(range(-24, 25, 8)), 4.0, 0.55, -21.0),
             place(P.pylon(0.0, 4.6), 19.0, -17.0, 1.9),
             place(P.factory(), -24.0, -19.0, 1.7),
             place(P.silo(), 24.0, -14.0, 1.5),
             place(P.danchi(), 16.0, -14.0, 1.5),
             place(P.office(), 18.0, -10.0, 1.6),
             place(P.water_tower(), 14.0, -9.5, 1.4),
             place(P.tree_5(0, 1.6), -25.0, -9.0),
             place(P.tree_1(0, 1.4), -19.0, -6.0),
             P.tree_3(-17.0, 1.5), place(P.rock(0, 1.3, 21), -15.0, -9.0),
             P.building_5(1.6),
             P.tree_2(-2.8, 1.5), P.tree_3(4.6, 1.5),
             place(P.tree_2(0, 1.4), 12.5, 3.0),
             place(P.rock(0, 1.0, 34), 7.5, 4.2),
             place(P.rock(0, 0.8, 47), -13.0, 4.0),
             place(P.rock(0, 1.5, 12), 16.0, 1.5)]

    out = os.path.join(OUT_DIR, "comp_2_pull.mp4")
    frames = int(DUR * FPS)
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-vcodec", "rawvideo",
         "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", out],
        stdin=subprocess.PIPE)

    for i in range(frames):
        t = i / FPS
        pt_ = max(0.0, min(1.0, (t - T_IN) / T_PULL))
        e = pt_ * pt_ * (3 - 2 * pt_)
        B.EYE = tuple(a + (b - a) * e for a, b in zip(EYE0, EYE1))
        B.CENTER = tuple(a + (b - a) * e for a, b in zip(C0, C1))
        B.CAM_X, B.CAM_Y, B.CAM_Z = B._camera_basis()
        surf = pygame.Surface((W, H))
        surf.fill(style["bg"])
        P.stars(surf, hash("comp_2") % 1000, W)
        lrng = random.Random(10700 + i)
        for sh in scene:
            B.draw_shape(surf, sh, style, P.MODELS["materials"], lrng)
        mx, mz = MIKU_W_POS
        feet = B.project(mx * B.M, 0, mz * B.M)
        head_ref = B.project(mx * B.M, -MIKU_WORLD_H * B.M, mz * B.M)
        if feet and head_ref:
            mw = (feet[1] - head_ref[1]) / 1.9
            d = DS.D(surf, MIKU_V, seed=600 + i)
            sw = round(math.sin(math.pi * 2 * t / 3.0) * 2) / 2 * 0.03
            DS.draw_miku(d, feet[0], feet[1] - 1.53 * mw, mw,
                         tail_swing=(sw, -sw), tail_swing2=(-sw, sw))
        if i in (0, 66, 131):
            pygame.image.save(surf, os.path.join(CHECK_DIR, f"comp2_pull_f{i}.png"))
        ff.stdin.write(pygame.image.tostring(surf, "RGB"))

    ff.stdin.close()
    ff.wait()
    print(f"saved {out}")


if __name__ == "__main__":
    main()
