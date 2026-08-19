#!/usr/bin/env python3
"""
Solar system loop (16:9, 12fps, 8s perfect loop): sun with rays, six orbit
rings on a tilted plane, planets circling at integer rev counts (so the clip
loops seamlessly), Saturn ring, Earth's moon. PV style: navy + white jitter
lines, boiling every frame.

Output: movie/current/solar_spin.mp4
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
DUR = 8.0
CY = -2.45          # system plane height (world units)

# (orbit radius, planet radius, revolutions per loop, phase)
PLANETS = [
    (1.05, 0.10, 9, 0.3),
    (1.55, 0.16, 6, 2.1),
    (2.10, 0.17, 4, 4.4),    # earth (gets a moon)
    (2.65, 0.13, 3, 1.2),
    (3.45, 0.30, 2, 5.3),
    (4.30, 0.26, 1, 3.7),    # saturn (gets a ring)
]


def ring_poly(cx, cy, cz, r, n=28, squash=1.0):
    return P.q(0, [(cx + r * math.cos(a), cy, cz + r * squash * math.sin(a))
                   for a in [math.pi * 2 * k / n for k in range(n)]])


def ball(cx, cy, cz, r, mat=5):
    """Camera-facing disc (billboard) so planets stay round from any angle."""
    X, Y = B.CAM_X, B.CAM_Y
    pts = []
    for k in range(10):
        a = math.pi * 2 * k / 10
        ca, sa = math.cos(a), math.sin(a)
        pts.append((cx + r * (X[0] * ca + Y[0] * sa),
                    cy + r * (X[1] * ca + Y[1] * sa),
                    cz + r * (X[2] * ca + Y[2] * sa)))
    return P.q(mat, pts)


def build_frame(t):
    """t in [0,1) — one full loop."""
    f = []
    # sun: filled disc + rays
    f.append(ball(0, CY, 0, 0.42, mat=5))
    for k in range(8):
        a = math.pi * 2 * k / 8 + t * math.pi * 2 / 8   # rays creep slowly
        f.append(P.seg((0.58 * math.cos(a), CY, 0.58 * math.sin(a)),
                       (0.82 * math.cos(a), CY, 0.82 * math.sin(a))))
    for orad, prad, revs, ph in PLANETS:
        f.append(ring_poly(0, CY, 0, orad))
    for i, (orad, prad, revs, ph) in enumerate(PLANETS):
        a = ph + math.pi * 2 * revs * t
        px, pz = orad * math.cos(a), orad * math.sin(a)
        f.append(ball(px, CY, pz, prad))
        if i == 2:   # moon
            ma = math.pi * 2 * 24 * t
            f.append(ball(px + 0.3 * math.cos(ma), CY, pz + 0.3 * math.sin(ma),
                          0.05))
        if i == 5:   # saturn ring
            f.append(P.q(0, [(px + rr * math.cos(b), CY + 0.09 * math.sin(b),
                              pz + rr * 0.45 * math.sin(b))
                             for rr in (0.42,)
                             for b in [math.pi * 2 * k / 14 for k in range(14)]]))
    return f


def main():
    pygame.init()
    pygame.display.set_mode((64, 64))
    with open(os.path.join(os.path.dirname(HERE), "core", "bg_models.json")) as f:
        P.MODELS = json.load(f)
    style = B.STYLES["inverted-soft-jitter"]
    B.VIEW_W, B.VIEW_H = W, H
    B.VIEW_XOFF, B.VIEW_YOFF = 0.0, 30.0
    B.CENTER = (0.0, CY * B.M, 0.0)

    out = os.path.join(OUT_DIR, "solar_spin.mp4")
    frames = int(DUR * FPS)
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-vcodec", "rawvideo",
         "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", out],
        stdin=subprocess.PIPE)

    for i in range(frames):
        t = i / frames                      # [0,1) -> seamless loop
        # camera: one slow orbit per loop + gentle bob + zoom breathing
        a = math.pi * 2 * t
        # lateral drift: the aim point wanders sideways once per loop
        B.CENTER = (38.0 * math.sin(a + 1.0), CY * B.M, 0.0)
        ease = t * t * (3 - 2 * t)
        B.EYE = (500 * math.sin(a),
                 -70 - 230 * ease,          # one-way rise: edge-on -> overview
                 500 * math.cos(a))
        B.CAM_X, B.CAM_Y, B.CAM_Z = B._camera_basis()
        B.VIEW_ZOOM = 1.45 + 0.18 * math.sin(a)
        surf = pygame.Surface((W, H))
        surf.fill(style["bg"])
        P.stars(surf, 424, W)
        lrng = random.Random(9100 + i)
        B.draw_shape(surf, {"data": build_frame(t)}, style,
                     P.MODELS["materials"], lrng)
        if i == 30:
            pygame.image.save(surf, os.path.join(CHECK_DIR, "solar_spin_f30.png"))
        ff.stdin.write(pygame.image.tostring(surf, "RGB"))

    ff.stdin.close()
    ff.wait()
    print(f"saved {out}")


if __name__ == "__main__":
    main()
