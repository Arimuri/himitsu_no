#!/usr/bin/env python3
"""
Background generator for the music video: procedural houses ported from my
OpenProcessing sketch (p5.js WEBGL) to pygame, with Vib-Ribbon-ized lines —
every projected edge is subdivided and wobbled along its whole length, then
extended past both ends like a sketchy architectural overdraw.

Grammar (same as the sketch): floor-0 always; floor picks trees; base is
random; base picks door / win / roof; roof picks roofaddon / top.
Missing id -> 1000 -> that part is skipped.

Renders a labeled 4x2 contact sheet (2 tiles per style, different house
seeds) + individual PNGs into ボカコレ2026S/movie/background/.
"""
import os
import math
import json
import random

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
HERE = os.path.dirname(os.path.abspath(__file__))
import sys
sys.path.insert(0, HERE)
import pygame
from scribble import Scribble, jitter_line

OUT_DIR = "/Users/arimura/Dropbox/ボカコレ2026S/movie/background"
TILE = 800
M = 70.0                      # model scale, as in the sketch

# ---- camera (p5: perspective(PI*0.48), setPosition(0,-50,500), lookAt(0,-200,0)) ----
FOV = math.pi * 0.48
EYE = (0.0, -50.0, 500.0)
CENTER = (0.0, -200.0, 0.0)
UP = (0.0, 1.0, 0.0)          # p5 WEBGL: world y points down
NEAR = 1.0
VIEW_ZOOM = 1.05              # extra framing knobs on top of the p5 camera
VIEW_YOFF = 30.0
VIEW_XOFF = 0.0
VIEW_W = TILE                 # override for non-square renders (e.g. 1280x720)
VIEW_H = TILE


def _norm(v):
    l = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    return (v[0] / l, v[1] / l, v[2] / l)


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _camera_basis():
    z = _norm((EYE[0] - CENTER[0], EYE[1] - CENTER[1], EYE[2] - CENTER[2]))
    x = _norm(_cross(UP, z))
    y = _cross(z, x)
    return x, y, z


CAM_X, CAM_Y, CAM_Z = _camera_basis()


def project(px, py, pz):
    """World -> screen. Returns None when behind the near plane."""
    dx, dy, dz = px - EYE[0], py - EYE[1], pz - EYE[2]
    vz = dx * CAM_Z[0] + dy * CAM_Z[1] + dz * CAM_Z[2]
    if vz > -NEAR:
        return None
    vx = dx * CAM_X[0] + dy * CAM_X[1] + dz * CAM_X[2]
    vy = dx * CAM_Y[0] + dy * CAM_Y[1] + dz * CAM_Y[2]
    focal = (VIEW_H / 2) / math.tan(FOV / 2)
    s = focal * VIEW_ZOOM / -vz
    return (VIEW_W / 2 + VIEW_XOFF + vx * s,
            VIEW_H / 2 + VIEW_YOFF + vy * s)


# ---- house grammar (mirrors ui.generate / getNext) ----
def generate_arch(models, rng):
    arch = {"floor": 0}

    def get_next(id_list, key):
        name = id_list[rng.randrange(len(id_list))]
        for i, entry in enumerate(models[key]):
            if entry.get("id") == name:
                return i
        return 1000  # "empty" or a missing id -> skip

    for key, ids in models["floor"][arch["floor"]].get("next", {}).items():
        arch[key] = get_next(ids, key)
    arch["base"] = rng.randrange(len(models["base"]))
    for key, ids in models["base"][arch["base"]].get("next", {}).items():
        arch[key] = get_next(ids, key)
    if arch.get("roof", 1000) < 1000:
        for key, ids in models["roof"][arch["roof"]].get("next", {}).items():
            arch[key] = get_next(ids, key)
    return arch


DRAW_ORDER = ["floor", "trees", "base", "door", "win", "roof", "roofaddon", "top"]


