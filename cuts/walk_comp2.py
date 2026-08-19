#!/usr/bin/env python3
"""comp_2 framing: Miku slowly toddling from the back of a busy little
world toward the camera.  Three variants, 8 s each, 12 fps, 16:9.
Outputs: movie/current/walk_comp2_{town,industry,funfair}.mp4
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

# slow approach straight down the centre of the frame
MIKU_P0, MIKU_P1 = (0.0, 0.35), (0.0, 5.2)      # (x, z) walk endpoints
MIKU_WORLD_H = 2.3
MIKU_V = {"render": "line", "bg": "black", "mono": True, "line_col": DS.WHITE,
          "scribble": True, "roughness": 2.0, "lw": 2}


def place(shape, x, z=0.0, sc=1.0):
    for face in shape["data"]:
        for v in face["vertices"]:
            v[0] = v[0] * sc + x
            v[1] = v[1] * sc
            v[2] = v[2] * sc + z
    return shape


# (z key, shape) so Miku can be interleaved at the right depth as she
# approaches the camera
VARIANTS = {
    "town": lambda: [
        (-99, P.ground(hx=18, zf=3.5, zb=-14)),
        (-8.5, P.power_line(tuple(range(-16, 17, 8)), 3.6, 0.5, -8.5)),
        (-5.5, place(P.danchi(), -7.5, -5.5, 1.35)),
        (-4.5, place(P.office(), 2.0, -4.5, 1.25)),
        (-3.0, place(P.water_tower(), 7.5, -3.0, 1.15)),
        (-1.0, place(P.tree_1(0, 1.5), -13.0, -1.0)),
        (0.0, P.building_5(1.4)), (0.0, P.tree_2(-3.0, 1.5)),
        (0.0, P.tree_3(4.8, 1.5)),
        (0.0, place(P.street_lamp(), -10.5, 0.0, 1.2)),
        (1.0, place(P.rock(0, 1.1, 21), 9.8, 1.0)),
        (-1.5, place(P.rock(0, 0.9, 5), 12.5, -1.5))],
    "industry": lambda: [
        (-99, P.ground(hx=18, zf=3.5, zb=-14)),
        (-8.0, place(P.crane(), 0.5, -8.0, 1.6)),
        (-7.0, place(P.pylon(0.0, 4.6), -9.0, -7.0, 1.7)),
        (-6.0, place(P.factory(), 4.0, -6.0, 1.5)),
        (-4.0, place(P.silo(), -3.5, -4.0, 1.25)),
        (-3.5, place(P.warehouse(), 9.0, -3.5, 1.35)),
        (-2.5, place(P.water_tower(), -13.0, -2.5, 1.1)),
        (-0.5, place(P.containers(), -8.0, -0.5, 1.15)),
        (1.5, place(P.rock(0, 1.1, 12), 8.6, 1.5)),
        (2.0, place(P.rock(0, 0.8, 34), -11.5, 2.0))],
    "funfair": lambda: [
        (-99, P.ground(hx=18, zf=3.5, zb=-14)),
        (-8.0, place(P.truss_bridge(), 6.0, -8.0, 1.6)),
        (-6.0, place(P.ferris_wheel(), -6.5, -6.0, 1.8)),
        (-4.5, place(P.wind_turbine(), 1.5, -4.5, 1.4)),
        (-3.0, place(P.lighthouse(), 10.0, -3.0, 1.2)),
        (-3.0, place(P.water_tower(), -12.0, -3.0, 1.05)),
        (0.0, P.tree_3(-2.5, 1.5)), (0.0, P.tree_2(7.5, 1.4)),
        (0.5, place(P.street_lamp(), -9.5, 0.5, 1.2)),
        (1.2, place(P.rock(0, 1.0, 47), 11.5, 1.2))],
}


def render(name, scene_fn):
    style = B.STYLES["inverted-soft-jitter"]
    P.setup_view(W, H, 0.58, 0, 20.0)
    scene = sorted(scene_fn(), key=lambda p: p[0])   # painter: far first
    out = os.path.join(OUT_DIR, f"walk_comp2_{name}.mp4")
    frames = int(DUR * FPS)
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-vcodec", "rawvideo",
         "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", out],
        stdin=subprocess.PIPE)

    for i in range(frames):
        t = i / (frames - 1)
        surf = pygame.Surface((W, H))
        surf.fill(style["bg"])
        P.stars(surf, hash("comp_2") % 1000, W)
        lrng = random.Random(12100 + i)
        # slow approach from the back toward the camera
        mx = MIKU_P0[0] + (MIKU_P1[0] - MIKU_P0[0]) * t
        mz = MIKU_P0[1] + (MIKU_P1[1] - MIKU_P0[1]) * t
        for zk, sh in scene:
            if zk <= mz:
                B.draw_shape(surf, sh, style, P.MODELS["materials"], lrng)
        feet = B.project(mx * B.M, 0, mz * B.M)
        head_ref = B.project(mx * B.M, -MIKU_WORLD_H * B.M, mz * B.M)
        mw = (feet[1] - head_ref[1]) / 1.9
        d = DS.D(surf, MIKU_V, seed=500 + i)
        phase = i / FPS * 1.7

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
                     leg_ang=(ang_l, ang_r))
        for zk, sh in scene:
            if zk > mz:
                B.draw_shape(surf, sh, style, P.MODELS["materials"], lrng)
        if i in (12, 48, 90):
            pygame.image.save(
                surf, os.path.join(CHECK_DIR, f"walk_comp2_{name}_f{i}.png"))
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
