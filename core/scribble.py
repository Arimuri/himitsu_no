"""
scribble.py — hand-drawn "scribble" primitives for pygame.

Python port of p5.scribble.js (Janneck Wullschleger), itself based on the
Handy library for Processing by Jo Wood, giCentre, City University London,
after an idea by Nikolaus Gradwohl.
The Handy library is licensed under the GNU Lesser General Public License;
this derived module inherits that license (LGPL).

Shared drawing backend for the ボカコレ2026S PV: both the Miku character
sketches and the background generator draw their linework through this module.
Every call re-rolls its randomness from the supplied rng — re-seed per frame
for boiling Vib-Ribbon lines, or per still for stable images.
"""
import math
import random

import pygame


def _catmull(pts, seg=8):
    """Sample a Catmull-Rom spline through pts (approximates p5 curveVertex)."""
    if len(pts) < 3:
        return list(pts)
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(len(P) - 3):
        p0, p1, p2, p3 = P[i], P[i + 1], P[i + 2], P[i + 3]
        for j in range(seg):
            t = j / seg
            t2, t3 = t * t, t * t * t
            out.append((
                0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t
                       + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                       + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3),
                0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t
                       + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                       + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3),
            ))
    out.append(P[-1])
    return out


def jitter_line(surf, color, w, x1, y1, x2, y2, rng, jit=2.0, seg=25.0, ext=0.12):
    """The other shared stroke: straight line subdivided ~seg px with jitter on
    every point, extended past both ends (architectural overshoot)."""
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy)
    if length < 1e-6:
        return
    # cap the overshoot in absolute px: giant projected edges (near-camera
    # geometry) otherwise grow 100px+ tails that flicker frame to frame
    cap = min(ext, 45.0 / length)
    e1, e2 = rng.uniform(0, cap), rng.uniform(0, cap)
    ax, ay = x1 - dx * e1, y1 - dy * e1
    bx, by = x2 + dx * e2, y2 + dy * e2
    steps = max(1, int(length * (1 + e1 + e2) // seg))
    j = min(jit, length * 0.12)
    pts = []
    for i in range(steps + 1):
        t = i / steps
        pts.append((int(ax + (bx - ax) * t + rng.uniform(-j, j)),
                    int(ay + (by - ay) * t + rng.uniform(-j, j))))
    pygame.draw.lines(surf, color, False, pts, w)


class Scribble:
    def __init__(self, rng=None, roughness=1.0, bowing=1.0, max_offset=2.0):
        self.rng = rng or random.Random()
        self.roughness = roughness
        self.bowing = bowing
        self.max_offset = max_offset
        self.ellipse_steps = 9

    def _off(self, lo, hi):
        return self.roughness * (self.rng.random() * (hi - lo) + lo)

    # --- line ---
    def _line_pass(self, x1, y1, x2, y2, o, mdx, mdy, div):
        pts = [
            (x1 + self._off(-o, o), y1 + self._off(-o, o)),
            (mdx + x1 + (x2 - x1) * div + self._off(-o, o),
             mdy + y1 + (y2 - y1) * div + self._off(-o, o)),
            (mdx + x1 + 2 * (x2 - x1) * div + self._off(-o, o),
             mdy + y1 + 2 * (y2 - y1) * div + self._off(-o, o)),
            (x2 + self._off(-o, o), y2 + self._off(-o, o)),
        ]
        return _catmull(pts)

    def line(self, surf, color, w, x1, y1, x2, y2):
        lensq = (x1 - x2) ** 2 + (y1 - y2) ** 2
        o = self.max_offset
        if self.max_offset ** 2 * 100 > lensq:
            o = math.sqrt(lensq) / 10
        div = 0.2 + self.rng.random() * 0.2
        mdx = self.bowing * self.max_offset * (y2 - y1) / 200
        mdy = self.bowing * self.max_offset * (x1 - x2) / 200
        mdx = self._off(-mdx, mdx)
        mdy = self._off(-mdy, mdy)
        for off in (o, o / 2):
            pts = self._line_pass(x1, y1, x2, y2, off, mdx, mdy, div)
            pygame.draw.lines(surf, color, False,
                              [(int(x), int(y)) for x, y in pts], w)

    # --- polygon / polyline outlines ---
    def polygon(self, surf, color, w, pts):
        n = len(pts)
        for i in range(n):
            p1, p2 = pts[i], pts[(i + 1) % n]
            self.line(surf, color, w, p1[0], p1[1], p2[0], p2[1])

    def polyline(self, surf, color, w, pts):
        for i in range(len(pts) - 1):
            p1, p2 = pts[i], pts[i + 1]
            self.line(surf, color, w, p1[0], p1[1], p2[0], p2[1])

    # --- smooth closed outline (for rounded rects etc.) ---
    def closed_curve(self, surf, color, w, pts):
        """Two jittered Catmull passes through a closed point loop."""
        for o in (self.max_offset, self.max_offset / 2):
            loop = [(x + self._off(-o, o), y + self._off(-o, o))
                    for x, y in pts]
            loop = loop + loop[:2]
            smooth = _catmull(loop, seg=6)
            pygame.draw.lines(surf, color, False,
                              [(int(x), int(y)) for x, y in smooth], w)

    # --- ellipse ---
    def _build_ellipse(self, cx, cy, rx, ry, offset, overlap):
        inc = (math.pi * 2) / self.ellipse_steps
        rad0 = self._off(-0.5, 0.5) - math.pi / 2
        pts = [(self._off(-offset, offset) + cx + 0.9 * rx * math.cos(rad0 - inc),
                self._off(-offset, offset) + cy + 0.9 * ry * math.sin(rad0 - inc))]
        theta = rad0
        while theta < math.pi * 2 + rad0 - 0.01:
            pts.append((self._off(-offset, offset) + cx + rx * math.cos(theta),
                        self._off(-offset, offset) + cy + ry * math.sin(theta)))
            theta += inc
        pts.append((self._off(-offset, offset)
                    + cx + rx * math.cos(rad0 + math.pi * 2 + overlap * 0.5),
                    self._off(-offset, offset)
                    + cy + ry * math.sin(rad0 + math.pi * 2 + overlap * 0.5)))
        pts.append((self._off(-offset, offset)
                    + cx + 0.98 * rx * math.cos(rad0 + overlap),
                    self._off(-offset, offset)
                    + cy + 0.98 * ry * math.sin(rad0 + overlap)))
        return _catmull(pts, seg=6)

    def ellipse(self, surf, color, w, cx, cy, ew, eh):
        rx, ry = abs(ew / 2), abs(eh / 2)
        rx += self._off(-rx * 0.05, rx * 0.05)
        ry += self._off(-ry * 0.05, ry * 0.05)
        inc = (math.pi * 2) / self.ellipse_steps
        overlap = inc * self._off(0.1, self._off(0.4, 1))
        for off, ov in ((1, overlap), (1.5, 0)):
            pts = self._build_ellipse(cx, cy, rx, ry, off, ov)
            pygame.draw.lines(surf, color, False,
                              [(int(x), int(y)) for x, y in pts], w)

    # --- hatched fill ---
    def hatch_fill(self, surf, color, w, pts, gap, angle_deg):
        """Fill a polygon with scribbled hatch lines at angle_deg."""
        a = math.radians(angle_deg)
        ca, sa = math.cos(a), math.sin(a)
        # rotate into hatch space (hatch lines become horizontal)
        rp = [(x * ca + y * sa, -x * sa + y * ca) for x, y in pts]
        ys = [p[1] for p in rp]
        y0, y1 = min(ys), max(ys)
        y = y0 + gap * (0.5 + self.rng.random() * 0.5)
        n = len(rp)
        while y < y1:
            xs = []
            for i in range(n):
                p1, p2 = rp[i], rp[(i + 1) % n]
                if (p1[1] <= y < p2[1]) or (p2[1] <= y < p1[1]):
                    t = (y - p1[1]) / (p2[1] - p1[1])
                    xs.append(p1[0] + (p2[0] - p1[0]) * t)
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                # rotate back to screen space
                ax, ay = xs[i] * ca - y * sa, xs[i] * sa + y * ca
                bx, by = xs[i + 1] * ca - y * sa, xs[i + 1] * sa + y * ca
                self.line(surf, color, w, ax, ay, bx, by)
            y += gap
