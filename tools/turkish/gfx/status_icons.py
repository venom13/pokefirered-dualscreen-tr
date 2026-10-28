"""Status condition icons: PSN PAR SLP FRZ BRN FNT -> ZHR FLÇ UYK DNM YNK BYL.
PkRS stays. The same icons are baked into three sheets (party/summary,
interface, battle healthbox), the battle one once per palette bank.

Old words are found by exact match of their white (colour 2) pixels against
templates cut from the summary sheet, so positions need not be hard-coded.
Colour indices may carry a palette bank in the high nibble; only the low
nibble is compared and rewritten.

usage: python -I status_icons.py <repo root>
"""
import os, sys
from collections import Counter
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pixfont as pf

G = sys.argv[1] + "/graphics/"
WHITE = 2
ORDER = ["PSN", "PAR", "SLP", "FRZ", "BRN", "PkRS", "FNT"]  # rows of the summary sheet
NEW = {"PSN": "ZHR", "PAR": "FLÇ", "SLP": "UYK", "FRZ": "DNM", "BRN": "YNK", "FNT": "BYL"}

F6 = {k: [r.replace("2", "1") for r in v.split("/")] for k, v in {
    "Z": "2222/...2/..2./.2../2.../2222",
    "H": "2..2/2..2/2222/2..2/2..2/2..2",
    "R": "222./2..2/2..2/222./2.2./2..2",
    "F": "2222/2.../222./2.../2.../2...",
    "L": "2.../2.../2.../2.../2.../2222",
    "Ç": ".22./2..2/2.../2..2/.22./..2.",
    "U": "2..2/2..2/2..2/2..2/2..2/.22.",
    "Y": "2..2/2..2/.22./.2../.2../.2..",
    "K": "2..2/2.2./22../2.2./2..2/2..2",
    "D": "222./2..2/2..2/2..2/2..2/222.",
    "N": "2..2/22.2/2.22/2..2/2..2/2..2",
    "M": "2...2/22.22/2.2.2/2...2/2...2/2...2",
    "B": "222./2..2/222./2..2/2..2/222.",
}.items()}


def white(px, x, y):
    return px[x, y] & 15 == WHITE


def templates():
    im = Image.open(G + "summary_screen/status_ailment_icons.png")
    px = im.load()
    out = {}
    for i, name in enumerate(ORDER):
        pts = [(x, y) for y in range(8 * i + 1, 8 * i + 7) for x in range(7, 25) if white(px, x, y)]
        x0, y0 = min(p[0] for p in pts), min(p[1] for p in pts)
        x1, y1 = max(p[0] for p in pts), max(p[1] for p in pts)
        out[name] = [[(x0 + x, y0 + y) in pts for x in range(x1 - x0 + 1)] for y in range(y1 - y0 + 1)]
    return out


def redraw(path, tmpl):
    im = Image.open(path)
    px = im.load()
    W, H = im.size
    hits = []
    for name, t in tmpl.items():
        if name not in NEW:
            continue
        th, tw = len(t), len(t[0])
        for y in range(H - th + 1):
            for x in range(W - tw + 1):
                if all(white(px, x + c, y + r) == t[r][c] for r in range(th) for c in range(tw)):
                    hits.append((name, x, y, tw, th))
    for name, x, y, tw, th in hits:
        body = Counter(px[x + c, y + r] for r in range(th) for c in range(tw)
                       if not white(px, x + c, y + r)).most_common(1)[0][0]
        for r in range(th):
            for c in range(tw):
                if white(px, x + c, y + r):
                    px[x + c, y + r] = body
        m = pf.mask_of(NEW[name], F6)
        for r, row in enumerate(m):
            for c, on in enumerate(row):
                if on:
                    px[x + c, y + r] = (px[x + c, y + r] & 0xF0) | WHITE
    im.save(path)
    print(path.split("graphics/")[1], Counter(h[0] for h in hits))


T = templates()
for f in ["summary_screen/status_ailment_icons.png", "interface/status_icons.png",
          "battle_interface/healthbox_elements.png"]:
    redraw(G + f, T)
