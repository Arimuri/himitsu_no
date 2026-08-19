#!/usr/bin/env python3
"""
Train crossing cut (3 s, 12 fps, 16:9): the motif_train composition —
frontal rails mid-frame — with the train sliding across the full width and
a level crossing in the near foreground, warning lamps blinking alternately.
Output: movie/current/train_cross.mp4
"""
import os, json, math, random, subprocess, sys
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "core"))
import pygame
import bg_sketch as B
import bg_props as P

OUT_DIR = "/Users/arimura/Dropbox/ボカコレ2026S/movie/current"
W, H = 1280, 720
FPS = 12
DUR = 4.5          # 0.75s empty lead-in / lead-out around a 3s pass


def main():
    pygame.init()
    pygame.display.set_mode((64, 64))
    with open(os.path.join(os.path.dirname(HERE), "core", "bg_models.json")) as f:
        P.MODELS = json.load(f)
    style = B.STYLES["inverted-soft-jitter"]
    P.setup_view(W, H, 1.35, 0.0, -80.0)

    # static: ground, long rails + sleepers, crossing in the foreground
    rails = []
    for z in (-0.46, 0.46):
        rails += [P.seg((-11, -0.06, z), (11, -0.06, z)),
                  P.seg((-11, -0.01, z), (11, -0.01, z))]
    x = -10.8
    while x < 10.8:
        rails.append(P.seg((x, 0, -0.62), (x, 0, 0.62)))
        x += 0.8
    static = [P.ground(14, 6, -8), {"data": rails}]

    out = os.path.join(OUT_DIR, "train_cross.mp4")
    frames = int(DUR * FPS)
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-vcodec", "rawvideo",
         "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", out],
        stdin=subprocess.PIPE)

    for i in range(frames):
        t = i / (frames - 1)
        tc = max(0.0, min(1.0, (t * DUR - 0.75) / 3.0))
        surf = pygame.Surface((W, H))
        surf.fill(style["bg"])
        P.stars(surf, 731, W)
        lrng = random.Random(9700 + i)
        for sh in static:
            B.draw_shape(surf, sh, style, P.MODELS["materials"], lrng)
        # train slides right-to-left across the whole frame
        tx = 12.5 - 25.0 * tc
        B.draw_shape(surf, P.train(tx, rails=False), style,
                     P.MODELS["materials"], lrng)
        # crossing up front, lamps blinking alternately
        B.draw_shape(surf, P.crossing(3.6), style, P.MODELS["materials"], lrng)
        blink = (i // 4) % 2
        for sgn, on in ((-1, blink == 0), (1, blink == 1)):
            if on:
                cx3d = B.project((3.6 + 0.18 * sgn) * B.M, -1.62 * B.M, 0)
                pygame.draw.circle(surf, (245, 245, 245),
                                   (int(cx3d[0]), int(cx3d[1])), 9)
        ff.stdin.write(pygame.image.tostring(surf, "RGB"))

    ff.stdin.close()
    ff.wait()
    print(f"saved {out}")


if __name__ == "__main__":
    main()
