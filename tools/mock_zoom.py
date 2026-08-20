#!/usr/bin/env python3
"""
9-second slow zoom mock (16:9, 12fps): trees (5 kinds), rocks and a power line
scattered randomly in space; tiny Miku standing dead-center in a very wide
shot; the camera zooms in slooowly. Mix style (jitter bg + scribble Miku).

Output: movie/mock_zoom.mp4 (+ f0 / f60 check stills)
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
FPS = 12
DUR = 9.0
SEED = 20260817
ZOOM0, ZOOM1 = 0.81, 2.05   # start = former 3s point, end closer
MIKU_WORLD_H = 2.3         # Miku's height in world units
MIKU_Z = -6.0

MIKU_V = {"render": "line", "bg": "black", "mono": True, "line_col": DS.WHITE,
          "scribble": True, "roughness": 2.0, "lw": 2}


def ref_house(seed):
    """The original-grammar house (as in bg_6) as a placeable prop."""
    arch = B.generate_arch(P.MODELS, random.Random(seed))
    faces = []
    for key in B.DRAW_ORDER:
        if key in ("floor", "trees"):
            continue
        idx = arch.get(key, 1000)
        if idx < 1000:
            for f in P.MODELS[key][idx]["data"]:
                faces.append({"mat": f.get("mat"),
                              "vertices": [list(v) for v in f["vertices"]]})
    return {"data": faces}


def build_scene(mode="ko", left_bld=None):
    """Random scatter, keeping the center corridor clear for Miku."""
    rng = random.Random(SEED)
    if mode == "ko":
        # U-shape: sides + back, open toward the camera.  the left flank
        # runs one span toward the camera so its wires stay in frame (the
        # eye sits right of center); near-pole overshoot flicker is gone
        # since the 45px cap in scribble.jitter_line
        perim = [(-22.5, 2), (-22.5, -8), (-22.5, -22), (-22.5, -36),
                 (0, -37), (22.5, -36), (22.5, -22), (22.5, -8)]
        items = list(P.power_ring(perim, h=6.0, sag=0.75, closed=False))
    else:
        # one absurdly long straight row far back, cropped at both ends
        row = [(x, -31) for x in range(-60, 61, 10)]
        items = list(P.power_ring(row, h=6.0, sag=0.75, closed=False))

    kinds = [P.tree_1, P.tree_2, P.tree_3, P.tree_4, P.tree_5]
    # curated slots: (builder, scale, x, z) + jitter.
    # only two giants; mid-size ring; foreground props on the flanks.
    slots = [
        (P.pylon, 2.5, 13.5, -23),           # giant far-right
        (left_bld or P.danchi, 1.6, -19.5, -13.0),
        (P.office, 1.6, 15.5, -11),
        (P.silo, 1.5, -8.5, -19),
        (P.water_tower, 1.6, 7.5, -17),
        (P.crane, 1.5, 19.0, -27),
        (P.tree_1, 3.2, -9.5, 2.6),          # foreground left, big
        (P.street_lamp, 1.5, 7.2, 3.4),      # foreground right
        (P.rock, 1.8, -5.8, 4.2),
    ]
    placed = []

    def place(shape, x, z, sc=1.0):
        for face in shape["data"]:
            for v in face["vertices"]:
                v[0] = v[0] * sc + x
                v[1] = v[1] * sc
                v[2] = v[2] * sc + z
        return shape

    def free(x, z, margin, cx_min=2.8):
        if abs(x) < cx_min:                # keep the whole center column clear
            return False
        return all(abs(x - px) > margin or abs(z - pz) > 2.5
                   for px, pz in placed)

    for i in range(5):
        for _ in range(80):
            x = rng.uniform(-21.0, 21.0)
            z = rng.uniform(-32.0, 5.0)
            if free(x, z, 2.2):
                break
        else:
            x = math.copysign(2.8 + abs(x) * 0.5, x or 1)
        placed.append((x, z))
        s = rng.uniform(1.15, 1.9)
        shape = kinds[i % 5](x, s)
        # push the tree to its depth (props are built at z=0)
        for face in shape["data"]:
            for v in face["vertices"]:
                v[2] += z
        items.append((z, shape))

    for bld, sc, sx, sz in slots:
        x = sx + rng.uniform(-1.2, 1.2)
        z = sz + rng.uniform(-1.2, 1.2)
        placed.append((x, z))
        items.append((z, place(bld(), x, z, sc)))

    # small keepsakes scattered around Miku's feet (she stands at 0, MIKU_Z)
    around = [
        (1.0, 4.8, -3.4, 31), (0.9, -4.6, -5.2, 34),
    ]
    for sc, dx, dz, sd in around:
        x, z = dx, MIKU_Z + dz
        items.append((z, place(P.rock(seed=sd), x, z, sc)))
    for bld, sc, dx, dz in ((P.tree_3, 1.5, -6.5, -1.6),
                            (P.tree_2, 1.45, 5.8, -4.0)):
        x, z = dx, MIKU_Z + dz
        items.append((z, place(bld(), x, z, sc)))
    for _ in range(16):
        x = rng.uniform(-6.5, 6.5)
        z = MIKU_Z + rng.uniform(-5.0, 5.0)
        if abs(x) < 0.9 and abs(z - MIKU_Z) < 0.9:
            continue
        a = rng.uniform(0, math.pi)
        l = rng.uniform(0.08, 0.2)
        items.append((z, {"data": [P.seg((x, 0, z),
                                         (x + math.cos(a) * l, -0.1,
                                          z + math.sin(a) * l * 0.4))]}))

    for i in range(3):
        for _ in range(80):
            x = rng.uniform(-21.0, 21.0)
            z = rng.uniform(-30.0, 5.0)
            if free(x, z, 3.2):
                break
        else:
            x = math.copysign(2.8 + abs(x) * 0.5, x or 1)
        placed.append((x, z))
        shape = P.rock(x, rng.uniform(0.55, 1.25), seed=rng.randrange(999))
        for face in shape["data"]:
            for v in face["vertices"]:
                v[2] += z
        items.append((z, shape))

    # grass ticks so the ground reads even when its edges leave the frame
    for _ in range(70):
        x = rng.uniform(-21.5, 21.5)
        z = rng.uniform(-32.0, 6.0)
        if abs(x) < 2.2:
            continue
        a = rng.uniform(0, math.pi)
        l = rng.uniform(0.12, 0.3)
        items.append((z, {"data": [P.seg((x, 0, z),
                                         (x + math.cos(a) * l, -0.12,
                                          z + math.sin(a) * l * 0.4))]}))

    items.sort(key=lambda it: it[0])       # painter: far (small z) first
    # ground as SHORT edge segments: the single quad's front corners sit
    # beside the camera and project enormous edges whose per-frame jitter
    # bow swept across the sky as a flickering diagonal
    gpts = [(-30, 9), (30, 9), (30, -40), (-30, -40)]
    gseg = []
    for k in range(4):
        (x0, z0), (x1, z1) = gpts[k], gpts[(k + 1) % 4]
        n = max(2, int(math.hypot(x1 - x0, z1 - z0) / 1.5))
        for j in range(n):
            t0, t1 = j / n, (j + 1) / n
            gseg.append(P.seg((x0 + (x1 - x0) * t0, 0, z0 + (z1 - z0) * t0),
                              (x0 + (x1 - x0) * t1, 0, z0 + (z1 - z0) * t1)))
    return [(-99, {"data": gseg})] + items


def smoothstep(t):
    return t * t * (3 - 2 * t)


LEFT_VARIANTS = [
    ("danchi", None), ("office", "office"), ("warehouse", "warehouse"),
    ("factory", "factory"), ("containers", "containers"),
    ("pagoda", "building_3"),
]


def render_leftvar(style):
    font = pygame.font.Font(os.path.join(HERE, "font.ttf"), 26)
    tiles = []
    for name, attr in LEFT_VARIANTS:
        bld = getattr(P, attr) if attr else None
        scene = build_scene("ko", left_bld=bld)
        B.VIEW_ZOOM = 1.35
        surf = pygame.Surface((W, H))
        surf.fill(style["bg"])
        lrng = random.Random(7042)
        for _, shape in scene:
            B.draw_shape(surf, shape, style, P.MODELS["materials"], lrng)
        feet = B.project(0, 0, MIKU_Z * B.M)
        head_ref = B.project(0, -MIKU_WORLD_H * B.M, MIKU_Z * B.M)
        mw = (feet[1] - head_ref[1]) / 1.9
        d = DS.D(surf, MIKU_V, seed=542)
        DS.draw_miku(d, feet[0], feet[1] - 1.53 * mw, mw)
        surf.blit(font.render(name, True, (245, 245, 245)), (24, 18))
        pygame.image.save(surf,
                          os.path.join(CHECK_DIR, f"leftbldg_{name}.png"))
        tiles.append(surf)
    sheet = pygame.Surface((W, H // 2 * 3))
    for i, tl in enumerate(tiles):
        small = pygame.transform.smoothscale(tl, (W // 2, H // 2))
        sheet.blit(small, ((i % 2) * (W // 2), (i // 2) * (H // 2)))
    out = os.path.join(CHECK_DIR, "leftbldg_sheet.png")
    pygame.image.save(sheet, out)
    print(f"saved {out}")


def main():
    pygame.init()
    pygame.display.set_mode((64, 64))
    with open(os.path.join(os.path.dirname(HERE), "core", "bg_models.json")) as f:
        P.MODELS = json.load(f)

    style = B.STYLES["inverted-soft-jitter"]
    B.VIEW_W, B.VIEW_H = W, H
    B.VIEW_XOFF, B.VIEW_YOFF = 0.0, 10.0
    B.FOV = math.pi * 0.36            # longer lens: keeps verticals vertical
    B.EYE = (140.0, -420.0, 900.0)    # bird's-eye, only slightly off-axis
    B.CENTER = (0.0, -70.0, -420.0)
    B.CAM_X, B.CAM_Y, B.CAM_Z = B._camera_basis()

    modes = sys.argv[1:] or ["ko", "row"]
    for mode in modes:
        if mode == "leftvar":
            render_leftvar(style)
        else:
            render(style, mode)


def render(style, mode):
    scene = build_scene(mode)
    suffix = "" if mode == "ko" else "_row"
    out = os.path.join(OUT_DIR, f"mock_zoom{suffix}.mp4")
    frames = int(DUR * FPS)
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-vcodec", "rawvideo",
         "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", out],
        stdin=subprocess.PIPE)

    for i in range(frames):
        t = i / (frames - 1)
        tz = min(1.0, t * DUR / (DUR - 1.0))   # zoom done at 8s, hold last 1s
        B.VIEW_ZOOM = ZOOM0 + (ZOOM1 - ZOOM0) * smoothstep(tz)

        surf = pygame.Surface((W, H))
        surf.fill(style["bg"])
        P.stars(surf, SEED * 31 + 7, W)

        lrng = random.Random(7000 + i)
        for _, shape in scene:
            B.draw_shape(surf, shape, style, P.MODELS["materials"], lrng)

        # Miku pinned to the world at (0, ground, MIKU_Z), screen center-ish
        feet = B.project(0, 0, MIKU_Z * B.M)
        head_ref = B.project(0, -MIKU_WORLD_H * B.M, MIKU_Z * B.M)
        hpx = feet[1] - head_ref[1]
        mw = hpx / 1.9                      # layout unit from figure height
        cy = feet[1] - 1.53 * mw
        d = DS.D(surf, MIKU_V, seed=500 + i)
        ts = i / FPS
        sw = round(math.sin(math.pi * 2 * ts / 3.2) * 2) / 2 * 0.03
        DS.draw_miku(d, feet[0], cy, mw,
                     tail_swing=(sw, -sw), tail_swing2=(-sw, sw))

        # giant foreground ferris wheel, cropped at the left edge, slow turn
        fw = P.ferris_wheel(ang=0.105 * (i / FPS))
        for face in fw["data"]:
            for v in face["vertices"]:
                v[0] = v[0] * 3.2 + 19.0
                v[1] = v[1] * 3.2
                v[2] = v[2] * 3.2 + 2.6
        B.draw_shape(surf, fw, style, P.MODELS["materials"],
                     random.Random(8800 + i))

        if i in (0, 60):
            pygame.image.save(surf,
                              os.path.join(CHECK_DIR, f"mock_zoom{suffix}_f{i}.png"))
        ff.stdin.write(pygame.image.tostring(surf, "RGB"))

    ff.stdin.close()
    ff.wait()
    print(f"saved {out}")


if __name__ == "__main__":
    main()
