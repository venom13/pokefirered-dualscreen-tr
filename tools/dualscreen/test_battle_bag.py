#!/usr/bin/env python3
"""ROM-free regression for the actual battle BAG controllers and item adapter.

Compiles their C functions with instrumented game/SDL boundaries under ASan and
UBSan. Verifies waiting, fallback, cancellation, validation, item consumption,
party/move targeting, healthbox refresh and preservation of FireRed party order.
Also compiles the actual Java panel reconciliation method (requires a JDK).
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
typedef uint8_t u8, bool8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef int32_t s32;
#define TRUE 1
#define FALSE 0
#define PLATFORM_SDL2 1
#include "constants/battle.h"
#include "constants/items.h"
#include "constants/item_effects.h"
#include "constants/species.h"
#include "constants/moves.h"
#include "platform/dualscreen.h"
#define PARTY_SIZE 6
#define MAX_MON_MOVES 4
#define MON_DATA_SPECIES 0
#define MON_DATA_IS_EGG 1
#define MON_DATA_MOVE1 2
#define B_SIDE_PLAYER 0
#define SE_USE_ITEM 1
#define SE_GLASS_FLUTE 2
#define QL_EVENT_USED_ITEM 1
#define HEALTHBOX_ALL 0
#define PALETTES_ALL 0
#define RGB_BLACK 0
#define SDL_AtomicLock(p) ((void)0)
#define SDL_AtomicUnlock(p) ((void)0)
#define DS_TAKEOVER_TTL_FRAMES 240
struct Pokemon { int species, egg, moves[4]; } gPlayerParty[6];
struct { int inBattle; } gMain;
struct { struct { u8 itemEffect[8]; } enigmaBerry; } save, *gSaveBlock1Ptr = &save;
u8 effects[8], *gItemEffectTable[ITEMS_COUNT];
u8 gActiveBattler, gBattlerInMenuId, gBattlersCount, gBattlerPartyIndexes[4];
u8 gHealthboxSpriteIds[4], gAbsentBattlerFlags, gBattlePartyCurrentOrder[3];
u8 gBattleBufferA[4][4];
u16 gSpecialVar_ItemId;
u32 gBattleTypeFlags;
void (*gBattlerControllerFuncs[4])(void);
u32 sBattleArmMode, sBattleArmFrame, sFrameCounter;
u32 sBattleMenuMode, sBattleMenuCaseId, sBattleMenuBattler, sBattleMenuResult, sBattleMenuSeq;
u32 sBattleChoicePending;
s32 sBattleChoiceA, sBattleChoiceB;
int live, uiActive, fade, done, emitted, count, effectFails, effectCalls, effectTarget, effectMove;
int boxes, lowHp, sound, full, enigmaType;
typedef void (*ItemUseFunc)(u8);
#define FN(name) void name(u8 task) {}
FN(BattleUseFunc_PokeBallEtc) FN(BattleUseFunc_Medicine) FN(BattleUseFunc_StatBooster)
FN(BattleUseFunc_PokeDoll) FN(BattleUseFunc_Ether) FN(BattleUseFunc_PokeFlute)
FN(ItemUseInBattle_EnigmaBerry)
ItemUseFunc ItemId_GetBattleFunc(u16 id) {
    switch(id) {
    case ITEM_POKE_BALL: return BattleUseFunc_PokeBallEtc;
    case ITEM_POTION: case ITEM_REVIVE: case ITEM_BLUE_FLUTE: return BattleUseFunc_Medicine;
    case ITEM_X_ATTACK: return BattleUseFunc_StatBooster;
    case ITEM_POKE_DOLL: return BattleUseFunc_PokeDoll;
    case ITEM_ETHER: case ITEM_ELIXIR: return BattleUseFunc_Ether;
    case ITEM_POKE_FLUTE: return BattleUseFunc_PokeFlute;
    case ITEM_ENIGMA_BERRY: return ItemUseInBattle_EnigmaBerry;
    default: return NULL;
    }
}
int ItemId_GetBattleUsage(u16 id) { return ItemId_GetBattleFunc(id) != NULL; }
int GetItemEffectType(u16 id) { return id == ITEM_ENIGMA_BERRY ? enigmaType : ITEM_EFFECT_HEAL_HP; }
int GetMonData(struct Pokemon *mon, int field) {
    if (field == MON_DATA_SPECIES) return mon->species;
    if (field == MON_DATA_IS_EGG) return mon->egg;
    assert(field >= 2 && field < 6); return mon->moves[field - 2];
}
int GetBattlerSide(int i) { return i & 1; }
int CheckBagHasItem(int id, int qty) { return count >= qty; }
void RemoveBagItem(int id, int qty) { assert(count >= qty); count -= qty; }
int IsPlayerPartyAndPokemonStorageFull(void) { return full; }
void ItemUse_SetQuestLogEvent(int event, struct Pokemon *mon, int item, int param) {}
int ExecuteTableBasedItemEffect(struct Pokemon *mon, int id, int target, int move) {
    assert(mon == &gPlayerParty[target]);
    assert(gBattlePartyCurrentOrder[0] == 0x01 && gBattlePartyCurrentOrder[1] == 0x23 && gBattlePartyCurrentOrder[2] == 0x45);
    effectCalls++; effectTarget = target; effectMove = move;
    gActiveBattler = 2; /* item helpers may change this global */
    return effectFails;
}
void UpdateHealthboxAttribute(int sprite, struct Pokemon *mon, int field) { boxes++; }
void HandleBattleLowHpMusicChange(void) { lowHp++; }
void PlaySE(int id) { sound = id; }
u32 DualScreen_BottomScreenLive(void) { return live; }
u32 DualScreen_BattleUiActive(void) { return uiActive; }
void ClearNavQueue(void) {}
void OpenBagAndChooseItem(void) {}
void BeginNormalPaletteFade(int a, int b, int c, int d, int e) { fade++; }
void BtlController_EmitOneReturnValue(int channel, int item) { assert(channel == 1); emitted = item; }
void PlayerBufferExecCompleted(void) { done++; }
void OakOldManBufferExecCompleted(void) { done++; }
'''
SUFFIX = r'''
void reset(void) {
    gMain.inBattle = live = uiActive = 1;
    gBattlersCount = 4; gActiveBattler = 0; gBattlerInMenuId = 0;
    gBattlerPartyIndexes[0] = 2; gBattlerPartyIndexes[2] = 4;
    gBattleBufferA[0][1] = 0x20; gBattleBufferA[0][2] = 0x13; gBattleBufferA[0][3] = 0x45;
    memcpy(gBattlePartyCurrentOrder, gBattleBufferA[0] + 1, 3);
    for (int i=0; i<6; ++i) { gPlayerParty[i].species = SPECIES_CHARMANDER; gPlayerParty[i].egg = 0;
        for (int m=0; m<4; ++m) gPlayerParty[i].moves[m] = MOVE_SCRATCH;
    }
    gBattleTypeFlags = gAbsentBattlerFlags = 0;
    fade = done = full = effectFails = effectCalls = boxes = lowHp = sound = 0;
    emitted = -999; count = 3;
    sBattleMenuMode = sBattleChoicePending = sBattleArmMode = 0;
    sFrameCounter = 500; sBattleMenuSeq = 0;
    memset(effects, 0, sizeof(effects));
    for (int i=0; i<ITEMS_COUNT; ++i) gItemEffectTable[i] = effects;
}
void submit(int item, int target) { sBattleChoiceA = item; sBattleChoiceB = target; sBattleChoicePending = 1; }
void tick(void) { sFrameCounter++; gBattlerControllerFuncs[0](); }
void orderPreserved(void) { assert(!memcmp(gBattlePartyCurrentOrder, gBattleBufferA[0]+1, 3)); assert(gActiveBattler == 0); }
int main(void) {
    void (*entries[])(void) = {PlayerHandleChooseItem, OakOldManHandleChooseItem};
    for (int entry=0; entry<2; ++entry) {
        for (int armed=0; armed<2; ++armed) {
            reset(); live = !armed; sBattleArmMode = armed ? 1 : 0; sBattleArmFrame = sFrameCounter;
            entries[entry]();
            assert(sBattleMenuMode == 1 && !fade && !done && gBattlerInMenuId == 0);
            for (int i=0; i<3600; ++i) tick(); /* a minute, well beyond the old 2.5 s timeout */
            assert(sBattleMenuMode == 1 && !fade && !done && !effectCalls && count == 3);
            submit(ITEM_POTION, -1); tick();
            assert(sBattleMenuMode == 1 && sBattleMenuResult == DS_BMENU_RESULT_BAD_TARGET && !done && count == 3);
            effectFails = 1; submit(ITEM_POTION, 2); tick();
            assert(sBattleMenuResult == DS_BMENU_RESULT_NO_EFFECT && !done && count == 3); orderPreserved();
            effectFails = 0; submit(ITEM_POTION, 2); tick();
            assert(!sBattleMenuMode && done == 1 && emitted == ITEM_POTION && count == 2 && boxes == 1 && lowHp == 1);
            orderPreserved();
            live = 1; entries[entry](); submit(-1, -1); tick();
            assert(!sBattleMenuMode && done == 2 && emitted == ITEM_NONE && gSpecialVar_ItemId == ITEM_NONE && count == 2);
        }
        for (int fallback=0; fallback<2; ++fallback) {
            reset(); if (fallback) uiActive = 0; else live = 0;
            entries[entry](); assert(fade == 1 && !sBattleMenuMode && gBattlerControllerFuncs[0] == OpenBagAndChooseItem);
        }
    }
    reset(); gBattleTypeFlags = BATTLE_TYPE_MULTI; PlayerHandleChooseItem(); assert(fade == 1);
    reset(); PlayerHandleChooseItem();
    int invalid[] = {-2, ITEMS_COUNT, 65536 + ITEM_POTION, 0x7fffffff};
    for (unsigned i=0; i<sizeof(invalid)/sizeof(*invalid); ++i) {
        submit(invalid[i], 2); tick(); assert(!done && sBattleMenuMode == 1 && count == 3 && !effectCalls);
    }
    reset(); assert(DualScreen_UseBattleItem(ITEM_POKE_BALL,-1,-1) == DS_BMENU_RESULT_USED && count == 2 && !effectCalls);
    full = 1; assert(DualScreen_UseBattleItem(ITEM_POKE_BALL,-1,-1) == DS_BMENU_RESULT_CANT_USE && count == 2);
    full = 0; gBattleTypeFlags = BATTLE_TYPE_TRAINER;
    assert(DualScreen_UseBattleItem(ITEM_POKE_BALL,-1,-1) == DS_BMENU_RESULT_CANT_USE);
    assert(DualScreen_UseBattleItem(ITEM_POKE_DOLL,-1,-1) == DS_BMENU_RESULT_CANT_USE);
    gBattleTypeFlags = 0; assert(DualScreen_UseBattleItem(ITEM_POKE_DOLL,-1,-1) == DS_BMENU_RESULT_USED && count == 1);
    reset(); assert(DualScreen_UseBattleItem(ITEM_X_ATTACK,-1,-1) == DS_BMENU_RESULT_USED && effectTarget == 2); orderPreserved();
    reset(); gPlayerParty[1].egg = 1;
    assert(DualScreen_UseBattleItem(ITEM_POTION,1,-1) == DS_BMENU_RESULT_BAD_TARGET && count == 3);
    assert(DualScreen_UseBattleItem(ITEM_POTION,6,-1) == DS_BMENU_RESULT_BAD_TARGET);
    reset(); assert(DualScreen_UseBattleItem(ITEM_BLUE_FLUTE,2,-1) == DS_BMENU_RESULT_USED && count == 3 && sound == SE_GLASS_FLUTE);
    assert(DualScreen_UseBattleItem(ITEM_POKE_FLUTE,-1,-1) == DS_BMENU_RESULT_USED && count == 3);
    reset(); effects[4] = ITEM4_HEAL_PP_ONE;
    assert(DualScreen_BattleItemCategory(ITEM_ETHER) == 6);
    assert(DualScreen_UseBattleItem(ITEM_ETHER,2,-1) == DS_BMENU_RESULT_BAD_TARGET && count == 3);
    PlayerHandleChooseItem(); submit(ITEM_ETHER, 2 | (4 << 8)); tick();
    assert(done == 1 && count == 2 && effectTarget == 2 && effectMove == 3); orderPreserved();
    reset(); assert(DualScreen_BattleItemCategory(ITEM_ELIXIR) == 5);
    assert(DualScreen_UseBattleItem(ITEM_ELIXIR,1,-1) == DS_BMENU_RESULT_USED && !boxes && effectMove == 0);
    reset(); enigmaType = ITEM_EFFECT_X_ITEM; assert(DualScreen_BattleItemCategory(ITEM_ENIGMA_BERRY) == 3);
    enigmaType = ITEM_EFFECT_HEAL_PP; save.enigmaBerry.itemEffect[4] = ITEM4_HEAL_PP_ONE;
    assert(DualScreen_BattleItemCategory(ITEM_ENIGMA_BERRY) == 6);
    enigmaType = ITEM_EFFECT_RAISE_LEVEL; assert(DualScreen_BattleItemCategory(ITEM_ENIGMA_BERRY) == 0);
    reset(); count = 0; assert(DualScreen_UseBattleItem(ITEM_POTION,2,-1) == DS_BMENU_RESULT_CANT_USE && !effectCalls);
    puts("PASS: battle BAG stays open 60 s; touch/button entry, both controllers, fallback, cancel, rejection, item/PP targets, inventory and healthboxes");
}
'''

def check_panel_sync():
    source = (ROOT / 'android/app/src/main/java/com/pokeemerald/experimental/DualScreenView.java').read_text()
    source = source.replace('private void syncBattlePanel', 'void syncBattlePanel')
    source = source.replace('private boolean battleSendOutWait', 'boolean battleSendOutWait')
    source = re.sub(r'(?m)^    ', '', source)
    java = r"""
