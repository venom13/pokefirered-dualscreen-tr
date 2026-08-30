# Credits and third-party notices

This project combines a FireRed decompilation with native-platform and Android
code adapted from the Emerald Dual Screen project. It must not be treated as a
blanket relicensing of everything in the repository.

## FireRed foundation

- Source: https://github.com/pret/pokefirered
- Starting commit: `c75f35230`.
- Upstream source history, contributor attribution, and file-level notices are
  retained. The upstream graphics, audio, game data, and small multiboot payloads
  remain part of the decompilation tree.

No license in this project grants rights to Pokémon game material, trademarks,
or other material owned by Nintendo, Creatures Inc., GAME FREAK, or others.
No full retail ROM or personal game save is added to this publication.

## Native platform and dual-screen code

- https://github.com/Goldoire/pokeemerald-dualscreen
- https://github.com/gradenGnostic/pokeemerald-multiplatform

Their scoped MIT notice for original port modifications is reproduced unchanged
in [LICENSES/pokeemerald-multiplatform.txt](LICENSES/pokeemerald-multiplatform.txt).
It expressly excludes the original game and independently licensed upstream or
third-party material. This notice is not a new license for the whole FireRed tree.

The platform source also retains attribution to mGBA, NanoboyAdvance, and libgcc
where present. Those origins are not covered by a blanket MIT assertion here.
Consult the corresponding upstream source and file-level terms before extracting
or redistributing those portions.

## SDL

SDL 2.30.7 is pinned as a Git submodule from https://github.com/libsdl-org/SDL.
Its zlib-style license is in `android/SDL2/LICENSE.txt`, and bundled dependencies
retain their own notices. Initialize submodules to obtain those files.

The SDL lifecycle patch under `android/patches/` is inherited historical material;
the current tested build uses the unpatched pinned SDL checkout.

## Tools

Conversion tools under `tools/` retain their authors' notices, including the
YamaArashi copyright/permission notices in applicable files. Android/Gradle and
other downloaded build dependencies have their own terms.

## Distribution status

This publication shares the source project. It does not ship a full retail ROM,
personal save, signing credential, APK, or native shared library. Development
builds compile game data; the asset-stripped FireRed distribution workflow still
requires implementation and validation. Do not describe a plain Gradle release
build as asset-free.

This is an unofficial fan project, with no endorsement or affiliation from the
game's rights holders.
