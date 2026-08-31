#ifndef GUARD_REGION_MAP_H
#define GUARD_REGION_MAP_H

#include "global.h"
#include "bg.h"

enum {
    REGIONMAP_TYPE_NORMAL,
    REGIONMAP_TYPE_WALL,
    REGIONMAP_TYPE_FLY,
    REGIONMAP_TYPE_COUNT
};

u8 *GetMapName(u8 *dest, u16 mapsec, u16 fill);
u8 *GetMapNameGeneric(u8 *dest, u16 mapsec);
u8 *GetMapNameGeneric_(u8 *dest, u16 mapsec);
void InitRegionMapWithExitCB(u8 type, void (*callback)(void));
void CB2_OpenFlyMap(void);

#ifdef PLATFORM_SDL2
struct DualScreenMapSection
{
    u8 region; // 0 Kanto, 1 Sevii 1-3, 2 Sevii 4-5, 3 Sevii 6-7
    u8 x, y, width, height; // FireRed's 22x15 grid, origin at pixel (32, 32)
};
const u16 *DualScreen_GetRegionMapPal(void);
const u32 *DualScreen_GetRegionMapGfxLZ(void);
const u32 *DualScreen_GetRegionMapTilemapLZ(u8 region);
bool32 DualScreen_GetRegionMapSection(u16 mapsec, struct DualScreenMapSection *out);
#endif

#endif // GUARD_REGION_MAP_H
