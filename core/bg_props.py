#!/usr/bin/env python3
"""
Original parametric props for the PV background — buildings and trees built
from scratch (no reference models), rendered through the same camera and
jitter-line pipeline as bg_sketch. Confirmed style: "mix" = jitter background
+ scribble Miku on the bright navy.

Outputs (all stills, 16:9 comps / 800px tiles):
  movie/background/buildings_sheet.png  + building_1..5.png   (5 variations)
  movie/background/trees_sheet.png      + tree_1..3.png       (3 variations)
  movie/comp_1..3.png                   (Miku vs background layouts)

World units match the ref models: ground y=0, up = -y, ~4 units = house width.
"""
import os
import json
import math
import random

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
HERE = os.path.dirname(os.path.abspath(__file__))
import sys
sys.path.insert(0, HERE)
import pygame

import bg_sketch as B
from scribble import jitter_line
import design_sketch as DS

BG_DIR = "/Users/arimura/Dropbox/ボカコレ2026S/movie/background"
MOVIE_DIR = "/Users/arimura/Dropbox/ボカコレ2026S/movie/current"
TILE = 800

MIKU_V = {"render": "line", "bg": "black", "mono": True, "line_col": DS.WHITE,
          "scribble": True, "roughness": 2.0, "lw": 2}


def q(mat, pts):
    return {"mat": mat, "vertices": [list(p) for p in pts]}


def box(ox, oz, w, h, d, mat_front=1, mat_side=2, y0=0.0):
    """Axis-aligned box sitting on the ground. Returns faces back-to-front."""
    x0, x1 = ox - w / 2, ox + w / 2
    z0, z1 = oz - d / 2, oz + d / 2
    yb, yt = y0, y0 - h
    return [
        q(mat_side, [(x0, yb, z0), (x1, yb, z0), (x1, yt, z0), (x0, yt, z0)]),
        q(mat_side, [(x0, yb, z0), (x0, yb, z1), (x0, yt, z1), (x0, yt, z0)]),
        q(mat_side, [(x1, yb, z0), (x1, yb, z1), (x1, yt, z1), (x1, yt, z0)]),
        q(mat_side, [(x0, yt, z0), (x1, yt, z0), (x1, yt, z1), (x0, yt, z1)]),
        q(mat_front, [(x0, yb, z1), (x1, yb, z1), (x1, yt, z1), (x0, yt, z1)]),
    ]


def gable(ox, oz, w, d, y_base, rh, mat=4):
    """Gable roof, ridge running left-right (x), peak toward the camera view."""
    x0, x1 = ox - w / 2, ox + w / 2
    z0, z1 = oz - d / 2, oz + d / 2
    yt = y_base - rh
    return [
        q(mat, [(x0, y_base, z0), (x1, y_base, z0), (x1, yt, oz), (x0, yt, oz)]),
        q(mat, [(x0, y_base, z1), (x1, y_base, z1), (x1, yt, oz), (x0, yt, oz)]),
        q(mat, [(x0, y_base, z0), (x0, y_base, z1), (x0, yt, oz)]),
        q(mat, [(x1, y_base, z0), (x1, y_base, z1), (x1, yt, oz)]),
    ]


def windows(ox, oz_front, w, y_top, rows, cols, ww=0.34, wh=0.4, mat=5):
    faces = []
    gx = w * 0.72
    for r in range(rows):
        for c in range(cols):
            cx = ox - gx / 2 + (c + 0.5) * gx / cols
            cy = y_top + 0.35 + r * (wh + 0.28)
            faces.append(q(mat, [(cx - ww / 2, cy, oz_front),
                                 (cx + ww / 2, cy, oz_front),
                                 (cx + ww / 2, cy + wh, oz_front),
                                 (cx - ww / 2, cy + wh, oz_front)]))
    return faces


def door(ox, oz_front, dw=0.55, dh=0.85, mat=3):
    return [q(mat, [(ox - dw / 2, 0, oz_front), (ox + dw / 2, 0, oz_front),
                    (ox + dw / 2, -dh, oz_front), (ox - dw / 2, -dh, oz_front)])]


def eave(ox, oz, w, d, y, th=0.12, mat=4):
    """Thin wide slab overhanging the walls — the ref houses' signature."""
    return box(ox, oz, w, th, d, mat, mat, y0=y)


def hip_roof(ox, oz, w, d, y, rh, shrink=0.45, mat=4):
    """Truncated pyramid roof (4 trapezoids + flat top)."""
    x0, x1 = ox - w / 2, ox + w / 2
    z0, z1 = oz - d / 2, oz + d / 2
    tw, td = w * shrink, d * shrink
    tx0, tx1 = ox - tw / 2, ox + tw / 2
    tz0, tz1 = oz - td / 2, oz + td / 2
    yt = y - rh
    return [
        q(mat, [(x0, y, z0), (x1, y, z0), (tx1, yt, tz0), (tx0, yt, tz0)]),
        q(mat, [(x0, y, z0), (x0, y, z1), (tx0, yt, tz1), (tx0, yt, tz0)]),
        q(mat, [(x1, y, z0), (x1, y, z1), (tx1, yt, tz1), (tx1, yt, tz0)]),
        q(mat, [(x0, y, z1), (x1, y, z1), (tx1, yt, tz1), (tx0, yt, tz1)]),
        q(mat, [(tx0, yt, tz0), (tx1, yt, tz0), (tx1, yt, tz1), (tx0, yt, tz1)]),
    ]


def railing(ox, w, y, z, h=0.32, n=6, mat=2):
    """Balcony/roof-deck balustrade: top rail + vertical slats."""
    x0, x1 = ox - w / 2, ox + w / 2
    f = [q(mat, [(x0, y - h, z), (x1, y - h, z),
                 (x1, y - h + 0.06, z), (x0, y - h + 0.06, z)])]
    for k in range(n + 1):
        x = x0 + (x1 - x0) * k / n
        f.append(q(0, [(x, y, z), (x, y - h, z)]))
    return f


# ---- five original buildings, layered like the ref (eaves / tiers / rails) ----
def building_1(ox=0.0):     # eaved cottage: base + wide eave + attic + hip roof
    f = box(ox, 0, 3.2, 1.4, 2.6)
    f += eave(ox, 0, 4.2, 3.4, -1.4)
    f += box(ox, 0, 2.3, 0.95, 2.0, 1, 2, y0=-1.52)
    f += eave(ox, 0, 3.0, 2.6, -2.47)
    f += hip_roof(ox, 0, 3.0, 2.6, -2.59, 0.65)
    f += door(ox - 0.15, 1.32)
    f += windows(ox + 0.65, 1.32, 1.7, -1.1, 1, 1, ww=0.5, wh=0.45)
    f += windows(ox, 1.02, 1.7, -2.28, 1, 2, ww=0.36, wh=0.36)
    return {"data": f}


def building_2(ox=0.0):     # balcony house: two floors, rail, shed roof, chimney
    f = box(ox, 0, 2.6, 1.5, 2.2)
    f += eave(ox, 0, 3.5, 2.9, -1.5)
    f += box(ox, -0.15, 2.4, 1.15, 1.9, 1, 2, y0=-1.62)
    f += railing(ox, 3.1, -1.62, 1.42, n=7)
    x0, x1 = ox - 1.55, ox + 1.55
    f += [q(4, [(x0, -2.77, -1.25), (x1, -2.77, -1.25), (x1, -3.28, 1.15),
                (x0, -3.08, 1.15)])]
    f += box(ox + 0.75, -0.5, 0.34, 0.75, 0.34, 2, 2, y0=-3.0)
    f += door(ox - 0.6, 1.12)
    f += windows(ox + 0.35, 1.12, 1.4, -1.25, 1, 2, ww=0.38, wh=0.42)
    f += windows(ox, 0.82, 1.7, -2.55, 1, 2, ww=0.4, wh=0.4)
    return {"data": f}


def building_3(ox=0.0):     # pagoda tower: three tiers with eaves + antenna
    f = box(ox, 0, 2.5, 1.15, 2.1)
    f += eave(ox, 0, 3.3, 2.8, -1.15)
    f += box(ox, 0, 1.95, 1.0, 1.65, 1, 2, y0=-1.27)
    f += eave(ox, 0, 2.7, 2.3, -2.27)
    f += box(ox, 0, 1.45, 0.9, 1.25, 1, 2, y0=-2.39)
    f += eave(ox, 0, 2.1, 1.8, -3.29)
    f += hip_roof(ox, 0, 2.1, 1.8, -3.41, 0.5)
    f += [q(2, [(ox - 0.03, -3.91, 0), (ox + 0.03, -3.91, 0),
                (ox + 0.03, -4.7, 0), (ox - 0.03, -4.7, 0)]),
          q(5, [(ox - 0.16, -4.55, 0), (ox + 0.16, -4.55, 0),
                (ox, -4.85, 0)])]
    f += door(ox, 1.07, dw=0.5)
    f += windows(ox, 1.07, 1.7, -0.95, 1, 2, ww=0.32, wh=0.34)
    f += windows(ox, 0.85, 1.3, -2.1, 1, 2, ww=0.28, wh=0.3)
    f += windows(ox, 0.65, 0.9, -3.15, 1, 1, ww=0.3, wh=0.3)
    return {"data": f}


def building_4(ox=0.0):     # shop: awning on posts, parapet, roof deck + sign
    f = box(ox, 0, 4.4, 1.3, 2.6)
    f += eave(ox, 0.35, 4.8, 2.2, -1.06, th=0.1)     # low awning slab
    for sx in (-2.05, 2.05):
        f.append(q(0, [(ox + sx, 0, 1.35), (ox + sx, -1.06, 1.35)]))
    f += [q(2, [(ox - 2.35, -1.3, 1.32), (ox + 2.35, -1.3, 1.32),
                (ox + 2.35, -1.6, 1.32), (ox - 2.35, -1.6, 1.32)])]
    f += railing(ox - 0.9, 2.3, -1.6, 1.28, n=5)
    f += box(ox + 1.35, -0.3, 1.5, 0.85, 1.6, 1, 2, y0=-1.6)
    f += [q(5, [(ox + 1.35 - 0.65, -2.45, 0.55), (ox + 1.35 + 0.65, -2.45, 0.55),
                (ox + 1.35 + 0.65, -3.15, 0.55), (ox + 1.35 - 0.65, -3.15, 0.55)]),
          q(0, [(ox + 0.85, -2.45, 0.55), (ox + 0.85, -1.6, 0.55)]),
          q(0, [(ox + 1.85, -2.45, 0.55), (ox + 1.85, -1.6, 0.55)])]
    f += door(ox - 1.45, 1.32, dw=0.7, dh=0.95)
    f += windows(ox + 0.45, 1.32, 2.4, -1.0, 1, 3, ww=0.48, wh=0.48)
    return {"data": f}


def building_5(ox=0.0):     # twin volumes: hip-roofed main + shed annex + fence
    f = box(ox - 1.05, 0, 2.1, 1.75, 2.3)
    f += eave(ox - 1.05, 0, 2.9, 2.9, -1.75)
    f += hip_roof(ox - 1.05, 0, 2.9, 2.9, -1.87, 0.8)
    f += box(ox + 1.2, 0.2, 1.7, 1.15, 1.8, 2, 1)
    x0, x1 = ox + 0.35, ox + 2.05
    f += [q(4, [(x0, -1.15, -0.7), (x1, -1.15, -0.7), (x1, -1.6, 1.15),
                (x0, -1.45, 1.15)])]
    f += railing(ox + 2.6, 1.0, 0.0, 1.1, h=0.5, n=4)
    f += door(ox + 1.2, 1.12, dw=0.5, dh=0.8)
    f += windows(ox - 1.05, 1.17, 1.6, -1.4, 2, 2, ww=0.34, wh=0.34)
    f += windows(ox + 1.2, 1.12, 1.1, -0.95, 1, 1, ww=0.4, wh=0.4)
    return {"data": f}


BUILDINGS = [building_1, building_2, building_3, building_4, building_5]


