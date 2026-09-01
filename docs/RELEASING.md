# Publishing an Android release

The public APK requires the user's own English FireRed Rev 1 ROM. The packaging
tool removes data ranges that match that ROM and records how to restore them.
It verifies byte-exact reconstruction before signing. Compiled game code,
unmatched tables, and upstream resources remain; this process is **not** a
complete copyright audit or a claim that the APK contains no game material.

## Build

Follow [BUILD_ANDROID.md](BUILD_ANDROID.md) to prepare the generated resources.
Update `dualScreenVersion` and increase `dualScreenVersionCode` in
`android/app/build.gradle`, then:

```sh
cd android
./SDL2/android-project/gradlew assembleRelease
cd ..
python3 -m venv /path/outside/repository/release-venv
/path/outside/repository/release-venv/bin/pip install pyelftools==0.32
```

The raw `app-release-unsigned.apk` is an intermediate artifact, **not** the
public download. Do not upload it. Release builds refuse to start without the
packaged asset manifest; debug builds without a manifest still open directly.

The public v0.1.3 release uses version code **10403**, following v0.1.2's
**10402** and local test build v0.1.4's **10400**. Keep the internal code increasing
independently of the display version so updates preserve existing installations
and saves.

## Signing key

Create and securely back up a dedicated Android release keystore outside the
repository. Keep using the same key for future updates. Store passwords in a
password manager or private files; never commit them or pass plaintext passwords
as command-line arguments. Losing this key prevents in-place updates.

The packaging tool requires an explicit keystore and alias; it never falls back
to a debug signing key. Set `FIRERED_STORE_PASSWORD` and
`FIRERED_KEY_PASSWORD` in the environment without printing them.

## Package

Use the unstripped library belonging to this exact release build. Gradle writes
it below `android/app/build/intermediates/cxx/RelWithDebInfo/<build-id>/obj/armeabi-v7a/`.
Do not use a debug library or guess the build-id directory.

```sh
/path/outside/repository/release-venv/bin/python tools/dualscreen/package_release.py \
  --apk android/app/build/outputs/apk/release/app-release-unsigned.apk \
  --unstripped /path/to/this/release/obj/armeabi-v7a/libmain.so \
  --rom /path/to/your/FireRed-Rev-1.gba \
  --build-tools "$ANDROID_HOME/build-tools/36.0.0" \
  --keystore /private/path/release.p12 \
  --alias pokefirered-dualscreen \
  --out dist/releases/v0.1.3/Pokemon-FireRed-Dual-Screen-0.1.3.apk
```

The expected ROM is 16,777,216 bytes, SHA-1
`dd5945db9b930750cb39d00c84da8571feebf417`. Neither the ROM nor the signing
credentials are added to the APK. The tool checks the native build IDs, validates
all matched ranges, tests exact restoration, aligns the ZIP, signs, and verifies
the final APK. An existing output file is never overwritten.

ZIP alignment of native libraries is not a claim of 16 KiB-page device support:
the native target remains ARMv7 and requires 32-bit ARM compatibility.

## Verify and publish

- Run `python3 tools/dualscreen/test_prepare_android.py` and
  `python3 tools/dualscreen/test_asset_loader.py`.
- Run the menu and battle regressions in `tools/dualscreen/`:
  `test_bag_menu_init.py`, `test_battle_bag.py`, `test_battle_party.py`,
  `test_battle_snapshot.py`, and `test_battle_switch_return.py`.
  The BAG/party tests also compile Java methods; set `JAVA_HOME` to JDK 17.
- Check APK package, version name/code, ARMv7 ABI, release signature, ZIP alignment,
  and absence of personal files.
- Device-test a fresh launch without a ROM, wrong-ROM rejection, correct-ROM
  import, cold restart, new game / Continue, a battle, and saving when hardware
  is available. Keep debug and release save directories separate. Report any
  untested areas in release notes.
- Commit the source, create/push the matching version tag, then upload only the
  signed, processed APK and a SHA-256 checksum to GitHub Releases.
- Verify the published tag commit and downloaded asset checksum.

ROMs, saves, raw development APKs, unprocessed native libraries, and private keys
must never be attached to a release.
