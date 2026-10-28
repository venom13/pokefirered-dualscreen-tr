# Turkish graphics pass

Scripts that redraw English text baked into PNGs under `graphics/`. Each screen
was approved one by one; words not listed here were deliberately left in
English (logos, copyright lines, physical button names such as START/SELECT,
Easy Chat modes, EXP./HP/No/PP labels, the HM icon, the Union Room "OK").

Run from the repository root with `python -I tools/turkish/gfx/<script>.py .`
on the **original** PNGs (several scripts cut glyphs from the English word or
assert on it). To redo a screen: `git checkout -- <its PNGs>`, then rerun its
script. `lv_symbol.py` edits the Latin fonts; after restoring a font from git,
run `tools/turkish/add_turkish_glyphs.py` first, then `lv_symbol.py`.

| Script | Screen | Change |
| --- | --- | --- |
| `title_press_start.py` | title | PRESS START -> START'A BAS |
| `naming_screen.py` | name entry | GERİ, TAMAM, B TUŞU; tabs BÜYÜK / küçük / diğer |
| `summary_screen.py` | Pokémon summary | 16 labels (AD, TÜR, EĞİTMEN, KİMLİK, EŞYA, ...) |
| `status_icons.py` | party / summary / battle | ZHR FLÇ UYK DNM YNK BYL (PkRS stays) |
| `lv_symbol.py` | fonts + battle boxes | Lv -> Sv |
| `type_icons.py` | type icons, move info | type names; TÜR / GÜÇ / İSABET / ETKİ |
| `trainer_card.py` | trainer card (FR + RSE) | EĞİTMEN KARTI, ROZETLER, EĞİTMEN: |
| `pc_storage.py` | PC boxes | POKé BİLGİ, KUTUYU KAPAT, TAKIM, VAZGEÇ |
| `small_screens_1.py` | Fame Checker, Teachy TV, slots, markings | ÜNLÜ ⇔ REHBERİ, SON, KREDİ / KAZANÇ, TAMAM / VAZGEÇ |
| `countdown_start.py` | minigame countdowns | START -> BAŞLA |
| `union_room_chat.py` | Union Room chat | GERİ, DEĞİŞTİR, GÖNDER, KAYDET |

Helpers: `pixfont.py` (glyph masks, stamping), `tilecanvas.py` (edit tiles in
their on-screen tilemap arrangement; sprites in 1D tile order use a list of
tile numbers as the map). Colour indices in some PNGs carry a palette bank in
the high nibble; the scripts compare and write the low nibble only.
