#!/usr/bin/env python3
"""ROM-free BAG/TM Case/Berry Pouch callback and graphics-loader regression.

Runs the actual C callbacks and graphics state machines with deferred host DMA.
Only the surrounding menu setup and graphics hardware are test doubles.
"""
from pathlib import Path
import os
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
MENUS = (
    ("src/item_menu.c", "CB2_OpenBagMenu", "LoadBagMenuGraphics", "DoLoadBagGraphics"),
    ("src/tm_case.c", "CB2_SetUpTMCaseUI_Blocking", "DoSetUpTMCaseUI", "HandleLoadTMCaseGraphicsAndPalettes"),
    ("src/berry_pouch.c", "CB2_InitBerryPouch", "RunBerryPouchInit", "BerryPouchLoadGfx"),
)


def function(source, name):
    match = re.search(r"(?m)^(?:static )?\w+ " + name + r"\([^;{}]*\)\s*\{", source)
    assert match, name
    end, depth = match.end(), 1
    while depth:
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    return source[match.start():end]


PREFIX = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef uint8_t bool8;
#define TRUE 1
#define FALSE 0
#define MALE 0
#define ITEMMENULOCATION_ITEMPC 4
#define BG_PLTT_ID(n) (n)
#define PLTT_SIZE_4BPP 32
#define FREE_AND_SET_NULL(p) do { free(p); (p) = NULL; } while (0)

static int pending, calls, busyChecks, frames, done, immediateDone, linkBusy, linkActive;
static int tutorial, copies, tilemaps, palettes, sheets, spritePalettes;
static void *sTempTileDataBuffers[16];
static int sTempTileDataBufferCursor;
static struct { int data[4]; } bag, *sBagMenuDisplay = &bag;
static struct { int seqId; } tm, *sTMCaseDynamicResources = &tm;
static struct { int data[4]; void *bg1TilemapBuffer; } berry, *sResources = &berry;
static struct { int location; } gBagMenuState;
static struct { int playerGender; } save, *gSaveBlock2Ptr = &save;
static void *sBagBgTilemapBuffer, *sTilemapBuffer;
static bool8 (*graphicsStep)(void);

#define ASSET(n) static const int n[1] = {0}
ASSET(gBagBg_Gfx); ASSET(gBagBg_Tilemap); ASSET(gBagBg_ItemPC_Tilemap);
ASSET(gBagBgPalette); ASSET(gBagBgPalette_FemaleOverride);
ASSET(gSpriteSheet_BagMale); ASSET(gSpriteSheet_BagFemale);
ASSET(gSpritePalette_Bag); ASSET(gBagSwapSpriteSheet); ASSET(gBagSwapSpritePalette);
ASSET(gTMCase_Gfx); ASSET(gTMCaseMenu_Tilemap); ASSET(gTMCase_Tilemap);
ASSET(gTMCaseMenu_Male_Pal); ASSET(gTMCaseMenu_Female_Pal); ASSET(sSpriteSheet_Disc);
ASSET(gBerryPouchBgGfx); ASSET(gBerryPouchBg1Tilemap); ASSET(gBerryPouchBgPals);
ASSET(gBerryPouchBgPal0FemaleOverride); ASSET(sBerryPouchSpriteSheet); ASSET(sBerryPouchSpritePal);

