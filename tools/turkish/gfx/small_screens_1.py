"""Screens 8-11 of the graphics pass:
  8  Fame Checker title  FAME <=> CHECKER -> ÜNLÜ <=> REHBERİ
  9  Teachy TV           THE END -> SON (the logo stays)
  10 Slot machine        CREDIT / PAYOUT -> KREDİ / KAZANÇ
  11 Marking menu        OK / CANCEL -> TAMAM / VAZGEÇ

usage: python -I small_screens_1.py <repo root>
"""
import os, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tilecanvas import TileCanvas, read_map
import pixfont as pf

G = sys.argv[1] + "/graphics/"


def glyphs(spec):
    return {k: [r.replace("#", "1") for r in v.split("/")] for k, v in spec.items()}


def stamp(put, m, x0, y0, ink, shadow=None, outline=None):
    h, w = len(m), len(m[0])
    on = lambda x, y: 0 <= y < h and 0 <= x < w and m[y][x]
    for y in range(-1, h + 1):
        for x in range(-1, w + 1):
            if on(x, y):
                put(x0 + x, y0 + y, ink)
            elif outline is not None and any(on(x + a, y + b) for a in (-1, 0, 1) for b in (-1, 0, 1)):
                put(x0 + x, y0 + y, outline)
            elif shadow is not None and (on(x - 1, y) or on(x, y - 1) or on(x - 1, y - 1)):
                put(x0 + x, y0 + y, shadow)


def direct(px):
    return lambda x, y, v: px.__setitem__((x, y), (px[x, y] & 0xF0) | v)


# --- 8: Fame Checker title (bg.png, ink 7 on the light pill 6) -----------------
im = Image.open(G + "fame_checker/bg.png")
px = im.load()
for (x1, x2), word in [((4, 25), "ÜNLÜ"), ((36, 70), "REHBERİ")]:
    for y in range(12, 21):
        for x in range(x1, x2 + 1):
            if px[x, y] & 15 == 7:
                px[x, y] = (px[x, y] & 0xF0) | 6
    m = pf.mask_of(word, pf.CAP9)  # row 0 = marks on the pill's top row
    x0 = (x1 + x2 + 1 - len(m[0])) // 2
    stamp(direct(px), m, x0, 12, 7)
im.save(G + "fame_checker/bg.png")

# --- 9: Teachy TV "THE END" -> "SON" (ink 1, outline 10, on transparent 0) ------
BIG = glyphs({
    "S": ".######/#######/##...../##...../##...../######./.######/.....##/.....##/.....##/#######/######.",
    "O": ".#####./#######/##...##/##...##/##...##/##...##/##...##/##...##/##...##/##...##/#######/.#####.",
    "N": "##...##/###..##/###..##/####.##/####.##/##.####/##.####/##..###/##..###/##...##/##...##/##...##",
})
im = Image.open(G + "teachy_tv/tiles.png")
px = im.load()
for y in range(105, 119):
    for x in range(11, 69):
        if px[x, y] & 15 in (1, 10):
            px[x, y] = px[x, y] & 0xF0
stamp(direct(px), pf.mask_of("SON", BIG, gap=3), 12, 106, 1, outline=10)
im.save(G + "teachy_tv/tiles.png")

# --- 10: slot machine CREDIT / PAYOUT (ink 3 on 15, on the bg.bin layout) -----
S5 = glyphs({
    "K": "#.#/#.#/##./#.#/#.#", "R": "##./#.#/##./#.#/#.#", "E": "###/#../##./#../###",
    "D": "##./#.#/#.#/#.#/##.", "İ": ".#./.../.#./.#./.#./.#.",
    "A": ".#./#.#/###/#.#/#.#", "Z": "###/..#/.#./#../###", "N": "#..#/##.#/#.##/#..#/#..#",
    "Ç": ".##/#../#../.##/.#.",
})
for k in "KREDAZN":  # one empty row on top: İ's dot uses it
    S5[k] = ["..."[:len(S5[k][0])]] + S5[k]
S5["Ç"] = ["..."] + S5["Ç"]
im = Image.open(G + "slot_machine/firered/bg.png")
px = im.load()
c = TileCanvas(px, im.width, read_map(G + "slot_machine/firered/bg.bin"), 32)
for (x1, x2), word in [((82, 109), "KREDİ"), ((130, 157), "KAZANÇ")]:
    for y in range(16, 22):
        for x in range(x1, x2 + 1):
            if c.get(x, y) == 3:
                c.set(x, y, 15)
    m = pf.mask_of(word, S5)
    stamp(c.set, m, (x1 + x2 + 1 - len(m[0])) // 2, 16, 3)
im.save(G + "slot_machine/firered/bg.png")

# --- 11: marking menu OK / CANCEL ---------------------------------------------
# The text sprite is 32x32 built from tiles 9..24 of markings2.png (1D order).
F7 = glyphs(dict(pf._C7, V="#..#/#..#/#..#/#..#/#..#/.##./.##."))
F7["Ç"] = F7["C"] + [".1.."]
im = Image.open(G + "misc/markings2.png")
px = im.load()
c = TileCanvas(px, im.width, list(range(9, 25)), 4)
for (y1, y2), word in [((4, 13), "TAMAM"), ((20, 30), "VAZGEÇ")]:
    for y in range(y1, y2 + 1):
        for x in range(32):
            if c.get(x, y) in (2, 5):
                c.set(x, y, 1)
    m = pf.mask_of(word, F7)
    stamp(c.set, m, (32 - len(m[0])) // 2, y1 + 1, 2, shadow=5)
im.save(G + "misc/markings2.png")
print("screens 8-11 redrawn")
