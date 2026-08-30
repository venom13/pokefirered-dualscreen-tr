# FireRed port notes

## Target and architecture

The Android port targets English FireRed Revision 1 (`BPRE`), based on
`pret/pokefirered` commit `c75f35230`. It reuses the native platform layer and
Android presentation approach from Goldoire's Emerald Dual Screen project.

- `src/`, `include/`, `data/`: FireRed engine and upstream decompilation data.
- `src/platform/sdl2.c`: rendering host, controls, audio, configuration, save I/O.
- `src/platform/bios.c`, `dma.c`, `gba_easy_draw.c`: host implementations of
  the GBA services needed by the compiled engine.
- `src/platform/dualscreen_bridge.c`: FireRed-specific game snapshots and JNI
  calls. The Android UI reads structured state rather than ROM memory offsets.
- `android/app/src/main/java/com/pokeemerald/experimental/`: Android activities,
  second-display presentation, party and battle UI. The inherited Java namespace
  remains; the install identity is FireRed-specific.
- `android/app/src/main/cpp/CMakeLists.txt`: preprocesses C and assembly data,
  then builds the ARMv7 shared library.
- `android/SDL2`: SDL 2.30.7 pinned as a Git submodule.
- `tools/dualscreen/prepare_android.py`: prepares build tools, generated data,
  graphics, and MIDI assembly without building a GBA ROM.

## Implemented and device-tested

- [x] Native Android launch on AYN Thor.
- [x] FireRed intro and player/rival name entry.
- [x] Transition from the intro to the overworld.
- [x] Oak's lab first rival battle and bottom-screen action/move menus.
- [x] FireRed-red lower-screen styling and startup logo.
- [x] HP ratios on player and opponent battle cards.
- [x] Player EXP bar and within-level EXP ratio.
- [x] Battle waiting-card layout without the loading-dot animation.
- [x] Separate name/type/PP rows in the Pokémon detail view.
- [x] In-game save, cold-start load, quest-log recap, and return to gameplay.

These are targeted smoke tests, not a full-game compatibility guarantee.

## Native compatibility fixes

- Use host memory for flash verification; do not execute stack-copied GBA code.
- Check flash sector/range boundaries and preserve the last save on write failure.
- Commit saves through a temporary file, flush/sync, and checked rename.
- Initialize the PC-storage pointer before the copyright screen loads save sectors.
- Skip probing nonexistent GBA wireless hardware on portable builds.
- Yield to host VBlank during synchronous new-game and quest-log map loading so
  queued tile copies can complete.
- Adapt naming-screen, battle transition, text, and controller paths to the
  portable engine's memory and callback model.

## Validation completed during development

- Native debug APK build and installation on AYN Thor.
- On-device startup, CONTINUE, recap playback, and return to playable overworld.
- Save-write and reload tests, including simulated write/flush/rename failures.
- AddressSanitizer/UndefinedBehaviorSanitizer host checks of extracted save and
  quest-log functions.
- Layout checks covering single/double battle waiting cards and move rows with
  real font widths, empty move slots, and zero PP.

The historical host test harnesses were run locally during development; this
initial publication does not claim they form a checked-in automated test suite.
For a clean-clone build, follow [BUILD_ANDROID.md](docs/BUILD_ANDROID.md).

## Remaining work

- [ ] Kanto/Sevii Islands map rendering for the MAP tab.
- [ ] Native FireRed move-type icon extraction (text fallback currently used).
- [ ] Longer playthrough and more devices / display sizes.
- [ ] Broader double-battle, switching, item-use, and special-battle validation.
- [ ] ARM64 native build.
- [ ] Audited asset-stripped packaging, matching manifest generation, signing,
      and release distribution.
- [ ] In-app save import/export UI (file-copy workflow currently supported).

Link cable / RFU multiplayer, ROM hacks, LeafGreen, and a desktop or 3D/voxel
release are outside the current validated scope. Files inherited for other
platforms are not a promise of support.

## Upstream workflow

The inherited ROM-matching CI is restricted to the original pret repository.
It is not an Android CI pipeline, and its historical GBA comparison assumptions
do not validate this native port. No build artifact is automatically published.
