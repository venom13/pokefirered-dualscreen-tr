#include "global.h"
#include "gba/gba.h"
#include "gba/flash_internal.h"

#ifdef PORTABLE
static const u16 sDummyMaxTime[] =
{
      10, 65469, TIMER_ENABLE | TIMER_INTR_ENABLE | TIMER_256CLK,
      10, 65469, TIMER_ENABLE | TIMER_INTR_ENABLE | TIMER_256CLK,
    2000, 65469, TIMER_ENABLE | TIMER_INTR_ENABLE | TIMER_256CLK,
    2000, 65469, TIMER_ENABLE | TIMER_INTR_ENABLE | TIMER_256CLK,
};

const struct FlashSetupInfo DUMMY_SAVE =
{
    ProgramFlashByte_DUMMY,
    ProgramFlashSector_DUMMY,
    EraseFlashChip_DUMMY,
    EraseFlashSector_DUMMY,
    WaitForFlashWrite_DUMMY,
    sDummyMaxTime,
    {
        131072,
        { 4096, 12, 32, 0 },
        { 3, 1 },
        { { 0xCC, 0xCC } }
    }
};

u16 WaitForFlashWrite_DUMMY(u8 phase, u8 *addr, u8 lastData)
{
    return 0;
}

u16 EraseFlashChip_DUMMY(void)
{
    memset(FLASH_BASE, 0xFF, sizeof(FLASH_BASE));
    return 0;
}

u16 EraseFlashSector_DUMMY(u16 sectorNum)
{
    if (gFlash == NULL || sectorNum >= gFlash->sector.count)
        return 1;
    memset(&FLASH_BASE[sectorNum << gFlash->sector.shift], 0xFF, gFlash->sector.size);
    return 0;
}

u16 ProgramFlashByte_DUMMY(u16 sectorNum, u32 offset, u8 data)
{
    if (gFlash == NULL || sectorNum >= gFlash->sector.count || offset >= gFlash->sector.size)
        return 1;
    FLASH_BASE[(sectorNum << gFlash->sector.shift) + offset] = data;
    return 0;
}

u16 ProgramFlashSector_DUMMY(u16 sectorNum, void *src)
{
    if (gFlash == NULL || src == NULL || sectorNum >= gFlash->sector.count)
        return 1;
    memcpy(&FLASH_BASE[sectorNum << gFlash->sector.shift], src, gFlash->sector.size);
    return 0;
}
#endif
