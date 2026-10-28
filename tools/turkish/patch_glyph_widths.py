#!/usr/bin/env python3
"""Give the Turkish glyph slots (0x60-0x65) the widths of their base letters
in every Latin glyph-width table of src/text.c. Idempotent."""
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEXT_C = os.path.join(ROOT, "src", "text.c")
TABLES = (
    "sFontSmallLatinGlyphWidths",
    "sFontNormalCopy1LatinGlyphWidths",
    "sFontNormalLatinGlyphWidths",
    "sFontMaleLatinGlyphWidths",
    "sFontFemaleLatinGlyphWidths",
)
BASE = {0x60: 0xC1, 0x61: 0xDB, 0x62: 0xC3, 0x63: 0xDD, 0x64: 0xCD, 0x65: 0xE7}


def main():
    src = open(TEXT_C, encoding="utf8").read()
    for name in TABLES:
        m = re.search(r"(" + name + r"\[\]\s*=\s*\{)([^}]*)(\})", src)
        if not m:
            sys.exit("table not found: " + name)
        body = m.group(2)
        nums = [(n.start(), n.end(), int(n.group())) for n in re.finditer(r"\d+", body)]
        values = [v for _, _, v in nums]
        for glyph, base in BASE.items():
            values[glyph] = values[base]
        out, last = [], 0
        for (start, end, _), value in zip(nums, values):
            out.append(body[last:start])
            out.append(str(value).rjust(end - start))
            last = end
        out.append(body[last:])
        src = src[: m.start(2)] + "".join(out) + src[m.end(2):]
        print(name, {hex(g): values[g] for g in BASE})
    open(TEXT_C, "w", encoding="utf8", newline="\n").write(src)
    return 0


if __name__ == "__main__":
    sys.exit(main())
