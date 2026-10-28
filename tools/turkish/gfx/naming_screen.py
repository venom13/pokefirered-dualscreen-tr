"""Naming screen: BACK -> GERİ, OK -> TAMAM, "B BUTTON" -> "B TUŞU",
page tabs UPPER / lower / others -> BÜYÜK / küçük / diğer.
START and SELECT captions stay (they name the buttons).

usage: python -I naming_screen.py <repo root>
"""
import os, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pixfont as pf

D = sys.argv[1] + "/graphics/naming_screen/"
WHITE, FACE, DARK, HILITE, PANEL = 1, 4, 15, 12, 13


def button_label(name, text, top):
    """Panel text: white letters on a dark-yellow box, rows top..top+8."""
    im = Image.open(D + name)
    px = im.load()
    pf.fill(px, (7, top, 33, top + 9), PANEL)       # clear the old box (corners stay)
    m = pf.mask_of(text, pf.BIG7)
    w = len(m[0])
    x0 = 7 + (26 - w) // 2
    pf.fill(px, (max(7, x0 - 1), top, min(33, x0 + w + 1), top + 9), HILITE)
    pf.stamp(px, m, x0, top, WHITE)
    return im, px


im, px = button_label("back_button.png", "GERİ", 4)
# caption under the button: keep the B key icon (cols 4-8), redraw the word
pf.fill(px, (9, 16, 38, 24), FACE)
pf.stamp(px, pf.mask_of("TUŞU", pf.SMALL5), 11, 17, WHITE, outline=DARK, clip=(9, 16, 38, 24))
im.save(D + "back_button.png")

im, px = button_label("ok_button.png", "TAMAM", 2)
im.save(D + "ok_button.png")

for name, text, bg, shadow in [("page_swap_upper.png", "BÜYÜK", 7, 6),
                               ("page_swap_lower.png", "küçük", 9, 8),
                               ("page_swap_others.png", "diğer", 11, 10)]:
    im = Image.open(D + name)
    px = im.load()
    pf.fill(px, (0, 0, 24, 8), bg)
    m = pf.mask_of(text, pf.TAB)
    pf.stamp(px, m, max(0, (23 - len(m[0])) // 2), 0, WHITE, shadow=shadow, clip=(0, 0, 24, 8))
    im.save(D + name)
print("naming screen redrawn")
