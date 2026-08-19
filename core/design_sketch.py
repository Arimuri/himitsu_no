#!/usr/bin/env python3
"""
Static design sketches for the Miku character — SIMPLE edition.

Kept: rounded head, shallow zigzag bangs, one ahoge, dot eyes, tiny mouth,
hanging tapered twin-tails + square scrunchies, one-piece dress, simple legs,
small teal tie. Removed: brows, blush, arms, sleeves, boot details, side hair,
tail stripes. Head is ~37% of figure height (was ~55%).

Style axis per variant (Vib-Ribbon linework <-> flat poster):
  render: "line" / "mix" (lines + selective fills) / "fill"
Renders a 3x2 contact sheet + singles into ボカコレ2026S/movie/character/.
"""
import os
import math
import random

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
SHRTY_DIR = os.path.dirname(os.path.abspath(__file__))
import sys
sys.path.insert(0, SHRTY_DIR)
import pygame
from scribble import Scribble, jitter_line

OUT_DIR = "/Users/arimura/Dropbox/ボカコレ2026S/movie/character"
TILE = 800

YELLOW = (255, 208, 51)
BLACK = (50, 92, 122)  # unified PV navy, brightened
TEAL = (82, 199, 190)
CREAM = (255, 246, 233)
DARK = (40, 42, 60)
PINK = (246, 110, 150)
WHITE = (245, 245, 245)
GREY = (238, 234, 226)

FILL_COL = {"hair": TEAL, "face": CREAM, "dark": DARK, "pink": PINK,
            "grey": GREY, "accent": TEAL}

# gentle shallow zigzag bangs
BANGS = [(0, 0.44), (0.26, 0.30), (0.5, 0.42), (0.74, 0.30), (1, 0.44)]


def rounded_rect_pts(x0, y0, w, h, r, steps=3):
    corners = [(x0 + w - r, y0 + r, -90, 0), (x0 + w - r, y0 + h - r, 0, 90),
               (x0 + r, y0 + h - r, 90, 180), (x0 + r, y0 + r, 180, 270)]
    pts = []
    for ccx, ccy, a0, a1 in corners:
        for i in range(steps + 1):
            a = math.radians(a0 + (a1 - a0) * i / steps)
            pts.append((ccx + r * math.cos(a), ccy + r * math.sin(a)))
    return pts


SHARP = False   # True = skip corner rounding (edges stay long -> full jitter)


def fillet(pts, r, closed=True, steps=3):
    """Round polygon/polyline corners with small quadratic arcs."""
    if SHARP:
        return list(pts)
    n = len(pts)
    out = []
    idx = range(n) if closed else range(1, n - 1)
    if not closed:
        out.append(pts[0])
    for i in idx:
        A, B, C = pts[(i - 1) % n], pts[i], pts[(i + 1) % n]
        la = math.hypot(B[0] - A[0], B[1] - A[1])
        lc = math.hypot(C[0] - B[0], C[1] - B[1])
        ta = min(r / la, 0.42) if la > 1e-6 else 0
        tc = min(r / lc, 0.42) if lc > 1e-6 else 0
        B1 = (B[0] + (A[0] - B[0]) * ta, B[1] + (A[1] - B[1]) * ta)
        B2 = (B[0] + (C[0] - B[0]) * tc, B[1] + (C[1] - B[1]) * tc)
        for k in range(steps + 1):
            t = k / steps
            out.append((
                (1 - t) ** 2 * B1[0] + 2 * (1 - t) * t * B[0] + t ** 2 * B2[0],
                (1 - t) ** 2 * B1[1] + 2 * (1 - t) * t * B[1] + t ** 2 * B2[1]))
    if not closed:
        out.append(pts[-1])
    return out


def rect_pts(cx, cy, w, h):
    return [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2),
            (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)]


def rot(pts, ang, ox=0, oy=0):
    ca, sa = math.cos(ang), math.sin(ang)
    return [(ox + x * ca - y * sa, oy + x * sa + y * ca) for x, y in pts]


