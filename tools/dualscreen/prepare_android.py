#!/usr/bin/env python3
"""Prepare decompilation resources for the native Android build, without a ROM build."""

import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
BINARY_INCLUDE = re.compile(
    r'\bINCBIN_[A-Z0-9_]+\s*\(([^)]*)\)|\.incbin\s+"([^"]+)"'
)
SOURCE_SUFFIXES = {".c", ".h", ".s", ".inc"}


def run(*args):
    subprocess.run(args, cwd=ROOT, check=True)


def binary_includes(source):
    for match in BINARY_INCLUDE.finditer(source):
        if match.group(1) is not None:
            # INCBIN can concatenate several files, including on multiple lines.
            yield from re.findall(r'"([^"]+)"', match.group(1))
        else:
            yield match.group(2)


def asset_targets():
    """Use the upstream Makefile for conversions; only collect its inputs here."""
    targets = set()
    for folder in ("src", "include", "data", "sound"):
        for path in (ROOT / folder).rglob("*"):
            if path.suffix not in SOURCE_SUFFIXES or not path.is_file():
                continue
            for target in binary_includes(path.read_text(errors="replace")):
                # GBA assets already tracked by upstream are inputs, not a request
                # to build a retail ROM. Never request a .gba/.elf target from make.
                if Path(target).suffix in {".gba", ".elf"}:
                    if not (ROOT / target).is_file():
                        raise RuntimeError(f"Missing upstream input: {target}")
                    continue
                if not target.startswith(("graphics/", "data/", "sound/")):
                    raise RuntimeError(f"Unexpected binary-include path: {target}")
                targets.add(target)
    targets.update(str(path.relative_to(ROOT).with_suffix(".s"))
                   for path in (ROOT / "sound/songs/midi").glob("*.mid"))
    return sorted(targets)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs", type=int, default=min(os.cpu_count() or 2, 8))
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error("--jobs must be positive")
    for command in ("make", "cc", "c++", "pkg-config"):
        if not shutil.which(command):
            parser.error(f"Missing build dependency: {command}")
    if not (ROOT / "android/SDL2/CMakeLists.txt").is_file():
        parser.error("SDL is missing. Run git submodule update --init --recursive.")
    run("pkg-config", "--exists", "libpng")
    jobs = f"-j{args.jobs}"
    run("make", "-f", "make_tools.mk", jobs)
    options = ("GAME_VERSION=FIRERED", "GAME_REVISION=1", "COMPARE=0",
               "NODEP=1", "SETUP_PREREQS=0")
    run("make", *options, "generated")
    # "generated" creates the global map tables, but per-map includes normally
    # hang off the GBA object rules. Request one output per map: its recipe also
    # writes events.inc/connections.inc. Avoid parallel duplicate recipes.
    maps = sorted(str(path.relative_to(ROOT).with_name("header.inc"))
                  for path in (ROOT / "data/maps").glob("*/map.json"))
    for start in range(0, len(maps), 150):
        run("make", *options, jobs, *maps[start:start + 150])
    targets = asset_targets()
    # Bound command-line length on macOS and Linux.
    for start in range(0, len(targets), 150):
        run("make", *options, jobs, *targets[start:start + 150])
    print(f"Prepared {len(targets)} Android asset targets; no retail ROM was built.")


if __name__ == "__main__":
    try:
        main()
    except (subprocess.CalledProcessError, RuntimeError) as error:
        print(f"Preparation failed: {error}", file=sys.stderr)
        sys.exit(1)
