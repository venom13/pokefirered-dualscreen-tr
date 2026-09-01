#!/usr/bin/env python3
"""ROM-free regression for Android save-path repair and atomic commits.

Compiles the real Platform_CommitSaveFile implementation with Android storage
APIs mocked on the host. The first case deliberately corrupts the persistent
save path to the files directory, reproducing the EISDIR failure seen on Thor.
"""
from pathlib import Path
import os
import subprocess
import tempfile

from test_bag_menu_init import function

ROOT = Path(__file__).resolve().parents[2]

PREFIX = r'''
#include <assert.h>
#include <errno.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

typedef uint32_t bool32;
#define TRUE 1
#define FALSE 0
#define __ANDROID__ 1
#define SDL_ANDROID_EXTERNAL_STORAGE_WRITE 1
#define SDL_snprintf snprintf

static unsigned char FLASH_BASE[128 * 1024];
static FILE *sSaveFile;
static char sSavePath[1024] = "pokeemerald.sav";
static const char *externalPath;
static int externalState = SDL_ANDROID_EXTERNAL_STORAGE_WRITE;

static const char *SDL_AndroidGetExternalStoragePath(void) { return externalPath; }
static int SDL_AndroidGetExternalStorageState(void) { return externalState; }
static void SDL_Log(const char *format, ...) { (void)format; }
static void CloseSaveFile(void) {
    if (sSaveFile != NULL) {
        fclose(sSaveFile);
        sSaveFile = NULL;
    }
}
'''

SUFFIX = r'''
static void expectFile(const char *path, unsigned char value) {
    FILE *file = fopen(path, "rb");
    assert(file != NULL);
    unsigned char buffer[4096];
    size_t total = 0, got;
    while ((got = fread(buffer, 1, sizeof(buffer), file)) != 0) {
        for (size_t i = 0; i < got; i++) assert(buffer[i] == value);
        total += got;
    }
    assert(!ferror(file));
    assert(total == sizeof(FLASH_BASE));
    assert(fclose(file) == 0);
}

int main(int argc, char **argv) {
    assert(argc == 2);
    externalPath = argv[1];

    // This is the observed fault: the durable buffer has lost the filename
    // suffix and points at an existing directory. Android's current external
    // directory must repair the target before the temp file is created.
    assert(snprintf(sSavePath, sizeof(sSavePath), "%s", argv[1]) < (int)sizeof(sSavePath));
    memset(FLASH_BASE, 0xA5, sizeof(FLASH_BASE));
    assert(Platform_CommitSaveFile());

    char path[1200];
    assert(snprintf(path, sizeof(path), "%s/pokefirered.sav", argv[1]) < (int)sizeof(path));
    expectFile(path, 0xA5);
    assert(snprintf(path, sizeof(path), "%s.tmp", argv[1]) < (int)sizeof(path));
    assert(access(path, F_OK) != 0);

    // Desktop/private-storage fallback still uses the configured path.
    externalState = 0;
    assert(snprintf(sSavePath, sizeof(sSavePath), "%s/fallback.sav", argv[1]) < (int)sizeof(sSavePath));
    memset(FLASH_BASE, 0x5A, sizeof(FLASH_BASE));
    assert(Platform_CommitSaveFile());
    expectFile(sSavePath, 0x5A);

    puts("PASS: Android save path is rebuilt and both commits are complete");
    return 0;
}
'''


def main():
    source = (ROOT / "src/platform/sdl2.c").read_text()
    storage_path = function(source, "BuildStorageFilePath")
    commit = function(source, "Platform_CommitSaveFile")
    with tempfile.TemporaryDirectory(prefix="firered-save-test-") as directory:
        temp = Path(directory)
        c_file = temp / "test.c"
        executable = temp / "test"
        c_file.write_text(PREFIX + storage_path + commit + SUFFIX)
        subprocess.run([
            os.environ.get("CC", "cc"), "-std=c11", "-O1", "-g",
            "-fsanitize=address,undefined", str(c_file), "-o", str(executable),
        ], check=True)
        subprocess.run([str(executable), str(temp)], check=True)


if __name__ == "__main__":
    main()
