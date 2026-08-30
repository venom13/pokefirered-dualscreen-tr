#!/usr/bin/env python3
"""Package an unsigned release APK with ROM holes and an explicit signing key.

Requires pyelftools==0.32, Android build-tools, JDK 17, and a local reference ROM.
Passwords are read by apksigner from the named environment variables, never
printed or placed on the command line. No debug-key fallback is allowed.
"""
import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import zipfile

from make_asset_holes import build

LIBRARY = "lib/armeabi-v7a/libmain.so"
MANIFEST = "assets/asset_manifest.bin"


def run(*args):
    subprocess.run([str(arg) for arg in args], check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("apk", "unstripped", "rom", "build-tools", "keystore", "alias", "out"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    output = Path(args.out).resolve()
    if output.exists():
        parser.error("output already exists; choose a new filename")
    if not os.environ.get("FIRERED_STORE_PASSWORD") or not os.environ.get("FIRERED_KEY_PASSWORD"):
        parser.error("set FIRERED_STORE_PASSWORD and FIRERED_KEY_PASSWORD")
    build_tools = Path(args.build_tools)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="firered-release-") as directory:
        temp = Path(directory)
        stripped = temp / "input.so"
        holed = temp / "holed.so"
        manifest = temp / "asset_manifest.bin"
        repacked = temp / "repacked.apk"
        aligned = temp / "aligned.apk"
        signed = temp / "signed.apk"
        with zipfile.ZipFile(args.apk) as apk:
            names = apk.namelist()
            if len(names) != len(set(names)) or LIBRARY not in names or MANIFEST in names:
                raise ValueError("expected an unmodified, single-copy ARMv7 build")
            if any(name.lower().endswith((".gba", ".sav", ".jks", ".keystore", ".p12", ".pfx", ".key", ".pem"))
                   for name in names):
                raise ValueError("private or unapproved payload in APK")
            stripped.write_bytes(apk.read(LIBRARY))
            build(args.unstripped, args.rom, stripped, holed, manifest)
            with zipfile.ZipFile(repacked, "w") as dest:
                for info in apk.infolist():
                    # A fresh apksigner signature is added after zip alignment.
                    if info.filename.upper().startswith("META-INF/") and info.filename.upper().endswith(
                            (".RSA", ".DSA", ".EC", ".SF", ".MF")):
                        continue
                    data = holed.read_bytes() if info.filename == LIBRARY else apk.read(info)
                    if info.filename == "resources.arsc" or info.filename.endswith(".so"):
                        info.compress_type = zipfile.ZIP_STORED
                    dest.writestr(info, data)
                dest.writestr(MANIFEST, manifest.read_bytes(), compress_type=zipfile.ZIP_DEFLATED)
        run(build_tools / "zipalign", "-P", "16", "-f", "4", repacked, aligned)
        run(build_tools / "apksigner", "sign", "--ks", args.keystore,
            "--ks-key-alias", args.alias,
            "--ks-pass", "env:FIRERED_STORE_PASSWORD",
            "--key-pass", "env:FIRERED_KEY_PASSWORD",
            "--v4-signing-enabled", "false", "--out", signed, aligned)
        run(build_tools / "apksigner", "verify", "--verbose", "--print-certs", signed)
        run(build_tools / "zipalign", "-c", "-P", "16", "4", signed)
        with zipfile.ZipFile(signed) as apk:
            if apk.read(LIBRARY) != holed.read_bytes() or apk.read(MANIFEST) != manifest.read_bytes():
                raise ValueError("signed APK payload differs")
        # Publish locally only after every check succeeds; refuse overwrites.
        with output.open("xb") as dest:
            dest.write(signed.read_bytes())
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    print(f"SHA256: {digest}  {output.name}")


if __name__ == "__main__":
    main()
