#!/usr/bin/env python3
"""ROM-free regressions for native Pokémon Storage sprite safety.

The first case reproduces Move Items opening on a box with empty slots. Further
cases force icon, palette, and sprite allocation failures across the shared PC
graphics paths so native builds never dereference GBA-style null pointers.
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
#include <string.h>

typedef uint8_t u8;
typedef int16_t s16;
typedef int32_t s32;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint8_t bool8;
#define TRUE 1
#define FALSE 0

#define IN_BOX_ROWS 5
#define IN_BOX_COLUMNS 6
#define IN_BOX_COUNT 30
#define PARTY_SIZE 6
#define MAX_ITEM_ICONS 3
#define MAX_SPRITES 64
#define SPECIES_NONE 0
#define ITEM_NONE 0
#define OPTION_MOVE_ITEMS 3
#define MODE_PARTY 0
#define MODE_BOX 1
#define MON_DATA_SPECIES_OR_EGG 1
#define MON_DATA_PERSONALITY 2
#define MON_DATA_HELD_ITEM 3
#define ST_OAM_OBJ_NORMAL 0
#define ST_OAM_OBJ_BLEND 1
#define GFXTAG_ITEM_ICON_0 100
#define PALTAG_ITEM_ICON_0 200
#define TAG_NONE 0xFFFF
#define TILE_SIZE_4BPP 32
#define OBJ_PLTT_ID(n) ((n) * 16)

struct OamData { u8 objMode; u8 priority; };
struct Sprite {
    struct OamData oam;
    s16 x, y;
    u8 invisible;
    u8 subpriority;
    void (*callback)(struct Sprite *);
};
struct Pokemon { u16 species; u16 heldItem; u32 personality; };
struct PokeStorageItemIcon {
    void *tiles;
    u16 palIndex;
    struct Sprite *sprite;
    bool8 active;
};
struct PokemonStorageSystemData {
    u8 boxOption;
    struct Sprite *boxMonsSprites[IN_BOX_COUNT];
    struct Sprite *partySprites[PARTY_SIZE];
    struct Sprite *movingMonSprite;
    struct PokeStorageItemIcon itemIcons[MAX_ITEM_ICONS];
    u16 movingItemId;
};

static struct PokemonStorageSystemData storage;
static struct PokemonStorageSystemData *gStorage = &storage;
static struct Pokemon gPlayerParty[PARTY_SIZE];
static struct Sprite sprites[MAX_SPRITES];
static struct Sprite gSprites[MAX_SPRITES];
static u16 boxSpecies[IN_BOX_COUNT], boxItems[IN_BOX_COUNT];
static u32 boxPersonalities[IN_BOX_COUNT];
static int iconCreateCount, failIconCreate;

static u32 GetBoxMonDataAt(u8 box, u8 pos, u8 request) {
    (void)box;
    if (request == MON_DATA_SPECIES_OR_EGG) return boxSpecies[pos];
    if (request == MON_DATA_PERSONALITY) return boxPersonalities[pos];
    if (request == MON_DATA_HELD_ITEM) return boxItems[pos];
    return 0;
}
static u32 GetCurrentBoxMonData(u8 pos, u8 request) {
    return GetBoxMonDataAt(0, pos, request);
}
static u32 GetMonData(struct Pokemon *mon, u8 request) {
    if (request == MON_DATA_SPECIES_OR_EGG) return mon->species;
    if (request == MON_DATA_PERSONALITY) return mon->personality;
    if (request == MON_DATA_HELD_ITEM) return mon->heldItem;
    return 0;
}
static struct Sprite *CreateMonIconSprite(u16 species, u32 personality, s16 x, s16 y, u8 priority, u8 subpriority) {
    (void)species; (void)personality; (void)x; (void)y; (void)priority; (void)subpriority;
    int current = iconCreateCount++;
    if (current == failIconCreate) return NULL;
    memset(&sprites[current], 0, sizeof(sprites[current]));
    return &sprites[current];
}
static u8 IsCursorInBox(void) { return TRUE; }
static u8 GetMonIconPriorityByCursorArea(void) { return IsCursorInBox() ? 2 : 1; }
static void SpriteCB_HeldMon(struct Sprite *sprite) { (void)sprite; }
static void SpriteCallbackDummy(struct Sprite *sprite) { (void)sprite; }

struct CompressedSpriteSheet { const void *data; u16 size; u16 tag; };
struct SpriteTemplate { u16 tileTag; u16 paletteTag; };
static const struct SpriteTemplate sSpriteTemplate_ItemIcon = {0};
static unsigned char fakeVram[65536];
#define OBJ_VRAM0 fakeVram
static int failSheetTag = -1, failPaletteTag = -1, failSpriteTag = -1;
static int freedSheets, freedPalettes;
static u16 loadedTileStarts[MAX_ITEM_ICONS];
static u16 LoadCompressedSpriteSheet(const struct CompressedSpriteSheet *sheet) {
    u16 index = sheet->tag - GFXTAG_ITEM_ICON_0;
    loadedTileStarts[index] = sheet->tag == failSheetTag ? TAG_NONE : index;
    return loadedTileStarts[index];
}
static u16 GetSpriteTileStartByTag(u16 tag) { return loadedTileStarts[tag - GFXTAG_ITEM_ICON_0]; }
static u8 AllocSpritePalette(u16 tag) {
    return tag == failPaletteTag ? 0xFF : (u8)(tag - PALTAG_ITEM_ICON_0 + 1);
}
static u8 CreateSprite(const struct SpriteTemplate *template, s16 x, s16 y, u8 subpriority) {
    (void)x; (void)y; (void)subpriority;
    if (template->tileTag == failSpriteTag) return MAX_SPRITES;
    return (u8)(template->tileTag - GFXTAG_ITEM_ICON_0);
}
static void FreeSpriteTilesByTag(u16 tag) { (void)tag; freedSheets++; }
static void FreeSpritePaletteByTag(u16 tag) { (void)tag; freedPalettes++; }
'''

SUFFIX = r'''
static void Reset(void) {
    memset(&storage, 0, sizeof(storage));
    memset(gPlayerParty, 0, sizeof(gPlayerParty));
    memset(sprites, 0, sizeof(sprites));
    memset(gSprites, 0, sizeof(gSprites));
    memset(boxSpecies, 0, sizeof(boxSpecies));
    memset(boxItems, 0, sizeof(boxItems));
    memset(boxPersonalities, 0, sizeof(boxPersonalities));
    for (int i = 0; i < MAX_ITEM_ICONS; i++) loadedTileStarts[i] = TAG_NONE;
    storage.boxOption = OPTION_MOVE_ITEMS;
    iconCreateCount = 0;
    failIconCreate = -1;
    failSheetTag = failPaletteTag = failSpriteTag = -1;
    freedSheets = freedPalettes = 0;
}

int main(void) {
    Reset();
    InitBoxMonSprites(0);
    for (int i = 0; i < IN_BOX_COUNT; i++) assert(storage.boxMonsSprites[i] == NULL);

    Reset();
    boxSpecies[0] = 1; boxSpecies[1] = 2;
    boxItems[0] = ITEM_NONE; boxItems[1] = 10;
    InitBoxMonSprites(0);
    assert(storage.boxMonsSprites[0]->oam.objMode == ST_OAM_OBJ_BLEND);
    assert(storage.boxMonsSprites[1]->oam.objMode == ST_OAM_OBJ_NORMAL);

    Reset();
    boxSpecies[0] = 1;
    failIconCreate = 0;
    InitBoxMonSprites(0);
    assert(storage.boxMonsSprites[0] == NULL);

    Reset();
    boxSpecies[4] = 1;
    failIconCreate = 0;
    CreateBoxMonIconAtPos(4);
    assert(storage.boxMonsSprites[4] == NULL);

    Reset();
    for (int i = 0; i < 3; i++) gPlayerParty[i].species = (u16)(i + 1);
    failIconCreate = 1;
    CreatePartyMonsSprites(FALSE);
    assert(storage.partySprites[0] != NULL && storage.partySprites[0]->invisible);
    assert(storage.partySprites[1] == NULL);
    assert(storage.partySprites[2] != NULL && storage.partySprites[2]->invisible);

    Reset();
    assert(!SetMovingMonSprite(MODE_BOX, 0));
    storage.boxMonsSprites[0] = &sprites[0];
    assert(SetMovingMonSprite(MODE_BOX, 0));
    assert(storage.boxMonsSprites[0] == NULL && storage.movingMonSprite == &sprites[0]);

    Reset();
    assert(CreateItemIconSprites());
    for (int i = 0; i < MAX_ITEM_ICONS; i++) {
        assert(storage.itemIcons[i].sprite != NULL);
        assert(storage.itemIcons[i].tiles != NULL);
        assert(storage.itemIcons[i].sprite->invisible);
        assert(!storage.itemIcons[i].active);
    }

    Reset();
    failSheetTag = GFXTAG_ITEM_ICON_0 + 1;
    assert(!CreateItemIconSprites());
    assert(storage.itemIcons[1].sprite == NULL);
    assert(GetNewItemIconIdx() == 0);
    assert(GetNewItemIconIdx() == 2);
    assert(GetNewItemIconIdx() == MAX_ITEM_ICONS);

    Reset();
    failPaletteTag = PALTAG_ITEM_ICON_0 + 1;
    assert(!CreateItemIconSprites());
    assert(storage.itemIcons[1].sprite == NULL && freedSheets == 1);

    Reset();
    failSpriteTag = GFXTAG_ITEM_ICON_0 + 1;
    assert(!CreateItemIconSprites());
    assert(storage.itemIcons[1].sprite == NULL && freedSheets == 1 && freedPalettes == 1);

    puts("PASS: Move Items empty slots, PC mon icons and allocation failures are null-safe");
    return 0;
}
'''


def main():
    graphics = (ROOT / "src/pokemon_storage_system_graphics.c").read_text()
    misc = (ROOT / "src/pokemon_storage_system_misc.c").read_text()
    code = PREFIX
    for name in (
        "InitBoxMonSprites", "CreateBoxMonIconAtPos", "CreatePartyMonsSprites",
        "SetMovingMonSprite",
    ):
        code += function(graphics, name) + "\n"
    code += function(misc, "CreateItemIconSprites") + "\n"
    code += function(misc, "GetNewItemIconIdx") + "\n"
    code += SUFFIX

    with tempfile.TemporaryDirectory(prefix="firered-storage-sprites-") as directory:
        directory = Path(directory)
        source = directory / "test.c"
        executable = directory / "test"
        source.write_text(code)
        subprocess.run([
            os.environ.get("CC", "cc"), "-std=gnu11", "-O1", "-g",
            "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
            str(source), "-o", str(executable),
        ], check=True)
        subprocess.run([str(executable)], check=True)


if __name__ == "__main__":
    main()
