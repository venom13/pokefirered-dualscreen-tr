"""Tiny helper for redrawing baked-in text in indexed GBA PNGs.

Glyphs are lists of strings ('1' = ink). `render()` lays a string out with a
fixed gap and returns an ink mask; `stamp()` writes the mask into a palette
image with optional outline (8-neighbour dilation) or drop shadow (+1,+1).
"""


def mask_of(text, font, gap=1, space=3):
    h = max(len(g) for g in font.values())
    cols = []
    for i, ch in enumerate(text):
        if ch == " ":
            cols += [[False] * h for _ in range(space)]
            continue
        g = font[ch]
        w = max(len(r) for r in g)
        for x in range(w):
            cols.append([y < len(g) and x < len(g[y]) and g[y][x] == "1" for y in range(h)])
        if i != len(text) - 1:
            cols += [[False] * h for _ in range(gap)]
    return [[c[y] for c in cols] for y in range(h)]  # rows


def width(text, font, gap=1, space=3):
    return len(mask_of(text, font, gap, space)[0])


def stamp(px, mask, x0, y0, ink, outline=None, shadow=None, clip=None):
    """Write mask at (x0, y0). clip = (x1, y1, x2, y2) exclusive bounds."""
    h, w = len(mask), len(mask[0])
    x1, y1, x2, y2 = clip if clip else (-10**9, -10**9, 10**9, 10**9)

    def put(x, y, c):
        if x1 <= x < x2 and y1 <= y < y2:
            px[x, y] = c

    on = lambda x, y: 0 <= y < h and 0 <= x < w and mask[y][x]
    if outline is not None:
        for y in range(-1, h + 1):
            for x in range(-1, w + 1):
                if not on(x, y) and any(on(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                    put(x0 + x, y0 + y, outline)
    if shadow is not None:
        for y in range(h + 1):
            for x in range(w + 1):
                if not on(x, y) and (on(x - 1, y) or on(x, y - 1) or on(x - 1, y - 1)):
                    put(x0 + x, y0 + y, shadow)
    for y in range(h):
        for x in range(w):
            if mask[y][x]:
                put(x0 + x, y0 + y, ink)


def fill(px, box, c):
    x1, y1, x2, y2 = box
    for y in range(y1, y2):
        for x in range(x1, x2):
            px[x, y] = c


# --- fonts -----------------------------------------------------------------

# 4x7 capitals of the naming-screen BACK/OK buttons (some 3 or 5 wide)
BIG7 = {  # row 0 is above the cap height (only the dot of İ uses it)
    "G": ["....", ".11.", "1..1", "1...", "1.11", "1..1", "1..1", ".111"],
    "E": ["....", "1111", "1...", "1...", "111.", "1...", "1...", "1111"],
    "R": ["....", "111.", "1..1", "1..1", "111.", "1.1.", "1..1", "1..1"],
    "İ": [".1.", "...", "111", ".1.", ".1.", ".1.", ".1.", "111"],
    "T": ["...", "111", ".1.", ".1.", ".1.", ".1.", ".1.", ".1."],
    "A": ["...", ".1.", "1.1", "1.1", "111", "1.1", "1.1", "1.1"],
    "M": [".....", "1...1", "11.11", "1.1.1", "1...1", "1...1", "1...1", "1...1"],
}

# 3x5 capitals of the "B BUTTON" / "START" / "SELECT" captions (row 5 = below baseline)
SMALL5 = {
    "T": ["111", ".1.", ".1.", ".1.", ".1.", "..."],
    "U": ["1.1", "1.1", "1.1", "1.1", "111", "..."],
    "Ş": ["111", "1..", "111", "..1", "111", ".1."],
}

# naming-screen page tabs: capitals 4x6 with a row for marks on top,
# lower case with x-height 4 (rows 2-5) and descenders in rows 6-7
TAB = {
    "B": ["....", "....", "111.", "1..1", "111.", "1..1", "111."],
    "Ü": ["1..1", "....", "1..1", "1..1", "1..1", "1..1", ".11."],
    "Y": ["....", "....", "1..1", "1..1", ".11.", "..1.", "..1."],
    "K": ["....", "....", "1..1", "1.1.", "11..", "1.1.", "1..1"],
    "k": ["1..", "1..", "1.1", "11.", "1.1", "1.1"],
    "ü": ["1.1", "...", "1.1", "1.1", "1.1", ".11"],
    "ç": ["...", "...", ".11", "1..", "1..", ".11", ".1."],
    "d": ["..1", "..1", ".11", "1.1", "1.1", ".11"],
    "i": ["1", ".", "1", "1", "1", "1"],
    "ğ": ["1.1", ".1.", ".11", "1.1", "1.1", ".11", "..1", "11."],
    "e": ["...", "...", ".1.", "111", "1..", ".11"],
    "r": ["...", "...", "1.1", "11.", "1..", "1.."],
}

# Summary-screen / move-info label capitals: 7 rows of cap height, with a row
# above (row 0: dots and breves) and a row below (row 8: cedillas).
_C7 = {
    "A": ".##./#..#/#..#/####/#..#/#..#/#..#",
    "B": "###./#..#/#..#/###./#..#/#..#/###.",
    "C": ".##./#..#/#.../#.../#.../#..#/.##.",
    "D": "###./#..#/#..#/#..#/#..#/#..#/###.",
    "E": "####/#.../#.../###./#.../#.../####",
    "G": ".##./#..#/#.../#.##/#..#/#..#/.###",
    "H": "#..#/#..#/#..#/####/#..#/#..#/#..#",
    "I": "###/.#./.#./.#./.#./.#./###",
    "K": "#..#/#.#./#.#./##../#.#./#.#./#..#",
    "L": "#.../#.../#.../#.../#.../#.../####",
    "M": "#...#/##.##/#.#.#/#...#/#...#/#...#/#...#",
    "N": "#..#/##.#/##.#/#.##/#.##/#..#/#..#",
    "O": ".##./#..#/#..#/#..#/#..#/#..#/.##.",
    "R": "###./#..#/#..#/###./#.#./#..#/#..#",
    "S": ".##./#..#/#.../.##./...#/#..#/.##.",
    "T": "#####/..#../..#../..#../..#../..#../..#..",
    "U": "#..#/#..#/#..#/#..#/#..#/#..#/.##.",
    "V": "#...#/#...#/#...#/.#.#./.#.#./.#.#./..#..",
    "Y": "#...#/#...#/.#.#./.#.#./..#../..#../..#..",
    "Z": "####/...#/..#./..#./.#../#.../####",
    ".": "./././././././#",
}
# accented capitals: the body is one row shorter so the mark keeps a gap
_SHORT = {
    "U": "#..#/#..#/#..#/#..#/#..#/.##.",
    "O": ".##./#..#/#..#/#..#/#..#/.##.",
    "I": "###/.#./.#./.#./.#./###",
    "G": ".##./#.../#.##/#..#/#..#/.###",
}
_MARK = {"Ü": ("U", "#..#", None), "Ö": ("O", "#..#", None), "İ": ("I", ".#.", None),
         "Ğ": ("G", ".##.", None), "Ş": ("S", None, ".#.."), "Ç": ("C", None, "..#.")}


def _cap9(rows, top=None, bottom=None):
    r = rows.split("/")
    w = max(len(x) for x in r)
    blank = "." * w
    return [(top or blank).replace("#", "1")] + [x.replace("#", "1") for x in r] + [(bottom or blank).replace("#", "1")]


CAP9 = {k: _cap9(v) for k, v in _C7.items()}
for _k, (_base, _top, _bottom) in _MARK.items():
    if _top:  # mark row, blank row, then the short body
        _w = len(_top)
        CAP9[_k] = [_top.replace("#", "1"), "." * _w] + [r.replace("#", "1") for r in _SHORT[_base].split("/")] + ["." * _w]
    else:
        CAP9[_k] = _cap9(_C7[_base], _top, _bottom)
