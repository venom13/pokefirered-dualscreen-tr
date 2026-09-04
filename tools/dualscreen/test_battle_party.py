#!/usr/bin/env python3
"""Run the real player party controller, choice mailbox and order helpers.

ROM-free ASan/UBSan regression for forced replacements and voluntary switches.
Only rendering, Pokemon accessors, SDL locks and response transport are mocked.
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
typedef uint32_t u32, bool32;
typedef int32_t s32;
#define PLATFORM_SDL2 1
#define TRUE 1
#define FALSE 0
#define PARTY_SIZE 6
#define NELEMS(a) (sizeof(a)/sizeof((a)[0]))
#define MON_DATA_SPECIES 0
#define MON_DATA_IS_EGG 1
#define MON_DATA_HP 2
#define B_SIDE_PLAYER 0
#define PALETTES_ALL 0
#define RGB_BLACK 0
#define SDL_AtomicLock(p) ((void)0)
#define SDL_AtomicUnlock(p) ((void)0)
#define DS_TAKEOVER_TTL_FRAMES 240
#include "constants/battle.h"
#include "constants/party_menu.h"
#include "constants/species.h"
#include "platform/dualscreen.h"
struct Pokemon { int species, egg, hp, identity; } gPlayerParty[6];
struct { u8 playerPartyIdx, battlerPreventingSwitchout, abilityPreventingSwitchout; } battle, *gBattleStruct = &battle;
struct { int data[16]; } gTasks[16];
u8 gActiveBattler, gBattlerInMenuId, gBattlersCount, gBattlerPartyIndexes[4];
u8 gBattleControllerData[4], gBattleBufferA[4][8], gBattlePartyCurrentOrder[3];
u32 gBattleTypeFlags;
void (*gBattlerControllerFuncs[4])(void);
u32 sBattleArmMode, sBattleArmFrame, sFrameCounter;
u32 sBattleMenuMode, sBattleMenuCaseId, sBattleMenuBattler, sBattleMenuResult, sBattleMenuSeq;
u32 sBattleChoicePending;
s32 sBattleChoiceA, sBattleChoiceB;
int live, uiActive, fades, tasks, done, emitted, navClears;
u8 emittedOrder[3];
int GetMonData(struct Pokemon *mon, int field) {
    if (field == MON_DATA_SPECIES) return mon->species;
    if (field == MON_DATA_IS_EGG) return mon->egg;
    assert(field == MON_DATA_HP); return mon->hp;
}
int GetBattlerSide(int i) { return i & 1; }
u32 DualScreen_BottomScreenLive(void) { return live; }
u32 DualScreen_BattleUiActive(void) { return uiActive; }
void DualScreen_PreserveBattlePrompt(u32 battler) { (void)battler; }
void ClearNavQueue(void) { navClears++; }
void TaskDummy(u8 task) {}
int CreateTask(void (*fn)(u8), int priority) { assert(fn == TaskDummy && priority == 255); tasks++; return 0; }
void BeginNormalPaletteFade(int a, int b, int c, int d, int e) { fades++; }
void OpenPartyMenuToChooseMon(void) {}
void BtlController_EmitChosenMonReturnValue(u8 buffer, u8 monId, u8 *order) {
    assert(buffer == 1); emitted = monId;
    assert((order == NULL) == (monId == PARTY_SIZE));
    if (order) memcpy(emittedOrder, order, 3);
}
void PlayerBufferExecCompleted(void) { done++; }
'''

SUFFIX = r'''
void reset(int action) {
    live = uiActive = 1;
    gBattlersCount = 2; gActiveBattler = gBattlerInMenuId = 0;
    memset(gBattlerPartyIndexes, 0, sizeof(gBattlerPartyIndexes));
    memset(gBattleBufferA, 0, sizeof(gBattleBufferA));
    gBattleBufferA[0][1] = action | 0x10;
    gBattleBufferA[0][2] = PARTY_SIZE;
    gBattleBufferA[0][3] = 23;
    gBattleBufferA[0][4] = 0x01; gBattleBufferA[0][5] = 0x23; gBattleBufferA[0][6] = 0x45;
    for (int i=0; i<6; i++) gPlayerParty[i] = (struct Pokemon){SPECIES_CHARMANDER, 0, 20+i, 100+i};
    if (action == PARTY_ACTION_SEND_OUT) gPlayerParty[0].hp = 0;
    gBattleTypeFlags = BATTLE_TYPE_TRAINER;
    fades = tasks = done = navClears = 0; emitted = -999;
    sBattleMenuMode = sBattleChoicePending = sBattleArmMode = sBattleMenuSeq = 0;
    sFrameCounter = 500;
}
void submit(int mon) { sBattleChoiceA = mon; sBattleChoiceB = -1; sBattleChoicePending = 1; }
void tick(void) { sFrameCounter++; gBattlerControllerFuncs[gActiveBattler](); }
void rejected(int mon, int result) {
    u8 before[3]; memcpy(before, gBattlePartyCurrentOrder, 3);
    submit(mon); tick();
    assert(!done && emitted == -999 && sBattleMenuMode == 2);
    assert(sBattleMenuResult == result && !sBattleChoicePending);
    assert(!memcmp(before, gBattlePartyCurrentOrder, 3));
}
void expectOpen(int action) {
    PlayerHandleChoosePokemon();
    assert(!fades && !tasks && !done && sBattleMenuMode == 2 && sBattleMenuCaseId == action);
    assert(gBattlerControllerFuncs[gActiveBattler] == DualScreen_WaitForMonChoice);
    assert(gBattlerInMenuId == gActiveBattler && sBattleMenuBattler == gActiveBattler);
    assert(battle.battlerPreventingSwitchout == 1 && battle.abilityPreventingSwitchout == 23);
    assert(battle.playerPartyIdx == gBattleBufferA[gActiveBattler][2]);
    assert(navClears == 1 && !sBattleChoicePending);
}
int main(void) {
    // No arming tap after faint: wait indefinitely with battle graphics intact.
    reset(PARTY_ACTION_SEND_OUT);
    submit(3); // an old menu's pending choice must not leak into this wait
    expectOpen(PARTY_ACTION_SEND_OUT);
    for (int frame=0; frame<3600; frame++) tick();
    assert(sBattleMenuMode == 2 && !done && !fades && !tasks);
    for (int mon=-3; mon<=0; mon++) rejected(mon, DS_BMENU_RESULT_BAD_TARGET);
    rejected(6, DS_BMENU_RESULT_BAD_TARGET);
    rejected(256, DS_BMENU_RESULT_BAD_TARGET);
    rejected(INT32_MAX, DS_BMENU_RESULT_BAD_TARGET);
    rejected(INT32_MIN, DS_BMENU_RESULT_BAD_TARGET);
    gPlayerParty[1].egg = 1; rejected(1, DS_BMENU_RESULT_BAD_TARGET); gPlayerParty[1].egg = 0;
    gPlayerParty[1].hp = 0; rejected(1, DS_BMENU_RESULT_BAD_TARGET); gPlayerParty[1].hp = 21;
    gPlayerParty[1].species = SPECIES_NONE; rejected(1, DS_BMENU_RESULT_BAD_TARGET); gPlayerParty[1].species = SPECIES_CHARMANDER;
    submit(1); tick(); assert(done == 1 && emitted == 1 && !sBattleMenuMode && !fades);
    assert(emittedOrder[0] == 0x10 && emittedOrder[1] == 0x23 && emittedOrder[2] == 0x45);
    // Current field mon, the other active mon and queued double-faint replacement.
    reset(PARTY_ACTION_SEND_OUT); gBattlersCount = 4; gBattlerPartyIndexes[2] = 2;
    gBattleBufferA[0][2] = 3; expectOpen(PARTY_ACTION_SEND_OUT);
    gPlayerParty[0].hp = 10; rejected(0, DS_BMENU_RESULT_BAD_TARGET);
    rejected(2, DS_BMENU_RESULT_BAD_TARGET); rejected(3, DS_BMENU_RESULT_BAD_TARGET);
    submit(1); tick(); assert(done == 1 && emitted == 1);
    u32 seq = sBattleMenuSeq;
    // A second forced wait immediately follows the first, for the other battler.
    gActiveBattler = 2; gPlayerParty[2].hp = 0;
    memcpy(gBattleBufferA[2], gBattleBufferA[0], 8); gBattleBufferA[2][2] = 1;
    PlayerHandleChoosePokemon(); assert(sBattleMenuSeq > seq && sBattleMenuBattler == 2);
    done = 0; emitted = -999; rejected(1, DS_BMENU_RESULT_BAD_TARGET);
    submit(4); tick(); assert(done == 1 && emitted == 4);
    // Voluntary cancel, including trapped cases. Forced cancel was rejected above.
    for (int action=0; action<=4; action++) {
        if (action == PARTY_ACTION_SEND_OUT) continue;
        reset(action); expectOpen(action);
        if (action != PARTY_ACTION_CHOOSE_MON) rejected(1, DS_BMENU_RESULT_CANT_USE);
        submit(-1); tick(); assert(done == 1 && emitted == PARTY_SIZE && !sBattleMenuMode);
    }
    // Physical and touch entry both work, but an absent bottom display can
    // never be armed into owning a forced selection.
    for (int forced=0; forced<2; forced++) {
        reset(forced ? PARTY_ACTION_SEND_OUT : PARTY_ACTION_CHOOSE_MON);
        live = 0; sBattleArmMode = 2; sBattleArmFrame = sFrameCounter;
        PlayerHandleChoosePokemon();
        assert(fades == forced && tasks == forced && sBattleMenuMode == (forced ? 0 : 2));
    }
    for (int fallback=0; fallback<5; fallback++) {
        reset(PARTY_ACTION_SEND_OUT);
        if (fallback == 0) live = 0;
        if (fallback == 1) uiActive = 0;
        if (fallback == 2) gBattleTypeFlags |= BATTLE_TYPE_MULTI;
        if (fallback == 3) gBattleTypeFlags |= BATTLE_TYPE_POKEDUDE;
        if (fallback == 4) gBattleTypeFlags |= BATTLE_TYPE_FIRST_BATTLE;
        PlayerHandleChoosePokemon();
        assert(fades == 1 && tasks == 1 && !sBattleMenuMode && !done);
        assert(gBattlerControllerFuncs[0] == OpenPartyMenuToChooseMon);
        assert(gTasks[0].data[0] == PARTY_ACTION_SEND_OUT);
    }
    // The trainer replacement prompt opens without an arm, clears stale
    // input, accepts Switch/Keep, and safely treats B/cancel as Keep.
    u8 promptChoice = 99;
    reset(PARTY_ACTION_CHOOSE_MON); submit(4);
    assert(DualScreen_TryOpenBattleSwitchPrompt());
    assert(sBattleMenuMode == 3 && sBattleMenuBattler == 0 && !sBattleChoicePending);
    submit(0); assert(DualScreen_PollBattleSwitchChoice(&promptChoice));
    assert(promptChoice == 0 && !sBattleMenuMode);
    reset(PARTY_ACTION_CHOOSE_MON);
    assert(DualScreen_TryOpenBattleSwitchPrompt());
    submit(-1); assert(DualScreen_PollBattleSwitchChoice(&promptChoice));
    assert(promptChoice == 1 && !sBattleMenuMode);
    reset(PARTY_ACTION_CHOOSE_MON); live = 0;
    assert(!DualScreen_TryOpenBattleSwitchPrompt() && !sBattleMenuMode);
    reset(PARTY_ACTION_CHOOSE_MON); uiActive = 0;
    assert(!DualScreen_TryOpenBattleSwitchPrompt() && !sBattleMenuMode);
    // Repeated switches across changing packed orders: field data must remain
    // byte-identical, and the returned order must swap the correct logical slots.
    for (int rotation=0; rotation<6; rotation++) for (int active=0; active<6; active++) {
        reset(PARTY_ACTION_CHOOSE_MON);
        u8 order[6];
        for (int i=0; i<6; i++) order[i] = (i+rotation)%6;
        gBattlerPartyIndexes[0] = active;
        for (int selected=0; selected<6; selected++) {
            if (selected == gBattlerPartyIndexes[0]) continue;
            for (int i=0; i<3; i++) gBattleBufferA[0][4+i] = (order[2*i]<<4) | order[2*i+1];
            struct Pokemon original[6]; memcpy(original, gPlayerParty, sizeof(original));
            PlayerHandleChoosePokemon(); done = 0;
            int oldPos=-1, newPos=-1;
            for (int i=0; i<6; i++) {
                if (order[i] == gBattlerPartyIndexes[0]) oldPos=i;
                if (order[i] == selected) newPos=i;
            }
            assert(oldPos >= 0 && newPos >= 0);
            u8 tmp=order[oldPos]; order[oldPos]=order[newPos]; order[newPos]=tmp;
            submit(selected); tick(); assert(done == 1 && emitted == selected);
            for (int i=0; i<3; i++) assert(emittedOrder[i] == ((order[2*i]<<4) | order[2*i+1]));
            assert(!memcmp(original, gPlayerParty, sizeof(original)) && !fades && !tasks);
            gBattlerPartyIndexes[0] = selected;
        }
    }
    puts("PASS: forced send-out waits, trainer switch prompt, no cancel, slot validation, doubles, fallback, voluntary switch/cancel and repeated party-order preservation");
}
'''


def check_panel():
    source = (ROOT / 'android/app/src/main/java/com/pokeemerald/experimental/DualScreenView.java').read_text()
    source = re.sub(r'(?m)^    ', '', source).replace('private boolean ', 'boolean ').replace('private void ', 'void ')
    java = r'''
class PartyPanelTest {
    static class DualScreenState {
        static class Mon { boolean isEgg; int hp=20; }
        boolean inBattle=true;
        int battleSub, battleSubCase, battleSubSeq, battleSubResult, battlePrevSel=6;
        int[] battleActive={0, -1};
        java.util.List<Mon> party=new java.util.ArrayList<>();
    }
    static class DualScreenBridge {
        static int submits, lastA, lastB;
        static void nativeBattleSubmit(int a, int b) { lastA=a; lastB=b; submits++; }
        static void nativeBattleArm(int mode) { assert mode==0; }
    }
    DualScreenState state=new DualScreenState();
    int battlePanel, lastSubSeq, lastBattlePanel, battlePartyFocus, battleSwitchFocus;
    int lastLiveMenu;
    long battleArmMs, battleCloseMs, battleNoticeMs;
    long lastLiveMenuMs;
    boolean battleBagItemsOpen, battleReturningToCommands;
    String battleNotice="";
    void invalidate() {}
    void resetBattleBag() { battleBagItemsOpen=false; }
'''
    for name in ('battleSendOutWait', 'syncBattlePanel', 'cancelBattlePanel',
                 'submitBattleSwitchPrompt', 'battlePartySlotEnabled'):
        java += function(source, name) + '\n'
    java += r'''
    public static void main(String[] args) {
        PartyPanelTest p=new PartyPanelTest();
        for (int i=0; i<6; i++) p.state.party.add(new DualScreenState.Mon());
        p.state.party.get(0).hp=0; p.state.party.get(2).isEgg=true;
        p.state.battleActive[1]=3; p.state.battlePrevSel=4;
        p.state.battleSub=2; p.state.battleSubCase=1;
        p.battleCloseMs=System.currentTimeMillis();
        p.battleArmMs=p.battleCloseMs-60000;
        for (int stalePanel : new int[]{0, 1, 3, 4}) {
            p.battlePanel=stalePanel; p.syncBattlePanel(); assert p.battlePanel==2;
            for (int i=0; i<1000; i++) p.syncBattlePanel();
            assert p.battlePanel==2;
            p.cancelBattlePanel(); assert p.battlePanel==2 && DualScreenBridge.submits==0;
        }
        for (int i=0; i<6; i++) assert p.battlePartySlotEnabled(i)==(i==1 || i==5);
        p.state.battleSub=0; p.syncBattlePanel(); assert p.battlePanel==0;
        p.state.battleSub=2; p.state.battleSubSeq++;
        p.state.battlePrevSel=1; p.syncBattlePanel(); assert p.battlePanel==2;
        assert !p.battlePartySlotEnabled(1) && p.battlePartySlotEnabled(4);
        p.battlePanel=0; p.state.battleSub=3; p.state.battleSubSeq++;
        p.syncBattlePanel(); assert p.battlePanel==5 && p.battleSwitchFocus==0;
        p.state.battleSub=0; p.battleCloseMs=System.currentTimeMillis();
        p.syncBattlePanel(); assert p.battlePanel==0;
        p.state.battleSub=2; p.battlePanel=2;
        p.state.battleSubCase=0; p.cancelBattlePanel();
        assert p.battlePanel==0 && DualScreenBridge.submits==1;
        assert DualScreenBridge.lastA==-1 && DualScreenBridge.lastB==-1;
        p.state.battleSub=3; p.battlePanel=5; p.submitBattleSwitchPrompt(0);
        assert p.battlePanel==0 && DualScreenBridge.submits==2;
        assert DualScreenBridge.lastA==0 && DualScreenBridge.lastB==-1;
        p.state.battleSub=3; p.battlePanel=5; p.submitBattleSwitchPrompt(9);
        assert p.battlePanel==0 && DualScreenBridge.submits==3;
        assert DualScreenBridge.lastA==1 && DualScreenBridge.lastB==-1;
        p.state.inBattle=false; p.syncBattlePanel(); assert p.battlePanel==0;
        System.out.println("PASS: actual Java forced party panel opens without tap, survives stale bag/PP panels, blocks cancel, filters slots and immediately opens the next replacement");
    }
}
'''
    jdk = Path(os.environ['JAVA_HOME']) / 'bin' if os.environ.get('JAVA_HOME') else None
    with tempfile.TemporaryDirectory(prefix='firered-party-panel-') as tmp:
        path = Path(tmp) / 'PartyPanelTest.java'
        path.write_text(java)
        subprocess.run([str(jdk / 'javac') if jdk else 'javac', str(path)], check=True)
        subprocess.run([str(jdk / 'java') if jdk else 'java', '-ea', '-cp', tmp, 'PartyPanelTest'], check=True, timeout=10)


def check_switch_prompt_command():
    source = (ROOT / 'src/battle_script_commands.c').read_text()
    code = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
typedef uint8_t u8;
typedef uint32_t u32;
#define PLATFORM_SDL2 1
#define BATTLE_TYPE_TRAINER (1u << 3)
#define CURSOR_POSITION 1
#define DPAD_UP 0x40
#define DPAD_DOWN 0x80
#define A_BUTTON 1
#define B_BUTTON 2
#define WINDOW_CLEAR 1
#define B_WIN_YESNO 7
#define SE_SELECT 5
#define JOY_NEW(key) (newKeys & (key))
u8 gBattleCommunication[8];
u8 script[4], *gBattlescriptCurrInstr = script;
u32 gBattleTypeFlags;
u32 newKeys;
const u8 gText_BattleYesNoChoice[] = {0};
int takeover, pollReady, pollChoice;
int openWindows, clearWindows, textCalls, createCalls, destroyCalls, soundCalls;
u32 DualScreen_TryOpenBattleSwitchPrompt(void) { return takeover; }
u32 DualScreen_PollBattleSwitchChoice(u8 *choice) {
    if (!pollReady) return 0;
    *choice = pollChoice;
    return 1;
}
void HandleBattleWindow(int a, int b, int c, int d, int mode) {
    if (mode == WINDOW_CLEAR) clearWindows++; else openWindows++;
}
void BattlePutTextOnWindow(const u8 *text, int window) { textCalls++; }
void BattleCreateYesNoCursorAt(void) { createCalls++; }
void BattleDestroyYesNoCursorAt(void) { destroyCalls++; }
void PlaySE(int sound) { assert(sound == SE_SELECT); soundCalls++; }
'''
    code += function(source, 'Cmd_yesnobox')
    code += r'''
void reset(void) {
    for (int i=0; i<8; i++) gBattleCommunication[i]=0;
    gBattlescriptCurrInstr=script;
    gBattleTypeFlags=BATTLE_TYPE_TRAINER;
    newKeys=0; takeover=1; pollReady=0; pollChoice=0;
    openWindows=clearWindows=textCalls=createCalls=destroyCalls=soundCalls=0;
}
int main(void) {
    reset();
    Cmd_yesnobox();
    assert(gBattleCommunication[0] == 2);
    assert(clearWindows == 1 && openWindows == 0 && textCalls == 0 && createCalls == 0);
    Cmd_yesnobox(); assert(gBattlescriptCurrInstr == script);
    pollReady=1; pollChoice=0; Cmd_yesnobox();
    assert(gBattleCommunication[CURSOR_POSITION] == 0);
    assert(gBattlescriptCurrInstr == script + 1 && soundCalls == 1);

    reset(); Cmd_yesnobox(); pollReady=1; pollChoice=1; Cmd_yesnobox();
    assert(gBattleCommunication[CURSOR_POSITION] == 1 && gBattlescriptCurrInstr == script + 1);

    // A missing bottom screen and the wild-battle prompt retain the original window.
    reset(); takeover=0; Cmd_yesnobox();
    assert(gBattleCommunication[0] == 1 && openWindows == 1 && textCalls == 1 && createCalls == 1);
    reset(); gBattleTypeFlags=0; Cmd_yesnobox();
    assert(gBattleCommunication[0] == 1 && openWindows == 1 && textCalls == 1 && createCalls == 1);
    puts("PASS: trainer switch Yes/No is owned by the bottom screen while fallback prompts retain the original window");
    return 0;
}
'''
    with tempfile.TemporaryDirectory(prefix='firered-switch-prompt-command-') as tmp:
        path = Path(tmp) / 'test.c'
        binary = Path(tmp) / 'test'
        path.write_text(code)
        subprocess.run([os.environ.get('CC', 'cc'), '-std=c11', '-O1', '-g',
                        '-fsanitize=address,undefined', '-fno-sanitize-recover=all',
                        str(path), '-o', str(binary)], check=True)
        subprocess.run([str(binary)], check=True, timeout=10)


def check_lower_screen_back():
    source = (ROOT / 'android/app/src/main/java/com/pokeemerald/experimental/PokeEmeraldActivity.java').read_text()
    source = re.sub(r'(?m)^    ', '', source).replace('public boolean ', 'boolean ')
    java = r'''
class KeyEvent {
    static final int ACTION_DOWN=0, ACTION_UP=1, KEYCODE_BUTTON_A=96, KEYCODE_BUTTON_B=97;
    final int action, keyCode, deviceId;
    KeyEvent(int action, int keyCode, int deviceId) {
        this.action=action; this.keyCode=keyCode; this.deviceId=deviceId;
    }
    int getAction() { return action; }
    int getKeyCode() { return keyCode; }
    int getDeviceId() { return deviceId; }
}
class DualScreenPresentation {
    boolean detailOpen, bagOpen, battleBagOpen;
    int backs;
    boolean handlePhysicalBack() {
        backs++;
        if (detailOpen) { detailOpen=false; return true; }
        if (bagOpen) { bagOpen=false; return true; }
        if (battleBagOpen) { battleBagOpen=false; return true; }
        return false;
    }
}
class ActivityBase {
    int passedToGame;
    boolean dispatchKeyEvent(KeyEvent event) { passedToGame++; return false; }
}
class PartyDetailBackTest extends ActivityBase {
    static final int NO_CAPTURED_DEVICE=Integer.MIN_VALUE;
    int partyDetailCancelDeviceId=NO_CAPTURED_DEVICE;
    DualScreenPresentation presentation;
'''
    java += function(source, 'dispatchKeyEvent') + r'''
    public static void main(String[] args) {
        PartyDetailBackTest activity=new PartyDetailBackTest();
        activity.presentation=new DualScreenPresentation();
        activity.presentation.detailOpen=true;
        assert activity.dispatchKeyEvent(new KeyEvent(KeyEvent.ACTION_DOWN, KeyEvent.KEYCODE_BUTTON_B, 7));
        assert activity.presentation.backs==1 && activity.partyDetailCancelDeviceId==7;

        // Repeats and the matching release remain consumed after the first
        // press closed the detail; none of that physical press reaches SDL.
        assert activity.dispatchKeyEvent(new KeyEvent(KeyEvent.ACTION_DOWN, KeyEvent.KEYCODE_BUTTON_B, 7));
        assert activity.presentation.backs==1 && activity.passedToGame==0;
        assert activity.dispatchKeyEvent(new KeyEvent(KeyEvent.ACTION_UP, KeyEvent.KEYCODE_BUTTON_B, 7));
        assert activity.partyDetailCancelDeviceId==NO_CAPTURED_DEVICE && activity.passedToGame==0;

        // The normal BAG item view and the battle BAG use the same consumed
        // press/release path as party detail.
        activity.presentation.bagOpen=true;
        assert activity.dispatchKeyEvent(new KeyEvent(KeyEvent.ACTION_DOWN, KeyEvent.KEYCODE_BUTTON_B, 8));
        assert activity.presentation.backs==2 && activity.partyDetailCancelDeviceId==8;
        assert activity.dispatchKeyEvent(new KeyEvent(KeyEvent.ACTION_UP, KeyEvent.KEYCODE_BUTTON_B, 8));
        activity.presentation.battleBagOpen=true;
        assert activity.dispatchKeyEvent(new KeyEvent(KeyEvent.ACTION_DOWN, KeyEvent.KEYCODE_BUTTON_B, 9));
        assert activity.presentation.backs==3 && activity.partyDetailCancelDeviceId==9;
        assert activity.dispatchKeyEvent(new KeyEvent(KeyEvent.ACTION_UP, KeyEvent.KEYCODE_BUTTON_B, 9));

        // B outside a lower-screen overlay and every unrelated button keep
        // their normal game path.
        assert !activity.dispatchKeyEvent(new KeyEvent(KeyEvent.ACTION_DOWN, KeyEvent.KEYCODE_BUTTON_B, 7));
        assert !activity.dispatchKeyEvent(new KeyEvent(KeyEvent.ACTION_DOWN, KeyEvent.KEYCODE_BUTTON_A, 7));
        assert activity.presentation.backs==4 && activity.passedToGame==2;
        System.out.println("PASS: physical B follows party and BAG back actions without leaking held/release events into the game");
    }
}
'''
    jdk = Path(os.environ['JAVA_HOME']) / 'bin' if os.environ.get('JAVA_HOME') else None
    with tempfile.TemporaryDirectory(prefix='firered-party-detail-back-') as tmp:
        path = Path(tmp) / 'PartyDetailBackTest.java'
        path.write_text(java)
        subprocess.run([str(jdk / 'javac') if jdk else 'javac', str(path)], check=True)
        subprocess.run([str(jdk / 'java') if jdk else 'java', '-ea', '-cp', tmp,
                        'PartyDetailBackTest'], check=True, timeout=10)


def main():
    code = PREFIX
    party = (ROOT / 'src/party_menu.c').read_text()
    for name in ('GetPartyIdFromBattleSlot', 'SetPartyIdAtBattleSlot', 'SwitchPartyMonSlots',
                 'GetPartyIdFromBattlePartyId', 'DualScreen_BattleSwitchOrder'):
        code += function(party, name) + '\n'
    bridge = (ROOT / 'src/platform/dualscreen_bridge.c').read_text()
    for name in ('DualScreen_TakeBattleTakeover', 'DualScreen_SetBattleMenuOpen',
                 'DualScreen_ClearBattleMenu', 'DualScreen_TakeBattleChoice',
                 'DualScreen_SetBattleMenuResult', 'DualScreen_TryOpenBattlePartyMenu',
                 'DualScreen_PollBattleMonChoice', 'DualScreen_TryOpenBattleSwitchPrompt',
                 'DualScreen_PollBattleSwitchChoice'):
        code += function(bridge, name) + '\n'
    controller = (ROOT / 'src/battle_controller_player.c').read_text()
    for name in ('DualScreen_WaitForMonChoice', 'PlayerHandleChoosePokemon'):
        code += function(controller, name) + '\n'
    code += SUFFIX
    with tempfile.TemporaryDirectory(prefix='firered-battle-party-') as tmp:
        source, binary = Path(tmp) / 'test.c', Path(tmp) / 'test'
        source.write_text(code)
        subprocess.run([os.environ.get('CC', 'cc'), '-std=c11', '-O1', '-g',
                        '-fsanitize=address,undefined', '-fno-sanitize-recover=all',
                        '-I', str(ROOT / 'include'), str(source), '-o', str(binary)], check=True)
        subprocess.run([str(binary)], check=True, timeout=10)
    check_panel()
    check_switch_prompt_command()
    check_lower_screen_back()


if __name__ == '__main__':
    main()
