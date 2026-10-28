"""PC box screen (graphics/pokemon_storage/menu.png, drawn through its .bin
tilemaps): PkMn DATA -> POKé BİLGİ, CLOSE BOX -> KUTUYU KAPAT,
PARTY POKéMON -> TAKIM, CANCEL -> VAZGEÇ.

The words are split over scattered tiles, so they are edited on a
TileCanvas laid out like the screen.

usage: python -I pc_storage.py <repo root>
"""
import os, sys
from collections import Counter
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tilecanvas import TileCanvas, read_map
import pixfont as pf

G = sys.argv[1] + "/graphics/pokemon_storage/"
im = Image.open(G + "menu.png")
px = im.load()


def canvas(name, w):
    return TileCanvas(px, im.width, read_map(G + name + ".bin"), w, 0x100)


def glyphs(spec):
    return {k: [r.replace("#", "1") for r in v.split("/")] for k, v in spec.items()}


def clear(c, box, inks, bg):
    x1, y1, x2, y2 = box
    for y in range(y1, y2 + 1):
        for x in range(x1, x2 + 1):
            if c.get(x, y) in inks:
                c.set(x, y, bg)


def stamp(c, m, x0, y0, ink, shadow=None, outline=None, ink_by_row=None):
    h, w = len(m), len(m[0])
    on = lambda x, y: 0 <= y < h and 0 <= x < w and m[y][x]
    for y in range(-1, h + 1):
        for x in range(-1, w + 1):
            if on(x, y):
                c.set(x0 + x, y0 + y, ink_by_row[y] if ink_by_row else ink)
            elif outline is not None and any(on(x + a, y + b) for a in (-1, 0, 1) for b in (-1, 0, 1)):
                c.set(x0 + x, y0 + y, outline)
            elif shadow is not None and (on(x - 1, y) or on(x, y - 1) or on(x - 1, y - 1)):
                c.set(x0 + x, y0 + y, shadow)


# 7-row single-stroke capitals (as CLOSE BOX / CANCEL / PARTY POKéMON)
C7 = dict(pf._C7)
C7["P"] = "###./#..#/#..#/###./#.../#.../#..."
C7["V"] = "#..#/#..#/#..#/#..#/#..#/.##./.##."  # 4 wide: VAZGEÇ fits the CANCEL box
F7 = glyphs(C7)
F7["Ç"] = F7["C"] + [".1.."]

# PkMn DATA: two-stroke letters, 6 rows, shaded by row and outlined
DATA = glyphs({
    "P": "####./##.##/##.##/####./##.../##...",
    "O": ".###./##.##/##.##/##.##/##.##/.###.",
    "K": "##.##/##.##/####./####./##.##/##.##",
    "B": "####./##.##/####./##.##/##.##/####.",
    "L": "##.../##.../##.../##.../##.../#####",
    "G": ".####/##.../##.##/##.##/##.##/.####",
    "İ": "##/../##/##/##/##",
    "é": "...##/...../.###./#####/##.../.####",
})

# --- PkMn DATA (two states, 16 rows apart) ---
c = canvas("pkmn_data", 8)
m = pf.mask_of("POKé BİLGİ", DATA, gap=1, space=3)
for oy in (0, 16):
    clear(c, (4, oy + 4, 60, oy + 13), {14, 10, 5, 3}, 2)
    stamp(c, m, 6, oy + 5, None, outline=3, ink_by_row=[14, 14, 14, 10, 10, 5])

# --- CLOSE BOX (normal with shadow, then the dim state) ---
c = canvas("close_box_button", 9)
m = pf.mask_of("KUTUYU KAPAT", F7, gap=1, space=3)
x0 = (72 - len(m[0])) // 2
assert x0 >= 5, x0
clear(c, (5, 5, 65, 12), {14, 9}, 8)
stamp(c, m, x0, 5, 14, shadow=9)
clear(c, (5, 21, 65, 27), {9}, 8)
stamp(c, m, x0, 21, 9)

# --- party panel: CANCEL and the PARTY POKéMON button ---
c = canvas("party_menu", 12)
m = pf.mask_of("VAZGEÇ", F7)
clear(c, (56, 140, 89, 147), {8, 7}, 6)
stamp(c, m, 56 + (34 - len(m[0])) // 2, 140, 8, shadow=7)
m = pf.mask_of("TAKIM", F7)
clear(c, (4, 163, 67, 171), {8, 7}, 14)
stamp(c, m, 4 + (64 - len(m[0])) // 2, 164, 8, shadow=7)

im.save(G + "menu.png")
print("PC storage buttons redrawn")
