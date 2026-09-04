#!/usr/bin/env python3
"""ROM-free regression for lower-screen overworld dialogue choices."""

from pathlib import Path
import os
import re
import subprocess
import tempfile

from test_bag_menu_init import function


ROOT = Path(__file__).resolve().parents[2]


def check_native_and_script_flow():
    bridge = (ROOT / "src/platform/dualscreen_bridge.c").read_text()
    menu = (ROOT / "src/script_menu.c").read_text()
    code = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "constants/characters.h"
typedef uint8_t u8, bool8;
typedef uint16_t u16;
typedef int16_t s16;
typedef uint32_t u32, bool32;
typedef int32_t s32;
#define PLATFORM_SDL2 1
#define TRUE 1
#define FALSE 0
#define SE_SELECT 5
#define SCR_MENU_CANCEL 127
#define SCR_MENU_UNSET 255
#define DUAL_SCREEN_FIELD_CHOICE_MAX 8
#define FIELD_CHOICE_LABEL_SIZE 64
#define FIELD_CHOICE_SOURCE_LIMIT 128
#define SDL_AtomicLock(lock) ((void)0)
#define SDL_AtomicUnlock(lock) ((void)0)
#define QL_DestroyAbortedDisplay 0
#define tDualScreenYesNo data[0]

struct MenuAction { const u8 *text; void *func; };
struct Task { s16 data[16]; } gTasks[4];
struct { int inBattle; } gMain;
static int sBattleMenuLock;
static u32 sFrameCounter = 100;
static u32 sFieldChoiceOpen, sFieldChoiceCount, sFieldChoiceDefault;
static s32 sFieldChoiceCancelResult;
static u32 sFieldChoiceSeq, sFieldChoiceOpenFrame, sFieldChoicePending;
static s32 sFieldChoiceSelection;
static char sFieldChoiceLabels[DUAL_SCREEN_FIELD_CHOICE_MAX][FIELD_CHOICE_LABEL_SIZE];
static int bottomLive, displayed, created, enabled, sounds, navClears;
static int taskActive;
static void (*activeTask)(u8);
static u16 gSpecialVar_Result;
static const u8 yesText[] = {CHAR_Y, CHAR_E, CHAR_S, EOS};
static const u8 noText[] = {CHAR_N, CHAR_O, EOS};
static const struct MenuAction sMultichoiceList_YesNo[] = {
    {yesText, 0}, {noText, 0}
};

static void Task_YesNoMenu_HandleInput(u8 taskId) { (void)taskId; }
static void Task_DualScreenFieldChoice_HandleInput(u8 taskId);
static bool32 TryOpenDualScreenFieldChoice(const struct MenuAction *list, u8 count,
                                           s16 cancelResult, u8 defaultChoice, bool8 yesNo);
static u32 DualScreen_BottomScreenLive(void) { return bottomLive; }
static void ClearNavQueue(void) { navClears++; }
static u8 GetExtCtrlCodeLength(u8 code) {
    if (code == EXT_CTRL_CODE_FONT || code == EXT_CTRL_CODE_CLEAR_TO) return 2;
    return 1;
}
static bool8 FuncIsActiveTask(void (*fn)(u8)) { return taskActive && activeTask == fn; }
static u8 CreateTask(void (*fn)(u8), u8 priority) {
    assert(priority == 80);
    created++;
    taskActive = 1;
    activeTask = fn;
    memset(gTasks[0].data, 0, sizeof(gTasks[0].data));
    return 0;
}
static void DestroyTask(u8 taskId) { assert(taskId == 0); taskActive = 0; }
static void ScriptContext_Enable(void) { enabled++; }
static void PlaySE(int song) { assert(song == SE_SELECT); sounds++; }
static int QL_AvoidDisplay(int callback) { (void)callback; return 0; }
static void DisplayYesNoMenuDefaultYes(void) { displayed++; }
'''
    for name in ("DecodeGbaChar", "DecodeGbaMenuLabel"):
        code += function(bridge, name) + "\n"
    for name in ("DualScreen_TryOpenFieldChoice", "DualScreen_FieldChoiceActive",
                 "DualScreen_PollFieldChoice"):
        code += function(bridge, name) + "\n"
    for name in ("TryOpenDualScreenFieldChoice",
                 "Task_DualScreenFieldChoice_HandleInput", "ScriptMenu_YesNo"):
        code += function(menu, name) + "\n"
    code += r'''