# ---- Vib-Ribbon line: extend both ends, subdivide ~25px, jitter every point ----
def vib_line(surf, col, p1, p2, width, rng, jit=2.0, seg=25.0, ext=0.12):
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    length = math.hypot(dx, dy)
    if length < 1e-6:
        return
    e1, e2 = rng.uniform(0, ext), rng.uniform(0, ext)
    ax, ay = p1[0] - dx * e1, p1[1] - dy * e1
    bx, by = p2[0] + dx * e2, p2[1] + dy * e2
    steps = max(1, int(length * (1 + e1 + e2) // seg))
    j = min(jit, length * 0.12)  # short edges wobble less -> details stay crisp
    pts = []
    for i in range(steps + 1):
        t = i / steps
        pts.append((int(ax + (bx - ax) * t + rng.uniform(-j, j)),
                    int(ay + (by - ay) * t + rng.uniform(-j, j))))
    pygame.draw.lines(surf, col, False, pts, width)


def draw_shape(surf, shape, style, materials, rng):
    """Fills first, then wobbled edges — same two-pass order as the sketch."""
    polys = []
    for face in shape["data"]:
        pts = []
        ok = True
        for v in face["vertices"]:
            p = project(v[0] * M, v[1] * M, v[2] * M)
            if p is None:
                ok = False
                break
            pts.append(p)
        polys.append(pts if ok and len(pts) >= 2 else None)

    fill_mode = style.get("fill_mode")
    blend = style.get("fill_blend", 0.0)   # 0 = as-is, 1 = vanish into bg
    if fill_mode is not None:
        for face, pts in zip(shape["data"], polys):
            mat = face.get("mat")
            if pts is None or len(pts) < 3 or not mat:
                continue  # mat 0 / missing -> noFill, as in the sketch
            col = materials[fill_mode][mat]
            if col[3] <= 0:
                continue
            c = tuple(int(col[k] + (style["bg"][k] - col[k]) * blend)
                      for k in range(3))
            pygame.draw.polygon(surf, c, [(int(x), int(y)) for x, y in pts])

    scr = None
    if style.get("scribble"):
        scr = Scribble(rng=rng, roughness=style.get("roughness", 2.0),
                       bowing=1.5, max_offset=2.5)

    def edges(pts):
        closed = pts + [pts[0]]
        for i in range(len(closed) - 1):
            if scr:
                scr.line(surf, style["line"], style["lw"],
                         closed[i][0], closed[i][1],
                         closed[i + 1][0], closed[i + 1][1])
            else:
                jitter_line(surf, style["line"], style["lw"],
                            closed[i][0], closed[i][1],
                            closed[i + 1][0], closed[i + 1][1], rng)

    if style.get("occlude") and fill_mode is not None:
        # painter per face: a face's fill hides the lines behind it, so
        # solid objects stop reading as transparent wire tangles
        for face, pts in zip(shape["data"], polys):
            if pts is None:
                continue
            mat = face.get("mat")
            if mat and len(pts) >= 3:
                col = materials[fill_mode][mat]
                if col[3] > 0:
                    c = tuple(int(col[k] + (style["bg"][k] - col[k]) * blend)
                              for k in range(3))
                    pygame.draw.polygon(surf, c,
                                        [(int(x), int(y)) for x, y in pts])
            edges(pts)
        return

    for pts in polys:
        if pts is None:
            continue
        edges(pts)


def draw_stars(surf, rng, col, count, lw=2):
    """Sparse '+' sparkles in the side margins, never on the house."""
    spots = []
    for side in (0, 1):
        xs = (26, 150) if side == 0 else (650, 774)
        for k in range(4):
            spots.append((xs, (40 + k * 190, 170 + k * 190)))
    rng.shuffle(spots)
    for xs, ys in spots[:count]:
        x = rng.randint(*xs)
        y = rng.randint(*ys)
        r = rng.choice((4, 7, 11))
        pygame.draw.line(surf, col, (x - r, y), (x + r, y), lw)
        pygame.draw.line(surf, col, (x, y - r), (x, y + r), lw)


STYLES = {
    "vib": {"bg": (10, 10, 14), "line": (245, 245, 245), "lw": 2,
            "fill_mode": None, "stars": 7, "star_col": (205, 205, 215)},
    "vib-yellow": {"bg": (255, 208, 51), "line": (40, 42, 60), "lw": 3,
                   "fill_mode": None, "stars": 4, "star_col": (40, 42, 60)},
    "shaded": {"bg": (234, 219, 200), "line": (0, 0, 0), "lw": 3,
               "fill_mode": 0, "stars": 0},
    "inverted": {"bg": (37, 73, 99), "line": (255, 255, 255), "lw": 3,
                 "fill_mode": 3, "stars": 0},
    # confirmed PV taste, softened: pale lines + fills sunk toward the bg so
    # the white character reads in front of the backdrop
    # PV style: same scribble stroke engine as the character, pale colors
    "inverted-soft": {"bg": (50, 92, 122), "line": (245, 245, 245), "lw": 1,
                      "fill_mode": 3, "fill_blend": 0.62, "stars": 0,
                      "scribble": True, "roughness": 2.0},
    # PV style alt: unified on the jitter/overshoot stroke instead
    "inverted-soft-jitter": {"bg": (50, 92, 122), "line": (245, 245, 245),
                             "lw": 2, "fill_mode": 3, "fill_blend": 0.62,
                             "stars": 0, "occlude": True},
}

# (style, house seed) per tile — 2 houses per style
TILES = [
    ("vib", 3), ("vib", 42),
    ("vib-yellow", 8), ("vib-yellow", 22),
    ("shaded", 18), ("shaded", 13),
    ("inverted", 1), ("inverted", 45),
]


def render_tile(models, style_name, seed, font):
    style = STYLES[style_name]
    surf = pygame.Surface((TILE, TILE))
    surf.fill(style["bg"])

    rng = random.Random(seed)           # grammar + line wobble, one stream
    arch = generate_arch(models, rng)
    if style["stars"]:
        draw_stars(surf, random.Random(seed * 31 + 7),
                   style["star_col"], style["stars"], max(2, style["lw"] - 1))
    for key in DRAW_ORDER:
        idx = arch.get(key, 1000)
        if idx < 1000:
            draw_shape(surf, models[key][idx], style, models["materials"], rng)

    label = font.render(f"{style_name}  #{seed}", True, style["line"])
    surf.blit(label, (24, 18))
    return surf, arch


def main():
    pygame.init()
    pygame.display.set_mode((64, 64))
    font = pygame.font.Font(os.path.join(HERE, "font.ttf"), 26)
    with open(os.path.join(HERE, "bg_models.json")) as f:
        models = json.load(f)
    os.makedirs(OUT_DIR, exist_ok=True)

    sheet = pygame.Surface((TILE * 4, TILE * 2))
    for i, (style_name, seed) in enumerate(TILES):
        tile, arch = render_tile(models, style_name, seed, font)
        pygame.image.save(tile, os.path.join(OUT_DIR, f"bg_{i + 1}.png"))
        sheet.blit(tile, ((i % 4) * TILE, (i // 4) * TILE))
        print(f"bg_{i + 1}: {style_name} #{seed} -> "
              + " ".join(f"{k}={v}" for k, v in arch.items()))
    out = os.path.join(OUT_DIR, "bg_sheet.png")
    pygame.image.save(sheet, out)
    print(f"saved {out}")


if __name__ == "__main__":
    main()
