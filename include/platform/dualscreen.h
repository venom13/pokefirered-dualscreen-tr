#ifndef GUARD_PLATFORM_DUALSCREEN_H
#define GUARD_PLATFORM_DUALSCREEN_H

// Second-screen state bridge. Called from the SDL frame loop each vblank,
// after the game's vblank interrupt handler has run and before the game
// thread is released. Snapshots live game state into a JSON buffer that the
// Android bottom-screen UI (or a desktop debug consumer) reads.
void DualScreen_FrameHook(void);

// Returns the most recent snapshot as a NUL-terminated JSON string.
// Thread-safe; may be called from any thread.
const char *DualScreen_GetSnapshotJson(void);

#ifdef __ANDROID__
// Restores zeroed asset ranges from the user's extracted ROM data before
// the game starts (bypassed in development builds). Returns FALSE on failure.
// See make_asset_holes.py.
bool32 DualScreen_FillAssets(const char *prefPath);
#endif

// True when the bottom screen owns the battle menus: the top screen then
// suppresses the action/move menu text and cursor, and input can arrive
// through the virtual key queue.
u32 DualScreen_BattleUiActive(void);

// Frame-thread only: all active battlers have been loaded for this encounter.
// inBattle alone becomes true while gBattleMons still holds the previous fight.
u32 DualScreen_BattleDataReady(void);

// One frame's worth of synthetic GBA button state, consumed by
// Platform_GetKeyInput. Returns 0 when the queue is empty.
u16 DualScreen_ConsumeVirtualKeys(void);

// Implemented in battle_controller_player.c: whether the player-controlled
// battler is currently on the action menu / move menu, and which battler
// that is (-1 if the menu is not open; matters in double battles).
u32 DualScreen_PlayerAtActionSelect(void);
u32 DualScreen_PlayerAtMoveSelect(void);
s32 DualScreen_PlayerActionBattler(void);
s32 DualScreen_PlayerMoveBattler(void);

// FireRed's first rival battle uses a separate Oak controller. Only report
// its interactive menus, never the Old Man's scripted inputs or Oak dialogue.
s32 DualScreen_FirstBattleActionBattler(void);
s32 DualScreen_FirstBattleMoveBattler(void);

// Command navigation must match DualScreenView.CMD_STEPS for both physical
// input and touchscreen-generated keys: FIGHT above BAG / RUN / POKeMON.
s32 DualScreen_ActionCursorStep(u32 cursor, u32 direction);

// ---------------------------------------------------------------------------
// Battle bag/party/prompt takeover (Gen 4 style): the bottom screen arms a takeover
// before key-walking the action cursor to BAG or POKeMON; the player battle
// controller then waits for a choice submitted over JNI instead of opening
// the GBA bag/party menu apps, and the battle never leaves the top screen.
// All backing state is runtime-only .bss in dualscreen_bridge.c.
// ---------------------------------------------------------------------------

// Result codes reported back to the bottom screen after a submission.
enum {
    DS_BMENU_RESULT_NONE = 0,
    DS_BMENU_RESULT_USED = 1,        // accepted; menu closed
    DS_BMENU_RESULT_NO_EFFECT = 2,   // "It won't have any effect."
    DS_BMENU_RESULT_CANT_USE = 3,    // blocked (box full, trainer battle, trapped)
    DS_BMENU_RESULT_BAD_TARGET = 4,  // invalid party choice
};

// Implemented in dualscreen_bridge.c: the pending-choice mailbox.
// Consumes an armed takeover (1 bag, 2 party), or uses a live bottom screen
// for physical-button entry. FALSE preserves the classic GBA menu.
u32 DualScreen_TakeBattleTakeover(u32 mode);
// The controller reports entering/leaving its bottom-screen wait state.
void DualScreen_SetBattleMenuOpen(u32 mode, u32 caseId, u32 battler);
void DualScreen_ClearBattleMenu(void);
// Snapshot access: current wait mode (0/1/2) plus details.
u32 DualScreen_BattleMenuInfo(u32 *caseId, u32 *battler, u32 *result, u32 *seq);
// Polls (and consumes) a choice submitted from the bottom screen.
u32 DualScreen_TakeBattleChoice(s32 *a, s32 *b);
// Reports a rejected submission; the wait state stays open.
void DualScreen_SetBattleMenuResult(u32 result);
// Returns TRUE only on cancel or accepted item use. Rejections keep waiting.
u32 DualScreen_PollBattleItemChoice(u16 *itemId);
// Opens the party wait before fading out the battle, including forced send-out.
// FALSE leaves the controller's classic menu path intact.
u32 DualScreen_TryOpenBattlePartyMenu(void);
// Returns TRUE for a valid field party index, or PARTY_SIZE on allowed cancel.
u32 DualScreen_PollBattleMonChoice(u8 *monId);
// Replaces the trainer battle's top-screen Yes/No switch prompt with a
// bottom-screen choice. The returned value matches the original cursor:
// 0 switches Pokémon, 1 keeps battling.
u32 DualScreen_TryOpenBattleSwitchPrompt(void);
u32 DualScreen_PollBattleSwitchChoice(u8 *choice);
// A cancelled bottom-screen menu leaves the same action prompt visible on
// the top display. The next choose-action command consumes this one-shot flag
// so it does not clear and retype identical text.
void DualScreen_PreserveBattlePrompt(u32 battler);
u32 DualScreen_TakePreservedBattlePrompt(u32 battler);
// Whether the bottom screen has fetched a snapshot recently (it polls ~8/s
// while its Presentation is actually showing). Flows that install a
// bottom-screen wait with no arming tap (forced send-out) must require this,
// so a desktop build or a stolen bottom display fails safe to the GBA menu.
u32 DualScreen_BottomScreenLive(void);

// Implemented in item_use.c: applies one battle-bag item exactly as the GBA
// bag + party menu would (validate, run the item effect table, consume the
// item, refresh the healthbox), without opening either menu. Returns a
// DS_BMENU_RESULT_* code; on DS_BMENU_RESULT_USED the caller returns the
// item id to the battle engine, whose own scripts (ball throw, "used item"
// message, run-away) then run unchanged.
u32 DualScreen_UseBattleItem(u16 itemId, s32 targetPartyId, s32 moveSlot);
// Matches Java's battle bag: 0 unavailable, 1 ball, 2 medicine, 3 X item,
// 4 escape, 5 all-move PP recovery, 6 single-move PP recovery, 7 Poke Flute.
u32 DualScreen_BattleItemCategory(u16 itemId);
// Presentation group for the battle bag: 1 HP/PP recovery, 2 Poke Balls,
// 3 status recovery, 4 battle/escape items; 0 means unavailable.
u32 DualScreen_BattleItemGroup(u16 itemId);

// Implemented in party_menu.c: the battle-order bookkeeping that
// TrySwitchInPokemon performs for a switch choice, for a mon given as a
// field party index.
void DualScreen_BattleSwitchOrder(u8 monId);

#endif // GUARD_PLATFORM_DUALSCREEN_H
