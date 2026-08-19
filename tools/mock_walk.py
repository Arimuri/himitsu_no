#!/usr/bin/env python3
"""
2-second motion mocks (16:9, 12fps): pyoko-pyoko walking Miku + orbiting
background camera, in the confirmed "mix" style (jitter background lines,
scribble Miku, bright navy). Several named shot variants; comparison files
are never overwritten — each variant gets its own output name.

Usage:  mock_walk.py [names...]   (default: all variants)

Credits: p5.scribble.js / Handy library (LGPL); BMWalker.js port available
but unused in the cheap walk.
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
from scribble import jitter_line

OUT_DIR = "/Users/arimura/Dropbox/ボカコレ2026S/movie/current"
CHECK_DIR = os.path.join(OUT_DIR, "check")
os.makedirs(CHECK_DIR, exist_ok=True)
W, H = 1280, 720
FPS = 12          # chunky stop-motion feel, like the source sketches
DUR = 2.0
SEED = 45

SCRIBBLE_V = {"render": "line", "bg": "black", "mono": True,
              "line_col": DS.WHITE, "scribble": True, "roughness": 2.0, "lw": 2}
VIBLINE_V = {"render": "line", "bg": "black", "mono": True,
             "line_col": DS.WHITE, "vibline": True, "lw": 2}

# name -> config. cam=(zoom0, zoom1, xoff); miku=(W, x0, x1, head_y)
WALK_VARIANTS = {
    "scribble": {"style": "inverted-soft", "miku_v": SCRIBBLE_V,
                 "scene": "house", "cam": (0.78, 0.84, -240),
                 "miku": (210, 0.60, 0.70, 0.40)},
    "jitter": {"style": "inverted-soft-jitter", "miku_v": VIBLINE_V,
               "scene": "house", "cam": (0.78, 0.84, -240),
               "miku": (210, 0.60, 0.70, 0.40)},
    "mix": {"style": "inverted-soft-jitter", "miku_v": SCRIBBLE_V,
            "scene": "house", "cam": (0.78, 0.84, -240),
            "miku": (210, 0.60, 0.70, 0.40)},
    # wide shot: small Miku walking past the original village (comp_2 layout)
    "far": {"style": "inverted-soft-jitter", "miku_v": SCRIBBLE_V,
            "scene": lambda: [P.ground(), P.building_5(1.6),
                              P.tree_2(-2.8, 1.5), P.tree_3(4.6, 1.5)],
            "cam": (0.56, 0.60, 0),
            "miku": (130, 0.24, 0.34, 0.47)},
}


def render_walk(models, name, cfg):
    style = B.STYLES[cfg["style"]]
    zoom0, zoom1, xoff = cfg["cam"]
    mw, mx0, mx1, my = cfg["miku"]
    arch = B.generate_arch(models, random.Random(SEED)) \
        if cfg["scene"] == "house" else None
    B.VIEW_W, B.VIEW_H = W, H
    B.VIEW_XOFF = float(xoff)
    B.VIEW_YOFF = 20.0

    out = os.path.join(OUT_DIR, f"mock_walk_{name}.mp4")
    frames = int(DUR * FPS)
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-vcodec", "rawvideo",
         "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", out],
        stdin=subprocess.PIPE)

    for i in range(frames):
        t = i / (frames - 1)
        tms = i / FPS * 1000.0
        boil = i

        # orbiting, slowly dollying camera
        a = math.radians(-12 + 24 * t)
        B.EYE = (B.CENTER[0] + 500 * math.sin(a), -50.0,
                 B.CENTER[2] + 500 * math.cos(a))
        B.CAM_X, B.CAM_Y, B.CAM_Z = B._camera_basis()
        B.VIEW_ZOOM = zoom0 + (zoom1 - zoom0) * t

        surf = pygame.Surface((W, H))
        surf.fill(style["bg"])

        P.stars(surf, SEED * 31 + 7, W)

        lrng = random.Random(7000 + boil)
        if arch is not None:
            for key in B.DRAW_ORDER:
                idx = arch.get(key, 1000)
                if idx < 1000:
                    B.draw_shape(surf, models[key][idx], style,
                                 models["materials"], lrng)
        else:
            for sh in cfg["scene"]():
                B.draw_shape(surf, sh, style, models["materials"], lrng)

        # Miku: pyoko-pyoko walk, quantized to held poses
        d = DS.D(surf, cfg["miku_v"], seed=500 + boil)
        ax = W * (mx0 + (mx1 - mx0) * t)
        phase = tms / 1000.0 * 2.5

        def q(v):
            return round(v * 2) / 2
        s = phase % 2.0
        hop = q(abs(math.sin(math.pi * phase))) * mw * 0.03
        swing = 0.24
        ang_l = q(math.sin(math.pi * s)) * swing if s < 1.0 else 0.0
        ang_r = q(math.sin(math.pi * (s - 1.0))) * swing if s >= 1.0 else 0.0
        sw = q(math.sin(math.pi * phase)) * 0.03
        sw2 = q(math.sin(math.pi * (phase - 0.45))) * 0.07
        DS.draw_miku(d, ax, H * my - hop, mw,
                     tail_swing=(sw, -sw), tail_swing2=(sw2, -sw2),
                     leg_ang=(ang_l, ang_r))

        if i == 12:
            pygame.image.save(surf,
                              os.path.join(CHECK_DIR, f"mock_walk_{name}_f12.png"))
        ff.stdin.write(pygame.image.tostring(surf, "RGB"))

    ff.stdin.close()
    ff.wait()
    print(f"saved {out}")


def main():
    pygame.init()
    pygame.display.set_mode((64, 64))
    with open(os.path.join(os.path.dirname(HERE), "core", "bg_models.json")) as f:
        models = json.load(f)
    names = sys.argv[1:] or ["mix", "far"]
    for name in names:
        render_walk(models, name, WALK_VARIANTS[name])


if __name__ == "__main__":
    main()