class PanelTest {
    static class State { boolean inBattle = true; int battleSub, battleSubCase, battleSubSeq, battleSubResult; }
    State state = new State();
    int battlePanel, lastSubSeq, lastBattlePanel, battlePartyFocus;
    long battleArmMs, battleCloseMs, battleNoticeMs;
    String battleNotice = "";
""" + function(source, 'battleSendOutWait') + function(source, 'syncBattlePanel') + r"""
    public static void main(String[] args) {
        PanelTest p = new PanelTest();
        p.battleArmMs = System.currentTimeMillis() - 60000;
        p.state.battleSub = 1; p.state.battleSubSeq = 1;
        p.syncBattlePanel(); assert p.battlePanel == 1;
        for (int panel : new int[]{1, 3, 4}) {
            p.battlePanel = panel;
            for (int i = 0; i < 500; i++) p.syncBattlePanel();
            assert p.battlePanel == panel; // bag and target steps do not time out
        }
        p.battlePanel = 1; p.state.battleSubResult = 2; p.state.battleSubSeq++;
        p.syncBattlePanel(); assert p.battlePanel == 1 && !p.battleNotice.isEmpty();
        p.state.battleSub = 0; p.syncBattlePanel(); assert p.battlePanel == 0;
        p.battleCloseMs = System.currentTimeMillis(); p.state.battleSub = 1;
        p.syncBattlePanel(); assert p.battlePanel == 0; // stale pre-cancel snapshot
        p.state.battleSubResult = 0; p.state.battleSubSeq++;
        p.syncBattlePanel(); assert p.battlePanel == 1; // immediate fresh reopen
        p.state.inBattle = false; p.syncBattlePanel(); assert p.battlePanel == 0;
        System.out.println("PASS: actual Java panel sync preserves bag/target/PP steps, reports rejection, closes on completion and reopens after cancel");
    }
}
"""
    jdk = Path(os.environ['JAVA_HOME']) / 'bin' if os.environ.get('JAVA_HOME') else None
    with tempfile.TemporaryDirectory(prefix='firered-bag-panel-') as tmp:
        path = Path(tmp) / 'PanelTest.java'
        path.write_text(java)
        subprocess.run([str(jdk / 'javac') if jdk else 'javac', str(path)], check=True)
        subprocess.run([str(jdk / 'java') if jdk else 'java', '-ea', '-cp', tmp, 'PanelTest'], check=True, timeout=10)


def main():
    code = PREFIX
    item = (ROOT / 'src/item_use.c').read_text()
    for name in ('DualScreen_BattleItemCategory', 'DualScreen_UseBattleItem'):
        code += function(item, name) + '\n'
    bridge = (ROOT / 'src/platform/dualscreen_bridge.c').read_text()
    for name in ('DualScreen_TakeBattleTakeover', 'DualScreen_SetBattleMenuOpen',
                 'DualScreen_ClearBattleMenu', 'DualScreen_TakeBattleChoice',
                 'DualScreen_SetBattleMenuResult', 'DualScreen_PollBattleItemChoice'):
        code += function(bridge, name) + '\n'
    for path, entry, wait in (
        ('src/battle_controller_player.c', 'PlayerHandleChooseItem', 'PlayerWait'),
        ('src/battle_controller_oak_old_man.c', 'OakOldManHandleChooseItem', 'OakWait'),
    ):
        source = (ROOT / path).read_text()
        for name in ('DualScreen_WaitForItemChoice', entry):
            code += function(source, name).replace('DualScreen_WaitForItemChoice', wait) + '\n'
    code += SUFFIX
    with tempfile.TemporaryDirectory(prefix='firered-battle-bag-') as tmp:
        source, binary = Path(tmp) / 'test.c', Path(tmp) / 'test'
        source.write_text(code)
        subprocess.run([os.environ.get('CC', 'cc'), '-std=c11', '-O1', '-g',
                        '-fsanitize=address,undefined', '-fno-sanitize-recover=all',
                        '-I', str(ROOT / 'include'), str(source), '-o', str(binary)], check=True)
        subprocess.run([str(binary)], check=True, timeout=10)
    check_panel_sync()

if __name__ == '__main__':
    main()