class D:
    """Style-aware drawing context with along-the-line wobble."""

    def __init__(self, surf, V, seed=7):
        self.s = surf
        self.V = V
        self.rng = random.Random(seed)
        self.lw = V.get("lw", 3)
        self.jit = V.get("jitter", 0.0)
        self.scr = None
        if V.get("scribble"):
            self.scr = Scribble(rng=self.rng,
                                roughness=V.get("roughness", 1.8),
                                bowing=V.get("bowing", 1.5),
                                max_offset=V.get("max_offset", 2.5))
        self.vib = bool(V.get("vibline"))

    def _line_col(self, tag):
        V = self.V
        base = V.get("line_col", DARK)
        if V.get("mono") or V["render"] == "fill":
            return base
        return {"hair": TEAL, "pink": PINK, "accent": TEAL}.get(tag, base)

    def _wobble(self, pts, closed=True):
        if self.jit <= 0:
            return pts
        j, out = self.jit, []
        n = len(pts)
        m = n if closed else n - 1
        for i in range(m):
            p1, p2 = pts[i], pts[(i + 1) % n]
            steps = max(1, int(math.hypot(p2[0] - p1[0], p2[1] - p1[1]) // 32))
            for st in range(steps):
                t = st / steps
                out.append((p1[0] + (p2[0] - p1[0]) * t + self.rng.uniform(-j, j),
                            p1[1] + (p2[1] - p1[1]) * t + self.rng.uniform(-j, j)))
        if not closed:
            out.append(pts[-1])
        return out

    def _outline(self, col, pts):
        if self.vib:
            n = len(pts)
            for i in range(n):
                p1, p2 = pts[i], pts[(i + 1) % n]
                for _ in range(2):   # double-drawn edges, like the building
                    jitter_line(self.s, col, self.lw, p1[0], p1[1],
                                p2[0], p2[1], self.rng)
        elif self.scr:
            self.scr.polygon(self.s, col, self.lw, pts)
        else:
            pygame.draw.polygon(self.s, col, pts, self.lw)

    def poly(self, tag, pts, force_fill=False):
        V = self.V
        raw = list(pts)
        pts = [(int(x), int(y)) for x, y in
               (raw if self.scr else self._wobble(raw, True))]
        if force_fill:
            col = FILL_COL[tag] if V["render"] != "line" else self._line_col(tag)
            pygame.draw.polygon(self.s, col, pts)
            return
        if V["render"] == "fill":
            pygame.draw.polygon(self.s, FILL_COL[tag], pts)
            self._outline(DARK, pts)
        elif V["render"] == "mix" and tag in V.get("fills", ()):
            pygame.draw.polygon(self.s, FILL_COL[tag], pts)
            oc = self._line_col(tag) if V["bg"] == "black" else DARK
            self._outline(oc, pts)
        else:
            self._outline(self._line_col(tag), pts)

    def lines(self, tag, pts):
        if self.vib:
            col = self._line_col(tag)
            for i in range(len(pts) - 1):
                for _ in range(2):   # double-drawn edges, like the building
                    jitter_line(self.s, col, self.lw, pts[i][0], pts[i][1],
                                pts[i + 1][0], pts[i + 1][1], self.rng)
            return
        if self.scr:
            self.scr.polyline(self.s, self._line_col(tag), self.lw, pts)
            return
        pts = [(int(x), int(y)) for x, y in self._wobble(pts, False)]
        pygame.draw.lines(self.s, self._line_col(tag), False, pts, self.lw)

    def rrect(self, tag, rect, r, force_fill=False):
        V = self.V
        rect = pygame.Rect(int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3]))
        if force_fill:
            col = FILL_COL[tag] if V["render"] != "line" else self._line_col(tag)
            pygame.draw.rect(self.s, col, rect, border_radius=int(r))
            return
        rpts = rounded_rect_pts(rect.x, rect.y, rect.w, rect.h, max(2, r))
        if self.vib:
            oc = self._line_col(tag)
            if V["render"] != "line" and tag in V.get("fills", ()):
                pygame.draw.rect(self.s, FILL_COL[tag], rect,
                                 border_radius=int(r))
            self._outline(oc, [(int(x), int(y)) for x, y in rpts])
            return
        if V["render"] == "fill":
            pygame.draw.rect(self.s, FILL_COL[tag], rect, border_radius=int(r))
            if self.scr:
                self.scr.closed_curve(self.s, DARK, self.lw, rpts)
            else:
                pygame.draw.rect(self.s, DARK, rect, self.lw, border_radius=int(r))
        elif V["render"] == "mix" and tag in V.get("fills", ()):
            pygame.draw.rect(self.s, FILL_COL[tag], rect, border_radius=int(r))
            oc = self._line_col(tag) if V["bg"] == "black" else DARK
            if self.scr:
                self.scr.closed_curve(self.s, oc, self.lw, rpts)
            else:
                pygame.draw.rect(self.s, oc, rect, self.lw, border_radius=int(r))
        else:
            if self.scr:
                self.scr.closed_curve(self.s, self._line_col(tag), self.lw, rpts)
            else:
                pygame.draw.rect(self.s, self._line_col(tag), rect, self.lw,
                                 border_radius=int(r))