static int IsActiveOverworldLinkBusy(void) { return linkBusy; }
static int MenuHelpers_IsLinkActive(void) { return linkActive; }
static int BagIsTutorial(void) { return tutorial; }
static void ResetTempTileDataBuffers(void) {
    assert(!pending && !sTempTileDataBufferCursor);
}
static void DecompressAndCopyTileDataToVram(int bg, const void *src, int size, int offset, int mode) {
    assert(bg == 1 && src && !size && !offset && !mode && !pending);
    sTempTileDataBuffers[sTempTileDataBufferCursor++] = malloc(32);
    assert(sTempTileDataBuffers[0]);
    pending = 3;
    copies++;
}
static int IsDma3ManagerBusyWithBgCopy(void) {
    assert(++busyChecks < 128); /* old tight loops fail instead of hanging tests */
#ifndef PORTABLE
    if (pending) pending--; /* GBA interrupts can run inside a busy loop */
#endif
    return pending != 0;
}
static void LZDecompressWram(const void *src, void *dest) {
    assert(src && !pending && !sTempTileDataBufferCursor);
    tilemaps++;
}
static void *GetBgTilemapBuffer(int bg) { assert(bg == 1); return NULL; }
static void LoadCompressedPalette(const void *src, int offset, int size) { palettes++; }
static void LoadCompressedSpriteSheet(const void *src) { sheets++; }
static void LoadCompressedSpritePalette(const void *src) { spritePalettes++; }
static void LoadDiscTypePalettes(void) { spritePalettes++; }
static bool8 StepMenu(void) {
    assert(++calls < 128);
    if (immediateDone || graphicsStep()) {
        done = TRUE;
        return TRUE;
    }
    return FALSE;
}
static bool8 LoadBagMenuGraphics(void) { return StepMenu(); }
static bool8 DoSetUpTMCaseUI(void) { return StepMenu(); }
static bool8 RunBerryPouchInit(void) { return StepMenu(); }
'''

SUFFIX = r'''
static void Reset(void) {
    assert(!pending && !sTempTileDataBufferCursor);
    memset(&bag, 0, sizeof(bag));
    memset(&tm, 0, sizeof(tm));
    memset(&berry, 0, sizeof(berry));
    calls = busyChecks = frames = done = immediateDone = linkBusy = linkActive = 0;
    copies = tilemaps = palettes = sheets = spritePalettes = 0;
}
int main(void) {
    void (*callbacks[])(void) = {CB2_OpenBagMenu, CB2_SetUpTMCaseUI_Blocking, CB2_InitBerryPouch};
    bool8 (*loaders[])(void) = {DoLoadBagGraphics, HandleLoadTMCaseGraphicsAndPalettes, BerryPouchLoadGfx};
    for (int menu = 0; menu < 3; menu++) {
        graphicsStep = loaders[menu];
        for (int entry = 0; entry < 24; entry++) {
            Reset();
            save.playerGender = entry & 1;
            tutorial = (entry >> 1) & 1;
            gBagMenuState.location = (entry & 4) ? ITEMMENULOCATION_ITEMPC : 0;
            while (!done) {
                int before = calls;
                callbacks[menu]();
#ifdef PORTABLE
                assert(calls == before + 1); /* bounded work, then return to main loop */
                if (pending) pending--; /* VBlank drains DMA outside the callback */
#endif
                assert(++frames < 32);
            }
            assert(copies == 1 && !pending && !sTempTileDataBufferCursor);
            assert(tilemaps == (menu == 1 ? 2 : 1));
            assert(palettes > 0 && sheets > 0 && spritePalettes > 0);
            if (menu == 0)
                assert(palettes == 1 + (!tutorial && save.playerGender != MALE));
            if (menu == 2)
                assert(palettes == 1 + (save.playerGender != MALE));
#ifndef PORTABLE
            assert(frames == 1); /* original GBA blocking behavior is unchanged */
#endif
        }
        Reset();
        linkBusy = TRUE;
        callbacks[menu]();
        assert(calls == 0 && !pending);
        Reset();
        immediateDone = TRUE;
        callbacks[menu]();
        assert(calls == 1 && done && !pending);
        Reset();
        linkActive = TRUE;
        callbacks[menu]();
        assert(calls == 1 && copies == 1 && pending);
        pending = 0;
        assert(!FreeTempTileDataBuffersIfPossible());
        Reset();
    }
    puts("PASS: BAG, TM Case and Berry Pouch open repeatedly; DMA, gender/tutorial, link guards and completion paths");
    return 0;
}
'''


def main():
    code = PREFIX
    code += function((ROOT / "src/new_menu_helpers.c").read_text(), "FreeTempTileDataBuffersIfPossible")
    for path, callback, setup, graphics in MENUS:
        source = (ROOT / path).read_text()
        assert graphics + "()" in function(source, setup)
        code += function(source, graphics) + "\n" + function(source, callback) + "\n"
    code += SUFFIX
    with tempfile.TemporaryDirectory(prefix="firered-bag-test-") as directory:
        directory = Path(directory)
        source = directory / "test.c"
        source.write_text(code)
        for portable in (True, False):
            binary = directory / ("portable" if portable else "gba")
            flags = ["-DPORTABLE"] if portable else []
            subprocess.run([os.environ.get("CC", "cc"), "-std=c11", "-g", "-O1",
                            "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
                            *flags, str(source), "-o", str(binary)], check=True)
            subprocess.run([str(binary)], check=True, timeout=5)


if __name__ == "__main__":
    main()
