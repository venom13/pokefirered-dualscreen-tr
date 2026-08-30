# Building FireRed Dual Screen for Android

This produces a **local development APK**, not an asset-stripped public release.
The documented environment is macOS with a POSIX shell; the preparation script
also uses standard Python/Make tooling, but Linux has not been device-validated.

## Requirements

- Git, Python 3, Make, and a C/C++ compiler.
- `pkg-config` and libpng development headers/libraries.
- Clang available at `/usr/bin/clang` (used by the current assembly preprocessing).
- ARM bare-metal binutils: `arm-none-eabi-as`, `arm-none-eabi-ld`,
  `arm-none-eabi-objcopy`. No agbcc build is needed for the Android target.
- JDK 17.
- Android SDK platform 36, NDK `26.3.11579264`, and CMake `3.22.1`.
- An Android device supporting 32-bit ARM apps; AYN Thor is the tested device.

On the development Mac, the Homebrew formulae used were
`arm-none-eabi-binutils`, `libpng`, `pkgconf`, and `openjdk@17`.
Install Xcode Command Line Tools for the host compiler. Configure `JAVA_HOME`
and `ANDROID_HOME` for your own machine; no personal SDK paths are committed.

If the ARM tools are not on PATH, add their bin directory to PATH. The CMake
configuration also accepts `ARM_NONE_EABI_TOOLCHAIN` as the toolchain root.

With Android command-line tools configured, the SDK components can be installed
using:

```sh
sdkmanager "platform-tools" "platforms;android-36" "build-tools;34.0.0" \
  "ndk;26.3.11579264" "cmake;3.22.1"
sdkmanager --licenses
```

Review and accept SDK licenses yourself. The existing Android Gradle Plugin is
8.1.1; it emits a warning about compileSdk 36. The development build succeeds
with the pinned configuration, but these versions are not a claim of Play Store
submission readiness.

## Clone

```sh
git clone --recurse-submodules https://github.com/venom13/pokefirered-dualscreen.git
cd pokefirered-dualscreen
```

For a clone made without submodules:

```sh
git submodule update --init --recursive
```

SDL is pinned to release 2.30.7, commit
`9519b9916cd29a14587af0507292f2bd31dd5752`. Do not replace it with SDL3.
The historical patch in `android/patches/` is retained for provenance; it is
**not applied** in the currently tested build.

## Prepare generated data

From the repository root:

```sh
python3 tools/dualscreen/prepare_android.py --jobs 4
```

This builds host conversion tools and generates the map headers, graphics,
sound samples, and MIDI assembly expected by the native CMake build. It does
not download a ROM, create a GBA ROM, install an APK, or change a save.

The resource collector has a small ROM-free regression test:

```sh
python3 tools/dualscreen/test_prepare_android.py
```

The normal Android development build uses the decompilation resources. Keep any
personal reference ROM outside version control. The optional runtime ROM picker
does not run unless a matching asset manifest has been separately packaged.

## Build and install

```sh
cd android
./SDL2/android-project/gradlew assembleDebug
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

Output: `android/app/build/outputs/apk/debug/app-debug.apk`.

Installed package: `com.pokefirered.dualscreen.debug`.
The app label is **Pokemon FireRed Dual Screen**.

The `-r` install flag updates an APK with the same package/signature while
preserving its data. If Android reports a signing conflict, back up your save
before considering uninstalling anything; do not clear application data as a
routine build step.

The source also defines the release identity `com.pokefirered.dualscreen`.
No release signing key, signing password, or ready-to-publish APK is included.
Do not upload development APKs or native libraries: they contain compiled game
data.

## Rebuild after edits

Rerun preparation after changing graphics, maps, sound, or other source assets.

The native preprocessing commands do not yet track every transitive header and
assembly include. For header/include changes, use a clean native build to avoid
stale generated C:

```sh
cd android
./SDL2/android-project/gradlew clean assembleDebug
```

Keep the generated source assets prepared by the previous step.

## Save backup and import with ADB

Examples below use the debug package. Connect and authorize exactly the intended
device; add `-s DEVICE_SERIAL` after `adb` when more than one device is connected.

Back up into a new local directory so no previous backup is overwritten:

```sh
adb shell am force-stop com.pokefirered.dualscreen.debug
mkdir firered-save-backup
adb pull /sdcard/Android/data/com.pokefirered.dualscreen.debug/files/pokefirered.sav firered-save-backup/
```

To import, first keep that backup and verify that your imported battery save is
131,072 bytes. Then, with the app still closed:

```sh
adb push /path/to/imported.sav /sdcard/Android/data/com.pokefirered.dualscreen.debug/files/pokefirered.sav
```

Open the app and choose CONTINUE. This replaces the app's active save.
For the release package, omit `.debug` in both the package name and directory.

## Troubleshooting

- **Missing SDL files:** initialize the Git submodule.
- **Missing `.4bpp`, `.gbapal`, `.bin`, headers, or song symbols:** rerun the
  preparation script before configuring/building CMake.
- **Missing libpng / pkg-config:** install the host development dependency and
  confirm `pkg-config --cflags --libs libpng` succeeds.
- **No matching ABI:** the current APK is ARMv7, not ARM64-only.
- **Unexpected speed:** check FAST FORWARD and the R2 toggle.
- **MAP unavailable:** this is a known incomplete feature, not a missing ROM.
- **Crash:** include the commit and a relevant `adb logcat -b crash -d` excerpt
  in an issue, with private information removed. Keep your save backup.

Do not attach ROMs, save files, keys, or locally built game-data-containing APKs
to public issue reports.
