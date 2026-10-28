"""Trainer card: TRAINER CARD -> EĞİTMEN KARTI, BADGES -> ROZETLER,
TRAINER: -> EĞİTMEN: (FireRed card), plus the RSE card shown over link.

Each word is erased (its ink colours set to the local background) and redrawn
with a font matching the stroke style of the original. Accent marks sit in
the free rows above the caps; where there is only one free row the accented
letter body is one row shorter ("tight").

usage: python -I trainer_card.py <repo root>
"""
import sys
from PIL import Image

D = sys.argv[1] + "/graphics/trainer_card/"


def font(spec):
    return {k: v.split("/") for k, v in spec.items()}


# big two-stroke logo letters, 9 rows
LOGO = font({
    "E": "######/##..../##..../##..../#####./##..../##..../##..../######",
    "G": ".#####/##..../##..../##..../##.###/##..##/##..##/##..##/.#####",
    "I": "####/.##./.##./.##./.##./.##./.##./.##./####",
    "T": "######/..##../..##../..##../..##../..##../..##../..##../..##..",
    "M": "##...##/###.###/#######/##.#.##/##...##/##...##/##...##/##...##/##...##",
    "N": "##..##/###.##/###.##/######/##.###/##.###/##..##/##..##/##..##",
    "K": "##..##/##.##./####../###.../###.../####../##.##./##..##/##..##",
    "A": "######/##..##/##..##/##..##/######/##..##/##..##/##..##/##..##",
    "R": "######/##..##/##..##/##..##/#####./##.##./##..##/##..##/##..##",
})
LOGO_MARKS = {"Ğ": ("G", ["#....#", ".####."]), "İ": ("I", [".##.", ".##."])}

# two-stroke 6-row letters (TRAINER: and the RSE banner); 5-row short forms
B2 = font({
    "A": ".####./##..##/##..##/######/##..##/##..##",
    "E": "#####/##.../####./##.../##.../#####",
    "G": ".#####/##..../##.###/##..##/##..##/.#####",
    "I": "####/.##./.##./.##./.##./####",
    "K": "##..##/##.##./####../####../##.##./##..##",
    "M": "##...##/###.###/#######/##.#.##/##...##/##...##",
    "N": "##..##/###.##/######/##.###/##..##/##..##",
    "R": "#####./##..##/##..##/#####./##.##./##..##",
    "T": "######/..##../..##../..##../..##../..##..",
    ":": "./././#/./#",
})
B2_SHORT = font({"G": ".#####/##..../##.###/##..##/.#####", "I": "####/.##./.##./.##./####"})
B2_MARKS = {"Ğ": ("G", ".####."), "İ": ("I", ".##.")}

# single-stroke small letters
S3 = font({"R": "##./#.#/##./#.#/#.#", "O": ".#./#.#/#.#/#.#/.#.", "Z": "###/..#/.#./#../###",
           "E": "###/#../##./#../###", "T": "###/.#./.#./.#./.#.", "L": "#../#../#../#../###"})
S4 = font({"R": "###./#..#/###./#.#./#..#/#..#", "O": ".##./#..#/#..#/#..#/#..#/.##.",
           "Z": "####/...#/..#./.#../#.../####", "E": "####/#.../###./#.../#.../####",
           "T": "#####/..#../..#../..#../..#../..#..", "L": "#.../#.../#.../#.../#.../####"})


def layout(text, glyph_for, gap=1, space=3):
    """-> list of (x offset, rows, top offset) per glyph; total width"""
    out, x = [], 0
    for ch in text:
        if ch == " ":
            x += space
            continue
        rows, top = glyph_for(ch)
        out.append((x, rows, top))
        x += max(len(r) for r in rows) + gap
    return out, x - gap


def logo_glyph(ch):
    if ch in LOGO_MARKS:
        base, marks = LOGO_MARKS[ch]
        return marks + ["." * len(marks[0])] + LOGO[base], -3
    return LOGO[ch], 0


def b2_glyph(tight):
    def g(ch):
        if ch in B2_MARKS:
            base, mark = B2_MARKS[ch]
            if tight:  # mark on the caps' top row, body one row shorter
                return [mark] + B2_SHORT[base], 0
            return [mark, "." * len(mark)] + B2[base], -2
        return B2[ch], 0
    return g


def plain(f):
    return lambda ch: (f[ch], 0)


def draw(px, text, glyph_for, x0, top, ink):
    items, w = layout(text, glyph_for)
    for dx, rows, dy in items:
        for r, row in enumerate(rows):
            for c, ch in enumerate(row):
                if ch == "#":
                    px[x0 + dx + c, top + dy + r] = (px[x0 + dx + c, top + dy + r] & 0xF0) | ink
    return w


def clear(px, box, inks, bg):
    x1, y1, x2, y2 = box
    for y in range(y1, y2 + 1):
        for x in range(x1, x2 + 1):
            if px[x, y] & 15 in inks:
                px[x, y] = (px[x, y] & 0xF0) | bg


# --- FireRed card --------------------------------------------------------------
im = Image.open(D + "tiles.png")
px = im.load()
clear(px, (64, 25, 127, 36), {8, 9}, 10)
assert draw(px, "EĞİTMEN", logo_glyph, 64, 28, 8) <= 64
clear(px, (64, 41, 95, 52), {8, 9}, 10)
assert draw(px, "KARTI", logo_glyph, 64, 44, 8) <= 32
clear(px, (96, 42, 127, 46), {14}, 15)
assert draw(px, "ROZETLER", plain(S3), 97, 42, 14) <= 31
clear(px, (0, 72, 63, 77), {5}, 13)
assert draw(px, "EĞİTMEN:", b2_glyph(True), 5, 72, 5) <= 58
im.save(D + "tiles.png")

# --- RSE card (link) -----------------------------------------------------------
im = Image.open(D + "rse/tiles.png")
px = im.load()
clear(px, (48, 1, 89, 6), {1}, 10)
assert draw(px, "ROZETLER", plain(S4), 49, 1, 1) <= 40
clear(px, (0, 67, 91, 76), {15, 8}, 13)
w = draw(px, "EĞİTMEN KARTI", b2_glyph(False), 2, 69, 15)
assert w <= 89, w
im.save(D + "rse/tiles.png")
print("trainer cards redrawn")
