#!/usr/bin/env python3
"""ROM-free regression for Summary-screen VBlank teardown ordering."""
from pathlib import Path
import os
import subprocess
import tempfile

from test_bag_menu_init import function

ROOT = Path(__file__).resolve().parents[2]

PREFIX = r'''
#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

typedef uint8_t u8;
typedef void (*MainCallback)(void);
#define TRUE 1
#define FREE_AND_SET_NULL_IF_SET(ptr) do { if ((ptr) != NULL) (ptr) = NULL; } while (0)

struct PokemonSummaryScreenData {
    u8 curPageIndex;
    MainCallback savedCallback;
};

static struct PokemonSummaryScreenData summary;
static struct PokemonSummaryScreenData *sMonSummaryScreen = &summary;
static int skills;
static int *sMonSkillsPrinterXpos = &skills;
static u8 sLastViewedMonIndex;
static void (*vblankCallback)(void);
static int stage, destroyedTask, restoredCallback;

static void DummyVBlank(void) { assert(0 && "released Summary state was accessed"); }
static void SavedCallback(void) { restoredCallback++; }
static void SetVBlankCallback(void (*callback)(void)) {
    assert(stage == 0 && sMonSummaryScreen != NULL);
    vblankCallback = callback;
    stage = 1;
}
static void PokeSum_DestroySprites(void) {
    assert(stage == 1 && vblankCallback == NULL && sMonSummaryScreen != NULL);
    stage = 2;
}
static void FreeAllSpritePalettes(void) { assert(stage++ == 2); }
static int IsCryPlayingOrClearCrySongs(void) { assert(stage == 3); return 0; }
static void StopCryAndClearCrySongs(void) { assert(0); }
static void PokeSum_RemoveWindows(u8 page) { assert(stage == 3 && page == 2); stage++; }
static void FreeAllWindowBuffers(void) { assert(stage++ == 4); }
static void DestroyTask(u8 taskId) { assert(stage == 5 && taskId == 7); destroyedTask = 1; stage++; }
static void SetMainCallback2(MainCallback callback) {
    assert(stage == 6 && callback == SavedCallback && sMonSummaryScreen != NULL);
    callback();
    stage++;
}
static u8 GetLastViewedMonIndex(void) { assert(stage == 7); return 4; }
'''

SUFFIX = r'''
int main(void) {
    summary.curPageIndex = 2;
    summary.savedCallback = SavedCallback;
    vblankCallback = DummyVBlank;

    Task_DestroyResourcesOnExit(7);

    assert(stage == 7 && destroyedTask && restoredCallback == 1);
    assert(vblankCallback == NULL);
    assert(sMonSummaryScreen == NULL && sMonSkillsPrinterXpos == NULL);
    assert(sLastViewedMonIndex == 4);
    puts("PASS: Summary disables VBlank before releasing its screen state");
    return 0;
}
'''


def main():
    source_text = (ROOT / "src/pokemon_summary_screen.c").read_text()
    code = PREFIX + function(source_text, "Task_DestroyResourcesOnExit") + SUFFIX

    with tempfile.TemporaryDirectory(prefix="firered-summary-exit-") as directory:
        directory = Path(directory)
        source = directory / "test.c"
        executable = directory / "test"
        source.write_text(code)
        subprocess.run([
            os.environ.get("CC", "cc"), "-std=c11", "-O1", "-g",
            "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
            str(source), "-o", str(executable),
        ], check=True)
        subprocess.run([str(executable)], check=True)


if __name__ == "__main__":
    main()
