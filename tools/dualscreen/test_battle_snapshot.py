#!/usr/bin/env python3
"""ROM-free regression for stale battler cards between encounters.

Compiles the actual battle init/intro callbacks, readiness query, snapshot
builder and frame publisher under ASan/UBSan. Hardware, controller transport
and unrelated player/bag serialization are test doubles. Mon serialization
records which battle structs the real snapshot builder exposes.
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
#include <stdarg.h>
#include <string.h>
typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32, bool32;
typedef int32_t s32;
#define PLATFORM_SDL2 1
#define TRUE 1
#define FALSE 0
#include "constants/battle.h"
#include "constants/pokemon.h"
#include "constants/flags.h"
#define PARTY_SIZE 6
#define BUFFER_A 0
#define REQUEST_ALL_BATTLE 0
#define MULTIUSE_STATE 0
#define SPRITES_INIT_STATE1 2
#define FLAG_SET_SEEN 1
#define FLAG_GET_SEEN 2
#define FLAG_GET_CAUGHT 3
#define PLAYER_NAME_LENGTH 7
#define MAP_NAME_LENGTH 20
#define BATTLE_TYPE_FRONTIER_NO_PYRAMID 0
#define BATTLE_TYPE_RECORDED_LINK 0
#define BATTLE_TYPE_PYRAMID 0
#define DISPLAY_WIDTH 240
#define DISPLAY_HEIGHT 160
#define WIN_RANGE(a,b) (((a) << 8) | (b))
#define SNAPSHOT_CAPACITY 28672
#define SNAPSHOT_FRAME_INTERVAL 8
#define A_BUTTON 1
#define B_BUTTON 2
#define DPAD_RIGHT 16
#define DPAD_LEFT 32
#define DPAD_UP 64
#define DPAD_DOWN 128
#define DPAD_ANY 240
#define NAV_UP 0
#define NAV_DOWN 1
#define NAV_LEFT 2
#define NAV_RIGHT 3
#define NAV_CONFIRM 4
#define NAV_CANCEL 5

struct { bool32 inBattle; u16 newKeys, newAndRepeatedKeys; } gMain;
struct BattlePokemon {
    u16 species, hp, maxHP;
    u8 type1, type2, ability, abilityNum, statStages[NUM_BATTLE_STATS];
    u32 personality, status2;
} gBattleMons[4], nextMons[4];
struct { u8 types[2]; } gSpeciesInfo[500];
struct { u16 hpOnSwitchout[2]; u8 playerPartyIdx; } battleStruct, *gBattleStruct = &battleStruct;
struct Pokemon { int unused; } gPlayerParty[6], gEnemyParty[6];
struct { u8 regionMapSectionId; } gMapHeader;
struct {
    u8 playerName[8], playerTrainerId[4], playerGender;
    unsigned playTimeHours, playTimeMinutes;
} save2, *gSaveBlock2Ptr = &save2;
struct { u32 money; struct { int mapGroup, mapNum; } location; struct { int x, y; } pos; }
    save1, *gSaveBlock1Ptr = &save1;
struct DualScreenMapSection { unsigned region; };
u8 gBattleBufferB[4][512], gBattleCommunication[8], gBattlersCount, gActiveBattler;
u8 gActionSelectionCursor[4], gMoveSelectionCursor[4], gBattlerPartyIndexes[4];
u8 gAbsentBattlerFlags, gReservedSpritePaletteCount, gBattleTerrain, gPlayerPartyCount;
u32 gBattleTypeFlags, gBattleControllerExecFlags, gTrainerBattleOpponent_A;
u16 gBattle_BG0_X, gBattle_BG0_Y, gBattle_BG1_X, gBattle_BG1_Y;
u16 gBattle_BG2_X, gBattle_BG2_Y, gBattle_BG3_X, gBattle_BG3_Y, gBattle_WIN0H, gBattle_WIN0V;
u16 gScanlineEffectRegBuffers[2][160];
void (*gBattleMainFunc)(void);
static bool32 sBattleMonsReady, sSnapshotInBattle, sSnapshotBattleReady;
static u32 sFrameCounter, sBattleMenuMode, sVirtualInputFrame, sButtonPressCount;
static u32 sFieldChoiceOpen, sFieldChoiceOpenFrame;
static int sVirtualKeyCount, sFrontBuffer, sBattleCursor, menu = 1, reads, publications;
static char sBuffers[2][SNAPSHOT_CAPACITY];
static void *sSnapshotMutex;
static u32 DualScreen_BattleDataReady(void);
static void BuildSnapshot(char *buffer, int capacity);
static void BattleIntroPrepareBackgroundSlide(void);
static void BattleIntroDrawTrainersOrMonsSprites(void);
static void BattleIntroDrawPartySummaryScreens(void) {}

// Hardware and field setup do not change battle-mon storage.
#define SetHBlankCallback(...) assert(!sBattleMonsReady)
#define SetVBlankCallback(...) ((void)0)
#define CpuFill32(...) ((void)0)
#define SetGpuReg(...) ((void)0)
#define ScanlineEffect_Clear() ((void)0)
#define ScanlineEffect_SetParams(...) ((void)0)
#define ResetPaletteFade() ((void)0)
#define BattleSetup_GetTerrainId() 0
#define InitBattleBgsVideo() ((void)0)
#define LoadBattleTextboxAndBackground() ((void)0)
#define ResetSpriteData() ((void)0)
#define ResetTasks() ((void)0)
#define DrawBattleEntryBackground() ((void)0)
#define FreeAllSpritePalettes() ((void)0)
#define SetUpBattleVars() ((void)0)
#define SetMainCallback2(...) ((void)0)
#define CreateNPCTrainerParty(...) ((void)0)
#define SetWildMonHeldItem() ((void)0)
#define AdjustFriendship(...) ((void)0)
int GetBattlerAtPosition(int i) { return i; }
int GetBattlerPosition(int i) { return i; }
int GetBattlerSide(int i) { return i & 1; }
int GetAbilityBySpecies(int species, int num) { return 1; }
int SpeciesToNationalPokedexNum(int species) { return species; }
void HandleSetPokedexFlag(int species, int flag, u32 personality) {}
void MarkBattlerForControllerExec(int i) { gBattleControllerExecFlags |= 1u << i; }
void BtlController_EmitGetMonData(int buffer, int request, int arg) {
    memcpy(&gBattleBufferB[gActiveBattler][4], &nextMons[gActiveBattler], sizeof(nextMons[0]));
}
void CheckStillLoading(void) {
    // Called inside the real copy loop; no partially updated doubles cards.
    char json[SNAPSHOT_CAPACITY];
    assert(!DualScreen_BattleDataReady());
    BuildSnapshot(json, sizeof(json));
    assert(strstr(json, "\"battle\":") == NULL);
}
void BtlController_EmitIntroSlide(int buffer, int terrain) { CheckStillLoading(); }
void BtlController_EmitDrawTrainerPic(int buffer) { CheckStillLoading(); }
void BtlController_EmitLoadMonSprite(int buffer) { CheckStillLoading(); }

int IsInGame(void) { return 1; }
int FlagGet(int flag) { return 0; }
unsigned GetKantoPokedexCount(int flag) { return 0; }
int GetTrainerCardStars(int arg) { return 0; }
u32 GetMoney(u32 *money) { return *money; }
void DecodeGbaString(char *dst, int capacity, const u8 *src, int length) { dst[0] = 0; }
void GetMapName(u8 *dst, int section, int arg) { dst[0] = 0; }
void DualScreen_GetRegionMapSection(int section, struct DualScreenMapSection *out) { out->region = 0; }
int ResolveBattleMenu(u8 *battler) { *battler = 0; return menu; }
u32 DualScreen_BattleMenuInfo(u32 *a, u32 *b, u32 *c, u32 *d) { *a = *b = *c = *d = 0; return sBattleMenuMode; }
int DualScreen_BattleUiActive(void) { return 1; }
int DualScreen_PlayerAtMoveSelect(void) { return menu == 2; }
int DualScreen_PlayerAtActionSelect(void) { return menu == 1; }
void PushNav(int direction) {}
void *SDL_CreateMutex(void) { static int mutex; return &mutex; }
void SDL_LockMutex(void *mutex) { publications++; }
void SDL_UnlockMutex(void *mutex) {}
void SDL_AtomicSet(int *dst, int value) { *dst = value; }

struct JsonWriter { char *buffer; int length, capacity; };
static void JsonPut(struct JsonWriter *w, const char *format, ...);
static void WriteFieldChoiceJson(struct JsonWriter *w) { (void)w; }
void WritePartyMonJson(struct JsonWriter *w, struct Pokemon *mon) { JsonPut(w, "{}"); }
void WriteBagJson(struct JsonWriter *w) { JsonPut(w, "\"bag\":[],"); }
void WriteBattleMonJson(struct JsonWriter *w, const struct BattlePokemon *mon,
                        const struct BattlePokemon **foes, int enemy, int partyId) {
    assert(DualScreen_BattleDataReady());
    reads++;
    // The actual snapshot builder chooses these pointers. Retain real HP and
    // identity in the output rather than replacing unready mons with full HP.
    JsonPut(w, "{\"species\":%u,\"hp\":%u,\"personality\":%u}",
            mon->species, mon->hp, mon->personality);
}
'''

SUFFIX = r'''
static void ExpectSnapshot(int ready, int count) {
    char json[SNAPSHOT_CAPACITY];
    reads = 0;
    BuildSnapshot(json, sizeof(json));
    assert((strstr(json, "\"battle\":") != NULL) == ready);
    assert(reads == (ready ? count : 0));
    if (ready) {
        char expected[128];
        snprintf(expected, sizeof(expected), "\"enemyMon\":{\"species\":%u,\"hp\":%u,\"personality\":%u}",
                 nextMons[1].species, nextMons[1].hp, nextMons[1].personality);
        assert(strstr(json, expected));
    }
}
static void StartEncounter(int count, u32 flags, int sameSpecies, int reducedHp) {
    gBattleTypeFlags = flags;
    for (int i = 0; i < count; i++) {
        nextMons[i] = (struct BattlePokemon){ .species = sameSpecies ? 16 : 19,
            .hp = reducedHp ? 7 : 20, .maxHP = 20, .personality = 1000 + sFrameCounter + i };
    }
    // The real init must reset readiness, including when the bridge did not
    // sample the intervening overworld frame.
    CB2_InitBattleInternal();
    gBattlersCount = count;
    gBattleControllerExecFlags = 0;
    gBattleCommunication[1] = 0;
    gBattleMainFunc = BattleIntroGetMonsData;
    assert(gMain.inBattle && !DualScreen_BattleDataReady());
    ExpectSnapshot(0, count);
    int before = publications;
    DualScreen_FrameHook();
    assert(publications == before + 1); // entry bypasses the 8-frame throttle
    assert(sBattleCursor == -1 && !strstr(sBuffers[sFrontBuffer], "\"battle\":"));

    int delay = 0, frames = 0;
    while (gBattleMainFunc != BattleIntroDrawPartySummaryScreens) {
        assert(++frames < 100);
        gBattleMainFunc();
        int ready = DualScreen_BattleDataReady();
        ExpectSnapshot(ready, count);
        before = publications;
        DualScreen_FrameHook();
        if (ready) {
            assert(publications == before + 1); // no delay when new mons arrive
            assert(strstr(sBuffers[sFrontBuffer], "\"battle\":"));
        } else {
            assert(sBattleCursor == -1);
            assert(!strstr(sBuffers[sFrontBuffer], "\"battle\":"));
        }
        // Transport completion is deliberately slow and spans snapshot polls.
        if (gBattleControllerExecFlags && ++delay == 5) {
            delay = 0;
            gBattleControllerExecFlags = 0;
        }
    }
    assert(DualScreen_BattleDataReady() && sBattleCursor >= 0);
    for (int i = 0; i < count; i++) {
        if ((flags & BATTLE_TYPE_SAFARI) && !(i & 1)) {
            assert(gBattleMons[i].species == 0 && gBattleMons[i].hp == 0);
        } else {
            assert(gBattleMons[i].personality == nextMons[i].personality);
            assert(gBattleMons[i].hp == nextMons[i].hp);
        }
    }
    // Ordinary damage and open BAG waiting must continue publishing live HP.
    nextMons[1].hp = gBattleMons[1].hp = 3;
    sBattleMenuMode = 1;
    menu = 0;
    for (int frame = 0; frame < 24; frame++) {
        DualScreen_FrameHook();
        ExpectSnapshot(1, count);
    }
    sBattleMenuMode = 0;
    menu = 1;
    // The forced doubles picker must see the first battler's queued choice,
    // while ordinary cards/BAG must not inherit that stale selection.
    for (int mode = 0; mode <= 2; mode++) {
        for (int selected = 0; selected <= PARTY_SIZE; selected++) {
            char json[SNAPSHOT_CAPACITY], expected[32];
            sBattleMenuMode = mode;
            battleStruct.playerPartyIdx = selected;
            BuildSnapshot(json, sizeof(json));
            snprintf(expected, sizeof(expected), "\"prevSel\":%d,", mode == 2 ? selected : PARTY_SIZE);
            assert(strstr(json, expected));
        }
    }
    sBattleMenuMode = 0;
}
int main(void) {
    assert(!DualScreen_BattleDataReady());
    const u32 flags[] = {0, BATTLE_TYPE_TRAINER, BATTLE_TYPE_DOUBLE | BATTLE_TYPE_TRAINER,
        BATTLE_TYPE_DOUBLE | BATTLE_TYPE_MULTI | BATTLE_TYPE_LINK, BATTLE_TYPE_SAFARI, BATTLE_TYPE_ROAMER};
    int encounters = 0;
    for (int kind = 0; kind < 6; kind++) {
        for (int same = 0; same < 2; same++) {
            for (int phase = 0; phase < SNAPSHOT_FRAME_INTERVAL; phase++) {
                sFrameCounter = sFrameCounter / 8 * 8 + phase;
                int count = flags[kind] & BATTLE_TYPE_DOUBLE ? 4 : 2;
                // Prior foe after damage + RUN, deliberately retained in RAM.
                gBattleMons[1].species = 16;
                gBattleMons[1].hp = 3;
                gMain.inBattle = 0;
                if (phase & 1) {
                    int before = publications;
                    DualScreen_FrameHook();
                    if (encounters) assert(publications == before + 1);
                    ExpectSnapshot(0, count);
                    assert(sBattleCursor == -1);
                }
                StartEncounter(count, flags[kind], same, kind == 5);
                encounters++;
            }
        }
    }
    gMain.inBattle = 0;
    assert(!DualScreen_BattleDataReady());
    gMain.inBattle = 1;
    gBattlersCount = 0;
    ExpectSnapshot(0, 0);
    gBattlersCount = 5;
    ExpectSnapshot(0, 0);
    printf("PASS: %d encounters, all snapshot phases, delayed controllers, same/different species, doubles, Safari, roamer HP, exit and BAG waiting\n", encounters);
    return 0;
}
'''


def main():
    battle = (ROOT / "src/battle_main.c").read_text()
    bridge = (ROOT / "src/platform/dualscreen_bridge.c").read_text()
    parts = [PREFIX]
    for name in ("DualScreen_BattleDataReady", "CB2_InitBattleInternal", "BattleIntroGetMonsData",
                 "BattleIntroPrepareBackgroundSlide", "BattleIntroDrawTrainersOrMonsSprites"):
        parts.append(function(battle, name))
    for name in ("JsonPut", "JsonPutString", "BuildSnapshot", "DualScreen_FrameHook"):
        parts.append(function(bridge, name))
    parts.append(SUFFIX)
    with tempfile.TemporaryDirectory(prefix="firered-battle-snapshot-") as tmp:
        source = Path(tmp) / "test.c"
        binary = Path(tmp) / "test"
        source.write_text("\n".join(parts))
        subprocess.run([os.environ.get("CC", "cc"), "-std=c11", "-g", "-O1",
                        "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
                        "-I", str(ROOT / "include"), str(source), "-o", str(binary)], check=True)
        subprocess.run([str(binary)], check=True)


if __name__ == "__main__":
    main()
