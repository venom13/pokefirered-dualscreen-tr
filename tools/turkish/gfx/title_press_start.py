"""Title screen: redraw "PRESS START" as "START'A BAS" in the same outlined font.

The text lives in graphics/title_screen/copyright_press_start.png, map row 16,
tiles 0x15-0x1A and 0x35-0x3A (12 tiles, 96 px). The blink is palette based,
so only the pixels of those tiles change. Glyphs S, T, A, R are cut from the
original strip (fill pixels = connected components); B and the apostrophe are
drawn in the same style. Fill is shaded by row, outline is the 8-neighbour
dilation of the fill in colour 1, background is colour 6.

usage: python -I title_press_start.py <repo root>
"""
import sys
from PIL import Image

ROOT = sys.argv[1]
PNG = ROOT + "/graphics/title_screen/copyright_press_start.png"
TILES = list(range(0x15, 0x1B)) + list(range(0x35, 0x3B))
BG, OUTLINE = 6, 1
ROW_SHADE = {2: 5, 3: 5, 4: 4, 5: 3, 6: 3}

im = Image.open(PNG)
px = im.load()
W = 8 * len(TILES)


def read_strip():
    s = [[BG] * W for _ in range(8)]
    for i, t in enumerate(TILES):
        tx, ty = (t % 16) * 8, (t // 16) * 8
        for y in range(8):
            for x in range(8):
                s[y][i * 8 + x] = px[tx + x, ty + y]
    return s


def components(s):
    """Fill pixels (not background/outline) grouped 4-connected, left to right."""
    seen, comps = set(), []
    for x in range(W):
        for y in range(8):
            if (x, y) in seen or s[y][x] in (BG, OUTLINE):
                continue
            stack, comp = [(x, y)], set()
            while stack:
                cx, cy = stack.pop()
                if (cx, cy) in seen or not (0 <= cx < W and 0 <= cy < 8) or s[cy][cx] in (BG, OUTLINE):
                    continue
                seen.add((cx, cy)); comp.add((cx, cy))
                stack += [(cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)]
            comps.append(comp)
    comps.sort(key=lambda c: min(p[0] for p in c))
    return comps


def to_mask(comp):
    x0 = min(p[0] for p in comp)
    w = max(p[0] for p in comp) - x0 + 1
    return [[(x0 + x, y) in comp for x in range(w)] for y in range(8)]


def from_rows(rows):
    """Rows for y = 2..6, 'X' = fill."""
    m = [[False] * len(rows[0]) for _ in range(8)]
    for i, r in enumerate(rows):
        for x, c in enumerate(r):
            m[2 + i][x] = c == "X"
    return m


strip = read_strip()
comps = components(strip)
# P R E S S  S T (A+R touch at one pixel) T
assert len(comps) == 9, len(comps)
ar = comps[7]
split = min(p[0] for p in ar) + 7
G = {"S": to_mask(comps[3]), "T": to_mask(comps[6]),
     "A": to_mask({p for p in ar if p[0] < split}), "R": to_mask({p for p in ar if p[0] >= split})}
G["B"] = from_rows(["XXXXXX.", "XX...XX", "XXXXXX.", "XX...XX", "XXXXXX."])
G["'"] = from_rows(["XX", "XX", ".X"])

TEXT, GAP, SPACE = "START'A BAS", 1, 9
out = [[BG] * W for _ in range(8)]
fill = [[False] * W for _ in range(8)]
x = 3  # same left edge as the original text
for ch in TEXT:
    if ch == " ":
        x += SPACE - GAP
        continue
    m = G[ch]
    for y in range(8):
        for dx, on in enumerate(m[y]):
            if on:
                fill[y][x + dx] = True
    x += len(m[0]) + GAP
assert x <= W, x
for y in range(8):
    for xx in range(W):
        if fill[y][xx]:
            out[y][xx] = ROW_SHADE.get(y, 3)
        elif any(fill[yy][xxx] for yy in range(max(0, y - 1), min(8, y + 2))
                 for xxx in range(max(0, xx - 1), min(W, xx + 2))):
            out[y][xx] = OUTLINE
for i, t in enumerate(TILES):
    tx, ty = (t % 16) * 8, (t // 16) * 8
    for y in range(8):
        for xx in range(8):
            px[tx + xx, ty + y] = out[y][i * 8 + xx]
im.save(PNG)
print("text width", x - 3, "px of", W - 3)
