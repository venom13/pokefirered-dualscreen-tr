#!/usr/bin/env python3
"""ROM-free regression for leaving the Pokemon Storage System.

Runs the real storage main callback and teardown helper with host test doubles.
The exit case frees gStorage from RunTasks, reproducing the frame in which a
NO answer to "Continue BOX operations?" used to continue into stale callbacks.
"""
from pathlib import Path
import os
import subprocess
import tempfile

from test_bag_menu_init import function

ROOT = Path(__file__).resolve().parents[2]

PREFIX = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

typedef void (*IntrCallback)(void);
struct PokemonStorageSystemData { int bg2_X; };
static struct PokemonStorageSystemData *gStorage;
static IntrCallback vblankCallback;
static int leaveStorage;
static int sequence;
static int bgCopies, scrolls, flashes, animations, oamBuilds;
static int tilemapFrees, multiMoveFrees, windowFrees;

#define FREE_AND_SET_NULL(pointer) do { free(pointer); (pointer) = NULL; } while (0)

static void FreePokeStorageData(void);
static void SetVBlankCallback(IntrCallback callback) {
    assert(gStorage != NULL);
    assert(sequence++ == 0);
    vblankCallback = callback;
}
static void TilemapUtil_Free(void) {
    assert(vblankCallback == NULL);
    assert(sequence++ == 1);
    tilemapFrees++;
}
static void MultiMove_Free(void) {
    assert(vblankCallback == NULL);
    assert(sequence++ == 2);
    multiMoveFrees++;
}
static void FreeAllWindowBuffers(void) {
    assert(gStorage == NULL);
    assert(sequence++ == 3);
    windowFrees++;
}
static void RunTasks(void) {
    if (leaveStorage)
        FreePokeStorageData();
}
static void DoScheduledBgTilemapCopiesToVram(void) { bgCopies++; }
static void ScrollBackground(void) { assert(gStorage != NULL); scrolls++; }
static void UpdateCloseBoxButtonFlash(void) { assert(gStorage != NULL); flashes++; }
static void AnimateSprites(void) { assert(gStorage != NULL); animations++; }
static void BuildOamBuffer(void) { assert(gStorage != NULL); oamBuilds++; }
'''

SUFFIX = r'''
static void StorageVBlank(void) { assert(gStorage != NULL); }

static void Reset(void) {
    free(gStorage);
    gStorage = calloc(1, sizeof(*gStorage));
    assert(gStorage != NULL);
    vblankCallback = StorageVBlank;
    leaveStorage = sequence = 0;
    bgCopies = scrolls = flashes = animations = oamBuilds = 0;
    tilemapFrees = multiMoveFrees = windowFrees = 0;
}

int main(void) {
    Reset();
    CB2_PokeStorage();
    assert(gStorage != NULL);
    assert(bgCopies == 1 && scrolls == 1 && flashes == 1);
    assert(animations == 1 && oamBuilds == 1);
    assert(vblankCallback == StorageVBlank);

    Reset();
    leaveStorage = 1;
    CB2_PokeStorage();
    assert(gStorage == NULL);
    assert(vblankCallback == NULL);
    assert(sequence == 4);
    assert(tilemapFrees == 1 && multiMoveFrees == 1 && windowFrees == 1);
    assert(bgCopies == 0 && scrolls == 0 && flashes == 0);
    assert(animations == 0 && oamBuilds == 0);

    puts("PASS: storage exit stops VBlank and skips callbacks after teardown");
    return 0;
}
'''


def main():
    source = (ROOT / "src/pokemon_storage_system_tasks.c").read_text()
    code = PREFIX
    code += function(source, "CB2_PokeStorage") + "\n"
    code += function(source, "FreePokeStorageData") + "\n"
    code += SUFFIX

    with tempfile.TemporaryDirectory(prefix="firered-storage-exit-test-") as directory:
        directory = Path(directory)
        c_file = directory / "test.c"
        executable = directory / "test"
        c_file.write_text(code)
        subprocess.run([
            os.environ.get("CC", "cc"), "-std=c11", "-O1", "-g",
            "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
            str(c_file), "-o", str(executable),
        ], check=True)
        subprocess.run([str(executable)], check=True)


if __name__ == "__main__":
    main()
