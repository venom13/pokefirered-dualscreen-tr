#!/usr/bin/env python3
"""ROM-free regression for the trainer replacement crash and party responses.

Runs the real opponent selector, player/tutorial selection callbacks, response
serializer and local buffer transfer under ASan/UBSan. AI scoring, party data,
link transport and completion callbacks are instrumented boundaries.
"""
from pathlib import Path
import os
import re
import subprocess
import tempfile
from test_bag_menu_init import function

ROOT = Path(__file__).resolve().parents[2]
PREFIX = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef int32_t s32;
#include "constants/battle.h"
#define TRUE 1
#define PARTY_SIZE 6
#define MON_DATA_HP 0
#define BUFFER_A 0
#define BUFFER_B 1
#define ARRAY_COUNT(a) (sizeof(a) / sizeof((a)[0]))
struct Pokemon { u16 hp; } gEnemyParty[PARTY_SIZE];
struct {
    u8 AI_monToSwitchIntoId[2], monToSwitchIntoId[4];
} battle, *gBattleStruct = &battle;
struct { void (*callback2)(void); } gMain;
struct { int active; } gPaletteFade;
u8 sBattleBuffersTransferData[256], gBattleBufferA[4][512], gBattleBufferB[4][512];
u8 gBattlePartyCurrentOrder[3], gBattlerPartyIndexes[4], gActiveBattler;
u8 gPartyMenuUseExitCallback, gSelectedMonPartyId;
u32 gBattleTypeFlags;
int aiChoice, completions, standby, linkCalls;
u8 linkData[8], linkBuffer;
u16 linkSize;
void BattleMainCB2(void) {}
void PartyMenuCB2(void) {}
int GetBattlerPosition(int battler) { return battler; }
int GetBattlerAtPosition(int position) { return position; }
int GetMostSuitableMonToSwitchInto(void) { return aiChoice; }
int GetMonData(struct Pokemon *mon, int field) { assert(field == MON_DATA_HP); return mon->hp; }
void OpponentBufferExecCompleted(void) { completions++; }
void PlayerBufferExecCompleted(void) { completions++; }
void OakOldManBufferExecCompleted(void) { completions++; }
void PokedudeBufferExecCompleted(void) { completions++; }
void PrintLinkStandbyMsg(void) { standby++; }
void PrepareBufferDataTransferLink(u8 buffer, u16 size, u8 *data) {
    assert(size <= sizeof(linkData));
    linkBuffer = buffer; linkSize = size; linkCalls++;
    memcpy(linkData, data, size);
}
'''

SUFFIX = r'''
static void Reset(void) {
    memset(&battle, 0, sizeof(battle));
    memset(gEnemyParty, 0, sizeof(gEnemyParty));
    memset(gBattlerPartyIndexes, 0, sizeof(gBattlerPartyIndexes));
    memset(sBattleBuffersTransferData, 0xDA, sizeof(sBattleBuffersTransferData));
    memset(gBattleBufferA, 0xBC, sizeof(gBattleBufferA));
    memset(gBattleBufferB, 0xBC, sizeof(gBattleBufferB));
    memset(linkData, 0xBC, sizeof(linkData));
    gBattlePartyCurrentOrder[0] = 0x20;
    gBattlePartyCurrentOrder[1] = 0x15;
    gBattlePartyCurrentOrder[2] = 0x34;
    gBattleTypeFlags = BATTLE_TYPE_TRAINER;
    gActiveBattler = 1;
    battle.AI_monToSwitchIntoId[0] = battle.AI_monToSwitchIntoId[1] = PARTY_SIZE;
    aiChoice = PARTY_SIZE;
    gMain.callback2 = BattleMainCB2;
    gPaletteFade.active = 0;
    completions = standby = linkCalls = 0;
}
static void Expect(u8 *data, int partyId, const u8 *order) {
    assert(data[0] == CONTROLLER_CHOSENMONRETURNVALUE);
    assert(data[1] == partyId);
    for (int i = 0; i < 3; i++) assert(data[2+i] == (order ? order[i] : 0));
    assert(data[5] == 0xBC); // five-byte wire format, no adjacent overwrite
    assert(gBattlePartyCurrentOrder[0] == 0x20 && gBattlePartyCurrentOrder[1] == 0x15
           && gBattlePartyCurrentOrder[2] == 0x34);
}
int main(void) {
    // Supplied party order is copied exactly on native and original GBA paths.
    for (int link = 0; link < 2; link++) {
        for (int buffer = BUFFER_A; buffer <= BUFFER_B; buffer++) {
            for (int partyId = 0; partyId < PARTY_SIZE; partyId++) {
                Reset();
                if (link) gBattleTypeFlags |= BATTLE_TYPE_LINK | BATTLE_TYPE_MULTI;
                BtlController_EmitChosenMonReturnValue(buffer, partyId, gBattlePartyCurrentOrder);
                Expect(link ? linkData : (buffer == BUFFER_A ? gBattleBufferA[1] : gBattleBufferB[1]),
                       partyId, gBattlePartyCurrentOrder);
                assert(linkCalls == link);
                if (link) assert(linkSize == 5 && linkBuffer == buffer);
            }
        }
    }
#ifdef PORTABLE
    // Route 22 rival: first party member fainted; next living mon is slot 1.
    // Also exercise later replacements and AI preselection/scoring paths.
    for (int mode = 0; mode < 3; mode++) {
        for (int partyId = 1; partyId < PARTY_SIZE; partyId++) {
            Reset();
            gEnemyParty[partyId].hp = 20;
            if (mode == 1) aiChoice = partyId;
            if (mode == 2) battle.AI_monToSwitchIntoId[0] = partyId;
            OpponentHandleChoosePokemon();
            assert(battle.monToSwitchIntoId[1] == partyId && completions == 1);
            assert(battle.AI_monToSwitchIntoId[0] == PARTY_SIZE);
            Expect(gBattleBufferB[1], partyId, NULL);
        }
    }
    // Doubles cannot choose either active foe's party slot.
    for (int battler = 1; battler <= 3; battler += 2) {
        Reset();
        gActiveBattler = battler;
        gBattleTypeFlags |= BATTLE_TYPE_DOUBLE;
        gBattlerPartyIndexes[3] = 1;
        gEnemyParty[0].hp = gEnemyParty[1].hp = gEnemyParty[2].hp = 20;
        OpponentHandleChoosePokemon();
        assert(battle.monToSwitchIntoId[battler] == 2 && completions == 1);
        Expect(gBattleBufferB[battler], 2, NULL);
    }
    // Real cancellation callers also pass NULL; wait until the party screen
    // and its fade finish before replying, and preserve a valid chosen order.
    void (*callbacks[])(void) = {PlayerWaitForMonSelection, OakWaitForMonSelection, PokedudeWaitForMonSelection};
    for (int controller = 0; controller < 3; controller++) {
        for (int chosen = 0; chosen < 2; chosen++) {
            for (int link = 0; link < 2; link++) {
                Reset();
                gActiveBattler = 0;
                gBattleBufferA[0][1] = 1;
                gPartyMenuUseExitCallback = chosen;
                gSelectedMonPartyId = 2;
                if (link) gBattleTypeFlags |= BATTLE_TYPE_LINK | BATTLE_TYPE_MULTI;
                gMain.callback2 = PartyMenuCB2;
                callbacks[controller]();
                assert(completions == 0 && linkCalls == 0);
                gMain.callback2 = BattleMainCB2;
                gPaletteFade.active = 1;
                callbacks[controller]();
                assert(completions == 0 && linkCalls == 0);
                gPaletteFade.active = 0;
                callbacks[controller]();
                assert(completions == 1 && linkCalls == link);
                Expect(link ? linkData : gBattleBufferB[0], chosen ? 2 : PARTY_SIZE,
                       chosen ? gBattlePartyCurrentOrder : NULL);
                assert(standby == (controller == 0));
            }
        }
    }
    Reset();
    PlayerHandleChosenMonReturnValue();
    assert(completions == 1);
    Expect(gBattleBufferB[1], 0, NULL);
    // A null response following a real order must not leak its previous bytes.
    BtlController_EmitChosenMonReturnValue(BUFFER_B, 2, gBattlePartyCurrentOrder);
    BtlController_EmitChosenMonReturnValue(BUFFER_B, PARTY_SIZE, NULL);
    Expect(gBattleBufferB[1], PARTY_SIZE, NULL);
    puts("PASS: rival replacements, AI choices, doubles, player/tutorial cancellation, link responses and unchanged party order");
#else
    puts("PASS: original GBA response format with supplied party orders");
#endif
    return 0;
}
'''


def main():
    controller = (ROOT / "src/battle_controllers.c").read_text()
    header = (ROOT / "include/battle_controllers.h").read_text()
    command_enum = re.search(r"enum\s*\{[^{}]*CONTROLLER_CHOSENMONRETURNVALUE[^{}]*\};", header).group(0)
    parts = [PREFIX, command_enum]
    for name in ("PrepareBufferDataTransfer", "BtlController_EmitChosenMonReturnValue"):
        parts.append(function(controller, name))
    opponent = (ROOT / "src/battle_controller_opponent.c").read_text()
    parts.append(function(opponent, "OpponentHandleChoosePokemon"))
    for filename, prefix in (("player", "Player"), ("oak_old_man", "Oak"), ("pokedude", "Pokedude")):
        source = (ROOT / f"src/battle_controller_{filename}.c").read_text()
        parts.append(function(source, "WaitForMonSelection").replace("WaitForMonSelection", prefix + "WaitForMonSelection"))
        if filename == "player":
            parts.append(function(source, "PlayerHandleChosenMonReturnValue"))
    parts.append(SUFFIX)
    with tempfile.TemporaryDirectory(prefix="firered-switch-return-") as tmp:
        source = Path(tmp) / "test.c"
        source.write_text("\n".join(parts))
        for portable in (True, False):
            binary = Path(tmp) / ("native" if portable else "gba")
            flags = ["-DPORTABLE"] if portable else []
            subprocess.run([os.environ.get("CC", "cc"), "-std=c11", "-g", "-O1",
                            "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
                            "-I", str(ROOT / "include"), *flags, str(source), "-o", str(binary)], check=True)
            subprocess.run([str(binary)], check=True)


if __name__ == "__main__":
    main()
