"""Minigame countdown: START -> BAŞLA in both countdown graphics.

  graphics/misc/minigame_countdown.png  two 64x32 sprites (1D tiles 48.. and 80..)
  graphics/link/321start.png            converted with -mwidth 4 -mheight 4, so its
                                        lower half is already laid out as on screen

The letters are rebuilt from 4px-stroke masks: fill shaded by row (the shade
of each row is sampled from the original word), a dark outline (8) and a
white outer outline (15) around it, on transparent 0.

usage: python -I countdown_start.py <repo root>
"""
import os, sys
from collections import Counter
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tilecanvas import TileCanvas

G = sys.argv[1] + "/graphics/"
DARK, WHITE = 8, 15
FILL = {14, 12, 10, 9, 11, 13}

B = ["##############..", "###############.", "################", "####........####", "####........####",
     "####........####", "####.......####.", "###############.", "##############..", "###############.",
     "####........####", "####........####", "####........####", "####........####", "####........####",
     "####........####", "####.......#####", "################", "###############.", "##############.."]
A = ["..############..", ".##############.", "################", "####........####", "####........####",
     "####........####", "####........####", "####........####", "################", "################",
     "################", "####........####", "####........####", "####........####", "####........####",
     "####........####", "####........####", "####........####", "####........####", "####........####"]
S = ["..############..", ".##############.", "################", "####........####", "####............",
     "####............", "####............", "#####...........", "###############.", ".###############",
     "..##############", "...........#####", "............####", "............####", "............####",
     "####........####", "####........####", "################", ".##############.", "..############.."]
SH = S + ["......####......", ".......###......", ".....####......."]  # Ş: cedilla below
L = ["####.........."] * 17 + ["##############"] * 3
WORD = [B, A, SH, L, A]
GAP = 4


class Region:
    def __init__(self, get, set_, w, h):
        self.get, self.set, self.w, self.h = get, set_, w, h


def redraw(r):
    rows = [y for y in range(r.h) if any(r.get(x, y) in FILL for x in range(r.w))]
    top = rows[0]
    shade = {}
    for y in rows:
        c = Counter(v for v in (r.get(x, y) for x in range(r.w)) if v in FILL)
        shade[y - top] = c.most_common(1)[0][0]
    for y in range(r.h):
        for x in range(r.w):
            r.set(x, y, 0)
    width = sum(len(g[0]) for g in WORD) + GAP * (len(WORD) - 1)
    x0 = (r.w - width) // 2
    fill = set()
    x = x0
    for g in WORD:
        for gy, row in enumerate(g):
            for gx, ch in enumerate(row):
                if ch == "#":
                    fill.add((x + gx, top + gy))
        x += len(g[0]) + GAP
    near = lambda p, d: any((p[0] + a, p[1] + b) in fill for a in range(-d, d + 1) for b in range(-d, d + 1))
    for y in range(r.h):
        for x in range(r.w):
            p = (x, y)
            if p in fill:
                r.set(x, y, shade.get(y - top, shade[max(shade)]))
            elif near(p, 1):
                r.set(x, y, DARK)
            elif near(p, 2):
                r.set(x, y, WHITE)
    return x0, width


def lo_set(px):
    return lambda x, y, v: px.__setitem__((x, y), (px[x, y] & 0xF0) | v)


# minigame_countdown: two 64x32 sprites side by side
im = Image.open(G + "misc/minigame_countdown.png")
px = im.load()
entries = []
for row in range(4):
    entries += list(range(48 + 8 * row, 56 + 8 * row)) + list(range(80 + 8 * row, 88 + 8 * row))
c = TileCanvas(px, im.width, entries, 16)
print("minigame_countdown", redraw(Region(c.get, c.set, 128, 32)))
im.save(G + "misc/minigame_countdown.png")

# 321start: lower half of the PNG, as on screen
im = Image.open(G + "link/321start.png")
px = im.load()
reg = Region(lambda x, y: px[x, 32 + y] & 15, lambda x, y, v: lo_set(px)(x, 32 + y, v), 96, 32)
print("321start", redraw(reg))
im.save(G + "link/321start.png")
