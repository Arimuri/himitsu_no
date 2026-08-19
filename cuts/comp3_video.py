#!/usr/bin/env python3
"""comp_3 as a living still: locked camera, boiling lines, Miku idling.
5 s, 12 fps.  Output: movie/current/comp_3.mp4"""
import os, json, math, random, subprocess, sys
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "core"))
import pygame
import bg_sketch as B
import design_sketch as DS
import bg_props as P

OUT_DIR = "/Users/arimura/Dropbox/ボカコレ2026S/movie/current"
W, H = 1280, 720
FPS = 12
DUR = 5.0
MIKU_V = {"render": "line", "bg": "black", "mono": True, "line_col": DS.WHITE,
          "scribble": True, "roughness": 2.0, "lw": 2}


def main():
    pygame.init()
    pygame.display.set_mode((64, 64))
    with open(os.path.join(os.path.dirname(HERE), "core", "bg_models.json")) as f:
        P.MODELS = json.load(f)
    style = B.STYLES["inverted-soft-jitter"]
    P.setup_view(W, H, 0.66, 230, 20.0)
    scene = [P.ground(), P.building_1(1.8), P.tree_3(-1.8, 1.3),
             P.constellation(-1.0, -18.0, 4.0, 6.2)]
    MIKU_POS = (-1.7, 6.2)            # world anchor
    C0, C1 = (0.0, -200.0, 0.0), (0.0, -2000.0, 0.0)

    out = os.path.join(OUT_DIR, "comp_3.mp4")
    frames = int(DUR * FPS)
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-vcodec", "rawvideo",
         "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", out],
        stdin=subprocess.PIPE)

    for i in range(frames):
        t = i / (frames - 1)
        # hold 1 s, then a 4 s tilt up into the sky
        pt = max(0.0, min(1.0, (t * DUR - 1.0) / 4.0))
        e = pt * pt * (3 - 2 * pt)
        B.CENTER = tuple(a + (b - a) * e for a, b in zip(C0, C1))
        B.CAM_X, B.CAM_Y, B.CAM_Z = B._camera_basis()
        surf = pygame.Surface((W, H))
        surf.fill(style["bg"])
        P.stars(surf, hash("comp_3") % 1000, W)
        lrng = random.Random(9800 + i)
        for sh in scene:
            B.draw_shape(surf, sh, style, P.MODELS["materials"], lrng)
        mx, mz = MIKU_POS
        feet = B.project(mx * B.M, 0, mz * B.M)
        head_ref = B.project(mx * B.M, -2.3 * B.M, mz * B.M)
        if feet and head_ref:
            mw = (feet[1] - head_ref[1]) / 1.9
            d = DS.D(surf, MIKU_V, seed=700 + i)
            ts = i / FPS
            sw = round(math.sin(math.pi * 2 * ts / 3.4) * 2) / 2 * 0.03
            DS.draw_miku(d, feet[0], feet[1] - 1.53 * mw, mw,
                         tail_swing=(sw, -sw), tail_swing2=(-sw, sw))
        ff.stdin.write(pygame.image.tostring(surf, "RGB"))

    ff.stdin.close()
    ff.wait()
    print(f"saved {out}")


if __name__ == "__main__":
    main()
