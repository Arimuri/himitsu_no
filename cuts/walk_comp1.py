#!/usr/bin/env python3
"""comp_1 framing: Miku seen from behind, toddling away from the camera
into the distance.  Three background variants, 5 s each, 12 fps, 16:9.
Outputs: movie/current/walk_comp1_{house,danchi,pylon}.mp4
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
DUR = 5.0

MIKU_V = {"render": "line", "bg": "black", "mono": True, "line_col": DS.WHITE,
          "scribble": True, "roughness": 2.0, "lw": 2}
# walking away: big foreground right -> small in the open right distance
MIKU_P0, MIKU_P1 = (2.85, 5.42), (5.2, 0.2)    # world (x, z) endpoints
MIKU_WORLD_H = 2.3


def place(shape, x, z=0.0, sc=1.0):
    for face in shape["data"]:
        for v in face["vertices"]:
            v[0] = v[0] * sc + x
            v[1] = v[1] * sc
            v[2] = v[2] * sc + z
    return shape


VARIANTS = {
    "house": lambda: [P.ground(), P.building_2(-0.8), P.tree_1(2.6, 1.5)],
    "danchi": lambda: [P.ground(), place(P.danchi(), -1.2, 0, 0.85),
                       place(P.water_tower(), 3.1, 0, 0.95)],
    "pylon": lambda: [P.ground(), place(P.pylon(0.0, 4.6), -0.8, 0, 0.8),
                      P.tree_5(2.8, 1.3)],
}


def render(name, scene_fn):
    style = B.STYLES["inverted-soft-jitter"]
    P.setup_view(W, H, 0.78, -240.0, 20.0)
    scene = scene_fn()
    out = os.path.join(OUT_DIR, f"walk_comp1_{name}.mp4")
    frames = int(DUR * FPS)
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-vcodec", "rawvideo",
         "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", out],
        stdin=subprocess.PIPE)

    for i in range(frames):
        t = i / (frames - 1)
        # static camera, just a slow eased push-in (an orbit made the
        # opening read too fast against the receding walk)
        B.EYE = (B.CENTER[0], -50.0, B.CENTER[2] + 500.0)
        B.CAM_X, B.CAM_Y, B.CAM_Z = B._camera_basis()
        e_ = t * t * (3 - 2 * t)
        B.VIEW_ZOOM = 0.78 + 0.08 * e_
        surf = pygame.Surface((W, H))
        surf.fill(style["bg"])
        P.stars(surf, hash("comp_1") % 1000, W)
        lrng = random.Random(11300 + i)
        mx = MIKU_P0[0] + (MIKU_P1[0] - MIKU_P0[0]) * t
        mz = MIKU_P0[1] + (MIKU_P1[1] - MIKU_P0[1]) * t
        if mz < 0:                     # gone past the props: draw her behind
            miku_first = True
        else:
            miku_first = False

        def draw_miku_now():
            feet = B.project(mx * B.M, 0, mz * B.M)
            head_ref = B.project(mx * B.M, -MIKU_WORLD_H * B.M, mz * B.M)
            if not (feet and head_ref):
                return
            mw = (feet[1] - head_ref[1]) / 1.9
            d = DS.D(surf, MIKU_V, seed=500 + i)
            phase = i / FPS * 1.4

            def qz(v):
                return round(v * 2) / 2
            s = phase % 2.0
            hop = qz(abs(math.sin(math.pi * phase))) * mw * 0.03
            ang_l = qz(math.sin(math.pi * s)) * 0.24 if s < 1.0 else 0.0
            ang_r = qz(math.sin(math.pi * (s - 1.0))) * 0.24 if s >= 1.0 else 0.0
            sw = qz(math.sin(math.pi * phase)) * 0.03
            sw2 = qz(math.sin(math.pi * (phase - 0.45))) * 0.07
            DS.draw_miku(d, feet[0], feet[1] - 1.53 * mw - hop, mw,
                         tail_swing=(sw, -sw), tail_swing2=(sw2, -sw2),
                         leg_ang=(ang_l, ang_r), back=True)

        if miku_first:
            draw_miku_now()
        for sh in scene:
            B.draw_shape(surf, sh, style, P.MODELS["materials"], lrng)
        if not miku_first:
            draw_miku_now()
        if i == 30:
            pygame.image.save(
                surf, os.path.join(CHECK_DIR, f"walk_comp1_{name}_f30.png"))
        ff.stdin.write(pygame.image.tostring(surf, "RGB"))

    ff.stdin.close()
    ff.wait()
    print(f"saved {out}")


def main():
    pygame.init()
    pygame.display.set_mode((64, 64))
    with open(os.path.join(os.path.dirname(HERE), "core", "bg_models.json")) as f:
        P.MODELS = json.load(f)
    names = sys.argv[1:] or list(VARIANTS)
    for name in names:
        render(name, VARIANTS[name])


if __name__ == "__main__":
    main()
