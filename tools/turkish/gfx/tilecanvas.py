"""Edit tile-sheet text in its on-screen arrangement.

A TileCanvas lays the tiles named by a tilemap out as they appear on screen
(flips honoured). Reads and writes go through to the tile sheet's pixels, so
a word split across scattered tiles can be erased and redrawn as one piece.
A tile used at several places changes everywhere it is used.
"""
import struct
from PIL import Image


def read_map(path):
    d = open(path, "rb").read()
    return list(struct.unpack("<%dH" % (len(d) // 2), d))


class TileCanvas:
    def __init__(self, px, sheet_w, entries, width_tiles, base=0):
        self.px, self.tw = px, sheet_w // 8
        self.wt = width_tiles
        self.ht = (len(entries) + width_tiles - 1) // width_tiles
        self.entries, self.base = entries, base

    @property
    def size(self):
        return self.wt * 8, self.ht * 8

    def _src(self, x, y):
        i = (y // 8) * self.wt + x // 8
        if not (0 <= x < self.wt * 8 and 0 <= y < self.ht * 8) or i >= len(self.entries):
            return None
        e = self.entries[i]
        t = (e & 0x3FF) - self.base
        if t < 0:
            return None
        sx, sy = x % 8, y % 8
        if e & 0x400:
            sx = 7 - sx
        if e & 0x800:
            sy = 7 - sy
        return (t % self.tw) * 8 + sx, (t // self.tw) * 8 + sy

    def get(self, x, y):
        s = self._src(x, y)
        return None if s is None else self.px[s] & 15

    def set(self, x, y, v):
        s = self._src(x, y)
        if s is not None:
            self.px[s] = (self.px[s] & 0xF0) | v

    def dump(self, chars=None):
        w, h = self.size
        rows = []
        for y in range(h):
            r = ""
            for x in range(w):
                v = self.get(x, y)
                r += " " if v is None else (chars.get(v, "%x" % v) if chars else "%x" % v)
            rows.append(r)
        return "\n".join(rows)

    def render(self, colors, scale=4):
        w, h = self.size
        im = Image.new("RGB", (w, h), (0, 0, 0))
        p = im.load()
        for y in range(h):
            for x in range(w):
                v = self.get(x, y)
                if v is not None:
                    p[x, y] = colors[v % len(colors)]
        return im.resize((w * scale, h * scale), Image.NEAREST)
