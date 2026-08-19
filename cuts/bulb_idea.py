#!/usr/bin/env python3
"""「考えたほうがいい」cut: a 3D light bulb lying on the ground, its cable
snaking across the floor and out of frame.  Static scene, slow orbiting
camera.  4 s, 12 fps, 16:9.  Output: movie/current/bulb_idea.mp4
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

YAW = 2.90                      # bulb axis heading: glass left, screw right
AXH = -0.72                     # axis height: glass equator rests on the ground
GC_T = 1.45                     # axis station of the glass sphere centre
GR = 0.72                       # glass radius

AX = (math.cos(YAW), 0.0, math.sin(YAW))
SIDE = (-AX[2], 0.0, AX[0])
UP = (0.0, -1.0, 0.0)


def at(t, u, v):
    """Local bulb frame -> world: t along axis, u sideways, v up."""
    return (AX[0] * t + SIDE[0] * u + UP[0] * v,
            AXH * 0 + AX[1] * t + SIDE[1] * u + UP[1] * v,
            AX[2] * t + SIDE[2] * u + UP[2] * v)


def pt(t, u, v):
    x, y, z = at(t, u, v)
    return (x, y + AXH, z)


def ring(t, r, n=10, mat=0):
    return P.q(mat, [pt(t, r * math.cos(a), r * math.sin(a))
                     for a in [math.pi * 2 * k / n for k in range(n)]])


def bulb3d():
    f = []
    # screw base: lathe of quads (solid, occluding)
    stations = [(0.0, 0.16), (0.12, 0.3), (0.5, 0.3), (0.62, 0.34)]
    n = 8
    rings = []
    for t, r in stations:
        rings.append([pt(t, r * math.cos(a), r * math.sin(a))
                      for a in [math.pi * 2 * k / n for k in range(n)]])
    for a_ring, b_ring in zip(rings, rings[1:]):
        for k in range(n):
            f.append(P.q(3, [a_ring[k], a_ring[(k + 1) % n],
                             b_ring[(k + 1) % n], b_ring[k]]))
    # screw thread lines
    for t in (0.2, 0.34, 0.48):
        f.append(ring(t, 0.305, n=10))
    # glass: sparse lathe wireframe (transparent)
    f.append(ring(0.98, 0.55))            # shoulder
    f.append(ring(GC_T, GR, n=14))        # equator ring
    f.append(ring(1.95, 0.5))             # toward the nose
    # profile great circle in the vertical axis plane = bulb silhouette
    pts = []
    for j in range(16):
        a = math.pi * 2 * j / 16
        pts.append(pt(GC_T + GR * math.cos(a), 0, GR * math.sin(a)))
    f.append(P.q(0, pts))
    # neck taper from screw to shoulder
    for a in [math.pi * 2 * k / 4 for k in range(4)]:
        f.append(P.seg(pt(0.62, 0.34 * math.cos(a), 0.34 * math.sin(a)),
                       pt(0.98, 0.55 * math.cos(a), 0.55 * math.sin(a))))
    # filament: two supports + zigzag, standing in the vertical axis plane
    f += P.chain([pt(0.75, 0.0, 0.12), pt(1.15, 0.0, 0.3),
                  pt(1.3, 0.0, 0.05), pt(1.45, 0.0, 0.38),
                  pt(1.6, 0.0, 0.05), pt(1.75, 0.0, 0.3)])
    return {"data": f}


def cable():
    """Messy cable: droops from the screw tip, then meanders and coils
    (real 360-degree loops) across the floor before exiting frame right."""
    tip = pt(-0.02, 0, 0)
    f = P.chain([tip, (tip[0] + 0.22, tip[1] + 0.3, tip[2] + 0.06),
                 (tip[0] + 0.5, -0.03, tip[2] + 0.12)])
    # turtle walk: (arc length, curvature); big curvature spans = coils
    plan = [(0.6, 0.5), (1.30, 5.0), (1.2, 1.6), (3.0, -0.35),
            (1.5, -4.4), (1.6, -1.5), (1.2, 0.9), (1.05, 5.9),
            (1.2, -0.9)]
    x, z = tip[0] + 0.5, tip[2] + 0.12
    hd = 0.15
    pts = [(x, -0.03, z)]
    for seg_len, curv in plan:
        n = max(2, int(seg_len / 0.08))
        ds = seg_len / n
        for _ in range(n):
            hd += (curv + 1.3 * math.sin(len(pts) * 0.55)) * ds
            x += math.cos(hd) * ds
            z += math.sin(hd) * ds
            pts.append((x, -0.03, z))
    # run the tail far out of frame (heading relaxes toward the right exit,
    # gentle waves only) so the cable end is never visible at any orbit angle
    for _ in range(int(14.0 / 0.08)):
        hd += (0.30 - hd) * 0.10 + 0.05 * math.sin(len(pts) * 0.3)
        x += math.cos(hd) * 0.08
        z += math.sin(hd) * 0.08
        pts.append((x, -0.03, z))
    f += P.chain(pts)
    return {"data": f}


def shadows():
    """One soft contact ellipse under the whole bulb."""
    c = pt(1.05, 0, 0)
    return {"data": [P.q(0, [(c[0] + 1.35 * math.cos(a), -0.01,
                              c[2] + 0.12 + 0.44 * math.sin(a))
                             for a in [math.pi * 2 * k / 14 for k in range(14)]])]}


def ground_lines():
    """Horizon + mid-ground wobble lines (a full quad would clip the camera)."""
    return {"data": [P.seg((-45, 0, -40), (45, 0, -40)),
                     P.seg((-32, 0, -18), (32, 0, -18))]}


def glow():
    """Steady soft glow: billboard disc + short ray fan (upper half only)."""
    c = pt(GC_T, 0, 0)
    X, Y = B.CAM_X, B.CAM_Y
    f = []
    disc = []
    for k in range(12):
        a = math.pi * 2 * k / 12
        ca, sa = math.cos(a), math.sin(a)
        disc.append((c[0] + 0.5 * (X[0] * ca + Y[0] * sa),
                     c[1] + 0.5 * (X[1] * ca + Y[1] * sa),
                     c[2] + 0.5 * (X[2] * ca + Y[2] * sa)))
    f.append(P.q(5, disc))
    for deg in (200, 245, 290, 335, 20):
        a = math.radians(deg)
        ca, sa = math.cos(a), math.sin(a)
        for r0, r1 in ((0.95, 1.22),):
            f.append(P.seg(
                (c[0] + r0 * (X[0] * ca + Y[0] * sa),
                 c[1] + r0 * (X[1] * ca + Y[1] * sa),
                 c[2] + r0 * (X[2] * ca + Y[2] * sa)),
                (c[0] + r1 * (X[0] * ca + Y[0] * sa),
                 c[1] + r1 * (X[1] * ca + Y[1] * sa),
                 c[2] + r1 * (X[2] * ca + Y[2] * sa))))
    return {"data": f}


def main():
    pygame.init()
    pygame.display.set_mode((64, 64))
    with open(os.path.join(os.path.dirname(HERE), "core", "bg_models.json")) as f:
        P.MODELS = json.load(f)
    style = B.STYLES["inverted-soft-jitter"]
    P.setup_view(W, H, 2.1, 0.0, 80.0)
    gc = pt(GC_T, 0, 0)
    scene = [ground_lines(), shadows(), cable(), bulb3d()]

    out = os.path.join(OUT_DIR, "bulb_idea.mp4")
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
        th = 0.35 - 0.5 * e           # slow orbit, staying side-on to the bulb
        R, hgt = 6.6, -4.8            # pulled back, high angle looking down
        B.EYE = ((gc[0] + R * math.sin(th)) * B.M, hgt * B.M,
                 (gc[2] + R * math.cos(th)) * B.M)
        B.CENTER = (gc[0] * B.M, (AXH - 0.1) * B.M, gc[2] * B.M)
        B.CAM_X, B.CAM_Y, B.CAM_Z = B._camera_basis()
        surf = pygame.Surface((W, H))
        surf.fill(style["bg"])
        P.stars(surf, hash("bulb") % 1000, W)
        lrng = random.Random(9900 + i)
        for sh in scene:
            B.draw_shape(surf, sh, style, P.MODELS["materials"], lrng)
        B.draw_shape(surf, glow(), style, P.MODELS["materials"], lrng)
        if i in (0, 24, 47):
            pygame.image.save(surf, os.path.join(CHECK_DIR, f"bulb_f{i}.png"))
        ff.stdin.write(pygame.image.tostring(surf, "RGB"))

    ff.stdin.close()
    ff.wait()
    print(f"saved {out}")


if __name__ == "__main__":
    main()
