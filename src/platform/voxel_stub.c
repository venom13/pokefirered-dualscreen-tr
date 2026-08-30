#include "global.h"
#include <stdbool.h>

#if defined(PLATFORM_SDL2) && (defined(NATIVE_LINUX) || defined(__ANDROID__))
bool gVoxelFirstPersonMode = false;

bool VoxelRenderer_Init(void)
{
    return false;
}

void VoxelRenderer_RenderFrame(void)
{
}

void VoxelRenderer_Shutdown(void)
{
}

void VoxelRenderer_HandleMouseMotion(int dx, int dy)
{
    (void)dx;
    (void)dy;
}
#endif