static void reset(void) {
    gMain.inBattle = 0;
    bottomLive = 1;
    displayed = created = enabled = sounds = navClears = 0;
    taskActive = 0;
    activeTask = 0;
    gSpecialVar_Result = 999;
    sFieldChoiceOpen = sFieldChoicePending = 0;
}
static void submit(s32 choice) {
    sFieldChoiceSelection = choice;
    sFieldChoicePending = 1;
}
int main(void) {
    reset();
    assert(ScriptMenu_YesNo(20, 8));
    assert(sFieldChoiceOpen && sFieldChoiceCount == 2 && sFieldChoiceDefault == 0);
    assert(sFieldChoiceCancelResult == 1 && !displayed && created == 1);
    assert(!strcmp(sFieldChoiceLabels[0], "YES") && !strcmp(sFieldChoiceLabels[1], "NO"));
    assert(gSpecialVar_Result == SCR_MENU_UNSET && navClears == 1);
    assert(!ScriptMenu_YesNo(20, 8));
    submit(0); activeTask(0);
    assert(gSpecialVar_Result == TRUE && !sFieldChoiceOpen && enabled == 1 && sounds == 1);

    reset(); assert(ScriptMenu_YesNo(20, 8));
    submit(1); activeTask(0);
    assert(gSpecialVar_Result == FALSE && enabled == 1);

    // A missing companion screen or a battle preserves the original bubble.
    reset(); bottomLive = 0; assert(ScriptMenu_YesNo(20, 8));
    assert(displayed == 1 && activeTask == Task_YesNoMenu_HandleInput && !sFieldChoiceOpen);
    reset(); gMain.inBattle = 1; assert(ScriptMenu_YesNo(20, 8));
    assert(displayed == 1 && activeTask == Task_YesNoMenu_HandleInput && !sFieldChoiceOpen);

    // Generic multichoice returns the original zero-based result and cancel code.
    static const u8 a[] = {CHAR_O, CHAR_N, CHAR_E, EOS};
    static const u8 b[] = {CHAR_T, CHAR_W, CHAR_O, EOS};
    static const u8 c[] = {CHAR_E, CHAR_X, CHAR_I, CHAR_T, EOS};
    static const struct MenuAction options[] = {{a, 0}, {b, 0}, {c, 0}};
    reset(); assert(TryOpenDualScreenFieldChoice(options, 3, SCR_MENU_CANCEL, 1, FALSE));
    assert(sFieldChoiceDefault == 1 && sFieldChoiceCancelResult == SCR_MENU_CANCEL);
    submit(2); activeTask(0); assert(gSpecialVar_Result == 2);
    reset(); assert(TryOpenDualScreenFieldChoice(options, 3, SCR_MENU_CANCEL, 0, FALSE));
    submit(SCR_MENU_CANCEL); activeTask(0); assert(gSpecialVar_Result == SCR_MENU_CANCEL);

    // Menus that ignore B reject a synthetic cancel and keep waiting.
    reset(); assert(TryOpenDualScreenFieldChoice(options, 3, -1, 0, FALSE));
    submit(SCR_MENU_CANCEL); activeTask(0);
    assert(sFieldChoiceOpen && taskActive && gSpecialVar_Result == 999);
    submit(1); activeTask(0); assert(gSpecialVar_Result == 1 && !taskActive);

    // Formatting controls are removed without truncating the visible price.
    static const u8 priced[] = {
        CHAR_F, CHAR_R, CHAR_E, CHAR_S, CHAR_H, CHAR_SPACE,
        CHAR_W, CHAR_A, CHAR_T, CHAR_E, CHAR_R,
        EXT_CTRL_CODE_BEGIN, EXT_CTRL_CODE_CLEAR_TO, 0x57,
        EXT_CTRL_CODE_BEGIN, EXT_CTRL_CODE_FONT, 1,
        CHAR_CURRENCY, CHAR_2, CHAR_0, CHAR_0, EOS
    };
    char decoded[64];
    DecodeGbaMenuLabel(decoded, sizeof(decoded), priced, sizeof(priced));
    assert(!strcmp(decoded, "FRESH WATER $200"));
    puts("PASS: field Yes/No and multichoice use the lower-screen mailbox with classic fallback and original cancel semantics");
    return 0;
}
'''
    with tempfile.TemporaryDirectory(prefix="firered-field-choice-") as tmp:
        source = Path(tmp) / "test.c"
        binary = Path(tmp) / "test"
        source.write_text(code)
        subprocess.run([os.environ.get("CC", "cc"), "-std=c11", "-O1", "-g",
                        "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
                        "-I", str(ROOT / "include"), str(source), "-o", str(binary)], check=True)
        subprocess.run([str(binary)], check=True, timeout=10)

    vertical = function(menu, "DrawVerticalMultichoiceMenu")
    grid = function(menu, "ScriptMenu_MultichoiceGrid")
    assert vertical.index("TryOpenDualScreenFieldChoice") < vertical.index("CreateWindowFromRect")
    assert grid.index("TryOpenDualScreenFieldChoice") < grid.index("CreateWindowFromRect")


def check_java_navigation():
    source = (ROOT / "android/app/src/main/java/com/pokeemerald/experimental/DualScreenView.java").read_text()
    source = re.sub(r"(?m)^    ", "", source)
    source = source.replace("private void ", "void ").replace("private boolean ", "boolean ")
    java = r'''
