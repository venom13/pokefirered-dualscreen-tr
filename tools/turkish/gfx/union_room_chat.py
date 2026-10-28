"""Union Room chat: key hints BACK / SWITCH / SEND -> GERİ / DEĞİŞTİR / GÖNDER
and the REGISTER label -> KAYDET. OK stays (TAMAM does not fit its slot).

The hint bar is drawn from union_room_chat/bg.png through bg.bin: white
(14) 3x5 letters on dark boxes (15). Accented letters use a 4-row body under
their mark so the cap height stays 5 rows.

usage: python -I union_room_chat.py <repo root>
"""
import os, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tilecanvas import TileCanvas, read_map
import pixfont as pf

G = sys.argv[1] + "/graphics/union_room_chat/"
WHITE, BOX = 14, 15


def glyphs(spec):
    return {k: [r.replace("#", "1") for r in v.split("/")] for k, v in spec.items()}


# rows: 0 = mark, 1-5 = caps, 6 = cedilla
F5 = glyphs({
    "G": ".../.##/#../#.#/#.#/.##", "E": ".../###/#../##./#../###", "R": ".../##./#.#/##./#.#/#.#",
    "D": ".../##./#.#/#.#/#.#/##.", "T": ".../###/.#./.#./.#./.#.", "N": ".../##./#.#/#.#/#.#/#.#",
    "İ": "#/./#/#/#/#", "Ğ": "###/.../.##/#../#.#/.##", "Ö": "#.#/.../.#./#.#/#.#/.#.",
    "Ş": ".../.##/#../.#./..#/##./.#.",
})
F7 = glyphs({
    "K": "#.#/#.#/##./#../##./#.#/#.#", "A": ".#./#.#/#.#/###/#.#/#.#/#.#",
    "Y": "#.#/#.#/#.#/.#./.#./.#./.#.", "D": "##./#.#/#.#/#.#/#.#/#.#/##.",
    "E": "###/#../#../##./#../#../###", "T": "###/.#./.#./.#./.#./.#./.#.",
})


def put_text(get, set_, box, top, word, font, bottom):
    x1, x2 = box
    for y in range(top, bottom + 1):
        for x in range(x1, x2 + 1):
            if get(x, y) is not None:
                set_(x, y, BOX)
    m = pf.mask_of(word, font)
    x0 = (x1 + x2 + 1 - len(m[0])) // 2
    assert x0 >= x1, (word, x0, x1)
    for r, row in enumerate(m):
        for c, on in enumerate(row):
            if on:
                set_(x0 + c, top + r, WHITE)


im = Image.open(G + "bg.png")
px = im.load()
c = TileCanvas(px, im.width, read_map(G + "bg.bin"), 32)
for box, word in [((94, 114), "GERİ"), ((149, 180), "DEĞİŞTİR"), ((215, 239), "GÖNDER")]:
    put_text(c.get, c.set, box, 0, word, F5, 7)
im.save(G + "bg.png")

im = Image.open(G + "icons.png")
px = im.load()
setp = lambda x, y, v: px.__setitem__((x, y), (px[x, y] & 0xF0) | v)
put_text(lambda x, y: px[x, y] & 15, setp, (1, 30), 52, "KAYDET", F7, 58)
im.save(G + "icons.png")
print("union room chat hints redrawn")
