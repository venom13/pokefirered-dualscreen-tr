"""Pokémon summary screen labels (graphics/summary_screen/bg.png).

The user picked the labels one by one; No, HP and EXP. stay English.
Each label sits in a grey pill (low nibble 13) with white text (14); the PNG
keeps the palette bank in the high nibble, so pixels are rewritten bank-wise.
Row 0 of a glyph goes on the pill's top row (dots, breves), row 8 on its
bottom row (cedillas); those rows are written only where the pill is grey.

usage: python -I summary_screen.py <repo root>
"""
import os, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pixfont as pf

PNG = sys.argv[1] + "/graphics/summary_screen/bg.png"
PILL, INK = 13, 14
# pill top y, pill x1, x2, new text, align ("c" centre / x for left edge)
LABELS = [
    (7, 53, 127, "EĞİTMEN NOTU", 60),   # TRAINER MEMO
    (45, 4, 44, "AD", "c"),             # NAME
    (60, 4, 44, "TÜR", "c"),            # TYPE
    (75, 4, 44, "EĞİTMEN", "c"),        # OT
    (90, 4, 44, "KİMLİK", "c"),         # IDNo
    (105, 4, 44, "EŞYA", "c"),          # ITEM
    (107, 76, 116, "DURUM", "c"),       # STATE
    (123, 75, 116, "GÜÇ", "c"),         # POWER
    (137, 75, 116, "İSABET", "c"),      # ACCURACY
    (150, 75, 116, "ETKİ", "c"),        # EFFECT
    (143, 4, 46, "SALDIRI", "c"),       # ATTACK
    (156, 4, 46, "SAVUNMA", "c"),       # DEFENSE
    (169, 4, 46, "Ö.SALD", "c"),        # SP.ATK
    (182, 4, 46, "Ö.SAV", "c"),         # SP.DEF
    (195, 4, 46, "HIZ", "c"),           # SPEED
    (243, 5, 68, "YETENEK", "c"),       # ABILITY
]

im = Image.open(PNG)
px = im.load()
for y, x1, x2, text, align in LABELS:
    # erase the old text: every white pixel on the pill's text rows
    for yy in range(y + 1, y + 8):
        for xx in range(x1, x2 + 1):
            if px[xx, yy] & 15 == INK:
                px[xx, yy] = (px[xx, yy] & 0xF0) | PILL
    m = pf.mask_of(text, pf.CAP9)
    w = len(m[0])
    x0 = (x1 + x2 + 1 - w) // 2 if align == "c" else align
    assert x1 + 2 <= x0 and x0 + w <= x2 - 1, (text, x0, w)
    for r, row in enumerate(m):
        for c, on in enumerate(row):
            if not on:
                continue
            xx, yy = x0 + c, y + r
            if r in (0, 8) and px[xx, yy] & 15 != PILL:
                continue
            px[xx, yy] = (px[xx, yy] & 0xF0) | INK
im.save(PNG)
print("summary labels redrawn:", len(LABELS))