def draw_tail(d, jx, jy, ang, W, ang2=None):
    """One twin-tail as a SINGLE region whose outline bends at one joint:
    base (scrunchie) -> mid joint -> flaring tip. Angles in signed radians."""
    if ang2 is None:
        ang2 = ang
    L1, L2 = W * 0.78, W * 0.92
    tw, tm, te = W * 0.10, W * 0.17, W * 0.24

    d1x, d1y = math.sin(ang), math.cos(ang)
    p1x, p1y = -d1y, d1x
    d2x, d2y = math.sin(ang2), math.cos(ang2)
    p2x, p2y = -d2y, d2x
    mx, my = jx + d1x * L1, jy + d1y * L1
    ex, ey = mx + d2x * L2, my + d2y * L2
    # miter perpendicular at the joint keeps the outline continuous
    pmx, pmy = p1x + p2x, p1y + p2y
    pl = math.hypot(pmx, pmy) or 1.0
    pmx, pmy = pmx / pl, pmy / pl

    outline = [
        (jx + p1x * tw / 2, jy + p1y * tw / 2),
        (jx - p1x * tw / 2, jy - p1y * tw / 2),
        (mx - pmx * tm / 2, my - pmy * tm / 2),
        (ex - p2x * te / 2, ey - p2y * te / 2),
        (ex + p2x * te / 2, ey + p2y * te / 2),
        (mx + pmx * tm / 2, my + pmy * tm / 2),
    ]
    d.poly("hair", fillet(outline, W * 0.045))


def draw_head(d, cx, cy, HW, H, back=False):
    """Head + bangs + ahoge + scrunchies + face, centered at (cx, cy).
    back=True: seen from behind — plain hair, no bangs, no face."""
    V = d.V
    line_only = V["render"] == "line"

    rr = HW * 0.16
    x0, y0 = cx - HW / 2, cy - H / 2
    head_pts = rounded_rect_pts(x0, y0, HW, H, rr)
    if line_only:
        # opaque mask so no stray line ever crosses the face
        mask = BLACK if V["bg"] == "black" else YELLOW
        pygame.draw.polygon(d.s, mask, [(int(x), int(y)) for x, y in head_pts])
    d.poly("face", head_pts)

    if back:
        # back of the head: ahoge + scrunchies only
        d.poly("hair", [(cx - HW * 0.03, cy - H * 0.49),
                        (cx + HW * 0.05, cy - H * 0.49),
                        (cx + HW * 0.10, cy - H * 0.68)])
        for sgn in (-1, 1):
            d.poly("pink", rect_pts(cx + sgn * HW * 0.56, cy - H * 0.40,
                                    HW * 0.12, HW * 0.12))
        return

    # bangs: rounded top + gentle zigzag (open polyline in pure line mode)
    edge_pts = fillet([(cx + (fx - 0.5) * HW, cy - H / 2 + fy * H)
                       for fx, fy in BANGS], HW * 0.05, closed=False)
    if line_only:
        d.lines("hair", edge_pts)
    else:
        band = [(x0, y0 + BANGS[0][1] * H), (x0, y0 + rr)]
        for ccx, a0 in ((x0 + rr, 180), (x0 + HW - rr, 270)):
            for i in range(4):
                a = math.radians(a0 + 90 * i / 3)
                band.append((ccx + rr * math.cos(a), y0 + rr + rr * math.sin(a)))
        band.append((x0 + HW, y0 + BANGS[-1][1] * H))
        band += list(reversed(edge_pts))
        d.poly("hair", band)

    # one simple ahoge
    d.poly("hair", [(cx - HW * 0.03, cy - H * 0.49),
                    (cx + HW * 0.05, cy - H * 0.49),
                    (cx + HW * 0.10, cy - H * 0.68)])

    # square scrunchies on the tail joints
    for sgn in (-1, 1):
        d.poly("pink", rect_pts(cx + sgn * HW * 0.56, cy - H * 0.40,
                                HW * 0.12, HW * 0.12))

    # face: dot eyes + tiny mouth, nothing else
    keep_jit = d.jit
    d.jit = 0
    ey = cy + H * 0.10
    bgc = BLACK if V["bg"] == "black" else YELLOW
    for sgn in (-1, 1):
        exx = cx + sgn * HW * 0.17
        ew, eh = HW * 0.062, H * 0.13
        d.rrect("dark", (exx - ew / 2, ey - eh / 2, ew, eh), ew * 0.5,
                force_fill=True)
        if V.get("glint"):
            hi = bgc if line_only else WHITE
            pygame.draw.circle(d.s, hi,
                               (int(exx - sgn * ew * 0.12), int(ey - eh * 0.22)),
                               int(ew * 0.22))
    my = cy + H * 0.30
    if V.get("mouth", "line") == "o":
        mw, mh = HW * 0.05, H * 0.045
        d.rrect("dark", (cx - mw / 2, my - mh / 2, mw, mh), mw * 0.45,
                force_fill=True)
    else:
        mw, mh = HW * 0.07, max(3, H * 0.020)
        d.rrect("dark", (cx - mw / 2, my - mh / 2, mw, mh), mh * 0.5,
                force_fill=True)
    d.jit = keep_jit


