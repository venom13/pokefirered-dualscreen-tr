#!/usr/bin/env python3
"""ROM-free host regression checks of the actual Android asset loader.

Compiles its C implementation with synthetic ELF metadata and mocked Android
loader/page APIs. This tests bounds, failure propagation, and permission
restoration; it does not replace an ARM Android installation test.
"""
from pathlib import Path
import os
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
PREFIX = r"""
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/mman.h>
typedef uint32_t u32;
typedef int bool32;
#define TRUE 1
#define FALSE 0
#define BASEROM_SIZE (16 * 1024 * 1024)
#define PT_LOAD 1
#define PT_GNU_RELRO 0x6474e552
#define PF_X 1
#define PF_W 2
#define PF_R 4
typedef struct { uint32_t e_phoff; uint16_t e_phnum; } TestEhdr;
typedef struct { uint32_t p_type, p_vaddr, p_memsz, p_filesz, p_flags; } TestPhdr;
#define ElfW(type) Test##type
typedef struct { void *dli_fbase; } Dl_info;
static unsigned char memory[0x6000] __attribute__((aligned(4096)));
static int protections[32], protectionCount, failProtect;
static int fake_dladdr(void *symbol, Dl_info *info) {
    info->dli_fbase = memory; return 1;
}
static long fake_sysconf(int name) { return 4096; }
static int fake_mprotect(void *page, size_t size, int prot) {
    if (failProtect) return -1;
    if (protectionCount >= 32 || size != 4096) abort();
    protections[protectionCount++] = prot;
    return 0;
}
static int GetOwnBuildId(unsigned char *out, int size) {
    memset(out, 0xAB, 20); return 20;
}
#define dladdr fake_dladdr
#define sysconf fake_sysconf
#define mprotect fake_mprotect
"""
SUFFIX = r"""
static void resetMemory(void) {
    memset(memory, 0, sizeof(memory));
    TestEhdr *ehdr = (TestEhdr *)memory;
    ehdr->e_phoff = 16; ehdr->e_phnum = 3;
    TestPhdr *ph = (TestPhdr *)(memory + 16);
    ph[0] = (TestPhdr){PT_LOAD, 0x1000, 0x1000, 0x1000, PF_R | PF_X};
    ph[1] = (TestPhdr){PT_LOAD, 0x2000, 0x2000, 0x2000, PF_R | PF_W};
    ph[2] = (TestPhdr){PT_GNU_RELRO, 0x2000, 0x1000, 0x1000, PF_R};
    protectionCount = failProtect = 0;
}
static void writeManifest(const char *dir, u32 entries[][3], u32 count, int badId, int truncated) {
    char path[1024];
    unsigned char header[44] = {0};
    memset(header + 20, badId ? 0xCD : 0xAB, 20);
    memcpy(header + 40, &count, 4);
    snprintf(path, sizeof(path), "%sasset_manifest.bin", dir);
    FILE *f = fopen(path, "wb");
    if (!f) abort();
    fwrite(header, 1, 44, f);
    fwrite(entries, 12, truncated ? 0 : count, f);
    fclose(f);
}
static int checks;
#define CHECK(condition) do { \
    checks++; if (!(condition)) { \
        fprintf(stderr, "FAIL line %d: %s\n", __LINE__, #condition); return 1; \
    } \
} while (0)
int main(int argc, char **argv) {
    if (argc != 2) return 2;
    char *dir = argv[1];
    u32 entries[3][3] = {{0x1100, 32, 0}, {0x2100, 32, 32}, {0x3100, 32, 64}};
    resetMemory();
    writeManifest(dir, entries, 3, 0, 0);
    CHECK(DualScreen_FillAssets(dir));
    CHECK(memory[0x1100] == 0x5A && memory[0x2100] == 0x5A && memory[0x3100] == 0x5A);
    CHECK(protectionCount == 6);
    CHECK(protections[0] == (PROT_READ | PROT_WRITE | PROT_EXEC));
    CHECK(protections[1] == (PROT_READ | PROT_EXEC));
    CHECK(protections[2] == (PROT_READ | PROT_WRITE) && protections[3] == PROT_READ);
    CHECK(protections[4] == (PROT_READ | PROT_WRITE) && protections[5] == protections[4]);

    resetMemory(); writeManifest(dir, entries, 3, 1, 0);
    CHECK(!DualScreen_FillAssets(dir) && protectionCount == 0);
    resetMemory(); writeManifest(dir, entries, 3, 0, 1);
    CHECK(!DualScreen_FillAssets(dir) && protectionCount == 0);
    resetMemory(); writeManifest(dir, entries, 0, 0, 0);
    CHECK(!DualScreen_FillAssets(dir) && protectionCount == 0);

    entries[2][2] = 0xFFFFFFF0;
    resetMemory(); writeManifest(dir, entries, 3, 0, 0);
    CHECK(!DualScreen_FillAssets(dir) && protectionCount == 0 && memory[0x1100] == 0);
    entries[2][2] = 64; entries[2][0] = 0x3FF0;
    resetMemory(); writeManifest(dir, entries, 3, 0, 0);
    CHECK(!DualScreen_FillAssets(dir) && protectionCount == 0);
    entries[2][0] = 0x2110;
    resetMemory(); writeManifest(dir, entries, 3, 0, 0);
    CHECK(!DualScreen_FillAssets(dir) && protectionCount == 0);
    entries[2][0] = 0x3100; entries[2][1] = 0;
    resetMemory(); writeManifest(dir, entries, 3, 0, 0);
    CHECK(!DualScreen_FillAssets(dir) && protectionCount == 0);

    entries[2][1] = 32;
    resetMemory(); failProtect = 1; writeManifest(dir, entries, 3, 0, 0);
    CHECK(!DualScreen_FillAssets(dir) && memory[0x1100] == 0);

    entries[0][0] = 0x2FF0;
    resetMemory(); writeManifest(dir, entries, 1, 0, 0);
    CHECK(DualScreen_FillAssets(dir) && protectionCount == 4);
    CHECK(protections[1] == PROT_READ && protections[3] == (PROT_READ | PROT_WRITE));

    char path[1024];
    snprintf(path, sizeof(path), "%sbaserom.gba", dir);
    CHECK(remove(path) == 0);
    resetMemory(); CHECK(!DualScreen_FillAssets(dir));
    snprintf(path, sizeof(path), "%sasset_manifest.bin", dir);
    CHECK(remove(path) == 0);
    CHECK(!DualScreen_FillAssets(dir));
    printf("PASS: %d asset-loader checks\n", checks);
    return 0;
}
"""


def main():
    source = (ROOT / "src/platform/dualscreen_bridge.c").read_text()
    start = source.index("// Restore the original segment permissions")
    end = source.index("#endif // __ANDROID__", start)
    with tempfile.TemporaryDirectory(prefix="firered-loader-test-") as directory:
        temp = Path(directory)
        c = temp / "test.c"
        c.write_text(PREFIX + source[start:end] + SUFFIX)
        (temp / "baserom.gba").write_bytes(b"\x5A" * (16 * 1024 * 1024))
        executable = temp / "test"
        subprocess.run([os.environ.get("CC", "cc"), "-std=c11", "-O1", "-g",
                        "-fsanitize=address,undefined", str(c), "-o", str(executable)],
                       check=True)
        subprocess.run([str(executable), str(temp) + "/"], check=True)


if __name__ == "__main__":
    main()
