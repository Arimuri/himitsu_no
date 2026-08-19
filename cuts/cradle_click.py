#!/usr/bin/env python3
"""「何回やったって」cut: five-ball Newton's cradle clicking left-right,
quantized pendulum poses, impact sparks, gentle camera drift.
4 s, 12 fps, 16:9 (loopable).  Output: movie/current/cradle_click.mp4
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
CYCLE = 16                      # frames per full left-right period
AMAX = 0.55                     # swing amplitude (rad)
YAW = 0.32                      # whole cradle turned for depth


def yaw_shape(shape, ang):
    ca, sa = math.cos(ang), math.sin(ang)
    for f in shape["data"]:
        for v in f["vertices"]:
            x, z = v[0], v[2]
            v[0] = x * ca + z * sa
            v[2] = -x * sa + z * ca
    return shape


def sparks(side):
    """Impact ticks at the contact point on the given side."""
    cx = -0.81 if side == "left" else 0.81
    f = []
    for deg in (150, 105, 60, 15):
        a = math.radians(deg)
        sgn = -1 if side == "left" else 1
        f.append(P.seg((cx + sgn * 0.32 * math.cos(a), -0.95 - 0.32 * math.sin(a), 0),
                       (cx + sgn * 0.62 * math.cos(a), -0.95 - 0.62 * math.sin(a), 0)))
    return f


def ground_lines():
    return {"data": [P.seg((-45, 0, -32), (45, 0, -32)),
                     P.seg((-32, 0, -14), (32, 0, -14))]}


def shadow():
    return {"data": [P.q(0, [(2.1 * math.cos(a), -0.01, 0.15 + 0.5 * math.sin(a))
                             for a in [math.pi * 2 * k / 14 for k in range(14)]])]}


def main():
    pygame.init()
    pygame.display.set_mode((64, 64))
    with open(os.path.join(os.path.dirname(HERE), "core", "bg_models.json")) as f:
        P.MODELS = json.load(f)
    style = B.STYLES["inverted-soft-jitter"]
    P.setup_view(W, H, 2.3, 0.0, 70.0)

    out = os.path.join(OUT_DIR, "cradle_click.mp4")
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
        th = 0.22 - 0.3 * e           # slow drift around the cradle
        R = 7.2
        B.EYE = (R * math.sin(th) * B.M, -2.6 * B.M, R * math.cos(th) * B.M)
        B.CENTER = (0.0, -1.5 * B.M, 0.0)
        B.CAM_X, B.CAM_Y, B.CAM_Z = B._camera_basis()

        # quantized pendulum: left out while s>0, right while s<0
        s = math.sin(math.pi * 2 * (i % CYCLE) / CYCLE)
        qs = round(s * 3) / 3
        a_l = AMAX * qs if qs > 0 else 0.0
        a_r = AMAX * -qs if qs < 0 else 0.0
        shape = yaw_shape(P.newton_cradle(0.0, a_l, a_r), YAW)
        extra = []
        if i % CYCLE == 0:
            extra = sparks("right")   # right ball just landed
        elif i % CYCLE == CYCLE // 2:
            extra = sparks("left")    # left ball just landed
        if extra:
            shape["data"] += [{"mat": f2.get("mat"),
                               "vertices": f2["vertices"]}
                              for f2 in yaw_shape({"data": extra}, YAW)["data"]]

        surf = pygame.Surface((W, H))
        surf.fill(style["bg"])
        P.stars(surf, hash("cradle") % 1000, W)
        lrng = random.Random(11500 + i)
        for sh in (shadow(), shape):
            B.draw_shape(surf, sh, style, P.MODELS["materials"], lrng)
        if i in (4, 8, 16):
            pygame.image.save(surf, os.path.join(CHECK_DIR, f"cradle_f{i}.png"))
        ff.stdin.write(pygame.image.tostring(surf, "RGB"))

    ff.stdin.close()
    ff.wait()
    print(f"saved {out}")


if __name__ == "__main__":
    main()
