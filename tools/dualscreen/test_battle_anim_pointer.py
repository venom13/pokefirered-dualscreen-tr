#!/usr/bin/env python3
"""Regression for signed sprite-data pointer reconstruction in battle animations."""
from pathlib import Path
import os
import re
import subprocess
import tempfile

from test_bag_menu_init import function

ROOT = Path(__file__).resolve().parents[2]
MONS = (ROOT / "src/battle_anim_mons.c").read_text()
NORMAL = (ROOT / "src/battle_anim_normal.c").read_text()

loader = function(MONS, "LoadPointerFromSpriteData6")
assert "(u16)sprite->data[6]" in loader
assert "(u16)sprite->data[7]" in loader
assert "LoadPointerFromSpriteData6(sprite)" in function(MONS, "SetCallbackToStoredInData6")
assert NORMAL.count("LoadPointerFromSpriteData6(sprite)") == 2
assert not re.search(r"data\[6\]\s*\|\s*\([^\n]*data\[7\]\s*<<\s*16", NORMAL)

program = r"""
#include <assert.h>
#include <stdint.h>
typedef uint16_t u16;
typedef uint32_t u32;
typedef int16_t s16;
struct Sprite { s16 data[8]; };
""" + loader + r"""
int main(void)
{
    struct Sprite sprite = {0};

    sprite.data[6] = (s16)0xDA12;
    sprite.data[7] = (s16)0xBA61;
    assert(LoadPointerFromSpriteData6(&sprite) == (uintptr_t)0xBA61DA12u);

    sprite.data[6] = (s16)0x1234;
    sprite.data[7] = (s16)0xFEDC;
    assert(LoadPointerFromSpriteData6(&sprite) == (uintptr_t)0xFEDC1234u);
    return 0;
}
"""

with tempfile.TemporaryDirectory() as tmp:
    source = Path(tmp) / "battle_anim_pointer.c"
    binary = Path(tmp) / "battle_anim_pointer"
    source.write_text(program)
    cc = os.environ.get("CC", "cc")
    subprocess.run(
        [cc, "-std=c11", "-Wall", "-Wextra", "-Werror", "-fsanitize=undefined", str(source), "-o", str(binary)],
        check=True,
    )
    subprocess.run([str(binary)], check=True)

print("battle animation pointer regression passed")
