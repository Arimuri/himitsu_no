#!/usr/bin/env python3
"""
Mock PV frames: the chosen background taste (bg_8 = "inverted" navy, seed 45)
composited with the simple Miku at 1280x720. Two character treatments:
  mock_1.png — Miku as scribble mix (teal/cream fills + white scribble lines)
  mock_2.png — Miku as pure white scribble linework
Output: ボカコレ2026S/movie/mock_frame_*.png
"""
import os
import json
import math
import random

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
HERE = os.path.dirname(os.path.abspath(__file__))
import sys
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "core"))
import pygame

import bg_sketch as B
import design_sketch as DS

OUT_DIR = "/Users/arimura/Dropbox/ボカコレ2026S/movie/current"
CHECK_DIR = os.path.join(OUT_DIR, "check")
os.makedirs(CHECK_DIR, exist_ok=True)
W, H = 1280, 720
SEED = 45

# (filename, background style, Miku variant) — scribble vs jitter comparison
MIKU_STYLES = [
    ("mock_frame_2.png", "inverted-soft",
     {"render": "line", "bg": "black", "mono": True, "line_col": DS.WHITE,
      "scribble": True, "roughness": 2.0, "lw": 2}),
    ("mock_frame_jitter.png", "inverted-soft-jitter",
     {"render": "line", "bg": "black", "mono": True, "line_col": DS.WHITE,
      "vibline": True, "lw": 2}),
    ("mock_frame_mix.png", "inverted-soft-jitter",
     {"render": "line", "bg": "black", "mono": True, "line_col": DS.WHITE,
      "scribble": True, "roughness": 2.0, "lw": 2}),
]


def main():
    pygame.init()
    pygame.display.set_mode((64, 64))

    with open(os.path.join(os.path.dirname(HERE), "core", "bg_models.json")) as f:
        models = json.load(f)

    # widescreen framing: house shifted left, Miku standing on the right
    B.VIEW_W, B.VIEW_H = W, H
    B.VIEW_ZOOM = 0.78
    B.VIEW_YOFF = 20.0
    B.VIEW_XOFF = -240.0

    for fname, style_name, miku_v in MIKU_STYLES:
        style = B.STYLES[style_name]
        surf = pygame.Surface((W, H))
        surf.fill(style["bg"])

        # a few white sparkle stars in the open sky areas
        srng = random.Random(SEED * 31 + 7)
        for _ in range(6):
            x = srng.choice([srng.randint(40, 300), srng.randint(980, 1240)])
            y = srng.randint(40, 260)
            r = srng.choice((4, 7, 10))
            pygame.draw.line(surf, (225, 230, 235), (x - r, y), (x + r, y), 2)
            pygame.draw.line(surf, (225, 230, 235), (x, y - r), (x, y + r), 2)

        rng = random.Random(SEED)
        arch = B.generate_arch(models, rng)
        for key in B.DRAW_ORDER:
            idx = arch.get(key, 1000)
            if idx < 1000:
                B.draw_shape(surf, models[key][idx], style,
                             models["materials"], rng)

        d = DS.D(surf, miku_v, seed=7)
        DS.draw_miku(d, W * 0.72, H * 0.40, 210)

        out = os.path.join(OUT_DIR, fname)
        pygame.image.save(surf, out)
        print(f"saved {out}")


if __name__ == "__main__":
    main()