def draw_miku(d, cx, cy, W, tail_swing=(0.0, 0.0), leg_ang=(0.0, 0.0),
              tail_swing2=None, back=False):
    """cx, cy = head center. W = layout unit. Standing pose.
    tail_swing: extra lean (radians) per tail (upper segment).
    tail_swing2: lower-segment extra lean (defaults to tail_swing = rigid).
    leg_ang: pendulum swing (radians) per leg, pivoting at the hidden hip root."""
    V = d.V
    HW = W * 0.62          # head width (decisively small face)
    H = HW * 0.84          # head height (closer to square)
    U = W * 0.72           # body vertical unit
    if tail_swing2 is None:
        tail_swing2 = tail_swing
    for i, (sgn, deg) in enumerate(((-1, 6), (1, 9))):
        draw_tail(d, cx + sgn * HW * 0.56, cy - H * 0.40,
                  (math.radians(deg) + tail_swing[i]) * sgn, W,
                  (math.radians(deg + 10) + tail_swing2[i]) * sgn)

    # legs first: pendulums from a root tucked up inside the dress
    for i, sgn in enumerate((-1, 1)):
        leg_len, leg_w = U * 0.60, W * 0.05
        local = rect_pts(0, leg_len / 2, leg_w, leg_len)
        pts = rot(local, leg_ang[i], cx + sgn * W * 0.075, cy + U * 1.52)
        d.poly("dark", fillet(pts, W * 0.02))

    # dress: opaque A-line trapezoid that hides the leg roots
    top_y = cy + H * 0.55
    bot_y = cy + U * 1.75
    dress = [(cx - W * 0.075, top_y), (cx + W * 0.075, top_y),
             (cx + W * 0.18, bot_y), (cx - W * 0.18, bot_y)]
    if V["render"] == "line":
        mask = BLACK if V["bg"] == "black" else YELLOW
        pygame.draw.polygon(d.s, mask, [(int(x), int(y)) for x, y in dress])
    d.poly("grey", dress)
    if not back:
        # small teal tie (front only)
        d.poly("accent", [(cx - W * 0.028, top_y + U * 0.05),
                          (cx + W * 0.028, top_y + U * 0.05),
                          (cx, top_y + U * 0.24)],
               force_fill=V["render"] != "line")

    draw_head(d, cx, cy, HW, H, back=back)


def draw_stars(surf, rng, col):
    for side in (0, 1):
        xs = (30, 168) if side == 0 else (632, 770)
        for k in range(4):
            x = rng.randint(*xs)
            y = rng.randint(50 + k * 180, 160 + k * 180)
            r = rng.choice((4, 7, 11))
            pygame.draw.line(surf, col, (x - r, y), (x + r, y), 2)
            pygame.draw.line(surf, col, (x, y - r), (x, y + r), 2)


# Confirmed direction: white linework on the PV navy. Line-quality variants only.
VARIANTS = [
    ("W1 wobble line", {"render": "line", "bg": "black", "mono": True,
                        "line_col": WHITE, "jitter": 2.0}),
    ("W2 scribble",    {"render": "line", "bg": "black", "mono": True,
                        "line_col": WHITE, "scribble": True,
                        "roughness": 2.0}),
    ("W3 scribble rough", {"render": "line", "bg": "black", "mono": True,
                           "line_col": WHITE, "scribble": True,
                           "roughness": 3.0, "lw": 4}),
]


def render_sheet(variants, out_name, cols, font):
    tiles = []
    for i, (name, v) in enumerate(variants):
        t = pygame.Surface((TILE, TILE))
        bg = BLACK if v["bg"] == "black" else YELLOW
        t.fill(bg)
        rng = random.Random(100 + i)
        draw_stars(t, rng, (205, 205, 215) if v["bg"] == "black" else DARK)
        d = D(t, v, seed=100 + i)
        draw_miku(d, TILE / 2, TILE * 0.30, TILE * 0.27)
        lab = WHITE if v["bg"] == "black" else DARK
        t.blit(font.render(name, True, lab), (24, 18))
        pygame.image.save(t, os.path.join(OUT_DIR, f"design_{name.split()[0]}.png"))
        tiles.append(t)

    rows = (len(tiles) + cols - 1) // cols
    sheet = pygame.Surface((TILE * cols, TILE * rows))
    for i, t in enumerate(tiles):
        sheet.blit(t, ((i % cols) * TILE, (i // cols) * TILE))
    out = os.path.join(OUT_DIR, out_name)
    pygame.image.save(sheet, out)
    print(f"saved {out}")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    pygame.init()
    pygame.display.set_mode((64, 64))
    font = pygame.font.Font(os.path.join(SHRTY_DIR, "font.ttf"), 26)
    render_sheet(VARIANTS, "design_sheet.png", 3, font)


if __name__ == "__main__":
    main()
