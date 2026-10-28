#!/usr/bin/env python3
"""Add the Turkish letters missing from FireRed's Latin fonts.

The game already has Ç ç Ö ö Ü ü. This derives Ğ ğ İ ı Ş ş from existing
glyphs (base letter + breve / dot / the cedilla of ç) so they match the
original pixel style, and writes them into unused glyph slots:

    0x60 Ğ   0x61 ğ   0x62 İ   0x63 ı   0x64 Ş   0x65 ş

Palette indices: 0 = outside the glyph box, 1 = ink, 2 = shadow, 3 = box.
The shadow is the ink offset right, down and down-right, as in the original
fonts. Idempotent: each run rebuilds the slots from the base glyphs.
"""
import os
import sys

from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FONTS = os.path.join(ROOT, "graphics", "fonts")

SLOTS = {
    "Ğ": 0x60, "ğ": 0x61, "İ": 0x62, "ı": 0x63, "Ş": 0x64, "ş": 0x65,
}
BASE = {  # new glyph -> glyph whose box and width it copies
    0x60: 0xC1,  # G
    0x61: 0xDB,  # g
    0x62: 0xC3,  # I
    0x63: 0xDD,  # i
    0x64: 0xCD,  # S
    0x65: 0xE7,  # s
}
CHAR_c, CHAR_c_CEDILLA = 0xD7, 0x19


class Font:
    def __init__(self, path, cell_w, cell_h):
        self.path = path
        self.im = Image.open(path)
        self.px = self.im.load()
        self.cw, self.ch = cell_w, cell_h
        self.cols = self.im.size[0] // cell_w

    def origin(self, glyph):
        return (glyph % self.cols) * self.cw, (glyph // self.cols) * self.ch

    def cells(self, glyph):
        x0, y0 = self.origin(glyph)
        return [[self.px[x0 + x, y0 + y] for x in range(self.cw)] for y in range(self.ch)]

    def ink(self, glyph):
        return {(x, y) for y, row in enumerate(self.cells(glyph)) for x, v in enumerate(row) if v == 1}

    def put(self, glyph, box, ink):
        x0, y0 = self.origin(glyph)
        grid = [[3 if v != 0 else 0 for v in row] for row in box]
        for x, y in ink:
            for dx, dy in ((1, 0), (0, 1), (1, 1)):
                sx, sy = x + dx, y + dy
                if sx < self.cw and sy < self.ch and (sx, sy) not in ink:
                    grid[sy][sx] = 2
        for x, y in ink:
            grid[y][x] = 1
        for y in range(self.ch):
            for x in range(self.cw):
                self.px[x0 + x, y0 + y] = grid[y][x]


def rows(ink):
    return sorted({y for _, y in ink})


def cols(ink):
    return sorted({x for x, _ in ink})


def shift(ink, dy):
    return {(x, y + dy) for x, y in ink}


def breve(ink):
    """Breve whose bottom row sits two rows above the letter (one row gap
    after the shadow), spanning the letter's ink columns."""
    xs, top = cols(ink), rows(ink)[0]
    bottom = top - 2
    return {(xs[0], bottom - 1), (xs[-1], bottom - 1)} | {(x, bottom) for x in range(xs[0] + 1, xs[-1])}


def stem_column(ink):
    ys = rows(ink)
    mid = ys[len(ys) // 2]
    xs = [x for x, y in ink if y == mid]
    return xs[len(xs) // 2]


def derive(font):
    g, G = font.ink(0xDB), font.ink(0xC1)
    i, I = font.ink(0xDD), font.ink(0xC3)
    s, S = font.ink(0xE7), font.ink(0xCD)
    c_last = rows(font.ink(CHAR_c))[-1]
    cedilla = {(x, y) for x, y in font.ink(CHAR_c_CEDILLA) if y >= c_last}

    # ı: drop everything above the first empty row under the dot.
    ys = rows(i)
    gap = next(y for y in range(ys[0], ys[-1]) if y not in ys)
    dotless = {(x, y) for x, y in i if y > gap}

    dot_row = rows(I)[0] - 2
    return {
        0x60: G | breve(G),
        0x61: g | breve(g),
        0x62: I | {(stem_column(I), dot_row)},
        0x63: dotless,
        0x64: shift(S, -1) | cedilla,
        0x65: shift(s, -1) | cedilla,
    }


def main():
    fonts = [Font(os.path.join(FONTS, n + ".png"), 16, 16) for n in ("latin_normal", "latin_male", "latin_female")]
    fonts.append(Font(os.path.join(FONTS, "latin_small.png"), 8, 16))
    for font in fonts:
        new = derive(font)
        for glyph, ink in new.items():
            font.put(glyph, font.cells(BASE[glyph]), ink)
        font.im.save(font.path, bits=2)  # the originals are 2bpp indexed PNGs
        print("updated", os.path.relpath(font.path, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
