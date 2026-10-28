"""Level symbol "Lv" -> "Sv" (seviye), matching the "Sv." used in text.

1. Font glyphs 0x34 (LV) and 0x105 (extra symbol LV_2) in the Latin fonts:
   the L (columns 0-2) becomes a 3-wide S of the same height; the v stays.
   Palette: 0 outside box, 1 ink, 2 shadow (ink shifted right/down), 3 box.
2. The "Lv" baked into the battle healthbox sheets (ink 1, shadow 3 on
   background 2): found by exact match, redrawn the same way.

usage: python -I lv_symbol.py <repo root>
"""
import sys
from PIL import Image

G = sys.argv[1] + "/graphics/"
S3 = ["111", "1..", "1..", "111", "..1", "..1", "111"]


def s_ink(top):
    return {(x, top + y) for y, r in enumerate(S3) for x, c in enumerate(r) if c == "1"}


def redo_glyph(px, x0, y0, cw, ch, INK=1, SH=2, BOX=3):
    cells = {(x, y): px[x0 + x, y0 + y] for y in range(ch) for x in range(cw)}
    ink = {p for p, v in cells.items() if v == INK}
    l_part = {p for p in ink if p[0] <= 2}
    top = min(y for _, y in l_part)
    assert max(y for _, y in l_part) - top == 6, "unexpected L height"
    ink = (ink - l_part) | s_ink(top)
    for (x, y), v in cells.items():
        if v in (SH, INK):
            px[x0 + x, y0 + y] = BOX
    for x, y in ink:
        for dx, dy in ((1, 0), (0, 1), (1, 1)):
            q = (x + dx, y + dy)
            if q in cells and q not in ink and cells[q] != 0:
                px[x0 + q[0], y0 + q[1]] = SH
    for x, y in ink:
        px[x0 + x, y0 + y] = INK


for name, cw in [("latin_normal", 16), ("latin_male", 16), ("latin_female", 16), ("latin_small", 8)]:
    im = Image.open(G + "fonts/" + name + ".png")
    px = im.load()
    cols = im.width // cw
    for g in (0x34, 0x105):
        x0, y0 = (g % cols) * cw, (g // cols) * 16
        if y0 + 16 <= im.height:
            redo_glyph(px, x0, y0, cw, 16)
    im.save(G + "fonts/" + name + ".png")
    print("font", name)

# battle healthbox "Lv": rows of ink (1) relative to the top of the L
LV = ["1.......", "1...1.1.", "1...1.1.", "1...1.1.", "1111.1.."]
S5 = [(c, r) for r, row in enumerate(["111", "1..", "111", "..1", "111"]) for c, ch in enumerate(row) if ch == "1"]
import glob, os
for path in sorted(glob.glob(G + "battle_interface/*.png")):
    im = Image.open(path)
    px = im.load()
    W, H = im.size
    n = 0
    for y in range(H - 6):
        for x in range(W - 7):
            if all((px[x + c, y + r] & 15 == 1) == (LV[r][c] == "1") for r in range(5) for c in range(8)):
                # clear L + its shadow (cols 0-3, rows 0-5) to the background, draw S
                for r in range(6):
                    for c in range(4):
                        if px[x + c, y + r] & 15 in (1, 3):
                            px[x + c, y + r] = (px[x + c, y + r] & 0xF0) | 2
                for c, r in S5:
                    px[x + c, y + r] = (px[x + c, y + r] & 0xF0) | 1
                for c, r in S5:
                    for dc, dr in ((1, 0), (0, 1), (1, 1)):
                        q = (x + c + dc, y + r + dr)
                        if px[q] & 15 == 2:
                            px[q] = (px[q] & 0xF0) | 3
                n += 1
    if n:
        im.save(path)
        print(os.path.basename(path), "Lv ->", n)
