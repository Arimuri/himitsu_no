#!/usr/bin/env python3
"""「やるせ無い人間の輝き」cut: three street lamps blinking in a slow wave,
Miku standing small at bottom right.  4 s, 12 fps, 16:9 (loopable).
Output: movie/current/lamp_glow.mp4
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

LAMP_XS = (-5.5, 0.0, 5.5)
MIKU_POS = (5.6, -2.6)           # just left of the rightmost lamp, further back
MIKU_WORLD_H = 2.3
GLOW_COL = (88, 134, 163)        # lit pool / bulb, clearly above bg

MIKU_V = {"render": "line", "bg": "black", "mono": True, "line_col": DS.WHITE,
          "scribble": True, "roughness": 2.0, "lw": 2}


def pool_poly(ox, flip=1):
    hx = ox + 0.5 * flip
    return [(hx + 0.6 * math.cos(a), 0, 0.5 + 0.35 * math.sin(a))
            for a in [math.pi * 2 * k / 10 for k in range(10)]]


def ray_faces(ox, flip=1):
    """Downward ray fan under the lamp head."""
    hx = ox + 0.5 * flip
    f = []
    for deg in (235, 270, 305):
        a = math.radians(deg)
        f.append(P.seg((hx + 0.4 * math.cos(a), -1.95 - 0.4 * math.sin(a), 0),
                       (hx + 0.75 * math.cos(a), -1.95 - 0.75 * math.sin(a), 0)))
    return f


def main():
    pygame.init()
    pygame.display.set_mode((64, 64))
    with open(os.path.join(os.path.dirname(HERE), "core", "bg_models.json")) as f:
        P.MODELS = json.load(f)
    style = B.STYLES["inverted-soft-jitter"]
    # slightly high, pulled-back camera; ground line lands just under the
    # rail height of the train cut (lyric-safe sky)
    P.setup_view(W, H, 1.12, 0.0, -21.0)
    B.EYE = (0.0, -100.0, 500.0)
    B.CAM_X, B.CAM_Y, B.CAM_Z = B._camera_basis()

    base = [P.ground()]
    for x in LAMP_XS:
        base.append(P.street_lamp(x))

    out = os.path.join(OUT_DIR, "lamp_glow.mp4")
    frames = int(DUR * FPS)
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-vcodec", "rawvideo",
         "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", out],
        stdin=subprocess.PIPE)

    for i in range(frames):
        surf = pygame.Surface((W, H))
        surf.fill(style["bg"])
        P.stars(surf, hash("lamps") % 1000, W)
        lrng = random.Random(10100 + i)
        # slow rolling blink: 2 s period, each lamp 1/3 cycle behind
        on = [((i + j * 8) // 12) % 2 == 0 for j in range(len(LAMP_XS))]
        for sh in base[:1]:
            B.draw_shape(surf, sh, style, P.MODELS["materials"], lrng)
        # lit extras under the outlines: bright pool fill + bulb dot
        for j, x in enumerate(LAMP_XS):
            if not on[j]:
                continue
            pts = [B.project(px * B.M, py * B.M, pz * B.M)
                   for px, py, pz in pool_poly(x)]
            pygame.draw.polygon(surf, GLOW_COL,
                                [(int(px), int(py)) for px, py in pts])
            hp = B.project((x + 0.5) * B.M, -1.86 * B.M, 0)
            pygame.draw.circle(surf, GLOW_COL, (int(hp[0]), int(hp[1])), 8)
        for sh in base[1:]:
            B.draw_shape(surf, sh, style, P.MODELS["materials"], lrng)
        lit = {"data": []}
        for j, x in enumerate(LAMP_XS):
            if on[j]:
                lit["data"] += ray_faces(x)
        if lit["data"]:
            B.draw_shape(surf, lit, style, P.MODELS["materials"], lrng)
        mx, mz = MIKU_POS
        feet = B.project(mx * B.M, 0, mz * B.M)
        head_ref = B.project(mx * B.M, -MIKU_WORLD_H * B.M, mz * B.M)
        if feet and head_ref:
            mw = (feet[1] - head_ref[1]) / 1.9
            d = DS.D(surf, MIKU_V, seed=800 + i)
            ts = i / FPS
            sw = round(math.sin(math.pi * 2 * ts / 3.2) * 2) / 2 * 0.03
            DS.draw_miku(d, feet[0], feet[1] - 1.53 * mw, mw,
                         tail_swing=(sw, -sw), tail_swing2=(-sw, sw))
        if i in (0, 6, 12):
            pygame.image.save(surf, os.path.join(CHECK_DIR, f"lamp_glow_f{i}.png"))
        ff.stdin.write(pygame.image.tostring(surf, "RGB"))

    ff.stdin.close()
    ff.wait()
    print(f"saved {out}")


if __name__ == "__main__":
    main()
