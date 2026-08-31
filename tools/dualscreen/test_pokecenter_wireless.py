#!/usr/bin/env python3
"""ROM-free regression for Pokemon Center's background Union Room startup."""
from pathlib import Path
import os
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]


def extract_function(source, name):
    match = re.search(r"(?m)^void " + name + r"\([^;{}]*\)\s*\{", source)
    if match is None:
        raise AssertionError("function missing: " + name)
    end, depth = match.end(), 1
    while depth:
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    return source[match.start():end]


def main():
    source = (ROOT / "src/union_room.c").read_text()
    # Reproduce the real map-script entry point, not a different wireless probe.
    map_script = (ROOT / "data/maps/ViridianCity_PokemonCenter_1F/scripts.inc").read_text()
    common = (ROOT / "data/scripts/cable_club.inc").read_text()
    assert "map_script MAP_SCRIPT_ON_RESUME, CableClub_OnResume" in map_script
    assert re.search(r"CableClub_OnResume::\s+special InitUnionRoom\s+end", common)

    prefix = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef uint8_t u8;
#define EOS 0xFF
static int playback, tasks, allocations;
#define QL_IS_PLAYBACK_STATE playback
struct WirelessLink_URoom {
    int state, textState, unknown, unreadPlayerId;
};
static struct { struct WirelessLink_URoom *uRoom; } sWirelessLinkMain;
static struct WirelessLink_URoom *sURoom;
static u8 sUnionRoomPlayerName[8];
static void Task_InitUnionRoom(u8 taskId) { abort(); }
static u8 CreateTask(void (*fn)(u8), u8 priority) {
    assert(fn == Task_InitUnionRoom && priority == 0);
    tasks++;
    return 0;
}
static void *AllocZeroed(size_t size) {
    allocations++;
    return calloc(1, size);
}
'''
    suffix = r'''
int main(void) {
    for (int replay = 0; replay < 2; replay++) {
        playback = replay;
        for (int entry = 0; entry < 20; entry++) {
            tasks = allocations = 0;
            sWirelessLinkMain.uRoom = sURoom = NULL;
            memset(sUnionRoomPlayerName, 'A', sizeof(sUnionRoomPlayerName));
            InitUnionRoom();
            assert(sUnionRoomPlayerName[0] == EOS);
#if defined(PORTABLE) || REVISION >= 0xA
            assert(tasks == 0 && allocations == 0);
            assert(sWirelessLinkMain.uRoom == NULL && sURoom == NULL);
#else
            assert(tasks == !playback && allocations == !playback);
            if (!playback) {
                assert(sURoom == sWirelessLinkMain.uRoom);
                assert(sURoom->state == 0 && sURoom->textState == 0);
                assert(sURoom->unknown == 0 && sURoom->unreadPlayerId == 0);
                free(sURoom);
            }
#endif
        }
    }
    puts("PASS: repeated Center entry and quest-log resume preserve expected RFU startup behavior");
    return 0;
}
'''
    with tempfile.TemporaryDirectory(prefix="firered-center-test-") as directory:
        temp = Path(directory)
        c = temp / "test.c"
        c.write_text(prefix + extract_function(source, "InitUnionRoom") + suffix)
        for portable, revision in ((True, 1), (False, 1), (True, 10), (False, 10)):
            executable = temp / f"test-{portable}-{revision}"
            flags = [f"-DREVISION={revision}"]
            if portable:
                flags.append("-DPORTABLE")
            subprocess.run([os.environ.get("CC", "cc"), "-std=c11", "-g", "-O1",
                            "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
                            *flags, str(c), "-o", str(executable)], check=True)
            subprocess.run([str(executable)], check=True, timeout=5)


if __name__ == "__main__":
    main()
