#!/usr/bin/env python3
"""「何回やったって」cut: two dice tossed into a donburi bowl — tumble in,
bounce, settle.  4 s, 12 fps, 16:9, static high-angle camera.
Output: movie/current/dice_bowl.mp4
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

PIPS = {1: [(0.0, 0.0)],
        2: [(-0.22, 0.22), (0.22, -0.22)],
        3: [(-0.24, -0.24), (0.0, 0.0), (0.24, 0.24)],
        4: [(-0.22, -0.22), (-0.22, 0.22), (0.22, -0.22), (0.22, 0.22)],
        5: [(-0.22, -0.22), (-0.22, 0.22), (0.22, -0.22), (0.22, 0.22),
            (0.0, 0.0)],
        6: [(-0.2, -0.24), (-0.2, 0.0), (-0.2, 0.24),
            (0.2, -0.24), (0.2, 0.0), (0.2, 0.24)]}
SIDES = [((0, 0, -1), (1, 0, 0), (0, 1, 0), 2, 4),
         ((1, 0, 0), (0, 0, 1), (0, 1, 0), 1, 5),
         ((0, 1, 0), (1, 0, 0), (0, 0, 1), 3, 6),
         ((-1, 0, 0), (0, 0, 1), (0, 1, 0), 1, 2),
         ((0, 0, 1), (1, 0, 0), (0, 1, 0), 2, 3),
         ((0, -1, 0), (1, 0, 0), (0, 0, 1), 3, 1)]

# per die: (enter, impact, settle, x path, entry y, rest pos, rest yaw)
DICE = [(0.30, 1.00, 1.45, 4.6, -4.2, (0.42, -0.62), 0.55),
        (0.55, 1.30, 1.75, 5.2, -4.6, (-0.38, -0.60), 1.25)]
E = 0.52                        # die edge length


def die_faces(cx, cy, cz, yaw, pitch):
    cyw, syw = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)

    def xf(x, y, z):
        x1, z1 = x * cyw - z * syw, x * syw + z * cyw
        y1, z2 = y * cp - z1 * sp, y * sp + z1 * cp
        return (cx + x1, cy + y1, cz + z2)

    h = E / 2
    faces = []
    for normal, bu, bv, mat, count in SIDES:
        corners = []
        for su, sv in ((-1, -1), (-1, 1), (1, 1), (1, -1)):
            lx = tuple(bu[j] * su * h + bv[j] * sv * h + normal[j] * h
                       for j in range(3))
            corners.append(xf(*lx))
        faces.append(P.q(mat, corners))
        r = 0.062 if count == 1 else 0.048
        for u, v in PIPS[count]:
            pts = []
            for k in range(8):
                a = math.pi * 2 * k / 8
                pu = u * E + r * math.cos(a)
                pv = v * E + r * math.sin(a)
                lx = tuple(bu[j] * pu + bv[j] * pv + normal[j] * (h + 0.008)
                           for j in range(3))
                pts.append(xf(*lx))
            faces.append(P.q(5, pts))
    faces.sort(key=lambda fc: sum(v[2] for v in fc["vertices"]) / len(
        fc["vertices"]))
    return faces


def bowl_halves():
    """Donburi as back and front halves so dice sit inside properly."""
    prof = [(0.55, 0.0), (0.62, -0.12), (1.28, -0.72), (1.5, -1.12)]
    n = 16
    back, front = [], []

    def ring(r, y):
        return [(r * math.cos(a), y, r * math.sin(a))
                for a in [math.pi * 2 * k / n for k in range(n)]]

    rim = ring(prof[3][0], prof[3][1])
    foot = ring(prof[0][0], prof[0][1])
    mid = ring(prof[2][0], prof[2][1])
    inner = ring(0.95, -0.55)
    for k in range(n):
        k2 = (k + 1) % n
        zmid = (rim[k][2] + rim[k2][2]) / 2
        quad_hi = P.q(2, [mid[k], mid[k2], rim[k2], rim[k]])
        quad_lo = P.q(1, [foot[k], foot[k2], mid[k2], mid[k]])
        (front if zmid > 0 else back).extend([quad_lo, quad_hi])
    back.append(P.q(3, inner))                    # bowl floor, seen from above
    return {"data": back}, {"data": front}


def sparks(cx, cy):
    f = []
    for deg in (140, 90, 40):
        a = math.radians(deg)
        f.append(P.seg((cx + 0.3 * math.cos(a), cy - 0.3 * math.sin(a), 0),
                       (cx + 0.5 * math.cos(a), cy - 0.5 * math.sin(a), 0)))
    return f


def ground_lines():
    return {"data": [P.seg((-45, 0, -32), (45, 0, -32)),
                     P.seg((-32, 0, -14), (32, 0, -14))]}


def shadow():
    return {"data": [P.q(0, [(1.75 * math.cos(a), -0.01,
                              0.2 + 0.62 * math.sin(a))
                             for a in [math.pi * 2 * k / 14 for k in range(14)]])]}


def main():
    pygame.init()
    pygame.display.set_mode((64, 64))
    with open(os.path.join(os.path.dirname(HERE), "core", "bg_models.json")) as f:
        P.MODELS = json.load(f)
    style = B.STYLES["inverted-soft-jitter"]
    P.setup_view(W, H, 2.0, 0.0, 55.0)
    B.EYE = (0.0, -230.0, 500.0)
    B.CENTER = (0.0, -60.0, 0.0)
    B.CAM_X, B.CAM_Y, B.CAM_Z = B._camera_basis()
    bowl_back, bowl_front = bowl_halves()

    out = os.path.join(OUT_DIR, "dice_bowl.mp4")
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
        P.stars(surf, hash("dicebowl") % 1000, W)
        lrng = random.Random(12900 + i)
        B.draw_shape(surf, ground_lines(), style, P.MODELS["materials"], lrng)
        B.draw_shape(surf, shadow(), style, P.MODELS["materials"], lrng)
        B.draw_shape(surf, bowl_back, style, P.MODELS["materials"], lrng)
        fx = []
        for t_in, t_hit, t_set, x0, y0, rest, ryaw in DICE:
            if t < t_in:
                continue
            rx, ry = rest
            if t < t_hit:                        # tumbling flight
                u = (t - t_in) / (t_hit - t_in)
                cx = x0 + (rx - x0) * u
                cy = y0 + (ry - y0) * (u ** 1.6)
                yaw = 4.5 * u + ryaw
                pitch = -3.2 * u - 0.35
            elif t < t_set:                      # small bounce inside
                u = (t - t_hit) / (t_set - t_hit)
                cx, cy = rx, ry - 0.38 * math.sin(math.pi * u)
                yaw = ryaw + 0.9 * (1 - u)
                pitch = -0.35
                if u < 0.25:
                    fx += sparks(rx, ry - 0.3)
            else:                                # settled
                cx, cy, yaw, pitch = rx, ry, ryaw, -0.35
            fx += die_faces(cx, cy, 0.0, yaw, pitch)
        if fx:
            B.draw_shape(surf, {"data": fx}, style, P.MODELS["materials"],
                         lrng)
        B.draw_shape(surf, bowl_front, style, P.MODELS["materials"], lrng)
        if i in (8, 13, 30):
            pygame.image.save(surf,
                              os.path.join(CHECK_DIR, f"dicebowl_f{i}.png"))
        ff.stdin.write(pygame.image.tostring(surf, "RGB"))

    ff.stdin.close()
    ff.wait()
    print(f"saved {out}")


if __name__ == "__main__":
    main()