# ---- three original tree-ish objects ----
def _tree_cross(ox, s, parts, rings):
    """Two crossed profile planes + horizontal rings = cheap solid tree."""
    f = []
    for mat, prof in parts:
        f.append(q(mat, [(ox + px * s, py * s, 0) for px, py in prof]))
        f.append(q(mat, [(ox, py * s, px * s) for px, py in prof]))
    for cy, r in rings:
        ring = [(ox + r * s * math.cos(a), cy * s, r * s * math.sin(a))
                for a in [math.pi * 2 * k / 8 for k in range(8)]]
        f.append(q(0, ring))
    return {"data": f}


def tree_1(ox=0.0, s=1.0):  # pine: crossed twin triangles + cone rings
    trunk = (2, [(-0.06, 0), (0.06, 0), (0.06, -0.5), (-0.06, -0.5)])
    t1 = (4, [(-0.55, -0.4), (0.55, -0.4), (0, -1.25)])
    t2 = (4, [(-0.42, -1.0), (0.42, -1.0), (0, -1.7)])
    return _tree_cross(ox, s, [trunk, t1, t2], [(-0.42, 0.5), (-1.02, 0.38)])

def tree_2(ox=0.0, s=1.0):  # round: crossed octagon blobs + equator ring
    trunk = (2, [(-0.06, 0), (0.06, 0), (0.06, -0.65), (-0.06, -0.65)])
    blob = (4, [(0.55 * math.cos(a), -1.15 + 0.6 * math.sin(a))
                for a in [math.pi * 2 * k / 8 + math.pi / 8 for k in range(8)]])
    return _tree_cross(ox, s, [trunk, blob], [(-1.15, 0.55)])

def tree_3(ox=0.0, s=1.0):  # poplar: crossed tall diamonds + waist ring
    trunk = (2, [(-0.05, 0), (0.05, 0), (0.05, -0.35), (-0.05, -0.35)])
    dia = (4, [(0, -0.3), (0.3, -1.05), (0, -1.9), (-0.3, -1.05)])
    return _tree_cross(ox, s, [trunk, dia], [(-1.05, 0.3)])


def tree_4(ox=0.0, s=1.0):  # umbrella/acacia: tall trunk + wide flat canopy
    trunk = (2, [(-0.06, 0), (0.06, 0), (0.04, -1.1), (-0.04, -1.1)])
    canopy = (4, [(-0.9, -1.05), (0.9, -1.05), (0.5, -1.5), (-0.5, -1.5)])
    return _tree_cross(ox, s, [trunk, canopy], [(-1.07, 0.88), (-1.48, 0.48)])


def tree_5(ox=0.0, s=1.0):  # bare branching tree, drawn in both planes
    lines = [((0, 0), (0, -1.05)),
             ((0, -0.55), (0.5, -1.2)), ((0.5, -1.2), (0.62, -1.55)),
             ((0.5, -1.2), (0.78, -1.35)),
             ((0, -0.8), (-0.45, -1.35)), ((-0.45, -1.35), (-0.62, -1.6)),
             ((0, -1.05), (0.18, -1.75)), ((0, -1.05), (-0.15, -1.6))]
    f = []
    for (ax, ay), (bx, by) in lines:
        f.append(seg((ox + ax * s, ay * s, 0), (ox + bx * s, by * s, 0)))
        f.append(seg((ox, ay * s, ax * s), (ox, by * s, bx * s)))
    return {"data": f}


def rock(ox=0.0, s=1.0, seed=0):
    """Boulders with real variety: flat slabs, tall spikes, wide lumps,
    occasionally a twin lump. Crossed profiles + waist ring."""
    rng = random.Random(seed)
    n = rng.randrange(6, 10)
    asp = rng.uniform(0.45, 1.3)      # flat .. tall
    wid = rng.uniform(1.0, 1.5)
    prof = []
    for k in range(n):
        a = math.pi * 2 * k / n + math.pi / n
        r = 0.5 + rng.uniform(-0.15, 0.22)
        px = wid * r * math.cos(a)
        py = min(0.0, (-0.34 + 0.62 * r * math.sin(a)) * asp)
        prof.append((px, py))
    parts = [(2, prof)]
    if rng.random() < 0.35:           # companion lump beside the main rock
        off = rng.uniform(0.6, 0.9) * (1 if rng.random() < 0.5 else -1)
        parts.append((2, [(off + 0.5 * px, 0.45 * py) for px, py in prof]))
    ring = (-0.28 * asp, (0.55 + rng.uniform(-0.05, 0.12)) * wid)
    return _tree_cross(ox, s, parts, [ring])

def seg(p1, p2):
    return q(0, [list(p1), list(p2)])


