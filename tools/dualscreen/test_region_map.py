#!/usr/bin/env python3
"""Test FireRed's actual Town Map JNI decoder and read-only location lookup.

Uses repository graphics (build them first), never a save or retail ROM.
Optional --preview-dir emits the decoded images for visual QA.
"""
import argparse
import ctypes
from pathlib import Path
import re
import struct
import subprocess
import tempfile
import zlib

ROOT = Path(__file__).resolve().parents[2]
JNI_NAME = "Java_com_pokeemerald_experimental_DualScreenBridge_nativeGetRegionMapImage"


def function(text, name):
    match = re.search(r"(?m)^[^\n;{}]*\b" + name + r"\([^;{}]*\)\s*\{", text)
    assert match, name
    end, depth = match.end(), 1
    while depth:
        depth += (text[end] == "{") - (text[end] == "}")
        end += 1
    return text[match.start():end]


def array(text, name):
    start = text.index("static const u8 " + name)
    return text[start:text.index("\n};", start) + 3]


def c_asset(name, path, word_size, capacity=0):
    data = path.read_bytes()
    data += bytes((-len(data)) % word_size)
    words = struct.unpack("<" + ("H" if word_size == 2 else "I") * (len(data) // word_size), data)
    return "u%d %s[%d] = {%s};\n" % (
        word_size * 8, name, max(capacity, len(words)), ",".join(map(str, words)))


PREFIX = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32, bool32;
typedef int16_t s16;
typedef int32_t jint;
typedef jint *jintArray;
typedef void *jclass;
typedef const struct MockJNI *JNIEnv;
struct MockJNI {
    jintArray (*NewIntArray)(JNIEnv *, int);
    void (*SetIntArrayRegion)(JNIEnv *, jintArray, int, int, const jint *);
};
#define JNIEXPORT
#define JNICALL
#define TRUE 1
#define FALSE 0
#define NELEMS(a) (sizeof(a) / sizeof((a)[0]))
#define MAP_WIDTH 22
#define MAP_HEIGHT 15
enum { REGIONMAP_KANTO, REGIONMAP_SEVII123, REGIONMAP_SEVII45, REGIONMAP_SEVII67 };
enum { LAYER_MAP, LAYER_DUNGEON, LAYER_COUNT };
struct DualScreenMapSection { u8 region, x, y, width, height; };
#define CPUReadMemory(p) ((u32)(p)[0] | ((u32)(p)[1] << 8) | ((u32)(p)[2] << 16) | ((u32)(p)[3] << 24))
#define CPUReadByte(p) (*(const u8 *)(p))
#define CPUWriteByte(p, v) (*(u8 *)(p) = (v))
int failAllocation;
static jintArray newArray(JNIEnv *env, int length) {
    return failAllocation == 2 ? NULL : calloc(length, sizeof(jint));
}
static void setRegion(JNIEnv *env, jintArray array, int start, int length, const jint *pixels) {
    memcpy(array + start, pixels, length * sizeof(jint));
}
static void *testMalloc(size_t size) {
    return failAllocation == 1 ? NULL : malloc(size);
}
'''

SUFFIX = r'''
jintArray render(int region) {
    static const struct MockJNI methods = {newArray, setRegion};
    JNIEnv env = &methods;
    return Java_com_pokeemerald_experimental_DualScreenBridge_nativeGetRegionMapImage(&env, NULL, region);
}
void release(jintArray pixels) { free(pixels); }
int checks(void) {
    const int sections[] = {MAPSEC_PALLET_TOWN, MAPSEC_VIRIDIAN_CITY,
        MAPSEC_ONE_ISLAND, MAPSEC_FOUR_ISLAND, MAPSEC_SIX_ISLAND,
        MAPSEC_VIRIDIAN_FOREST, MAPSEC_SILPH_CO};
    const int expected[][3] = {{0,4,11}, {0,4,8}, {1,1,8}, {2,3,4}, {3,17,5}, {0,4,6}, {0,14,6}};
    struct DualScreenMapSection info;
    for (int i = 0; i < NELEMS(sections); i++) {
        assert(DualScreen_GetRegionMapSection(sections[i], &info));
        assert(info.region == expected[i][0] && info.x == expected[i][1] && info.y == expected[i][2]);
        assert(info.width > 0 && info.height > 0);
    }
    for (int section = 0; section <= MAPSEC_NONE; section++) {
        if (DualScreen_GetRegionMapSection(section, &info)) {
            assert(info.region < 4 && info.x + info.width <= 22 && info.y + info.height <= 15);
        }
    }
    assert(!DualScreen_GetRegionMapSection(MAPSEC_NONE, &info));
    assert(!DualScreen_GetRegionMapSection(65535, &info));
    assert(!DualScreen_GetRegionMapSection(MAPSEC_PALLET_TOWN, NULL));
    assert(!render(-1) && !render(4) && !render(256));
    for (int region = 0; region < 4; region++) {
        for (int repeat = 0; repeat < 4; repeat++) {
            jintArray pixels = render(region);
            assert(pixels);
            for (int i = 0; i < 240 * 160; i++) assert(((u32)pixels[i] >> 24) == 255);
            release(pixels);
        }
    }
    for (int failure = 1; failure <= 2; failure++) {
        failAllocation = failure;
        assert(!render(0));
    }
    failAllocation = 0;
    u32 original = sKanto_Tilemap[0];
    sKanto_Tilemap[0] = 0;
    assert(!render(0));
    sKanto_Tilemap[0] = original;
    original = sRegionMap_Gfx[0];
    sRegionMap_Gfx[0] = 0;
    assert(!render(0));
    sRegionMap_Gfx[0] = original;
    return 0;
}
#ifdef TEST_ASAN
int main(void) { return checks(); }
#endif
'''


def expected_pixels(gfx, tilemap, palette):
    entries = struct.unpack("<600H", tilemap)
    pixels = []
    for y in range(160):
        for x in range(240):
            entry = entries[(y // 8) * 30 + x // 8]
            sx = (7 - x % 8) if entry & 0x400 else x % 8
            sy = (7 - y % 8) if entry & 0x800 else y % 8
            nibble = (gfx[(entry & 1023) * 32 + sy * 4 + sx // 2] >> (4 * (sx % 2))) & 15
            color = palette[(entry >> 12) * 16 + nibble if nibble else 0]
            pixels.append(0xFF000000 | ((color & 31) << 19) | (((color >> 5) & 31) << 11) | (((color >> 10) & 31) << 3))
    return pixels


def literal_lz(data):
    return bytes([0x10]) + len(data).to_bytes(3, "little") + b"".join(b"\0" + data[i:i+8] for i in range(0, len(data), 8))


def write_png(path, pixels):
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    rows = b"".join(b"\0" + b"".join(struct.pack(">I", ((p & 0xFFFFFF) << 8) | 255)
                                    for p in pixels[y*240:(y+1)*240]) for y in range(160))
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 240,160,8,6,0,0,0))
                     + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview-dir", type=Path)
    args = parser.parse_args()
    bridge = (ROOT / "src/platform/dualscreen_bridge.c").read_text()
    region = (ROOT / "src/region_map.c").read_text()
    graphics = ROOT / "graphics/region_map"
    code = PREFIX + '\n#include "' + str(ROOT / "include/constants/region_map_sections.h") + '"\n'
    for filename in ("kanto", "sevii_123", "sevii_45", "sevii_67"):
        code += '#include "' + str(ROOT / ("src/data/region_map/region_map_layout_" + filename + ".h")) + '"\n'
    code += array(region, "sSeviiMapsecs") + "\n"
    code += c_asset("sRegionMap_Pal", graphics / "region_map.gbapal", 2)
    code += c_asset("sRegionMap_Gfx", graphics / "region_map.4bpp.lz", 4)
    names = ("sKanto_Tilemap", "sSevii123_Tilemap", "sSevii45_Tilemap", "sSevii67_Tilemap")
    files = ("kanto", "sevii_123", "sevii_45", "sevii_67")
    for name, filename in zip(names, files):
        code += c_asset(name, graphics / (filename + ".bin.lz"), 4, 1024)
    for name in ("GetSelectedMapSection", "DualScreen_GetRegionMapPal", "DualScreen_GetRegionMapGfxLZ",
                 "DualScreen_GetRegionMapTilemapLZ", "DualScreen_GetRegionMapSection"):
        code += function(region, name) + "\n"
    code += function((ROOT / "src/platform/bios.c").read_text(), "LZ77UnCompWram") + "\n"
    code += function(bridge, "Bgr555ToArgb") + "\n#define malloc testMalloc\n"
    code += function(bridge, JNI_NAME) + "\n#undef malloc\n" + SUFFIX
    with tempfile.TemporaryDirectory(prefix="firered-townmap-test-") as directory:
        temp = Path(directory)
        source = temp / "test.c"
        source.write_text(code)
        executable = temp / "test"
        subprocess.run(["clang", "-std=c11", "-g", "-O1", "-DTEST_ASAN",
                        "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
                        str(source), "-o", str(executable)], check=True)
        subprocess.run([str(executable)], check=True, timeout=10)
        print("PASS: four regions, real location tables, repeated rendering, invalid IDs/assets and allocation failures; ASan/UBSan clean")
        library = temp / "map.dylib"
        subprocess.run(["clang", "-std=c11", "-O2", "-dynamiclib", str(source), "-o", str(library)], check=True)
        lib = ctypes.CDLL(str(library))
        lib.render.argtypes = [ctypes.c_int]
        lib.render.restype = ctypes.POINTER(ctypes.c_uint32)
        lib.release.argtypes = [ctypes.POINTER(ctypes.c_uint32)]

        def render(which):
            result = lib.render(which)
            if not result:
                return None
            pixels = list(result[:240*160])
            lib.release(result)
            return pixels

        gfx = (graphics / "region_map.4bpp").read_bytes()
        palette = struct.unpack("<80H", (graphics / "region_map.gbapal").read_bytes())
        for which, filename in enumerate(files):
            pixels = render(which)
            assert pixels == expected_pixels(gfx, (graphics / (filename + ".bin")).read_bytes(), palette)
            assert len(set(pixels)) > 8
            if args.preview_dir:
                args.preview_dir.mkdir(parents=True, exist_ok=True)
                write_png(args.preview_dir / (filename + ".png"), pixels)
        print("PASS: all 153,600 pixels match original uncompressed FireRed map assets")

        native_map = (ctypes.c_ubyte * 4096).in_dll(lib, "sKanto_Tilemap")
        original = bytes(native_map)
        entries = struct.unpack("<600H", (graphics / "kanto.bin").read_bytes())
        for flip in (0x400, 0x800, 0xC00):
            transformed = struct.pack("<600H", *(entry ^ flip for entry in entries))
            encoded = literal_lz(transformed)
            native_map[:len(encoded)] = encoded
            assert render(0) == expected_pixels(gfx, transformed, palette)
        for invalid in (1023, 0xF000):
            encoded = literal_lz(struct.pack("<600H", *([invalid] * 600)))
            native_map[:len(encoded)] = encoded
            assert render(0) is None
        native_map[:] = original
        assert render(0) is not None
        print("PASS: horizontal/vertical flips, palette-bank/tile bounds and recovery")
    view = (ROOT / "android/app/src/main/java/com/pokeemerald/experimental/DualScreenView.java").read_text()
    assert "nativeGetRegionMapImage(state.mapRegion)" in view
    assert "regionMapRegion != state.mapRegion" in view
    assert "(e.x + 4)" in view and "(e.y + 4)" in view


if __name__ == "__main__":
    main()
