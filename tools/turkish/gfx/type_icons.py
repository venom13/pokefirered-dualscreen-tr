"""Type icons and move-info labels in graphics/interface/menu_info.png.

Icons are 32x12 cells; text is ink 15 with a shadow 14 to the right/below on
the type's body colour (some bodies are two-tone, so each row keeps its own
colour, read from the cell's last column). Labels (TYPE POWER ACCURACY
EFFECT; PP stays) are ink 15 with a 14 outline on a 14 pill.
New words use a 3-wide, 6-row capital font so that accented letters keep the
same cap height: marks go two rows above the caps, cedillas one row below.
Colour indices carry a palette bank in the high nibble; only the low nibble
is rewritten.

usage: python -I type_icons.py <repo root>
"""
import sys
from PIL import Image

PNG = sys.argv[1] + "/graphics/interface/menu_info.png"
INK, SHADE = 15, 14

_T6 = {
    "A": ".#./#.#/#.#/###/#.#/#.#", "B": "##./#.#/##./#.#/#.#/##.",
    "C": ".##/#../#../#../#../.##", "D": "##./#.#/#.#/#.#/#.#/##.",
    "E": "###/#../##./#../#../###", "G": ".##/#../#.#/#.#/#.#/.##",
    "H": "#.#/#.#/###/#.#/#.#/#.#", "I": "###/.#./.#./.#./.#./###",
    "J": "..#/..#/..#/..#/#.#/.#.", "K": "#.#/#.#/##./#.#/#.#/#.#",
    "L": "#../#../#../#../#../###", "M": "#...#/##.##/#.#.#/#...#/#...#/#...#",
    "N": "#..#/##.#/#.##/#..#/#..#/#..#", "O": ".#./#.#/#.#/#.#/#.#/.#.",
    "P": "##./#.#/##./#../#../#..", "R": "##./#.#/##./#.#/#.#/#.#",
    "S": ".##/#../.#./..#/..#/##.", "T": "###/.#./.#./.#./.#./.#.",
    "U": "#.#/#.#/#.#/#.#/#.#/###", "V": "#.#/#.#/#.#/#.#/.#./.#.",
    "Y": "#.#/#.#/.#./.#./.#./.#.", "Z": "###/..#/.#./.#./#../###",
}
_MARKS = {"Ü": ("U", "#.#", ""), "Ö": ("O", "#.#", ""), "İ": ("I", ".#.", ""),
          "Ç": ("C", "", ".#."), "Ş": ("S", "", ".#.")}


def glyph(ch):
    base, top, bottom = _MARKS.get(ch, (ch, "", ""))
    body = _T6[base].split("/")
    w = len(body[0])
    rows = [top or "." * w, "." * w] + body + [bottom or "." * w]
    return [r.replace("#", "1") for r in rows]  # 9 rows: mark, gap, 6 caps, cedilla


def mask(text):
    cols = []
    for i, ch in enumerate(text):
        g = glyph(ch)
        cols += [[g[y][x] == "1" for y in range(9)] for x in range(len(g[0]))]
        if i < len(text) - 1:
            cols.append([False] * 9)
    return [[c[y] for c in cols] for y in range(9)]


im = Image.open(PNG)
px = im.load()


def setlo(x, y, v, bank=None):
    px[x, y] = ((px[x, y] & 0xF0) if bank is None else bank) | v


def lo(x, y):
    return px[x, y] & 15


# --- type icons --------------------------------------------------------------
TYPES = [  # cell origin, new name (NORMAL and ??? stay)
    ((32, 16), "ATEŞ"), ((64, 16), "SU"), ((96, 16), "ÇİMEN"),
    ((0, 32), "ELEKTR"), ((32, 32), "KAYA"), ((64, 32), "TOPRAK"), ((96, 32), "BUZ"),
    ((0, 48), "UÇAN"), ((32, 48), "DÖVÜŞ"), ((64, 48), "HAYALT"), ((96, 48), "BÖCEK"),
    ((0, 64), "ZEHİR"), ((32, 64), "PSİŞİK"), ((64, 64), "ÇELİK"), ((96, 64), "KARA"),
    ((0, 80), "EJDER"),
]
for (cx, cy), name in TYPES:
    for y in range(cy + 1, cy + 11):
        body = lo(cx + 31, y)
        for x in range(cx + 1, cx + 31):
            if lo(x, y) in (INK, SHADE):
                setlo(x, y, body)
    m = mask(name)
    w = len(m[0])
    x0, y0 = cx + (32 - w) // 2, cy + 1  # mark row = body row under the border
    on = lambda c, r: 0 <= r < 9 and 0 <= c < w and m[r][c]
    for r in range(10):
        for c in range(w + 1):
            if not on(c, r) and (on(c - 1, r) or on(c, r - 1) or on(c - 1, r - 1)):
                if cx < x0 + c < cx + 31 and y0 + r < cy + 11:
                    setlo(x0 + c, y0 + r, SHADE)
            elif on(c, r):
                setlo(x0 + c, y0 + r, INK)

# --- move-info labels ----------------------------------------------------------
LABELS = [  # x1, x2, first text row of the old label, new text
    (64, 101, 83, "TÜR"),       # TYPE
    (0, 37, 99, "GÜÇ"),         # POWER
    (64, 101, 99, "İSABET"),    # ACCURACY
    (64, 101, 115, "ETKİ"),     # EFFECT
]
for x1, x2, top, text in LABELS:
    pill_rows = range(top + 1, top + 6)
    for y in range(top - 3, top + 9):
        for x in range(x1, x2 + 1):
            if lo(x, y) in (INK, SHADE):
                setlo(x, y, SHADE if y in pill_rows else 0)
    m = mask(text)
    w = len(m[0])
    pill = [x for x in range(x1, x2 + 1) if lo(x, top + 3) == SHADE]
    bank = px[pill[0], top + 3] & 0xF0  # rows above the old label are bank 0
    x0 = (pill[0] + pill[-1] + 1 - w) // 2
    y0 = top - 2  # caps start on the old first text row
    on = lambda c, r: 0 <= r < 9 and 0 <= c < w and m[r][c]
    for r in range(-1, 10):
        for c in range(-1, w + 1):
            if on(c, r):
                setlo(x0 + c, y0 + r, INK, bank)
            elif any(on(c + dc, r + dr) for dc in (-1, 0, 1) for dr in (-1, 0, 1)):
                setlo(x0 + c, y0 + r, SHADE, bank)

im.save(PNG)
print("type icons:", len(TYPES), "labels:", len(LABELS))
