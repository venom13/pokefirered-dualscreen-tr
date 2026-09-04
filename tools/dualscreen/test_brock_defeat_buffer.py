#!/usr/bin/env python3
"""Regression for Brock's long defeat speech and battle teardown snapshots."""

from pathlib import Path
import re

from test_bag_menu_init import function


ROOT = Path(__file__).resolve().parents[2]
HEADER = (ROOT / "include/battle_message.h").read_text()
BATTLE = (ROOT / "src/battle_main.c").read_text()
FREE = (ROOT / "src/battle_util2.c").read_text()
TEXT = (ROOT / "data/maps/PewterCity_Gym/text.inc").read_text()


def encoded_length(lines):
    """Count the charmap bytes used by this particular text block."""
    constants = {
        "FONT_NORMAL": 3,
        "PLAYER": 2,
        "PAUSE_MUSIC": 2,
        "PLAY_BGM": 2,
        "MUS_OBTAIN_BADGE": 2,
        "PAUSE 0xFE": 3,
        "PAUSE 0x56": 3,
        "RESUME_MUSIC": 2,
        "FONT_MALE": 3,
    }
    size = 0
    for line in lines:
        match = re.search(r'\.string "(.*)"', line)
        if not match:
            continue
        value = match.group(1)
        pos = 0
        while pos < len(value):
            if value[pos] == "\\":
                size += 1
                pos += 2
            elif value[pos] == "{":
                end = value.index("}", pos)
                size += constants[value[pos + 1:end]]
                pos = end + 1
            else:
                size += 1
                pos += 1
    return size


block = TEXT.split("PewterCity_Gym_Text_BrockDefeat::", 1)[1].split(
    "PewterCity_Gym_Text_TakeThisWithYou::", 1
)[0]
raw_size = encoded_length(block.splitlines())
player_name_size = int(
    re.search(
        r"#define\s+PLAYER_NAME_LENGTH\s+(\d+)",
        (ROOT / "include/constants/global.h").read_text(),
    ).group(1)
)
# The encoded {PLAYER} placeholder occupies two source bytes and expands to
# the full player name in gDisplayedStringBattle.
expanded_size = raw_size - 2 + player_name_size

portable_size = int(
    re.search(
        r"#ifdef PLATFORM_SDL2\s*"
        r"#define DISPLAYED_BATTLE_STRING_LENGTH\s+(\d+)",
        HEADER,
    ).group(1)
)
assert expanded_size > 300
assert portable_size >= expanded_size
assert "gDisplayedStringBattle[DISPLAYED_BATTLE_STRING_LENGTH]" in HEADER
assert "gDisplayedStringBattle[DISPLAYED_BATTLE_STRING_LENGTH]" in BATTLE

teardown = function(BATTLE, "FreeResetData_ReturnToOvOrDoEvolutions")
hide = teardown.index("sBattleMonsReady = FALSE")
release = teardown.index("FreeBattleResources()")
assert hide < release

free_resources = function(FREE, "FreeBattleResources")
assert "TRY_FREE_AND_SET_NULL(gPokedudeBattlerStates[i])" in free_resources

print(
    f"Brock defeat regression passed: {expanded_size} expanded bytes fit "
    f"in the {portable_size}-byte portable buffer"
)