def chain(pts):
    return [seg(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]


def pylon(ox=0.0, h=4.6):
    """Transmission tower: proper 4-legged lattice (tapering in x and z)."""
    f = []
    w0, wt, d0, dt = 0.95, 0.22, 0.55, 0.14

    def wat(y):
        return w0 + (wt - w0) * (-y / h)

    def dat(y):
        return d0 + (dt - d0) * (-y / h)
    ys = [0, -0.9, -1.8, -2.7, -3.6, -h]
    for ya, yb in zip(ys, ys[1:]):
        wa, wb, da, db = wat(ya), wat(yb), dat(ya), dat(yb)
        for zsgn in (1, -1):
            za, zb = da * zsgn, db * zsgn
            f += [seg((ox - wa, ya, za), (ox - wb, yb, zb)),
                  seg((ox + wa, ya, za), (ox + wb, yb, zb)),
                  seg((ox - wa, ya, za), (ox + wb, yb, zb)),
                  seg((ox + wa, ya, za), (ox - wb, yb, zb)),
                  seg((ox - wb, yb, zb), (ox + wb, yb, zb))]
        f += [seg((ox - wb, yb, db), (ox - wb, yb, -db)),
              seg((ox + wb, yb, db), (ox + wb, yb, -db))]
    for ay, aw in ((-3.1, 1.15), (-3.9, 0.85)):
        dz = dat(ay) * 0.8
        for zsgn in (1, -1):
            f.append(seg((ox - aw, ay, dz * zsgn), (ox + aw, ay, dz * zsgn)))
        f += [seg((ox - aw, ay, dz), (ox - aw, ay, -dz)),
              seg((ox + aw, ay, dz), (ox + aw, ay, -dz)),
              seg((ox - aw + 0.08, ay, dz), (ox - aw + 0.08, ay + 0.22, dz)),
              seg((ox + aw - 0.08, ay, dz), (ox + aw - 0.08, ay + 0.22, dz))]
    return {"data": f}

def truss_bridge(ox=0.0, span=6.2, h=1.15, deck_y=-0.95, n=6, hw=0.5):
    """Truss bridge: two parallel trusses + deck cross-beams + top laterals."""
    x0, x1 = ox - span / 2, ox + span / 2
    ty = deck_y - h
    f = []
    step = (span - 1.0) / n
    for z in (-hw, hw):
        f += [seg((x0, deck_y, z), (x1, deck_y, z)),
              seg((x0, deck_y + 0.14, z), (x1, deck_y + 0.14, z)),
              seg((x0 + 0.5, ty, z), (x1 - 0.5, ty, z)),
              seg((x0, deck_y, z), (x0 + 0.5, ty, z)),
              seg((x1, deck_y, z), (x1 - 0.5, ty, z))]
        for k in range(n + 1):
            x = x0 + 0.5 + step * k
            f.append(seg((x, deck_y, z), (x, ty, z)))
            if k < n:
                if k % 2 == 0:
                    f.append(seg((x, deck_y, z), (x + step, ty, z)))
                else:
                    f.append(seg((x, ty, z), (x + step, deck_y, z)))
    for k in range(n + 1):
        x = x0 + 0.5 + step * k
        f += [seg((x, deck_y, -hw), (x, deck_y, hw)),
              seg((x, ty, -hw), (x, ty, hw))]
    f += box(x0 + 0.3, 0, 0.5, -deck_y - 0.14, 1.15, 2, 2)
    f += box(x1 - 0.3, 0, 0.5, -deck_y - 0.14, 1.15, 2, 2)
    return {"data": f}

def crane(ox=0.0, h=4.3, jib=3.3):
    """Tower crane: square lattice mast + triangular lattice jib + cables."""
    f = []
    m = 0.2
    ys = [0, -0.72, -1.44, -2.16, -2.88, -3.6, -h]
    for ya, yb in zip(ys, ys[1:]):
        for zsgn in (1, -1):
            z = m * zsgn
            f += [seg((ox - m, ya, z), (ox - m, yb, z)),
                  seg((ox + m, ya, z), (ox + m, yb, z)),
                  seg((ox - m, ya, z), (ox + m, yb, z))]
        f += [seg((ox - m, yb, m), (ox - m, yb, -m)),
              seg((ox + m, yb, m), (ox + m, yb, -m)),
              seg((ox - m, yb, m), (ox + m, yb, m)),
              seg((ox - m, yb, -m), (ox + m, yb, -m))]
    jy = -h
    tip, back = ox + jib, ox - 1.3
    for zsgn in (1, -1):
        z = 0.16 * zsgn
        f.append(seg((ox - m, jy, z), (tip, jy, z)))
    f.append(seg((ox, jy - 0.3, 0), (tip - 0.1, jy, 0)))
    steps = 6
    for k in range(steps):
        xa = ox + (tip - ox) * k / steps
        xb = ox + (tip - ox) * (k + 1) / steps
        f += [seg((xa, jy, 0.16), (xb, jy, -0.16)),
              seg((xa, jy - 0.3 * (1 - k / steps), 0),
                  (xb, jy, 0.16 if k % 2 else -0.16))]
    f += [seg((ox, jy, 0.16), (back, jy, 0.16)),
          seg((ox, jy, -0.16), (back, jy, -0.16)),
          seg((back, jy, 0.16), (back, jy, -0.16))]
    f += box(back + 0.25, 0, 0.5, 0.45, 0.6, 2, 2, y0=jy + 0.5)
    apex = (ox, jy - 0.55, 0)
    f += [seg((ox - m, jy, 0), apex), seg((ox + m, jy, 0), apex),
          seg(apex, (tip - 0.05, jy, 0)), seg(apex, (back + 0.1, jy, 0))]
    hx = ox + jib * 0.62
    f += [seg((hx, jy, 0), (hx, jy + 1.6, 0)),
          seg((hx, jy + 1.6, 0), (hx + 0.12, jy + 1.75, 0))]
    return {"data": f}

def ferris_wheel(ox=0.0, r=1.85, ang=0.0, hw=0.38, gondolas=True):
    """Ferris wheel: two parallel rims + spokes, tie rods, 3D gondolas."""
    cy = -r - 0.6
    f = []
    for zsgn in (1, -1):
        z = hw * zsgn
        f += [seg((ox - 1.15, 0, z), (ox, cy, z)),
              seg((ox + 1.15, 0, z), (ox, cy, z))]
    f.append(seg((ox, cy, hw), (ox, cy, -hw)))
    for z in (hw, -hw):
        ring = [(ox + r * math.cos(a), cy + r * math.sin(a), z)
                for a in [math.pi * 2 * k / 22 for k in range(22)]]
        f.append(q(0, ring))
    tips = []
    for k in range(8):
        a = ang + math.pi * 2 * k / 8
        px, py = ox + r * math.cos(a), cy + r * math.sin(a)
        for z in (hw, -hw):
            f.append(seg((ox, cy, z), (px, py, z)))
        f.append(seg((px, py, hw), (px, py, -hw)))
        tips.append((px, py))
    for px, py in tips:
        f += box(px, 0, 0.26, 0.3, 0.3, 1, 2, y0=py + 0.36)
    return {"data": f}

def wind_turbine(ox=0.0, h=3.5, ang=0.35):
    """Wind turbine: 4-edged tapering pole + nacelle box + flat rotor."""
    f = []
    for xs in (-1, 1):
        for zs in (-1, 1):
            f.append(seg((ox + 0.10 * xs, 0, 0.10 * zs),
                         (ox + 0.035 * xs, -h, 0.035 * zs)))
    base = [(ox + 0.12 * math.cos(a), 0, 0.12 * math.sin(a))
            for a in [math.pi / 4 + math.pi / 2 * k for k in range(4)]]
    f.append(q(0, base))
    f += box(ox, 0, 0.28, 0.16, 0.24, 2, 2, y0=-h)
    for k in range(3):
        a = ang + math.pi * 2 * k / 3
        dx, dy = math.cos(a), math.sin(a)
        px, py = -dy, dx
        L, wb = 1.45, 0.09
        f.append(q(1, [(ox + px * wb / 2, -h - 0.08 + py * wb / 2, 0.13),
                       (ox - px * wb / 2, -h - 0.08 - py * wb / 2, 0.13),
                       (ox + dx * L, -h - 0.08 + dy * L, 0.13)]))
    return {"data": f}

def train(ox=0.0, cars=2, rails=True):
    """Train: 3D cars, wheels and rails on both sides, sleepers, pantograph."""
    f = []
    if rails:
        for z in (-0.46, 0.46):
            f += [seg((ox - 4.6, -0.06, z), (ox + 4.6, -0.06, z)),
                  seg((ox - 4.6, -0.01, z), (ox + 4.6, -0.01, z))]
        x = ox - 4.4
        while x < ox + 4.4:
            f.append(seg((x, 0, -0.62), (x, 0, 0.62)))
            x += 0.8
    for c in range(cars):
        cx = ox + (c - (cars - 1) / 2) * 2.95
        f += box(cx, 0, 2.75, 0.8, 0.9, 1, 2, y0=-0.22)
        f += windows(cx, 0.46, 2.4, -0.62, 1, 4, ww=0.4, wh=0.32)
        for wx in (cx - 1.0, cx - 0.55, cx + 0.55, cx + 1.0):
            for z in (-0.46, 0.46):
                ring = [(wx + 0.13 * math.cos(a), -0.13 + 0.13 * math.sin(a), z)
                        for a in [math.pi * 2 * k / 8 for k in range(8)]]
                f.append(q(0, ring))
    px = ox - (cars - 1) / 2 * 2.95
    for z in (-0.2, 0.2):
        f += [seg((px - 0.3, -1.02, z), (px, -1.3, z)),
              seg((px + 0.3, -1.02, z), (px, -1.3, z))]
    f.append(seg((px - 0.35, -1.32, -0.2), (px + 0.35, -1.32, 0.2)))
    return {"data": f}

def crossing(ox=0.0):
    """Railroad crossing: pole (two edges), X sign, lamps, striped barrier."""
    f = [seg((ox - 0.04, 0, 0.04), (ox - 0.04, -2.1, 0.04)),
         seg((ox + 0.04, 0, -0.04), (ox + 0.04, -2.1, -0.04)),
         q(0, [(ox + 0.14 * math.cos(a), 0, 0.14 * math.sin(a))
               for a in [math.pi * 2 * k / 8 for k in range(8)]])]
    for sgn in (-1, 1):
        f.append(q(2, [(ox - 0.42, -2.1 + 0.1 * sgn - 0.05, 0),
                       (ox + 0.42, -2.1 - 0.1 * sgn - 0.05, 0),
                       (ox + 0.42, -2.1 - 0.1 * sgn + 0.05, 0),
                       (ox - 0.42, -2.1 + 0.1 * sgn + 0.05, 0)]))
    for sgn in (-1, 1):
        ring = [(ox + 0.18 * sgn + 0.09 * math.cos(a),
                 -1.62 + 0.09 * math.sin(a), 0)
                for a in [math.pi * 2 * k / 8 for k in range(8)]]
        f.append(q(0, ring))
    bx0, by0 = ox + 0.06, -1.3
    bx1, by1 = ox + 1.9, -0.55
    for t0 in [i / 4 for i in range(4)]:
        t1 = t0 + 0.25
        mat = 5 if int(t0 * 4) % 2 == 0 else 0
        f.append(q(mat, [(bx0 + (bx1 - bx0) * t0, by0 + (by1 - by0) * t0 - 0.045, 0),
                         (bx0 + (bx1 - bx0) * t1, by0 + (by1 - by0) * t1 - 0.045, 0),
                         (bx0 + (bx1 - bx0) * t1, by0 + (by1 - by0) * t1 + 0.045, 0),
                         (bx0 + (bx1 - bx0) * t0, by0 + (by1 - by0) * t0 + 0.045, 0)]))
    return {"data": f}

def constellation(ox=0.0, oy=-4.6, s=1.0, oz=0.0):
    """Connected stars with real depth — rotates like a mobile."""
    pts = [(-1.6, -0.2, 0.5), (-0.8, 0.25, -0.6), (0.0, 0.0, 0.2),
           (0.6, -0.6, -0.4), (1.4, -0.45, 0.6), (1.1, 0.35, -0.3)]
    world = [(ox + px * s, oy + py * s, oz + pz * s) for px, py, pz in pts]
    f = chain(world) + [seg(world[2], world[5])]
    for x, y, z in world:
        r = 0.09
        f += [seg((x - r, y, z), (x + r, y, z)),
              seg((x, y - r, z), (x, y + r, z)),
              seg((x, y, z - r), (x, y, z + r))]
    return {"data": f}

def water_tower(ox=0.0):
    """Water tower: 4 braced legs, octagonal prism tank, cone roof."""
    f = []
    for xs in (-1, 1):
        for zs in (-1, 1):
            f.append(seg((ox + 0.6 * xs, 0, 0.45 * zs),
                         (ox + 0.4 * xs, -2.1, 0.3 * zs)))
    for zs in (-1, 1):
        f += [seg((ox - 0.6, 0, 0.45 * zs), (ox + 0.4, -2.1, 0.3 * zs)),
              seg((ox + 0.6, 0, 0.45 * zs), (ox - 0.4, -2.1, 0.3 * zs))]
    for yy, wl, dl in ((-1.0, 0.5, 0.375), (-2.1, 0.4, 0.3)):
        f += [seg((ox - wl, yy, dl), (ox + wl, yy, dl)),
              seg((ox - wl, yy, -dl), (ox + wl, yy, -dl)),
              seg((ox - wl, yy, dl), (ox - wl, yy, -dl)),
              seg((ox + wl, yy, dl), (ox + wl, yy, -dl))]
    octa = [math.pi * 2 * k / 8 + math.pi / 8 for k in range(8)]
    top_r, bot_y, top_y = 0.72, -2.15, -3.25
    bot = [(ox + top_r * math.cos(a), bot_y, top_r * math.sin(a)) for a in octa]
    top = [(ox + top_r * math.cos(a), top_y, top_r * math.sin(a)) for a in octa]
    f += [q(0, bot), q(0, top)]
    for pb, pt in zip(bot, top):
        f.append(seg(pb, pt))
    apex = (ox, -3.85, 0)
    for pt in top[::2]:
        f.append(seg(pt, apex))
    return {"data": f}

def lighthouse(ox=0.0):
    """Lighthouse: octagonal frustum tower, band rings, lantern, beams."""
    octa = [math.pi * 2 * k / 8 + math.pi / 8 for k in range(8)]

    def ring(y, r):
        return [(ox + r * math.cos(a), y, r * math.sin(a)) for a in octa]
    f = [q(0, ring(0, 0.55)), q(0, ring(-2.5, 0.32))]
    for pb, pt in zip(ring(0, 0.55)[::2], ring(-2.5, 0.32)[::2]):
        f.append(seg(pb, pt))
    for yy, rr_ in ((-0.85, 0.47), (-1.7, 0.39)):
        f.append(q(0, ring(yy, rr_)))
    f += box(ox, 0, 0.55, 0.4, 0.5, 5, 2, y0=-2.5)
    dome = ring(-2.9, 0.3)
    apex = (ox, -3.32, 0)
    f.append(q(0, dome))
    for pt in dome[::2]:
        f.append(seg(pt, apex))
    for sgn in (-1, 1):
        f += [seg((ox + sgn * 0.3, -2.72, 0), (ox + sgn * 3.1, -3.35, 0)),
              seg((ox + sgn * 0.3, -2.68, 0), (ox + sgn * 3.1, -2.05, 0))]
    return {"data": f}

def street_lamp(ox=0.0, flip=1):
    """Street lamp: two-edged pole, arm, head box, ground light pool."""
    f = [seg((ox, 0, 0.05), (ox, -2.25, 0.02)),
         seg((ox, 0, -0.05), (ox, -2.25, -0.02)),
         q(0, [(ox + 0.12 * math.cos(a), 0, 0.12 * math.sin(a))
               for a in [math.pi * 2 * k / 8 for k in range(8)]]),
         seg((ox, -2.25, 0), (ox + 0.42 * flip, -2.25, 0)),
         seg((ox + 0.2 * flip, -2.25, 0), (ox, -2.05, 0))]
    hx = ox + 0.5 * flip
    f += box(hx, 0, 0.34, 0.17, 0.3, 5, 5, y0=-2.08)
    pool = [(hx + 0.6 * math.cos(a), 0, 0.5 + 0.35 * math.sin(a))
            for a in [math.pi * 2 * k / 10 for k in range(10)]]
    f.append(q(0, pool))
    return {"data": f}

def lamp_row(xs=(-3.6, 0.0, 3.6)):
    f = []
    for x in xs:
        f += street_lamp(x)["data"]
    return {"data": f}


def dimension_h(x0, x1, y, ext=0.35):
    """Horizontal blueprint dimension line with arrowheads and fake digits."""
    f = [seg((x0, y - ext, 0), (x0, y + 0.1, 0)),
         seg((x1, y - ext, 0), (x1, y + 0.1, 0)),
         seg((x0, y, 0), (x1, y, 0))]
    for xx, sgn in ((x0, 1), (x1, -1)):
        f += [seg((xx, y, 0), (xx + 0.14 * sgn, y - 0.06, 0)),
              seg((xx, y, 0), (xx + 0.14 * sgn, y + 0.06, 0))]
    mx = (x0 + x1) / 2
    for k in range(3):
        f.append(seg((mx - 0.14 + k * 0.12, y - 0.1, 0),
                     (mx - 0.10 + k * 0.12, y - 0.22, 0)))
    return f


def centerline_v(x, y0, y1):
    """Dash-dot center line (通り芯)."""
    f = []
    y = y0
    while y > y1:
        f.append(seg((x, y, 0), (x, max(y - 0.3, y1), 0)))
        yd = y - 0.42
        if yd > y1:
            f.append(seg((x, yd, 0), (x, yd - 0.04, 0)))
        y -= 0.58
    return f


def drafting(ox=0.0):
    """building_1 annotated like a blueprint: dimensions, center line, hatch."""
    f = list(building_1(ox)["data"])
    f += dimension_h(ox - 2.1, ox + 2.1, 0.55)
    f += dimension_h(ox - 2.6, ox - 2.6, 0)[:0]
    yv = [seg((ox - 2.75, 0.1, 0), (ox - 2.4, 0.1, 0)),
          seg((ox - 2.75, -3.24, 0), (ox - 2.4, -3.24, 0)),
          seg((ox - 2.6, 0.1, 0), (ox - 2.6, -3.24, 0)),
          seg((ox - 2.6, 0.1, 0), (ox - 2.66, -0.04, 0)),
          seg((ox - 2.6, 0.1, 0), (ox - 2.54, -0.04, 0)),
          seg((ox - 2.6, -3.24, 0), (ox - 2.66, -3.1, 0)),
          seg((ox - 2.6, -3.24, 0), (ox - 2.54, -3.1, 0))]
    f += yv
    f += centerline_v(ox, 0.4, -3.9)
    for k in range(4):
        f.append(seg((ox + 2.3 + k * 0.14, 0.05, 0),
                     (ox + 2.44 + k * 0.14, 0.45, 0)))
    return {"data": f}


def power_line(xs=(-4.5, 0.0, 4.5), h=2.4, sag=0.4, oz=0.0):
    """Utility poles (two-edged, with base ring and crossarm) + sagging wires."""
    f = []
    ytop = -h + 0.22
    for x in xs:
        f += [seg((x - 0.05, 0, oz + 0.05), (x - 0.03, -h, oz + 0.02)),
              seg((x + 0.05, 0, oz - 0.05), (x + 0.03, -h, oz - 0.02)),
              q(0, [(x + 0.14 * math.cos(a), 0, oz + 0.14 * math.sin(a))
                    for a in [math.pi * 2 * k / 8 for k in range(8)]]),
              seg((x - 0.42, -h + 0.30, oz), (x + 0.42, -h + 0.30, oz)),
              seg((x - 0.42, -h + 0.22, oz), (x + 0.42, -h + 0.22, oz)),
              seg((x - 0.42, -h + 0.30, oz), (x - 0.42, -h + 0.22, oz)),
              seg((x + 0.42, -h + 0.30, oz), (x + 0.42, -h + 0.22, oz))]
    for xa, xb in zip(xs, xs[1:]):
        for k in (0, 1):
            yo = ytop + 0.10 * k
            pts = [(xa + (xb - xa) * i / 12,
                    yo + sag * 4 * (i / 12) * (1 - i / 12), oz)
                   for i in range(13)]
            for i in range(12):
                f.append(q(0, [list(pts[i]), list(pts[i + 1])]))
    return {"data": f}

def power_ring(pts, h=6.0, sag=0.7, closed=True):
    """Tall poles at (x, z) waypoints, wires enclosing the space.
    Returns a list of (z_key, shape) pieces for painter sorting."""
    pieces = []
    n = len(pts)
    ytop = -h + 0.34
    for i, (x, z) in enumerate(pts):
        pa, pb = pts[(i - 1) % n], pts[(i + 1) % n]
        dx, dz = pb[0] - pa[0], pb[1] - pa[1]
        L = math.hypot(dx, dz) or 1.0
        ax, az = -dz / L, dx / L
        arm = 0.16 * h
        f = [seg((x - 0.07, 0, z + 0.07), (x - 0.045, -h, z + 0.03)),
             seg((x + 0.07, 0, z - 0.07), (x + 0.045, -h, z - 0.03)),
             q(0, [(x + 0.18 * math.cos(a), 0, z + 0.18 * math.sin(a))
                   for a in [math.pi * 2 * k / 8 for k in range(8)]]),
             seg((x - ax * arm, -h + 0.30, z - az * arm),
                 (x + ax * arm, -h + 0.30, z + az * arm)),
             seg((x - ax * arm, -h + 0.44, z - az * arm),
                 (x + ax * arm, -h + 0.44, z + az * arm)),
             seg((x - ax * arm, -h + 0.30, z - az * arm),
                 (x - ax * arm, -h + 0.44, z - az * arm)),
             seg((x + ax * arm, -h + 0.30, z + az * arm),
                 (x + ax * arm, -h + 0.44, z + az * arm))]
        pieces.append((z, {"data": f}))
    m = n if closed else n - 1
    for i in range(m):
        (xa, za), (xb, zb) = pts[i], pts[(i + 1) % n]
        f = []
        for k in (0, 1):
            yo = ytop + 0.14 * k
            w = [(xa + (xb - xa) * t, yo + sag * 4 * t * (1 - t),
                  za + (zb - za) * t) for t in [j / 14 for j in range(15)]]
            for j in range(14):
                f.append(q(0, [list(w[j]), list(w[j + 1])]))
        pieces.append((max(za, zb), {"data": f}))
    return pieces


def moon(ox=4.2, oy=-4.4, r=0.55, z=-3.0):
    pts = [(ox + r * math.cos(math.pi * 2 * k / 14),
            oy + r * math.sin(math.pi * 2 * k / 14), z) for k in range(14)]
    return {"data": [q(5, pts)]}


def ground(hx=14, zf=3.5, zb=-6):
    return {"data": [q(0, [(-hx, 0, zf), (hx, 0, zf),
                           (hx, 0, zb), (-hx, 0, zb)])]}


def setup_view(w, h, zoom, xoff=0.0, yoff=40.0):
    B.VIEW_W, B.VIEW_H = w, h
    B.VIEW_ZOOM, B.VIEW_XOFF, B.VIEW_YOFF = zoom, xoff, yoff
    B.EYE = (0.0, -50.0, 500.0)
    B.CAM_X, B.CAM_Y, B.CAM_Z = B._camera_basis()


def draw_scene(surf, shapes, style, seed):
    rng = random.Random(seed)
    for sh in shapes:
        B.draw_shape(surf, sh, style, MODELS["materials"], rng)


_STAR_CACHE = {}


def stars(surf, seed, w):
    """World-anchored sky stars: crosses on a far dome (r 160-280 world),
    projected with the CURRENT camera each call — they pan, parallax and
    zoom with the scene.  Wire taste, boiling strokes."""
    if seed not in _STAR_CACHE:
        rng = random.Random(seed)
        pts = []
        for _ in range(10):
            az = rng.uniform(0, math.pi * 2)
            el = rng.uniform(0.12, 0.95)
            R = rng.uniform(160.0, 280.0)
            arm = rng.uniform(2.2, 4.6)
            pts.append((R * math.cos(el) * math.sin(az), -R * math.sin(el),
                        R * math.cos(el) * math.cos(az), arm))
        _STAR_CACHE[seed] = pts
    srng = random.Random()
    for sx, sy, sz, arm in _STAR_CACHE[seed]:
        for dx, dy, dz in ((arm, 0, 0), (0, arm, 0), (0, 0, arm)):
            a = B.project((sx - dx) * B.M, (sy - dy) * B.M, (sz - dz) * B.M)
            b = B.project((sx + dx) * B.M, (sy + dy) * B.M, (sz + dz) * B.M)
            if not (a and b):
                continue
            if max(abs(a[0] - b[0]), abs(a[1] - b[1])) > 70:
                continue                    # too close to the camera
            if (max(a[0], b[0]) < -80 or min(a[0], b[0]) > surf.get_width() + 80
                    or max(a[1], b[1]) < -80
                    or min(a[1], b[1]) > surf.get_height() + 80):
                continue
            jitter_line(surf, (245, 245, 245), 2, a[0], a[1], b[0], b[1], srng)


def tile_sheet(items, out_name, prefix, font, zoom, yoff=40.0):
    style = B.STYLES["inverted-soft-jitter"]
    tiles = []
    for i, builder in enumerate(items):
        setup_view(TILE, TILE, zoom, 0.0, yoff)
        t = pygame.Surface((TILE, TILE))
        t.fill(style["bg"])
        stars(t, 60 + i, TILE)
        draw_scene(t, [ground(), builder()], style, 900 + i)
        t.blit(font.render(f"{prefix}{i + 1}", True, (245, 245, 245)), (24, 18))
        pygame.image.save(t, os.path.join(BG_DIR, f"{prefix}_{i + 1}.png"))
        tiles.append(t)
    cols = len(tiles)
    sheet = pygame.Surface((TILE * cols, TILE))
    for i, t in enumerate(tiles):
        sheet.blit(t, (i * TILE, 0))
    out = os.path.join(BG_DIR, out_name)
    pygame.image.save(sheet, out)
    print(f"saved {out}")


# ---- Miku vs background layout studies (16:9, mix style) ----
COMPS = [
    # (name, zoom, xoff, scene builder(), miku_x, miku_y, miku_W)
    ("comp_1", 0.78, -240, lambda: [ground(), building_2(-0.8), tree_1(2.6, 1.5)],
     0.70, 0.40, 210),
    ("comp_2", 0.58, 0, lambda: [ground(), building_5(1.6), tree_2(-2.8, 1.5),
                                 tree_3(4.6, 1.5)],
     0.30, 0.47, 130),
    ("comp_3", 0.66, 230, lambda: [ground(), building_1(1.8), tree_3(-1.8, 1.3)],
     0.22, 0.34, 330),
]


def render_comps(font):
    style = B.STYLES["inverted-soft-jitter"]
    W, H = 1280, 720
    for name, zoom, xoff, scene, mx, my, mw in COMPS:
        setup_view(W, H, zoom, xoff, 20.0)
        surf = pygame.Surface((W, H))
        surf.fill(style["bg"])
        stars(surf, hash(name) % 1000, W)
        draw_scene(surf, scene(), style, 1300 + zoom * 100)
        d = DS.D(surf, MIKU_V, seed=77)
        DS.draw_miku(d, W * mx, H * my, mw)
        surf.blit(font.render(name, True, (245, 245, 245)), (24, 18))
        out = os.path.join(MOVIE_DIR, f"{name}.png")
        pygame.image.save(surf, out)
        print(f"saved {out}")


# ---- inorganic / industrial motifs (無機質) ----
def danchi(ox=0.0):
    """Danchi slab: long block, wide sash windows, balcony rails, stair
    towers, roof tank + antenna — plus ONE flared eave cap as the only
    borrowed accent from the 1251077 grammar."""
    f = []
    bx, dz = ox, 0.0
    zf = dz + 0.66
    f += box(bx, dz, 6.8, 2.9, 1.3)
    for ty in (-0.5, -1.4, -2.3):              # wide sliding windows, 4 bays
        for k in range(4):
            cx = bx - 2.25 + k * 1.5
            f.append(q(5, [(cx - 0.42, ty + 0.19, zf),
                           (cx + 0.42, ty + 0.19, zf),
                           (cx + 0.42, ty - 0.19, zf),
                           (cx - 0.42, ty - 0.19, zf)]))
    for ty in (-0.95, -1.85, -2.75):           # balcony rails, lines only
        f.append(seg((bx - 3.3, ty, zf + 0.01), (bx + 3.3, ty, zf + 0.01)))
    for tx in (-2.9, 2.9):                     # stair towers with slits
        f += box(bx + tx, dz + 0.25, 0.85, 3.25, 1.1, 2, 2)
        f.append(q(5, [(bx + tx - 0.08, -1.4, dz + 0.81),
                       (bx + tx + 0.08, -1.4, dz + 0.81),
                       (bx + tx + 0.08, -2.1, dz + 0.81),
                       (bx + tx - 0.08, -2.1, dz + 0.81)]))
    # the single accent: a thin flared eave cap on the roofline
    x0, x1 = bx - 3.4, bx + 3.4
    xf0, xf1 = bx - 3.95, bx + 3.95
    f += [q(4, [(x0, -2.9, dz + 0.65), (x1, -2.9, dz + 0.65),
                (xf1, -3.14, dz + 0.95), (xf0, -3.14, dz + 0.95)]),
          q(4, [(x0, -2.9, dz - 0.65), (x1, -2.9, dz - 0.65),
                (xf1, -3.14, dz - 0.95), (xf0, -3.14, dz - 0.95)]),
          q(4, [(xf0, -3.14, dz - 0.95), (xf1, -3.14, dz - 0.95),
                (xf1, -3.14, dz + 0.95), (xf0, -3.14, dz + 0.95)])]
    f += box(bx - 1.3, dz, 0.65, 0.45, 0.65, 2, 2, y0=-3.14)
    f += [seg((bx + 1.8, -3.14, dz), (bx + 1.8, -3.9, dz)),
          seg((bx + 1.65, -3.72, dz), (bx + 1.95, -3.72, dz))]
    return {"data": f}

def office(ox=0.0):
    """Faceless office tower: uniform grid, roof plant, antenna."""
    f = box(ox, 0, 2.5, 4.2, 2.0)
    f += windows(ox, 1.02, 2.1, -3.95, 5, 3, ww=0.34, wh=0.42)
    f += box(ox + 0.55, 0, 0.9, 0.45, 0.9, 2, 2, y0=-4.2)
    f += [seg((ox - 0.6, -4.2, 0), (ox - 0.6, -5.0, 0)),
          seg((ox - 0.75, -4.75, 0), (ox - 0.45, -4.75, 0))]
    return {"data": f}


def warehouse(ox=0.0):
    """Long low warehouse: shallow gable, big shutter with slats."""
    f = box(ox, 0, 4.6, 1.6, 2.8)
    f += gable(ox, 0, 5.0, 3.0, -1.6, 0.5)
    f += door(ox - 1.1, 1.42, dw=1.7, dh=1.25, mat=5)
    for k in range(4):
        y = -0.22 - k * 0.28
        f.append(seg((ox - 1.9, y, 1.44), (ox - 0.25, y, 1.44)))
    f += windows(ox + 1.3, 1.42, 1.4, -1.42, 1, 2, ww=0.4, wh=0.3)
    return {"data": f}


def silo(ox=0.0):
    """Octagonal silo: prism, dome, side pipe, ladder."""
    octa = [math.pi * 2 * k / 8 + math.pi / 8 for k in range(8)]

    def ring(y, r):
        return [(ox + r * math.cos(a), y, r * math.sin(a)) for a in octa]
    f = [q(0, ring(0, 0.8)), q(0, ring(-2.7, 0.8)), q(0, ring(-1.35, 0.8))]
    for pb, pt in zip(ring(0, 0.8)[::2], ring(-2.7, 0.8)[::2]):
        f.append(seg(pb, pt))
    dome = ring(-2.7, 0.62)
    apex = (ox, -3.35, 0)
    for pt in dome[::2]:
        f.append(seg(pt, apex))
    f += [seg((ox + 0.8, -0.4, 0), (ox + 1.35, -0.4, 0)),
          seg((ox + 1.35, -0.4, 0), (ox + 1.35, 0, 0)),
          seg((ox - 0.95, 0, 0), (ox - 0.95, -2.6, 0))]
    for k in range(6):
        y = -0.3 - k * 0.42
        f.append(seg((ox - 1.05, y, 0), (ox - 0.85, y, 0)))
    return {"data": f}


def factory(ox=0.0):
    """Factory hall with sawtooth roof + two chimneys + pipe."""
    f = box(ox - 0.7, 0, 3.2, 1.5, 2.2)
    for k in range(2):
        x0 = ox - 2.3 + k * 1.6
        f.append(q(4, [(x0, -1.5, 0.9), (x0 + 1.6, -1.5, 0.9),
                       (x0 + 1.6, -2.15, 0.9)]))
        f.append(q(4, [(x0, -1.5, -0.9), (x0 + 1.6, -1.5, -0.9),
                       (x0 + 1.6, -2.15, -0.9)]))
        f.append(seg((x0 + 1.6, -2.15, 0.9), (x0 + 1.6, -2.15, -0.9)))
    f += box(ox + 1.55, 0.3, 0.42, 3.1, 0.42, 2, 2)
    f += box(ox + 2.25, -0.3, 0.36, 2.6, 0.36, 2, 2)
    f += [seg((ox + 1.55, -1.5, 0), (ox + 0.9, -1.5, 0)),
          q(0, [(ox + 1.55 + 0.3 * math.cos(a), -3.1, 0.3 * math.sin(a))
                for a in [math.pi * 2 * k / 8 for k in range(8)]])]
    return {"data": f}


def containers(ox=0.0):
    """Stacked shipping containers with corrugation lines."""
    f = []
    spots = [(-1.05, 0, 0), (1.05, 0, 0.2), (0.0, -0.95, 0.1)]
    for cx, cy, cz in spots:
        f += box(ox + cx, cz, 2.0, 0.95, 1.0, 1, 2, y0=cy)
        for k in range(5):
            x = ox + cx - 0.75 + k * 0.375
            f.append(seg((x, cy - 0.08, cz + 0.51), (x, cy - 0.87, cz + 0.51)))
    return {"data": f}


INORGANIC = [danchi, office, warehouse, silo, factory, containers]


# ---- lyric motifs: 絡み合い (entangled) / 交差 (crossing) ----
def entwine_wires(ox=0.0):
    """Two wires leaving two poles and twisting around each other."""
    f = []
    for sgn in (-1, 1):
        x = ox + sgn * 2.5
        f += [seg((x - 0.05, 0, 0.05), (x - 0.03, -2.4, 0.02)),
              seg((x + 0.05, 0, -0.05), (x + 0.03, -2.4, -0.02)),
              seg((x - 0.3, -2.15, 0), (x + 0.3, -2.15, 0))]
    n = 44
    for phase in (0.0, math.pi):
        pts = []
        for k in range(n + 1):
            t = k / n
            r = 0.34 * math.sin(math.pi * t)
            th = phase + t * math.pi * 5
            pts.append((ox - 2.2 + 4.4 * t, -2.15 + r * math.cos(th),
                        r * math.sin(th)))
        f += chain(pts)
    return {"data": f}


def double_helix(ox=0.0):
    """Vertical double helix with rungs — deeply intertwined."""
    f = []
    n = 40
    strands = []
    for phase in (0.0, math.pi):
        pts = []
        for k in range(n + 1):
            t = k / n
            th = phase + t * math.pi * 4
            pts.append((ox + 0.5 * math.cos(th), -0.25 - 2.6 * t,
                        0.5 * math.sin(th)))
        strands.append(pts)
        f += chain(pts)
    for k in range(0, n + 1, 5):
        f.append(seg(strands[0][k], strands[1][k]))
    return {"data": f}


def trefoil(ox=0.0):
    """Trefoil knot: one strand, knotted forever."""
    n = 66
    pts = []
    for k in range(n + 1):
        t = math.pi * 2 * k / n
        pts.append((ox + 0.34 * (math.sin(t) + 2 * math.sin(2 * t)),
                    -1.55 + 0.34 * (math.cos(t) - 2 * math.cos(2 * t)),
                    0.34 * -math.sin(3 * t)))
    return {"data": chain(pts)}


def linked_rings(ox=0.0):
    """Two interlocked rings in perpendicular planes."""
    f = []
    n = 28
    for k in range(n):
        a0 = math.pi * 2 * k / n
        a1 = math.pi * 2 * (k + 1) / n
        f.append(seg((ox - 0.38 + 0.75 * math.cos(a0),
                      -1.55 + 0.75 * math.sin(a0), 0),
                     (ox - 0.38 + 0.75 * math.cos(a1),
                      -1.55 + 0.75 * math.sin(a1), 0)))
        ca, sa = math.cos(1.0), math.sin(1.0)
        f.append(seg((ox + 0.38 + 0.75 * math.cos(a0) * ca,
                      -1.55 + 0.75 * math.sin(a0),
                      0.75 * math.cos(a0) * sa),
                     (ox + 0.38 + 0.75 * math.cos(a1) * ca,
                      -1.55 + 0.75 * math.sin(a1),
                      0.75 * math.cos(a1) * sa)))
    return {"data": f}


def braid(ox=0.0):
    """Two strands crossing over and over — like two twin-tails braided."""
    f = []
    n = 40
    for sgn in (-1, 1):
        pts = []
        for k in range(n + 1):
            t = k / n
            pts.append((ox + sgn * 0.32 * math.sin(math.pi * 3 * t),
                        -0.25 - 2.6 * t,
                        sgn * 0.14 * math.cos(math.pi * 3 * t)))
        f += chain(pts)
    return {"data": f}


def cross_wires(ox=0.0):
    """Wires from two pole pairs crossing in an X, a star at the junction."""
    f = []
    for x, z, h in ((-2.5, -0.9, 2.7), (2.5, 0.9, 2.2),
                    (-2.5, 0.9, 2.2), (2.5, -0.9, 2.7)):
        f += [seg((ox + x - 0.04, 0, z + 0.04), (ox + x - 0.03, -h, z + 0.02)),
              seg((ox + x + 0.04, 0, z - 0.04), (ox + x + 0.03, -h, z - 0.02))]
    for (xa, za, ya), (xb, zb, yb) in (
            ((-2.5, -0.9, -2.75), (2.5, 0.9, -1.5)),
            ((-2.5, 0.9, -1.5), (2.5, -0.9, -2.75))):
        pts = [(ox + xa + (xb - xa) * t, ya + (yb - ya) * t
                + 0.55 * 4 * t * (1 - t) * 0.35, za + (zb - za) * t)
               for t in [k / 16 for k in range(17)]]
        f += chain(pts)
    r = 0.16
    yj = -2.18
    f += [seg((ox - r, yj, 0), (ox + r, yj, 0)),
          seg((ox, yj - r, 0), (ox, yj + r, 0)),
          seg((ox - r * 0.7, yj - r * 0.7, 0), (ox + r * 0.7, yj + r * 0.7, 0)),
          seg((ox - r * 0.7, yj + r * 0.7, 0), (ox + r * 0.7, yj - r * 0.7, 0))]
    return {"data": f}


def orbits(ox=0.0):
    """Two tilted orbits sharing a center, never letting go."""
    f = []
    n = 30
    for tilt in (0.6, -0.6):
        ca, sa = math.cos(tilt), math.sin(tilt)
        pts = []
        for k in range(n + 1):
            a = math.pi * 2 * k / n
            x, y, z = 1.05 * math.cos(a), 0.0, 0.55 * math.sin(a)
            pts.append((ox + x * ca, -1.55 + x * sa * 0.6 + z * sa,
                        z * ca - y))
        f += chain(pts)
    for sgn in (-1, 1):
        px = ox + sgn * 0.95
        py = -1.55 + sgn * 0.35
        for r in (0.09,):
            f += [seg((px - r, py, 0), (px + r, py, 0)),
                  seg((px, py - r, 0), (px, py + r, 0))]
    return {"data": f}


def contrail_x(ox=0.0):
    """Two contrails crossing in the sky, tiny paper planes at the tips."""
    f = []
    for sgn in (-1, 1):
        x0, y0 = ox - 2.7 * sgn, -0.6 - (0.1 if sgn > 0 else 0)
        x1, y1 = ox + 2.7 * sgn, -2.7 + (0.15 if sgn > 0 else 0)
        for off in (-0.035, 0.035):
            f.append(seg((x0, y0 + off, 0), (x1, y1 + off, 0)))
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy)
        ux, uy = dx / L, dy / L
        px, py = -uy, ux
        f.append(q(1, [(x1, y1, 0),
                       (x1 - ux * 0.34 + px * 0.12, y1 - uy * 0.34 + py * 0.12, 0),
                       (x1 - ux * 0.34 - px * 0.12, y1 - uy * 0.34 - py * 0.12, 0)]))
    return {"data": f}


