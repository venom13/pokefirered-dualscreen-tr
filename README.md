# Pokémon FireRed Dual Screen

<img src="android/app/src/main/res/mipmap-xxxhdpi/ic_launcher.png" alt="FireRed Dual Screen icon" width="96">

A work-in-progress **native Android dual-screen port of Pokémon FireRed** for
the AYN Thor and similar devices. The game runs as compiled C code with an SDL2
host, not inside a GBA CPU emulator.

Built on [pret/pokefirered](https://github.com/pret/pokefirered), with the Android
host and dual-screen interface adapted from
[Goldoire/pokeemerald-dualscreen](https://github.com/Goldoire/pokeemerald-dualscreen).

> **Status: experimental, source-only publication.** Early-game play, the first
> rival battle, saving, and loading have been tested on an AYN Thor. A complete
> playthrough and other devices have not been validated. No downloadable APK is
> published with this initial source release.

## Features

- **Two-screen interface:** gameplay on the upper display; party, battle controls,
  bag, trainer card, and settings on the lower display.
- **FireRed styling:** red interface accents, a white-accented launcher icon, and
  a FireRed logo on the lower display until the first usable game state arrives.
- **Party details:** Pokémon icons, levels, HP, status, stats, nature, ability,
  moves, PP, and experience progress.
- **Touch battle menus:** Fight, Bag, Pokémon, and Run, plus move selection.
  The classic top-screen battle menus remain selectable in settings.
- **HP for both sides:** player and opponent cards show current / maximum HP.
- **Experience progress:** the player's battle card includes an EXP bar and
  `Next Level: current progress / required EXP`.
- **Roomier waiting state:** when no battle choice is requested, Pokémon cards
  fill the available space without a loading-dot animation.
- **Readable move details:** move names occupy their own line; type and PP appear
  underneath without overlapping.
- **Optional battle hints:** move-effectiveness markers and opponent weaknesses.
- **Fast forward:** 2×, 3×, or 4×, with a separate choice to keep music at normal
  speed or accelerate it too.
- **Display options:** optional wider rendering, artwork/black/white background,
  touch controls, and volume settings.
- **Standard flash saves:** 128 KiB FireRed saves, including import/export by file
  copy. Writes use a temporary file and checked replacement.

## Compatibility and limitations

| Area | Current status |
| --- | --- |
| Game target | English FireRed, USA/Europe, Revision 1 |
| Tested hardware | AYN Thor, dual-screen Android |
| Android minimum | API 21 (Android 5.0), as declared by the app |
| Native architecture | `armeabi-v7a` only; the device must support 32-bit ARM apps |
| Early game | Intro, player/rival naming, first rival battle, save and Continue tested |
| Lower-screen map | Not implemented; the MAP tab currently shows “Map unavailable” |
| Move-type icons | Text badges are used; the native type-icon bridge is not yet implemented |
| Multiplayer | GBA link cable / wireless-adapter functionality is not supported |
| Other games | LeafGreen, Emerald, translations, and ROM hacks are not supported targets |
| Other platforms | Android is the validated build; inherited desktop/voxel code is not a supported feature |

Widescreen is experimental. Some screens still use the original 240×160 layout,
and transitions can show rendering artifacts. This port does not claim a complete,
bug-free FireRed playthrough.

## Getting started

1. Follow [the Android build guide](docs/BUILD_ANDROID.md).
2. Install the locally built debug APK on a compatible Android device.
3. Launch **Pokemon FireRed Dual Screen**.
4. Use the lower screen's PARTY, BAG, CARD, and settings tabs. Battle choices
   appear there when the game requests an action.

### ROM and asset handling

The reference ROM for this port is:

| Field | Value |
| --- | --- |
| Title | Pokémon FireRed Version (USA, Europe) (Rev 1) |
| Game code / revision | `BPRE` / `1` |
| Size | 16 MiB (16,777,216 bytes) |
| SHA-1 | `dd5945db9b930750cb39d00c84da8571feebf417` |

**Do not upload your game ROM, saves, or locally built APKs to this repository.**

The current development build compiles the decompilation's game data into the
native library and therefore opens directly. A ROM-selection / asset-restoration
gate is inherited from the Emerald port, but it only activates when a matching
`asset_manifest.bin` is packaged. An asset-stripped FireRed release pipeline is
**not included or validated yet**; merely running `assembleRelease` does not make
an asset-free distribution.

This repository retains upstream decompilation resources and small upstream
multiboot payloads under `data/`. It is not presented as a repository containing
no copyrighted game material. No full retail game ROM or personal save is added.
See [credits and notices](THIRD_PARTY_NOTICES.md).

## Saves

Use the game's **SAVE** option. Save states from an emulator are not supported.

The save filename is `pokefirered.sav` and its size is **131,072 bytes**.

| Build | Save directory on the device |
| --- | --- |
| Local debug | `Android/data/com.pokefirered.dualscreen.debug/files/` |
| Release identity | `Android/data/com.pokefirered.dualscreen/files/` |

Debug and release builds have separate app identities and separate saves.
The FireRed app also stays separate from the Emerald app.

### Import a save

1. Export a normal 128 KiB FireRed battery/flash save from your emulator or
   cartridge backup.
2. Close / force-stop FireRed Dual Screen.
3. Back up any existing `pokefirered.sav`.
4. Copy the imported file to the appropriate directory and name it
   `pokefirered.sav`.
5. Reopen the app and choose CONTINUE.

### Export or back up a save

Save in-game, wait for the success message, close the app, and copy
`pokefirered.sav` out of that directory. Keep a backup before updating or
experimenting with a new build. Uninstalling the app can remove its data.

Android may restrict file-manager access to `Android/data`; ADB commands are
provided in the [build guide](docs/BUILD_ANDROID.md#save-backup-and-import-with-adb).
The adjacent `pokefirered.cfg` stores this port's display and audio preferences,
not game progress.

## Controls and settings

- **D-pad / left stick:** move and navigate.
- **A / B:** confirm / cancel.
- **Start / Select, L / R:** regular GBA controls.
- **Touch:** choose lower-screen tabs, Pokémon cards, battle actions, and moves.
- **R2:** toggles fast forward. If the game seems unexpectedly fast, press R2
  again and check the FAST FORWARD setting.
- **HINTS:** OFF/ON for battle effectiveness and weakness information.
- **BATTLE MENUS:** BOTTOM for touch menus; TOP for the classic game menus.
- **FF MUSIC:** NORMAL keeps the music's tempo; SPED UP follows fast forward.

Controller mappings can vary between Android devices.

## EXP and game rules

The EXP ratio is progress **within the current level**, not lifetime EXP:

```text
Next Level: (total EXP - current level's starting EXP)
          / (next level's EXP threshold - current level's starting EXP)
```

At level 100 it displays `Next Level: MAX`. The threshold comes from the
Pokémon species' growth curve.

The project aims to keep FireRed's gameplay rules. The shiny threshold remains
`8 / 65536`, or **1 in 8,192**; the dual-screen changes do not increase it.

## Development and reporting issues

- [Android build instructions](docs/BUILD_ANDROID.md)
- [Port architecture, validation, and remaining work](DUALSCREEN_PORT.md)
- [Upstream GBA build documentation](INSTALL.md) — retained for reference, not
  the Android build procedure.

When reporting an issue, include the device model, Android version, build commit,
exact steps, and whether you resumed a save or started a new game. A screenshot
and relevant crash log are useful. Remove personal information from logs and
never attach a ROM or signing key.

## Credits

- [pret/pokefirered](https://github.com/pret/pokefirered): FireRed/LeafGreen
  decompilation and original game engine foundation.
- [Goldoire/pokeemerald-dualscreen](https://github.com/Goldoire/pokeemerald-dualscreen):
  dual-screen Android host, UI, and design this port adapts.
- [gradenGnostic/pokeemerald-multiplatform](https://github.com/gradenGnostic/pokeemerald-multiplatform):
  native SDL2/platform foundation behind the Emerald port.
- [SDL](https://github.com/libsdl-org/SDL): windowing, input, rendering, and audio.
- [samyost1/tmc-android](https://github.com/samyost1/tmc-android) and
  [samyost1/zelda3-android](https://github.com/samyost1/zelda3-android):
  dual-screen precedents credited by the Emerald project.
- FireRed adaptation and device testing maintained by
  [venom13](https://github.com/venom13), with assistance from AI coding tools.

This is an unofficial fan project, not affiliated with or endorsed by Nintendo,
Creatures Inc., or GAME FREAK. Pokémon names and game material belong to their
respective owners. Existing third-party license notices are retained; there is
no blanket license grant over the original game. Read
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) before redistributing any part.
