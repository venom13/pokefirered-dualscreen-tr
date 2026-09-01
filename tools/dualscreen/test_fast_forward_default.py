#!/usr/bin/env python3
"""Verify that a saved fast-forward preference never accelerates startup."""
from pathlib import Path
import os
import subprocess
import tempfile

from test_bag_menu_init import function

ROOT = Path(__file__).resolve().parents[2]

PREFIX = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

typedef uint8_t u8;
enum {
    PLATFORM_SETTING_FULLSCREEN,
    PLATFORM_SETTING_WINDOW_SCALE,
    PLATFORM_SETTING_INTEGER_SCALE,
    PLATFORM_SETTING_VSYNC,
    PLATFORM_SETTING_BORDER,
    PLATFORM_SETTING_VOLUME,
    PLATFORM_SETTING_BACKGROUND_MODE,
    PLATFORM_SETTING_WIDESCREEN,
    PLATFORM_SETTING_TOUCH_CONTROLS,
    PLATFORM_SETTING_BATTLE_UI_TOP,
    PLATFORM_SETTING_FAST_FORWARD,
    PLATFORM_SETTING_VOXEL_RENDERER,
    PLATFORM_SETTING_FF_AUDIO,
    PLATFORM_SETTING_BATTLE_HINTS,
    PLATFORM_SETTING_COUNT,
};
#define FF_HOTKEY_DEFAULT_SPEED 1

static char sConfigPath[1024];
static u8 sBorderBackground;
static int sHasBorderBackgroundConfig;
static u8 sBackgroundOrderVersion;
static u8 sPlatformSettings[PLATFORM_SETTING_COUNT];
static u8 sFastForwardSetting;
static u8 sFastForwardResume = FF_HOTKEY_DEFAULT_SPEED;
'''

SUFFIX = r'''
int main(int argc, char **argv)
{
    assert(argc == 2);
    strcpy(sConfigPath, argv[1]);
    sPlatformSettings[PLATFORM_SETTING_FAST_FORWARD] = 2;
    ReadConfigFile();
    assert(sPlatformSettings[PLATFORM_SETTING_FAST_FORWARD] == 0);
    assert(sFastForwardSetting == 3);
    assert(sFastForwardResume == 3);
    assert(sPlatformSettings[PLATFORM_SETTING_VOLUME] == 6);
    puts("PASS: saved 4x preference is retained for R2 while startup remains 1x");
    return 0;
}
'''


def main():
    source_text = (ROOT / "src/platform/sdl2.c").read_text()
    code = PREFIX + function(source_text, "ReadConfigFile") + SUFFIX

    with tempfile.TemporaryDirectory(prefix="firered-fast-forward-") as directory:
        directory = Path(directory)
        source = directory / "test.c"
        executable = directory / "test"
        config = directory / "pokefirered.cfg"
        source.write_text(code)
        config.write_text("volume=6\nfastForward=3\n")
        subprocess.run([
            os.environ.get("CC", "cc"), "-std=c11", "-O1", "-g",
            "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
            str(source), "-o", str(executable),
        ], check=True)
        subprocess.run([str(executable), str(config)], check=True)


if __name__ == "__main__":
    main()
