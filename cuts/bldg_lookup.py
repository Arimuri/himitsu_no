#!/usr/bin/env python3
"""「遠いとこまで行きたいなら」cut: from the ground line, gazing up at a
cluster of buildings, then a long tilt up into the night sky, ending on a
cratered moon with a slow push-in.
9 s, 12 fps, 16:9.  Output: movie/current/bldg_lookup.mp4
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
DUR = 9.0

# tilt stops short of vertical: fully overhead, the tower's converging
# lines ran straight into the moon
C0, C1 = (0.0, -170.0, 0.0), (0.0, -1250.0, 0.0)
T_HOLD, T_PAN = 1.2, 4.2        # then ~3.6 s resting on the moon


def place(shape, x, z, sc=1.0):
    for face in shape["data"]:
        for v in face["vertices"]:
            v[0] = v[0] * sc + x
            v[1] = v[1] * sc
            v[2] = v[2] * sc + z
    return shape


MOON = (-1.6, -17.0, 5.6, 2.2)   # (x, y, z, r) near the end-framing axis


def roof_first(shape, n):
    """Move the last n faces (roof furniture) to the front of the paint
    order: authored order assumes a from-above camera, so seen from the
    street the furniture would otherwise paint over the walls/eaves that
    should hide it.  Everything else keeps the authored order."""
    shape["data"] = shape["data"][-n:] + shape["data"][:-n]
    return shape


def build_scene():
    s = [P.ground(hx=20, zf=3.5, zb=-24)]
    # back row first (painter order), then closer — tight and tall so the
    # opening reads as gazing up from the street
    s.append(place(P.warehouse(), -12.5, -12.0, 3.0))
    s.append(place(P.pylon(0.0, 4.6), 12.0, -13.0, 3.0))
    s.append(place(P.factory(), 9.5, -10.0, 3.0))
    s.append(place(P.silo(), -8.5, -8.0, 2.8))
    tower = P.office()
    tower["data"] = tower["data"][:-2]     # drop the roof antenna: at x5 it
    s.append(place(roof_first(tower, 5),   # stabbed the moon in the end frame
                   1.0, -7.5, 5.0))        # (5 = roof plant box)
    s.append(place(roof_first(P.danchi(), 7), 5.2, -6.5, 2.6))   # tank+ant.
    s.append(place(roof_first(P.office(), 7), -4.5, -5.5, 3.2))  # box+ant.
    s.append(place(P.containers(), -1.2, -2.8, 1.4))
    return s


def moon_face():
    """Camera-facing plain disc so the moon stays round through the tilt."""
    mx, my, mz, r = MOON
    X, Y = B.CAM_X, B.CAM_Y
    pts = []
    for k in range(16):
        a = math.pi * 2 * k / 16
        u, v = math.cos(a), math.sin(a)
        pts.append((mx + r * (X[0] * u + Y[0] * v),
                    my + r * (X[1] * u + Y[1] * v),
                    mz + r * (X[2] * u + Y[2] * v)))
    return {"data": [P.q(5, pts)]}


def main():
    pygame.init()
    pygame.display.set_mode((64, 64))
    with open(os.path.join(os.path.dirname(HERE), "core", "bg_models.json")) as f:
        P.MODELS = json.load(f)
    style = B.STYLES["inverted-soft-jitter"]
    P.setup_view(W, H, 0.85, 0.0, 40.0)
    scene = build_scene()

    out = os.path.join(OUT_DIR, "bldg_lookup.mp4")
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
        # once the tilt lands, push in slowly on the moon
        zt = max(0.0, min(1.0, (t - T_HOLD - T_PAN) / 3.4))
        B.VIEW_ZOOM = 0.85 + 0.38 * zt * zt * (3 - 2 * zt)
        surf = pygame.Surface((W, H))
        surf.fill(style["bg"])
        P.stars(surf, hash("lookup") % 1000, W)
        lrng = random.Random(10300 + i)
        for sh in scene:
            B.draw_shape(surf, sh, style, P.MODELS["materials"], lrng)
        B.draw_shape(surf, moon_face(), style, P.MODELS["materials"], lrng)
        if i in (0, 45, 70, 107):
            pygame.image.save(surf, os.path.join(CHECK_DIR, f"bldg_lookup_f{i}.png"))
        ff.stdin.write(pygame.image.tostring(surf, "RGB"))

    ff.stdin.close()
    ff.wait()
    print(f"saved {out}")


if __name__ == "__main__":
    main()
