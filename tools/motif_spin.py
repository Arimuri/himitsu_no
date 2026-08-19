#!/usr/bin/env python3
"""
Motif showcase videos: each motif pinned to the screen center, rotating.
Two takes (both 12fps, 1280x720, mix-style navy + jitter lines):
  motif_spin_roll.mp4 — in-plane spin (Vib-Ribbon obstacle style)
  motif_spin_yaw.mp4  — turntable around the vertical axis (wireframe showcase;
                        flat props collapse to a line edge-on, which is the fun)
12 motifs x 2 s each.
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
from scribble import jitter_line

OUT_DIR = "/Users/arimura/Dropbox/ボカコレ2026S/movie/current"
CHECK_DIR = os.path.join(OUT_DIR, "check")
os.makedirs(CHECK_DIR, exist_ok=True)
W, H = 1280, 720
FPS = 12
SEG_SEC = 2.0
MOTIF_SEC = 0.857   # per-motif cut length (2 beats @ 140 BPM)
REV_SEC = 4.0       # turntable speed: one revolution per 4 s
CX, CY = W / 2, H / 2

SPIN = [
    ("pylon", lambda: P.pylon()),
    ("bridge", lambda: P.truss_bridge()),
    ("crane", lambda: P.crane()),
    ("ferris", lambda: P.ferris_wheel()),
    ("turbine", lambda: P.wind_turbine()),
    ("train", lambda: P.train()),
    ("crossing", lambda: P.crossing()),
    ("stars", lambda: P.constellation(0, -3.6, 1.2)),
    ("watertower", lambda: P.water_tower()),
    ("lighthouse", lambda: P.lighthouse()),
    ("lamps", lambda: P.lamp_row((-2.2, 0.0, 2.2))),
    ("drafting", lambda: P.drafting()),
]


def yaw_shape(shape, cx, cz, ang):
    ca, sa = math.cos(ang), math.sin(ang)
    out = []
    for face in shape["data"]:
        vs = []
        for x, y, z in face["vertices"]:
            dx, dz = x - cx, z - cz
            vs.append([cx + dx * ca + dz * sa, y, cz - dx * sa + dz * ca])
        out.append({"mat": face.get("mat"), "vertices": vs})
    return {"data": out}


def project_faces(shape):
    polys = []
    for face in shape["data"]:
        pts = []
        ok = True
        for v in face["vertices"]:
            p = B.project(v[0] * B.M, v[1] * B.M, v[2] * B.M)
            if p is None:
                ok = False
                break
            pts.append(p)
        polys.append((face.get("mat"), pts if ok and len(pts) >= 2 else None))
    return polys


def draw_polys(surf, polys, style, rng, xform):
    blend = style.get("fill_blend", 0.0)
    mats = P.MODELS["materials"][style["fill_mode"]]
    for mat, pts in polys:
        if pts is None or len(pts) < 3 or not mat:
            continue
        col = mats[mat]
        if col[3] <= 0:
            continue
        c = tuple(int(col[k] + (style["bg"][k] - col[k]) * blend)
                  for k in range(3))
        pygame.draw.polygon(surf, c,
                            [(int(x), int(y)) for x, y in map(xform, pts)])
    for mat, pts in polys:
        if pts is None:
            continue
        tp = [xform(p) for p in pts]
        closed = tp + [tp[0]]
        for i in range(len(closed) - 1):
            jitter_line(surf, style["line"], style["lw"],
                        closed[i][0], closed[i][1],
                        closed[i + 1][0], closed[i + 1][1], rng)


def bbox_center_scale(polys):
    xs, ys = [], []
    for _, pts in polys:
        if pts:
            xs += [p[0] for p in pts]
            ys += [p[1] for p in pts]
    bx, by = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    r = max(math.hypot(x - bx, y - by) for x, y in zip(xs, ys))
    s = min(1.6, (0.40 * min(W, H)) / max(r, 1.0))
    return bx, by, s


def render(mode):
    style = B.STYLES["inverted-soft-jitter"]
    out = os.path.join(OUT_DIR, f"motif_spin_{mode}.mp4")
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-vcodec", "rawvideo",
         "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", out],
        stdin=subprocess.PIPE)
    font = pygame.font.Font(os.path.join(HERE, "font.ttf"), 26)

    # precompute per-motif geometry
    P.setup_view(W, H, 1.0, 0.0, 0.0)
    pre = []
    for name, build in SPIN:
        shape = build()
        xs = [v[0] for f in shape["data"] for v in f["vertices"]]
        zs = [v[2] for f in shape["data"] for v in f["vertices"]]
        wcx, wcz = (min(xs) + max(xs)) / 2, (min(zs) + max(zs)) / 2
        base = project_faces(shape)
        bx, by, s = bbox_center_scale(base)
        pre.append((name, shape, wcx, wcz, base, bx, by, s))

    def blank(mi):
        surf = pygame.Surface((W, H))
        surf.fill(style["bg"])
        srng = random.Random(31 * mi + 7)
        for _ in range(6):
            x = srng.choice([srng.randint(40, 300), srng.randint(980, 1240)])
            y = srng.randint(40, 640)
            rr = srng.choice((4, 7, 10))
            jitter_line(surf, (245, 245, 245), 2, x - rr, y, x + rr, y,
                        random.Random())
            jitter_line(surf, (245, 245, 245), 2, x, y - rr, x, y + rr,
                        random.Random())
        return surf

    if mode == "yaw":
        # beat-cut montage: motif switches every MOTIF_SEC (time-exact, so
        # 10/11-frame segments alternate), rotation phase runs continuously
        frames = int(round(MOTIF_SEC * len(SPIN) * FPS))
        for fi in range(frames):
            t = fi / FPS
            mi = min(int(t / MOTIF_SEC), len(SPIN) - 1)
            name, shape, wcx, wcz, base, bx, by, s = pre[mi]
            ang = math.pi * 2 * t / REV_SEC
            rng = random.Random(5000 + fi)
            surf = blank(mi)
            polys = project_faces(yaw_shape(shape, wcx, wcz, ang))
            bx2, by2, s2 = bbox_center_scale(polys)

            def xform(p, bx2=bx2, by2=by2):
                return (CX + (p[0] - bx2) * s, CY + (p[1] - by2) * s)

            draw_polys(surf, polys, style, rng, xform)
            surf.blit(font.render(name, True, (245, 245, 245)), (24, 18))
            if fi == 40:
                pygame.image.save(surf, os.path.join(
                    OUT_DIR, f"motif_spin_{mode}_check.png"))
            ff.stdin.write(pygame.image.tostring(surf, "RGB"))
    else:
        seg_frames = int(SEG_SEC * FPS)
        for mi, (name, shape, wcx, wcz, base, bx, by, s) in enumerate(pre):
            for fi in range(seg_frames):
                ang = math.pi * 2 * fi / seg_frames
                rng = random.Random(5000 + mi * 100 + fi)
                surf = blank(mi)
                ca, sa = math.cos(ang), math.sin(ang)

                def xform(p):
                    dx, dy = (p[0] - bx) * s, (p[1] - by) * s
                    return (CX + dx * ca - dy * sa, CY + dx * sa + dy * ca)

                draw_polys(surf, base, style, rng, xform)
                surf.blit(font.render(name, True, (245, 245, 245)), (24, 18))
                ff.stdin.write(pygame.image.tostring(surf, "RGB"))

    ff.stdin.close()
    ff.wait()
    print(f"saved {out}")


def main():
    pygame.init()
    pygame.display.set_mode((64, 64))
    with open(os.path.join(os.path.dirname(HERE), "core", "bg_models.json")) as f:
        P.MODELS = json.load(f)
    for mode in (sys.argv[1:] or ["yaw"]):
        render(mode)


if __name__ == "__main__":
    main()
