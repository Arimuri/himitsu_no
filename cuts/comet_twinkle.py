#!/usr/bin/env python3
"""Shooting-star cut: comets actually streak across the sky, one after
another, trails crossing; twinkling heads and ambient sparks.
4 s, 12 fps, 16:9 (loopable).  Output: movie/current/comet_twinkle.mp4
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

OUT_DIR = "/Users/arimura/Dropbox/ボカコレ2026S/movie/current"
CHECK_DIR = os.path.join(OUT_DIR, "check")
os.makedirs(CHECK_DIR, exist_ok=True)
W, H = 1280, 720
FPS = 12
DUR = 4.0

# (t0, t1, p0, p1, curve, size) — each streak runs off-frame to off-frame
STREAKS = [
    (0.35, 1.55, (10.5, -6.8), (-10.5, -1.6), 0.6, 1.0),
    (1.75, 2.95, (-10.5, -6.2), (10.5, -1.0), 0.5, 1.0),
]


def path(p0, p1, curve, s):
    return (p0[0] + (p1[0] - p0[0]) * s,
            p0[1] + (p1[1] - p0[1]) * s + curve * math.sin(math.pi * s), 0)


def head(f, hx, hy, size, k):
    r = (0.13 + 0.025 * k) * size
    f.append(P.q(5, [(hx + r * math.cos(a), hy + r * math.sin(a), 0)
                     for a in [math.pi * 2 * j / 8 for j in range(8)]]))
    tr = (0.26 + 0.07 * k) * size
    for dx, dy in ((tr, 0), (0, tr)):
        f.append(P.seg((hx - dx, hy - dy, 0), (hx + dx, hy + dy, 0)))


def main():
    pygame.init()
    pygame.display.set_mode((64, 64))
    with open(os.path.join(os.path.dirname(HERE), "core", "bg_models.json")) as f:
        P.MODELS = json.load(f)
    style = B.STYLES["inverted-soft-jitter"]
    P.setup_view(W, H, 1.5, 0.0, 105.0)

    out = os.path.join(OUT_DIR, "comet_twinkle.mp4")
    frames = int(DUR * FPS)
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-vcodec", "rawvideo",
         "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", out],
        stdin=subprocess.PIPE)

    for i in range(frames):
        t = i / FPS
        surf = pygame.Surface((W, H))
        surf.fill(style["bg"])
        P.stars(surf, hash("comets") % 1000, W)
        lrng = random.Random(12300 + i)
        f = []
        for t0, t1, p0, p1, curve, size in STREAKS:
            s = (t - t0) / (t1 - t0)
            if not -0.1 <= s <= 1.15:
                continue
            hx, hy, _ = path(p0, p1, curve, s)
            # solid tail right behind the head, then trailing dashes
            s_tail = s - 0.045 * size
            f.append(P.seg(path(p0, p1, curve, s_tail), (hx, hy, 0)))
            for k in range(5):
                sk = s - 0.085 - k * 0.075
                if sk < -0.05:
                    break
                f.append(P.seg(path(p0, p1, curve, sk),
                               path(p0, p1, curve, sk + 0.038)))
            head(f, hx, hy, size, (i // 2) % 2)
        # ambient twinkles on a fixed schedule
        for k, (sx, sy, ph) in enumerate([(-4.8, -6.5, 0), (5.1, -6.0, 4),
                                          (0.6, -2.3, 8), (-3.6, -2.9, 14),
                                          (4.5, -3.3, 19), (-6.6, -4.4, 10)]):
            if ((i + ph) // 4) % 3 == 0:
                r = 0.14
                f.append(P.seg((sx - r, sy, 0), (sx + r, sy, 0)))
                f.append(P.seg((sx, sy - r, 0), (sx, sy + r, 0)))
        B.draw_shape(surf, {"data": f}, style, P.MODELS["materials"], lrng)
        if i in (10, 27, 40):
            pygame.image.save(surf,
                              os.path.join(CHECK_DIR, f"comet_f{i}.png"))
        ff.stdin.write(pygame.image.tostring(surf, "RGB"))

    ff.stdin.close()
    ff.wait()
    print(f"saved {out}")


if __name__ == "__main__":
    main()
