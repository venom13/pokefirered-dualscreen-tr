#!/usr/bin/env python3
"""Regression for task-driven affine animation command traversal."""
from pathlib import Path
import os
import subprocess
import tempfile

from test_bag_menu_init import function

ROOT = Path(__file__).resolve().parents[2]
SOURCE = (ROOT / "src/battle_anim_mons.c").read_text()
runner = function(SOURCE, "RunAffineAnimFromTaskData")

assert "(const union AffineAnimCmd *)LoadPointerFromVars" in runner
assert "+ task->data[7]" in runner
assert "task->data[7] << 3" not in runner

program = r"""
#include <assert.h>
#include <stdint.h>
typedef uint8_t u8, bool8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef int16_t s16;
#define TRUE 1
#define FALSE 0
#define AFFINEANIMCMDTYPE_LOOP 0x7FFD
#define AFFINEANIMCMDTYPE_JUMP 0x7FFE
#define AFFINEANIMCMDTYPE_END  0x7FFF
struct AffineAnimFrameCmd { s16 xScale; s16 yScale; u8 rotation; u8 duration; };
struct AffineAnimLoopCmd { s16 type; s16 count; };
struct AffineAnimJumpCmd { s16 type; u16 target; };
union AffineAnimCmd {
    s16 type;
    struct AffineAnimFrameCmd frame;
    struct AffineAnimLoopCmd loop;
    struct AffineAnimJumpCmd jump;
};
struct Task { s16 data[16]; };
struct Sprite { s16 y2; } gSprites[1];
static const union AffineAnimCmd commands[] = {
    {.frame = {-12, 20, 0, 8}},
    {.frame = {12, -20, 0, 8}},
    {.loop = {AFFINEANIMCMDTYPE_LOOP, 2}},
    {.type = AFFINEANIMCMDTYPE_END},
};
static const union AffineAnimCmd *sAnimTaskAffineAnim;
static int scaleCalls, resetCalls;
static s16 lastX, lastY;
static void *LoadPointerFromVars(s16 lo, s16 hi) { (void)lo; (void)hi; return (void *)commands; }
static void SetSpriteRotScale(u8 sprite, s16 x, s16 y, u16 rotation) {
    assert(sprite == 0 && rotation == 0); scaleCalls++; lastX = x; lastY = y;
}
static void SetBattlerSpriteYOffsetFromYScale(u8 sprite) { assert(sprite == 0); }
static void ResetSpriteRotScale(u8 sprite) { assert(sprite == 0); resetCalls++; }
""" + runner + r"""
int main(void)
{
    struct Task task = {0};
    task.data[10] = 0x100;
    task.data[11] = 0x100;

    assert(sizeof(union AffineAnimCmd) == 6);
    for (int frame = 0; frame < 8; frame++)
        assert(RunAffineAnimFromTaskData(&task));
    assert(task.data[7] == 1 && lastX == 160 && lastY == 416);

    assert(RunAffineAnimFromTaskData(&task));
    assert(scaleCalls == 9 && lastX == 172 && lastY == 396);
    assert(task.data[7] == 1 && resetCalls == 0);
    return 0;
}
"""

with tempfile.TemporaryDirectory() as tmp:
    source = Path(tmp) / "battle_affine_anim.c"
    binary = Path(tmp) / "battle_affine_anim"
    source.write_text(program)
    cc = os.environ.get("CC", "cc")
    subprocess.run(
        [cc, "-std=c11", "-Wall", "-Wextra", "-Werror", "-fsanitize=address,undefined", str(source), "-o", str(binary)],
        check=True,
    )
    subprocess.run([str(binary)], check=True)

print("battle affine animation regression passed")