LYRICS = [
    ("entwine", entwine_wires), ("helix", double_helix),
    ("trefoil", trefoil), ("rings", linked_rings),
    ("braid", braid), ("crosswire", cross_wires),
    ("orbits", orbits), ("contrail", contrail_x),
]


def lyric_sheet(font, cols=4, items=None, out_name="lyrics_sheet.png"):
    style = B.STYLES["inverted-soft-jitter"]
    tiles = []
    for i, (name, build) in enumerate(items or LYRICS):
        setup_view(TILE, TILE, 1.45, 0.0, 60)
        t = pygame.Surface((TILE, TILE))
        t.fill(style["bg"])
        stars(t, 500 + i, TILE)
        draw_scene(t, [build()], style, 4000 + i)
        t.blit(font.render(name, True, (245, 245, 245)), (24, 18))
        pygame.image.save(t, os.path.join(BG_DIR, f"lyric_{name}.png"))
        tiles.append(t)
    rows = (len(tiles) + cols - 1) // cols
    sheet = pygame.Surface((TILE * cols, TILE * rows))
    sheet.fill(style["bg"])
    for i, t in enumerate(tiles):
        sheet.blit(t, ((i % cols) * TILE, (i // cols) * TILE))
    out = os.path.join(BG_DIR, out_name)
    pygame.image.save(sheet, out)
    print(f"saved {out}")


# ---- himitsu motifs: lyric-derived, second batch ----
def key_motif(ox=0.0):
    f = []
    ring = [(ox - 1.25 + 0.45 * math.cos(a), -1.55 + 0.45 * math.sin(a), 0)
            for a in [math.pi * 2 * k / 12 for k in range(12)]]
    f.append(q(0, ring))
    for dy in (-0.05, 0.05):
        f.append(seg((ox - 0.8, -1.55 + dy, 0), (ox + 1.35, -1.55 + dy, 0)))
    f += [seg((ox + 1.35, -1.55, 0), (ox + 1.35, -1.15, 0)),
          seg((ox + 1.05, -1.55, 0), (ox + 1.05, -1.25, 0)),
          seg((ox + 0.8, -1.55, 0), (ox + 0.8, -1.32, 0))]
    return {"data": f}


def padlock(ox=0.0):
    f = [q(1, rect_pts_xy(ox, -1.25, 1.5, 1.15))]
    sh = [(ox + 0.52 * math.cos(a), -1.85 + 0.52 * math.sin(a), 0)
          for a in [math.pi - math.pi * k / 8 for k in range(9)]]
    f += chain(sh)
    f += [seg((ox - 0.52, -1.85, 0), (ox - 0.52, -1.83 + 0.0, 0)),
          q(0, [(ox + 0.12 * math.cos(a), -1.3 + 0.12 * math.sin(a), 0)
                for a in [math.pi * 2 * k / 8 for k in range(8)]]),
          seg((ox, -1.4, 0), (ox, -1.0, 0))]
    return {"data": f}


def envelope(ox=0.0):
    f = [q(1, rect_pts_xy(ox, -1.5, 2.3, 1.45))]
    f += [seg((ox - 1.15, -2.22, 0), (ox, -1.45, 0)),
          seg((ox + 1.15, -2.22, 0), (ox, -1.45, 0))]
    sealr = [(ox + 0.22 * math.cos(a), -1.45 + 0.22 * math.sin(a), 0)
             for a in [math.pi * 2 * k / 10 for k in range(10)]]
    f.append(q(5, sealr))
    f += [seg((ox - 0.1, -1.55, 0), (ox + 0.1, -1.35, 0)),
          seg((ox - 0.1, -1.35, 0), (ox + 0.1, -1.55, 0))]
    return {"data": f}


def bulb(ox=0.0, rays=True):
    glass = [(ox + 0.72 * math.cos(a), -1.95 + 0.72 * math.sin(a), 0)
             for a in [math.pi * 2 * k / 14 for k in range(14)]]
    f = [q(0, glass)]
    f += [seg((ox - 0.28, -1.3, 0), (ox - 0.2, -0.95, 0)),
          seg((ox + 0.28, -1.3, 0), (ox + 0.2, -0.95, 0)),
          seg((ox - 0.2, -0.95, 0), (ox + 0.2, -0.95, 0)),
          seg((ox - 0.2, -0.82, 0), (ox + 0.2, -0.82, 0)),
          seg((ox - 0.18, -0.7, 0), (ox + 0.18, -0.7, 0))]
    f += chain([(ox - 0.25, -1.35, 0), (ox - 0.12, -1.75, 0),
                (ox, -1.55, 0), (ox + 0.12, -1.78, 0), (ox + 0.25, -1.35, 0)])
    if rays:
        for k in range(6):
            a = math.pi * 2 * k / 6 + 0.3
            f.append(seg((ox + 0.95 * math.cos(a), -1.95 + 0.95 * math.sin(a), 0),
                         (ox + 1.25 * math.cos(a), -1.95 + 1.25 * math.sin(a), 0)))
    return {"data": f}


def mobius(ox=0.0):
    f = []
    n = 44
    pts_a, pts_b = [], []
    for k in range(n + 1):
        t = math.pi * 2 * k / n
        cxp = ox + 1.05 * math.cos(t)
        cyp = -1.55 + 0.42 * math.sin(t)
        czp = 0.45 * math.sin(t)
        wx = 0.26 * math.cos(t / 2)
        wy = 0.26 * math.sin(t / 2)
        pts_a.append((cxp + wx * 0.3, cyp + wy, czp + wx))
        pts_b.append((cxp - wx * 0.3, cyp - wy, czp - wx))
    f += chain(pts_a) + chain(pts_b)
    for k in range(0, n, 4):
        f.append(seg(pts_a[k], pts_b[k]))
    return {"data": f}


def balloon(ox=0.0):
    prof = []
    for k in range(10):
        a = math.pi * (k / 9.0)
        r = 0.95 * math.sin(a) ** 0.8 if a > 0 else 0.05
        prof.append((ox + 0.95 * math.cos(a + math.pi), -2.4 + 1.0 * -math.sin(a)))
    env = [(ox + 0.95 * math.cos(a), -2.3 + 0.95 * math.sin(a), 0)
           for a in [math.pi * 2 * k / 14 for k in range(14)]]
    f = [q(0, env)]
    f += [seg((ox - 0.35, -1.42, 0), (ox - 0.2, -0.95, 0)),
          seg((ox + 0.35, -1.42, 0), (ox + 0.2, -0.95, 0)),
          seg((ox - 0.5, -1.6, 0), (ox - 0.28, -1.0, 0)),
          seg((ox + 0.5, -1.6, 0), (ox + 0.28, -1.0, 0))]
    f += box(ox, 0, 0.55, 0.4, 0.5, 1, 2, y0=-0.6)
    f.append(seg((ox, -3.25, 0), (ox, -2.95, 0)))
    f += chain([(ox - 0.6, -2.95, 0), (ox - 0.3, -3.15, 0), (ox, -3.2, 0),
                (ox + 0.3, -3.15, 0), (ox + 0.6, -2.95, 0)])
    return {"data": f}


def float_house(ox=0.0):
    h = building_1(ox)
    f = []
    for face in h["data"]:
        vs = [[v[0] * 0.55 + ox * 0.45, v[1] * 0.55 - 1.15, v[2] * 0.55]
              for v in face["vertices"]]
        f.append({"mat": face.get("mat"), "vertices": vs})
    sh = [(ox + 1.15 * math.cos(a), -0.02, 0.45 * math.sin(a))
          for a in [math.pi * 2 * k / 12 for k in range(12)]]
    f.append(q(0, sh))
    return {"data": f}


def mirror(ox=0.0):
    frame = [(ox + 0.62 * math.cos(a), -1.75 + 1.0 * math.sin(a), 0)
             for a in [math.pi * 2 * k / 16 for k in range(16)]]
    inner = [(ox + 0.52 * math.cos(a), -1.75 + 0.88 * math.sin(a), 0)
             for a in [math.pi * 2 * k / 16 for k in range(16)]]
    f = [q(0, frame), q(0, inner)]
    f += [seg((ox - 0.45, -0.9, 0), (ox - 0.7, 0, 0)),
          seg((ox + 0.45, -0.9, 0), (ox + 0.7, 0, 0)),
          seg((ox - 0.35, 0, 0), (ox - 0.85, 0, 0)),
          seg((ox + 0.35, 0, 0), (ox + 0.85, 0, 0))]
    return {"data": f}


def rect_pts_xy(cx, cy, w, h):
    return [(cx - w / 2, cy - h / 2, 0), (cx + w / 2, cy - h / 2, 0),
            (cx + w / 2, cy + h / 2, 0), (cx - w / 2, cy + h / 2, 0)]


HIMITSU = [
    ("key", key_motif), ("padlock", padlock), ("envelope", envelope),
    ("bulb", bulb), ("mobius", mobius), ("balloon", balloon),
    ("floathouse", float_house), ("mirror", mirror),
]


# ---- kashi2 motifs: lyric-derived, third batch ----
def stilt_house(ox=0.0):
    """「根拠のない暮らし」: a tiny house perched on one skinny stilt."""
    f = [seg((ox - 0.04, 0, 0), (ox + 0.02, -2.2, 0)),
         seg((ox + 0.05, 0, 0.04), (ox + 0.06, -2.2, 0.02)),
         seg((ox - 0.45, -1.15, 0), (ox + 0.03, -1.7, 0)),
         seg((ox + 0.5, -1.15, 0), (ox + 0.05, -1.7, 0))]
    hx = ox + 0.12
    f += box(hx, 0, 1.15, 0.8, 0.85, 1, 2, y0=-2.2)
    for zs in (0.425, -0.425):
        f.append(seg((hx - 0.62, -3.0, zs), (hx, -3.42, zs)))
        f.append(seg((hx + 0.62, -3.0, zs), (hx, -3.42, zs)))
    f.append(seg((hx, -3.42, 0.425), (hx, -3.42, -0.425)))
    f.append(q(0, [(hx - 0.18, -2.2, 0.43), (hx - 0.18, -2.62, 0.43),
                   (hx + 0.08, -2.62, 0.43), (hx + 0.08, -2.2, 0.43)]))
    for tx in (-0.55, 0.4, 0.75):
        f.append(seg((ox + tx, 0, 0.1), (ox + tx - 0.08, -0.18, 0.1)))
    return {"data": f}


def clothesline(ox=0.0):
    """「暮らし」: two poles, a sagging line, laundry drying."""
    f = []
    for xs in (-1.85, 1.85):
        f += [seg((ox + xs - 0.03, 0, 0), (ox + xs, -2.05, 0)),
              seg((ox + xs + 0.05, 0, 0.03), (ox + xs + 0.03, -2.05, 0.01)),
              seg((ox + xs - 0.3, -2.05, 0), (ox + xs + 0.3, -2.05, 0)),
              seg((ox + xs - 0.2, -1.75, 0), (ox + xs, -2.05, 0))]
    line = [(ox - 1.85 + 3.7 * k / 12,
             -2.05 + 0.28 * math.sin(math.pi * k / 12), 0) for k in range(13)]
    f += chain(line)
    # shirt / towel / pants hanging from the line
    def ly(x):
        return -2.05 + 0.28 * math.sin(math.pi * (x + 1.85) / 3.7)
    sx = ox - 0.95
    f.append(q(0, [(sx - 0.32, ly(-0.95) + 0.02, 0), (sx - 0.5, ly(-0.95) + 0.3, 0),
                   (sx - 0.36, ly(-0.95) + 0.42, 0), (sx - 0.24, ly(-0.95) + 0.26, 0),
                   (sx - 0.26, ly(-0.95) + 0.82, 0), (sx + 0.26, ly(-0.95) + 0.82, 0),
                   (sx + 0.24, ly(-0.95) + 0.26, 0), (sx + 0.36, ly(-0.95) + 0.42, 0),
                   (sx + 0.5, ly(-0.95) + 0.3, 0), (sx + 0.32, ly(-0.95) + 0.02, 0)]))
    tx = ox + 0.1
    f.append(q(0, [(tx - 0.26, ly(0.1), 0), (tx - 0.26, ly(0.1) + 0.62, 0),
                   (tx + 0.26, ly(0.1) + 0.62, 0), (tx + 0.26, ly(0.1), 0)]))
    f.append(seg((tx - 0.26, ly(0.1) + 0.2, 0), (tx + 0.26, ly(0.1) + 0.2, 0)))
    px = ox + 1.05
    f.append(q(0, [(px - 0.22, ly(1.05), 0), (px - 0.26, ly(1.05) + 0.75, 0),
                   (px - 0.06, ly(1.05) + 0.75, 0), (px, ly(1.05) + 0.3, 0),
                   (px + 0.06, ly(1.05) + 0.75, 0), (px + 0.26, ly(1.05) + 0.75, 0),
                   (px + 0.22, ly(1.05), 0)]))
    for gx in (sx - 0.2, sx + 0.2, tx - 0.16, tx + 0.16, px - 0.14, px + 0.14):
        f.append(seg((gx, ly(gx - ox) - 0.07, 0), (gx, ly(gx - ox) + 0.08, 0)))
    return {"data": f}


def telescope(ox=0.0):
    """「美しい世界を見たいなら」: tripod telescope aimed at a small star."""
    f = []
    hub = (ox + 0.15, -1.45, 0)
    for lx, lz in ((-0.62, 0.3), (0.72, 0.3), (0.12, -0.45)):
        f.append(seg((ox + 0.15 + lx, 0, lz), hub))
    ax = (-0.72, -0.62)                 # tube axis direction (up-left)
    n = (0.62 / 0.95, -0.72 / 0.95)     # perpendicular
    def st(t, r, sgn):
        return (hub[0] + ax[0] * t + n[0] * r * sgn,
                hub[1] + ax[1] * t + n[1] * r * sgn, 0)
    for t0, r0, t1, r1 in ((-0.35, 0.13, 0.0, 0.13), (0.0, 0.24, 1.5, 0.3)):
        for sgn in (-1, 1):
            f.append(seg(st(t0, r0, sgn), st(t1, r1, sgn)))
        f.append(seg(st(t1, r1, -1), st(t1, r1, 1)))
        f.append(seg(st(t0, r0, -1), st(t0, r0, 1)))
    for k in range(3):
        t = 1.85 + 0.42 * k
        f.append(seg(st(t, 0, 0), st(t + 0.2, 0, 0)))
    sp = st(3.15, 0, 0)
    for dx, dy in ((0.16, 0), (0, 0.16)):
        f.append(seg((sp[0] - dx, sp[1] - dy, 0), (sp[0] + dx, sp[1] + dy, 0)))
    return {"data": f}


def sparkler(ox=0.0):
    """「やるせない人間のかがやき」: a drooping sparkler mid-burn."""
    tip = (ox - 0.38, -1.95, 0)
    f = [seg((ox + 0.55, -0.55, 0), tip),
         seg((ox + 0.57, -0.51, 0.02), (tip[0] + 0.02, tip[1] + 0.03, 0.02))]
    f.append(q(5, [(tip[0] + 0.11 * math.cos(a), tip[1] + 0.11 * math.sin(a), 0)
                   for a in [math.pi * 2 * k / 8 for k in range(8)]]))
    for k, (a, ln) in enumerate([(0.3, 0.62), (0.85, 0.4), (1.5, 0.68),
                                 (2.1, 0.42), (2.75, 0.6), (3.4, 0.38),
                                 (4.05, 0.66), (4.7, 0.44), (5.35, 0.58),
                                 (5.95, 0.4)]):
        p0 = (tip[0] + 0.16 * math.cos(a), tip[1] + 0.16 * math.sin(a), 0)
        p1 = (tip[0] + (0.16 + ln) * math.cos(a),
              tip[1] + (0.16 + ln) * math.sin(a), 0)
        f.append(seg(p0, p1))
        if k % 3 == 0:                  # forked spark
            b = a + 0.35
            f.append(seg(p1, (p1[0] + 0.2 * math.cos(b),
                              p1[1] + 0.2 * math.sin(b), 0)))
    for dx, dy in ((-0.5, 1.05), (-0.15, 1.3), (0.25, 1.15)):
        p = (tip[0] + dx, tip[1] + dy, 0)
        f.append(seg((p[0] - 0.05, p[1], 0), (p[0] + 0.05, p[1], 0)))
        f.append(seg((p[0], p[1] - 0.05, 0), (p[0], p[1] + 0.05, 0)))
    return {"data": f}


def paper_plane(ox=0.0):
    """「遠いところまで行きたいなら」: a paper dart with a dashed trail."""
    nose = (ox + 1.05, -2.75, 0.0)
    tl = (ox - 0.85, -2.2, 0.6)
    tr = (ox - 0.95, -2.45, -0.55)
    keel = (ox - 0.78, -2.3, 0.0)
    f = [q(2, [nose, tl, keel]), q(3, [nose, keel, tr]),
         q(0, [nose, keel, (ox - 0.72, -1.9, 0.0)])]
    # dashed swooping trail behind
    for k in range(5):
        t0 = k / 5.0
        t1 = t0 + 0.55 / 5.0
        def tp(t):
            return (ox - 1.15 - 2.1 * t + 1.0 * t * t,
                    -2.05 + 1.3 * t - 0.5 * t * t, 0.35 * t)
        f.append(seg(tp(t0), tp(t1)))
    return {"data": f}


def bus_stop(ox=0.0):
    """「遠いところまで行きたいなら」: lonely bus stop, sign and bench."""
    px = ox - 0.55
    f = [seg((px - 0.03, 0, 0), (px, -2.5, 0)),
         seg((px + 0.05, 0, 0.03), (px + 0.04, -2.5, 0.01))]
    f.append(q(0, [(px + 0.44 * math.cos(a), -2.95 + 0.44 * math.sin(a), 0)
                   for a in [math.pi * 2 * k / 12 for k in range(12)]]))
    for k in range(2):
        yy = -3.0 + 0.14 * k
        f.append(seg((px - 0.2, yy, 0), (px + 0.2, yy, 0)))
    f.append(seg((px - 0.14, -3.18, 0), (px + 0.14, -3.18, 0)))
    bx = ox + 0.85
    f += box(bx, 0.1, 1.35, 0.09, 0.5, 2, 2, y0=-0.78)
    for lx in (-0.55, 0.55):
        for lz in (0.28, -0.08):
            f.append(seg((bx + lx, -0.78, 0.1 + lz), (bx + lx, 0, 0.1 + lz)))
    f.append(seg((bx - 0.675, -1.3, 0.34), (bx + 0.675, -1.3, 0.34)))
    for lx in (-0.55, 0.55):
        f.append(seg((bx + lx, -1.3, 0.34), (bx + lx, -0.78, 0.34)))
    return {"data": f}


def dice(ox=0.0):
    """「何回やったって」: a tumbling die, three faces showing (1/3/2)."""
    e = 1.4
    yaw, pitch = 0.6, -0.38
    cy_, sy_ = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)
    mid = -1.7                          # cube centre height (floats mid-tile)

    def xf(x, y, z):
        """local cube coords (±e/2, centred at origin) -> world."""
        x1, z1 = x * cy_ - z * sy_, x * sy_ + z * cy_
        y1, z2 = y * cp - z1 * sp, y * sp + z1 * cp
        return (ox + x1, mid + y1, z2)

    h = e / 2
    PIPS = {1: [(0.0, 0.0)],
            2: [(-0.22, 0.22), (0.22, -0.22)],
            3: [(-0.24, -0.24), (0.0, 0.0), (0.24, 0.24)],
            4: [(-0.22, -0.22), (-0.22, 0.22), (0.22, -0.22), (0.22, 0.22)],
            5: [(-0.22, -0.22), (-0.22, 0.22), (0.22, -0.22), (0.22, 0.22),
                (0.0, 0.0)],
            6: [(-0.2, -0.24), (-0.2, 0.0), (-0.2, 0.24),
                (0.2, -0.24), (0.2, 0.0), (0.2, 0.24)]}
    # all six faces, opposite sides summing to 7; ordered back-to-front for
    # the sheet orientation (per-frame sorting handles the turntable)
    SIDES = [  # (normal, base_u, base_v, mat, pip count)
        ((0, 0, -1), (1, 0, 0), (0, 1, 0), 2, 4),
        ((1, 0, 0), (0, 0, 1), (0, 1, 0), 1, 5),
        ((0, 1, 0), (1, 0, 0), (0, 0, 1), 3, 6),
        ((-1, 0, 0), (0, 0, 1), (0, 1, 0), 1, 2),
        ((0, 0, 1), (1, 0, 0), (0, 1, 0), 2, 3),
        ((0, -1, 0), (1, 0, 0), (0, 0, 1), 3, 1),
    ]
    faces = []

    def pip(base_u, base_v, normal, u, v, r=0.13):
        pts = []
        for k in range(8):
            a = math.pi * 2 * k / 8
            pu = u * e + r * math.cos(a)
            pv = v * e + r * math.sin(a)
            lx = tuple(base_u[j] * pu + base_v[j] * pv
                       + normal[j] * (h + 0.02) for j in range(3))
            pts.append(xf(*lx))
        return q(5, pts)

    for normal, bu, bv, mat, count in SIDES:
        corners = []
        for su, sv in ((-1, -1), (-1, 1), (1, 1), (1, -1)):
            lx = tuple(bu[j] * su * h + bv[j] * sv * h + normal[j] * h
                       for j in range(3))
            corners.append(xf(*lx))
        faces.append(q(mat, corners))
        r = 0.17 if count == 1 else 0.13
        for u, v in PIPS[count]:
            faces.append(pip(bu, bv, normal, u, v, r))
    return {"data": faces}


def string_phone(ox=0.0):
    """「何回言ったって君は聞いてないから」: two paper cups, one string."""
    f = []
    for sgn in (-1, 1):
        bx = ox + 1.55 * sgn            # cup bottom faces inward
        mx = ox + 2.1 * sgn             # mouth faces outward
        base = [(bx, -1.75 + 0.2 * math.sin(a), 0.2 * math.cos(a))
                for a in [math.pi * 2 * k / 8 for k in range(8)]]
        mouth = [(mx, -1.75 + 0.31 * math.sin(a), 0.31 * math.cos(a))
                 for a in [math.pi * 2 * k / 8 for k in range(8)]]
        f.append(q(0, base))
        f.append(q(0, mouth))
        for k in range(0, 8, 2):
            f.append(seg(base[k], mouth[k]))
    line = [(ox - 1.55 + 3.1 * k / 14,
             -1.75 + 0.52 * math.sin(math.pi * k / 14), 0) for k in range(15)]
    f += chain(line)
    return {"data": f}


def radio_waves(ox=0.0):
    """「そばにいないでもきっとわかるよ」: a mast whispering in arcs."""
    f = []
    for sgn in (-1, 1):
        f.append(seg((ox + 0.3 * sgn, 0, 0), (ox + 0.07 * sgn, -2.55, 0)))
    for k in range(3):
        y = -0.55 - 0.7 * k
        w0 = 0.3 - 0.075 * k
        w1 = 0.3 - 0.098 * k
        f.append(seg((ox - w0, y, 0), (ox + w1, y - 0.7, 0)))
        f.append(seg((ox + w0, y, 0), (ox - w1, y - 0.7, 0)))
    tipy = -2.85
    f.append(seg((ox + 0.07, -2.55, 0), (ox, tipy, 0)))
    f.append(seg((ox - 0.07, -2.55, 0), (ox, tipy, 0)))
    f.append(q(5, [(ox + 0.07 * math.cos(a), tipy - 0.06 + 0.07 * math.sin(a), 0)
                   for a in [math.pi * 2 * k / 8 for k in range(8)]]))
    for sgn in (-1, 1):
        for r in (0.55, 0.95, 1.35):
            arc = [(ox + sgn * r * math.cos(a), tipy - r * math.sin(a), 0)
                   for a in [math.radians(-25 + 50 * k / 5) for k in range(6)]]
            f += chain(arc)
    return {"data": f}


def comets(ox=0.0):
    """「結局はめぐりあう」: two comets whose trails cross."""
    f = []
    def head(hx, hy):
        f.append(q(5, [(hx + 0.13 * math.cos(a), hy + 0.13 * math.sin(a), 0)
                       for a in [math.pi * 2 * k / 8 for k in range(8)]]))
        for dx, dy in ((0.24, 0), (0, 0.24)):
            f.append(seg((hx - dx, hy - dy, 0), (hx + dx, hy + dy, 0)))
    def trail(fn, n=6):
        for k in range(n):
            t0 = k / n
            t1 = t0 + 0.55 / n
            f.append(seg(fn(t0), fn(t1)))
    head(ox + 1.15, -2.9)
    trail(lambda t: (ox + 1.15 - 2.6 * t + 0.5 * t * t,
                     -2.9 + 1.9 * t - 0.45 * t * t, 0))
    head(ox - 1.2, -2.55)
    trail(lambda t: (ox - 1.2 + 2.5 * t + 0.4 * t * t,
                     -2.55 + 1.75 * t - 0.6 * t * t, 0))
    return {"data": f}


def newton_cradle(ox=0.0, a_l=0.0, a_r=0.0):
    """「何回やったって」: five-ball Newton's cradle.  a_l / a_r = outward
    swing angle of the end balls (radians)."""
    RY, BY, R = -2.55, -0.95, 0.27      # rail height, ball rest height, radius
    L = BY - RY                          # pendulum arm (to ball centre), 1.6
    xs = [ox + k * 2 * R for k in (-2, -1, 0, 1, 2)]
    f = []
    for zs in (-0.5, 0.5):               # rails
        f.append(seg((ox - 1.55, RY, zs), (ox + 1.55, RY, zs)))
    for xe in (ox - 1.55, ox + 1.55):    # end crossbars + splayed legs
        f.append(seg((xe, RY, -0.5), (xe, RY, 0.5)))
        for zs in (-0.5, 0.5):
            f.append(seg((xe, RY, zs),
                         (xe + math.copysign(0.4, xe - ox), 0, zs * 1.45)))
    for bi, bx in enumerate(xs):
        ang = -a_l if bi == 0 else (a_r if bi == 4 else 0.0)
        cx = bx + L * math.sin(ang)      # hangs down (+y) from the rail
        cy = RY + L * math.cos(ang)
        tx = cx - R * math.sin(ang)      # string meets the top of the ball
        ty = cy - R * math.cos(ang)
        for zs in (-0.5, 0.5):
            f.append(seg((bx, RY, zs), (tx, ty, zs)))
        f.append(q(5, [(cx + R * math.cos(a), cy + R * math.sin(a), 0)
                       for a in [math.pi * 2 * k / 12 for k in range(12)]]))
    return {"data": f}


# ---- 何回やったって motifs: repetition / retry / chance ----
def gacha(ox=0.0):
    """Capsule machine: globe of capsules, crank, flap."""
    f = box(ox, 0, 1.15, 1.5, 0.7, 1, 2)
    zf = 0.36
    f.append(q(0, [(ox + 0.62 * math.cos(a), -2.12 + 0.62 * math.sin(a), 0)
                   for a in [math.pi * 2 * k / 14 for k in range(14)]]))
    for cx, cy, r in ((ox - 0.25, -1.85, 0.16), (ox + 0.1, -1.75, 0.15),
                      (ox + 0.33, -1.95, 0.14), (ox - 0.02, -2.05, 0.15)):
        f.append(q(0, [(cx + r * math.cos(a), cy + r * math.sin(a), 0.01)
                       for a in [math.pi * 2 * k / 8 for k in range(8)]]))
    f.append(seg((ox - 0.62, -1.5, 0), (ox + 0.62, -1.5, 0)))
    # crank on the body front
    f.append(q(0, [(ox + 0.2 * math.cos(a), -1.05 + 0.2 * math.sin(a), zf)
                   for a in [math.pi * 2 * k / 8 for k in range(8)]]))
    f.append(seg((ox, -1.05, zf), (ox + 0.16, -0.92, zf + 0.05)))
    # flap + feet
    f.append(q(5, [(ox - 0.2, -0.42, zf), (ox + 0.2, -0.42, zf),
                   (ox + 0.2, -0.18, zf), (ox - 0.2, -0.18, zf)]))
    return {"data": f}


def claw_machine(ox=0.0):
    """Crane game cabinet: glass box, claw, uncatchable prizes."""
    f = box(ox, 0, 1.7, 2.9, 1.0, 1, 2)
    zf = 0.51
    f.append(q(5, [(ox - 0.72, -1.5, zf), (ox + 0.72, -1.5, zf),
                   (ox + 0.72, -2.75, zf), (ox - 0.72, -2.75, zf)]))
    # claw on its cable, three fingers
    cx = ox + 0.22
    f.append(seg((cx, -2.75, zf - 0.2), (cx, -2.28, zf - 0.2)))
    for da in (-0.5, 0.0, 0.5):
        f.append(seg((cx, -2.28, zf - 0.2),
                     (cx + 0.16 * math.sin(da), -2.05, zf - 0.2)))
    # prizes piled at the bottom
    for px, py, r in ((ox - 0.4, -1.68, 0.17), (ox - 0.05, -1.63, 0.15),
                      (ox + 0.35, -1.7, 0.18)):
        f.append(q(0, [(px + r * math.cos(a), py + r * math.sin(a), zf - 0.25)
                       for a in [math.pi * 2 * k / 8 for k in range(8)]]))
    # sloped control panel with stick + buttons
    f.append(q(2, [(ox - 0.85, -1.45, zf), (ox + 0.85, -1.45, zf),
                   (ox + 0.85, -1.25, zf + 0.3), (ox - 0.85, -1.25, zf + 0.3)]))
    f.append(seg((ox - 0.3, -1.35, zf + 0.16), (ox - 0.3, -1.55, zf + 0.2)))
    for bx in (0.15, 0.4):
        f.append(seg((ox + bx - 0.04, -1.36, zf + 0.16),
                     (ox + bx + 0.04, -1.36, zf + 0.16)))
    return {"data": f}


def metronome(ox=0.0):
    """Metronome mid-swing."""
    f = []
    for zs in (0.3, -0.3):
        f.append(q(2 if zs > 0 else 0,
                   [(ox - 0.55, 0, zs), (ox + 0.55, 0, zs),
                    (ox + 0.2, -1.9, zs), (ox - 0.2, -1.9, zs)]))
    for sx in (-1, 1):
        f.append(seg((ox + 0.55 * sx, 0, 0.3), (ox + 0.55 * sx, 0, -0.3)))
        f.append(seg((ox + 0.2 * sx, -1.9, 0.3), (ox + 0.2 * sx, -1.9, -0.3)))
    a = 0.45
    f.append(seg((ox, -0.35, 0.31), (ox + 1.35 * math.sin(a),
                                     -0.35 - 1.35 * math.cos(a), 0.31)))
    wx = ox + 0.95 * math.sin(a)
    wy = -0.35 - 0.95 * math.cos(a)
    f.append(q(5, [(wx - 0.1, wy - 0.09, 0.32), (wx + 0.1, wy - 0.09, 0.32),
                   (wx + 0.07, wy + 0.09, 0.32), (wx - 0.07, wy + 0.09, 0.32)]))
    for k in range(3):
        f.append(seg((ox - 0.12 + k * 0.12, -1.75, 0.31),
                     (ox - 0.1 + k * 0.12, -1.6, 0.31)))
    return {"data": f}


def hourglass(ox=0.0):
    """Hourglass mid-run: frame posts, two bulbs, falling sand."""
    f = []
    for yy in (0.0, -2.3):
        f.append(q(0, [(ox + 0.62 * math.cos(a), yy + 0.13 * math.sin(a),
                        0.62 * math.sin(a) * 0.35)
                       for a in [math.pi * 2 * k / 10 for k in range(10)]]))
    for sx in (-1, 1):
        f.append(seg((ox + 0.58 * sx, 0, 0), (ox + 0.58 * sx, -2.3, 0)))
    for sx in (-1, 1):
        f += chain([(ox + 0.45 * sx, -0.13, 0), (ox + 0.42 * sx, -0.7, 0),
                    (ox + 0.05 * sx, -1.12, 0), (ox + 0.05 * sx, -1.22, 0),
                    (ox + 0.42 * sx, -1.62, 0), (ox + 0.45 * sx, -2.17, 0)])
    f.append(q(5, [(ox - 0.34, -0.14, 0.01), (ox + 0.34, -0.14, 0.01),
                   (ox + 0.06, -0.42, 0.01), (ox - 0.06, -0.42, 0.01)]))
    f.append(seg((ox, -1.17, 0.01), (ox, -0.5, 0.01)))
    f.append(q(5, [(ox - 0.2, -0.98, 0.01), (ox + 0.2, -0.98, 0.01),
                   (ox, -1.14, 0.01)]))
    return {"data": f}


def swing_set(ox=0.0, a=0.28):
    """Playground swing, seat hanging at angle `a`, nobody on it."""
    f = []
    for sx in (-1, 1):
        for zs in (0.42, -0.42):
            f.append(seg((ox + sx * 1.05 + zs * 0.35, 0, zs),
                         (ox + sx * 0.95, -2.15, 0)))
    f.append(seg((ox - 0.95, -2.15, 0), (ox + 0.95, -2.15, 0)))
    for cx in (-0.28, 0.28):
        f.append(seg((ox + cx, -2.15, 0),
                     (ox + cx + 1.55 * math.sin(a), -2.15 + 1.55 * math.cos(a),
                      0)))
    sx0 = ox - 0.28 + 1.55 * math.sin(a)
    sy = -2.15 + 1.55 * math.cos(a)
    f.append(q(2, [(sx0 - 0.06, sy, 0.03), (sx0 + 0.62, sy, 0.03),
                   (sx0 + 0.6, sy + 0.1, 0.03), (sx0 - 0.04, sy + 0.1, 0.03)]))
    return {"data": f}


def toppling_blocks(ox=0.0):
    """Block tower mid-collapse + blocks already fallen."""
    f = []
    e = 0.5

    def cube(cx, cy, ang, mat=2):
        c, s = math.cos(ang), math.sin(ang)
        pts = []
        for dx, dy in ((-e / 2, -e / 2), (e / 2, -e / 2), (e / 2, e / 2),
                       (-e / 2, e / 2)):
            pts.append((cx + dx * c - dy * s, cy + dx * s + dy * c, 0))
        f.append(q(mat, pts))
    cube(ox - 0.3, -0.25, 0.02)
    cube(ox - 0.34, -0.75, -0.03, 1)
    cube(ox - 0.22, -1.25, 0.12)
    cube(ox + 0.28, -1.72, 0.55, 3)          # the one tipping off
    cube(ox + 1.0, -0.25, 0.06, 1)           # already fallen
    cube(ox + 1.62, -0.25, -0.45)
    for k in range(3):
        a = 0.6 + k * 0.5
        f.append(seg((ox + 0.55 + 0.35 * math.cos(a), -1.75 - 0.35 * math.sin(a), 0),
                     (ox + 0.55 + 0.55 * math.cos(a), -1.75 - 0.55 * math.sin(a), 0)))
    return {"data": f}


NANKAI = [
    ("gacha", gacha), ("claw", claw_machine), ("metronome", metronome),
    ("hourglass", hourglass), ("swing", swing_set),
    ("blocks", toppling_blocks),
]


KASHI2 = [
    ("stilthouse", stilt_house), ("clothesline", clothesline),
    ("telescope", telescope), ("sparkler", sparkler),
    ("paperplane", paper_plane), ("busstop", bus_stop),
    ("dice", dice), ("stringphone", string_phone),
    ("radiowaves", radio_waves), ("comets", comets),
    ("newton", lambda ox=0.0: newton_cradle(ox, 0.55, 0.0)),
]


# ---- motif catalog (name, scene builder, zoom, yoff) ----
MOTIFS = [
    ("pylon", lambda: [ground(), pylon()], 0.95, 160),
    ("bridge", lambda: [ground(), truss_bridge()], 1.15, 70),
    ("crane", lambda: [ground(), crane()], 0.95, 160),
    ("ferris", lambda: [ground(), ferris_wheel()], 1.05, 130),
    ("turbine", lambda: [ground(), wind_turbine()], 1.1, 140),
    ("train", lambda: [ground(), train()], 1.5, 40),
    ("crossing", lambda: [ground(), crossing()], 1.7, 70),
    ("stars", lambda: [constellation(0, -3.6, 1.2)], 1.1, 220),
    ("watertower", lambda: [ground(), water_tower()], 1.25, 130),
    ("lighthouse", lambda: [ground(), lighthouse()], 1.25, 120),
    ("lamps", lambda: [ground(), lamp_row()], 1.25, 70),
    ("drafting", lambda: [ground(), drafting()], 1.15, 110),
]


def motif_sheet(font, cols=4):
    style = B.STYLES["inverted-soft-jitter"]
    tiles = []
    for i, (name, scene, zoom, yoff) in enumerate(MOTIFS):
        setup_view(TILE, TILE, zoom, 0.0, yoff)
        t = pygame.Surface((TILE, TILE))
        t.fill(style["bg"])
        stars(t, 300 + i, TILE)
        draw_scene(t, scene(), style, 2000 + i)
        t.blit(font.render(name, True, (245, 245, 245)), (24, 18))
        pygame.image.save(t, os.path.join(BG_DIR, f"motif_{name}.png"))
        tiles.append(t)
    rows = (len(tiles) + cols - 1) // cols
    sheet = pygame.Surface((TILE * cols, TILE * rows))
    sheet.fill(style["bg"])
    for i, t in enumerate(tiles):
        sheet.blit(t, ((i % cols) * TILE, (i // cols) * TILE))
    out = os.path.join(BG_DIR, "motifs_sheet.png")
    pygame.image.save(sheet, out)
    print(f"saved {out}")


def main():
    global MODELS
    pygame.init()
    pygame.display.set_mode((64, 64))
    font = pygame.font.Font(os.path.join(HERE, "font.ttf"), 26)
    with open(os.path.join(HERE, "bg_models.json")) as f:
        MODELS = json.load(f)   # only the materials table is used
    os.makedirs(BG_DIR, exist_ok=True)

    which = set(sys.argv[1:])
    if not which or "props" in which:
        tile_sheet(BUILDINGS, "buildings_sheet.png", "building", font, 1.35, 110)
        tile_sheet([lambda: tree_1(0, 1.7), lambda: tree_2(0, 1.7),
                    lambda: tree_3(0, 1.7), lambda: tree_4(0, 1.7),
                    lambda: tree_5(0, 1.7)], "trees_sheet.png", "tree", font,
                   1.9, 130)
        tile_sheet([lambda sd=sd: rock(0, 2.2, sd) for sd in
                    (1, 4, 9, 12, 17, 23)], "rocks_sheet.png", "rock", font,
                   1.9, 60)
        render_comps(font)
    if not which or "motifs" in which:
        motif_sheet(font)
    if not which or "lyrics" in which:
        lyric_sheet(font)
    if not which or "himitsu" in which:
        lyric_sheet(font, items=HIMITSU, out_name="himitsu_sheet.png")
    if not which or "kashi2" in which:
        lyric_sheet(font, items=KASHI2, out_name="kashi2_sheet.png")
    if not which or "nankai" in which:
        lyric_sheet(font, items=NANKAI, out_name="nankai_sheet.png")
    if not which or "inorganic" in which:
        tile_sheet([lambda: danchi(), lambda: office(), lambda: warehouse(),
                    lambda: silo(), lambda: factory(), lambda: containers()],
                   "inorganic_sheet.png", "inorganic", font, 1.25, 100)


if __name__ == "__main__":
    main()