class FieldChoiceNavigationTest {
    static final int NAV_UP=0, NAV_DOWN=1, NAV_LEFT=2, NAV_RIGHT=3, NAV_CONFIRM=4, NAV_CANCEL=5;
    static class RectF {}
    static class DualScreenState {
        boolean fieldChoiceOpen;
        int fieldChoiceSeq, fieldChoiceDefault, fieldChoiceCancel=-1;
        java.util.List<String> fieldChoiceLabels=new java.util.ArrayList<>();
    }
    static class DualScreenBridge {
        static int submits, choice;
        static void nativeFieldChoiceSubmit(int value) { submits++; choice=value; }
    }
    DualScreenState state=new DualScreenState();
    RectF[] fieldChoiceButtons={new RectF(),new RectF(),new RectF(),new RectF(),
                                new RectF(),new RectF(),new RectF(),new RectF()};
    int fieldChoiceFocus, lastFieldChoiceSeq=-1, dismissedFieldChoiceSeq=-1;
    long fieldChoiceDismissMs;
    void invalidate() {}
'''
    for name in ("syncFieldChoice", "fieldChoiceVisible", "navigateFieldChoice",
                 "submitFieldChoice"):
        java += function(source, name) + "\n"
    java += r'''
    void open(int seq, int count, int defaultChoice, int cancel) {
        state=new DualScreenState(); state.fieldChoiceOpen=true; state.fieldChoiceSeq=seq;
        state.fieldChoiceDefault=defaultChoice; state.fieldChoiceCancel=cancel;
        for (int i=0; i<count; i++) state.fieldChoiceLabels.add("OPTION"+i);
        syncFieldChoice();
    }
    public static void main(String[] args) {
        FieldChoiceNavigationTest v=new FieldChoiceNavigationTest();
        v.open(1, 2, 0, 1); assert v.fieldChoiceFocus==0 && v.fieldChoiceVisible();
        v.navigateFieldChoice(NAV_DOWN); assert v.fieldChoiceFocus==1;
        v.navigateFieldChoice(NAV_UP); assert v.fieldChoiceFocus==0;
        v.navigateFieldChoice(NAV_CANCEL);
        assert DualScreenBridge.submits==1 && DualScreenBridge.choice==1 && !v.fieldChoiceVisible();

        v.open(2, 3, 1, -1); assert v.fieldChoiceFocus==1;
        v.navigateFieldChoice(NAV_CANCEL); assert DualScreenBridge.submits==1;
        v.navigateFieldChoice(NAV_LEFT); assert v.fieldChoiceFocus==0;
        v.navigateFieldChoice(NAV_DOWN); assert v.fieldChoiceFocus==2;
        v.navigateFieldChoice(NAV_CONFIRM);
        assert DualScreenBridge.submits==2 && DualScreenBridge.choice==2;

        v.open(3, 5, 0, 127);
        v.navigateFieldChoice(NAV_RIGHT); assert v.fieldChoiceFocus==1;
        v.navigateFieldChoice(NAV_DOWN); assert v.fieldChoiceFocus==3;
        v.navigateFieldChoice(NAV_LEFT); assert v.fieldChoiceFocus==2;
        System.out.println("PASS: lower-screen field choice focus, confirm, cancel and stale-snapshot suppression");
    }
}
'''
    jdk = Path(os.environ["JAVA_HOME"]) / "bin" if os.environ.get("JAVA_HOME") else None
    with tempfile.TemporaryDirectory(prefix="firered-field-choice-java-") as tmp:
        path = Path(tmp) / "FieldChoiceNavigationTest.java"
        path.write_text(java)
        subprocess.run([str(jdk / "javac") if jdk else "javac", str(path)], check=True)
        subprocess.run([str(jdk / "java") if jdk else "java", "-ea", "-cp", tmp,
                        "FieldChoiceNavigationTest"], check=True, timeout=10)


if __name__ == "__main__":
    check_native_and_script_flow()
    check_java_navigation()
