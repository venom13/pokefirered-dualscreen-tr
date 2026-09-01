#!/usr/bin/env python3
"""ROM-free regression for Summary-screen markings sprite lifetime."""
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

typedef uint8_t u8;
typedef uint32_t u32;
#define TRUE 1
#define FALSE 0
#define MON_DATA_MARKINGS 1
#define TAG_PSS_UNK_8C 140

struct Pokemon { u8 unused; };
struct Sprite { int x, y; u8 invisible; };
struct PokemonSummaryScreenData {
    struct Pokemon currentMon;
    struct Sprite *markingSprite;
};

static struct PokemonSummaryScreenData summary;
static struct PokemonSummaryScreenData *sMonSummaryScreen = &summary;
static const uint16_t sMonMarkingSpritePalette[1] = {0};
static struct Sprite createdSprite;
static u32 markings;
static int createFails, createCalls, destroyCalls, animCalls;

static void PokeSum_ShowOrHideMonMarkingsSprite(u8 invisible);
static u32 GetMonData(struct Pokemon *mon, int field) {
    assert(mon == &summary.currentMon && field == MON_DATA_MARKINGS);
    return markings;
}
static void DestroySpriteAndFreeResources(struct Sprite *sprite) {
    assert(sprite != NULL);
    destroyCalls++;
}
static struct Sprite *CreateMonMarkingAllCombosSprite(int tileTag, int paletteTag, const uint16_t *palette) {
    assert(tileTag == TAG_PSS_UNK_8C && paletteTag == TAG_PSS_UNK_8C);
    assert(palette == sMonMarkingSpritePalette);
    createCalls++;
    return createFails ? NULL : &createdSprite;
}
static void StartSpriteAnim(struct Sprite *sprite, u32 animation) {
    assert(sprite != NULL && animation == markings);
    animCalls++;
}
'''

SUFFIX = r'''
static void Reset(void) {
    summary.markingSprite = NULL;
    createdSprite = (struct Sprite){0};
    markings = 3;
    createFails = createCalls = destroyCalls = animCalls = 0;
}

int main(void) {
    Reset();
    PokeSum_CreateMonMarkingsSprite();
    assert(summary.markingSprite == &createdSprite);
    assert(createCalls == 1 && destroyCalls == 0 && animCalls == 1);
    assert(createdSprite.x == 20 && createdSprite.y == 91 && createdSprite.invisible == TRUE);

    PokeSum_UpdateMonMarkingsAnim();
    assert(animCalls == 2 && createdSprite.invisible == FALSE);

    PokeSum_CreateMonMarkingsSprite();
    assert(summary.markingSprite == &createdSprite);
    assert(createCalls == 2 && destroyCalls == 1 && animCalls == 3);

    PokeSum_DestroyMonMarkingsSprite();
    assert(summary.markingSprite == NULL && destroyCalls == 2);
    PokeSum_DestroyMonMarkingsSprite();
    PokeSum_ShowOrHideMonMarkingsSprite(FALSE);
    PokeSum_UpdateMonMarkingsAnim();
    assert(destroyCalls == 2 && animCalls == 3);

    Reset();
    summary.markingSprite = &createdSprite;
    createFails = TRUE;
    PokeSum_CreateMonMarkingsSprite();
    assert(summary.markingSprite == NULL);
    assert(createCalls == 1 && destroyCalls == 1 && animCalls == 0);

    puts("PASS: Summary markings sprite is safe before creation and after allocation failure");
    return 0;
}
'''


def main():
    source_text = (ROOT / "src/pokemon_summary_screen.c").read_text()
    code = PREFIX
    for name in (
        "PokeSum_CreateMonMarkingsSprite",
        "PokeSum_DestroyMonMarkingsSprite",
        "PokeSum_ShowOrHideMonMarkingsSprite",
        "PokeSum_UpdateMonMarkingsAnim",
    ):
        code += function(source_text, name) + "\n"
    code += SUFFIX

    with tempfile.TemporaryDirectory(prefix="firered-summary-markings-") as directory:
        directory = Path(directory)
        source = directory / "test.c"
        executable = directory / "test"
        source.write_text(code)
        subprocess.run([
            os.environ.get("CC", "cc"), "-std=c11", "-O1", "-g",
            "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
            str(source), "-o", str(executable),
        ], check=True)
        subprocess.run([str(executable)], check=True)


if __name__ == "__main__":
    main()
