#!/usr/bin/env python3
"""Remove ROM-matching data ranges from a release libmain.so.

Data-symbol ranges in the built library whose bytes appear
verbatim in the retail FireRed ROM (the decomp is byte-matching, so many
assets do) is recorded in a manifest and zeroed in the output library.
At each launch the app restores those ranges from the user's own ROM,
which reproduces the original library exactly.

Usage:
  make_asset_holes.py analyze <libmain.so> <rom.gba>  (rom is always argv[3])
  make_asset_holes.py build <unstripped.so> <rom.gba> <in.so> <out.so> <manifest.bin>

Manifest format (little endian): ROM SHA-1 (20 bytes), target library's
GNU build id (20 bytes; runtime refuses to fill a mismatched library),
u32 count, then per entry u32 vaddr, u32 size, u32 romOffset.
"""
import hashlib
import struct
import sys

from elftools.elf.elffile import ELFFile

MIN_SIZE = 32


def collect_entries(so_path, rom):
    entries = []
    matched = unmatched = 0
    with open(so_path, "rb") as f:
        elf = ELFFile(f)
        symtab = elf.get_section_by_name(".symtab")
        if symtab is None:
            sys.exit("no .symtab: use the unstripped libmain.so")
        rodata = [s for s in elf.iter_sections()
                  if s.name in (".rodata", ".data.rel.ro", ".data", "script_data")]
        ranges = [(s["sh_addr"], s["sh_addr"] + s["sh_size"], s) for s in rodata]

        def section_for(addr):
            for lo, hi, s in ranges:
                if lo <= addr < hi:
                    return lo, hi, s
            return None, None, None

        # Some data comes from assembly objects whose symbols carry no size;
        # derive effective sizes from the distance to the next symbol.
        addr_syms = []
        for sym in symtab.iter_symbols():
            addr = sym["st_value"]
            lo, hi, section = section_for(addr)
            if section is not None:
                addr_syms.append((addr, sym["st_size"], hi))
        addr_syms.sort()
        candidates = []
        for i, (addr, size, section_end) in enumerate(addr_syms):
            if size == 0:
                nxt = section_end
                for j in range(i + 1, len(addr_syms)):
                    if addr_syms[j][0] > addr:
                        nxt = min(addr_syms[j][0], section_end)
                        break
                size = nxt - addr
            size = min(size, section_end - addr)
            if size >= MIN_SIZE:
                candidates.append((addr, size))
        # Drop candidates fully contained in a previous one (aliases).
        candidates.sort()
        pruned = []
        for addr, size in candidates:
            if pruned and addr + size <= pruned[-1][0] + pruned[-1][1]:
                continue
            pruned.append((addr, size))

        # ARM32 uses REL relocations with in-place addends: any relocation
        # target word in .data holds a link-time address the loader rewrites,
        # so it must never be zeroed or filled from ROM. Split candidate
        # ranges around every relocation target.
        reloc_offsets = []
        for relsec_name in (".rel.dyn", ".rela.dyn", ".rel.plt", ".rela.plt"):
            relsec = elf.get_section_by_name(relsec_name)
            if relsec is not None:
                reloc_offsets.extend(r["r_offset"] for r in relsec.iter_relocations())
        reloc_offsets.sort()
        import bisect

        def split_around_relocs(addr, size):
            parts = []
            start = addr
            end = addr + size
            i = bisect.bisect_left(reloc_offsets, start - 3)
            while i < len(reloc_offsets) and reloc_offsets[i] < end:
                r = reloc_offsets[i]
                if r + 4 > start:
                    if r > start:
                        parts.append((start, r - start))
                    start = r + 4
                i += 1
            if end > start:
                parts.append((start, end - start))
            return [(a, s) for a, s in parts if s >= MIN_SIZE]

        pruned = [part for addr, size in pruned
                  for part in split_around_relocs(addr, size)]

        def match_range(data, addr):
            # Whole-range match, else strip alignment padding, else split:
            # derived ranges often span several objects and padding gaps.
            rom_off = rom.find(data)
            if rom_off >= 0:
                return [(addr, len(data), rom_off)]
            stripped = data.rstrip(b"\x00")
            if MIN_SIZE <= len(stripped) < len(data):
                rom_off = rom.find(stripped)
                if rom_off >= 0:
                    return [(addr, len(stripped), rom_off)]
            if len(data) < MIN_SIZE * 2:
                return []
            mid = (len(data) // 2) & ~3
            return match_range(data[:mid], addr) + match_range(data[mid:], addr + mid)

        for addr, size in pruned:
            lo, hi, section = section_for(addr)
            data = section.data()[addr - lo : addr - lo + size]
            if len(data) != size:
                continue
            found = match_range(data, addr)
            for faddr, fsize, frow in found:
                entries.append((faddr, fsize, frow))
                matched += fsize
            unmatched += size - sum(f[1] for f in found)
    entries.sort()
    # Merge adjacent/overlapping ranges with contiguous ROM offsets.
    merged = []
    for addr, size, rom_off in entries:
        if merged:
            paddr, psize, prom = merged[-1]
            if addr <= paddr + psize and rom_off == prom + (addr - paddr):
                merged[-1] = (paddr, max(paddr + psize, addr + size) - paddr, prom)
                continue
        merged.append((addr, size, rom_off))
    return merged, matched, unmatched


def vaddr_to_file_offset(elf, vaddr):
    for seg in elf.iter_segments():
        if seg["p_type"] != "PT_LOAD":
            continue
        if seg["p_vaddr"] <= vaddr < seg["p_vaddr"] + seg["p_filesz"]:
            return vaddr - seg["p_vaddr"] + seg["p_offset"]
    return None


ROM_SHA1 = "dd5945db9b930750cb39d00c84da8571feebf417"
ROM_SIZE = 16 * 1024 * 1024


def build_id(path):
    with open(path, "rb") as f:
        elf = ELFFile(f)
        if elf.elfclass != 32 or not elf.little_endian or elf["e_machine"] != "EM_ARM":
            raise ValueError("expected a little-endian ARM32 library")
        section = elf.get_section_by_name(".note.gnu.build-id")
        if section is not None:
            for note in section.iter_notes():
                if note["n_type"] == "NT_GNU_BUILD_ID":
                    value = bytes.fromhex(note["n_desc"])
                    if len(value) == 20:
                        return value
    raise ValueError("expected a 20-byte GNU build id")


def file_range(elf, addr, size):
    for seg in elf.iter_segments():
        if (seg["p_type"] == "PT_LOAD" and seg["p_vaddr"] <= addr
                and addr + size <= seg["p_vaddr"] + seg["p_filesz"]):
            return addr - seg["p_vaddr"] + seg["p_offset"]
    raise ValueError(f"range {addr:#x}+{size:#x} is not file-backed")


def build(unstripped, rom_path, input_path, output_path, manifest_path):
    from pathlib import Path

    rom = Path(rom_path).read_bytes()
    if len(rom) != ROM_SIZE or hashlib.sha1(rom).hexdigest() != ROM_SHA1:
        raise ValueError("requires the exact USA/Europe FireRed Rev 1 ROM")
    target_id = build_id(input_path)
    if target_id != build_id(unstripped):
        raise ValueError("stripped and unstripped library build ids differ")
    entries, _, unmatched = collect_entries(unstripped, rom)
    if not entries:
        raise ValueError("no matching data ranges")
    original = Path(input_path).read_bytes()
    holed = bytearray(original)
    previous_end = 0
    with open(input_path, "rb") as f:
        elf = ELFFile(f)
        for addr, size, offset in entries:
            if size <= 0 or addr < previous_end or offset + size > len(rom):
                raise ValueError("overlapping or out-of-bounds asset range")
            file_offset = file_range(elf, addr, size)
            if original[file_offset:file_offset + size] != rom[offset:offset + size]:
                raise ValueError("asset range does not reproduce the input library")
            holed[file_offset:file_offset + size] = bytes(size)
            previous_end = addr + size

        # A public package must reproduce the original, including every byte
        # outside the holes. Never publish if this round trip fails.
        restored = bytearray(holed)
        for addr, size, offset in entries:
            file_offset = file_range(elf, addr, size)
            restored[file_offset:file_offset + size] = rom[offset:offset + size]
        if restored != original:
            raise ValueError("byte-exact ROM restoration failed")

    manifest = bytes.fromhex(ROM_SHA1) + target_id + struct.pack("<I", len(entries))
    manifest += b"".join(struct.pack("<III", *entry) for entry in entries)
    Path(output_path).write_bytes(holed)
    Path(manifest_path).write_bytes(manifest)
    removed = sum(entry[1] for entry in entries)
    print(f"Removed {removed:,} ROM-matching bytes in {len(entries):,} ranges.")
    print(f"Unmatched candidate bytes retained: {unmatched:,}.")
    print("Byte-exact restoration: PASS. This is not a complete copyright audit.")
    return entries


def main():
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["analyze", "build"])
    parser.add_argument("unstripped")
    parser.add_argument("rom")
    parser.add_argument("outputs", nargs="*")
    args = parser.parse_args()
    if args.mode == "analyze":
        from pathlib import Path
        rom = Path(args.rom).read_bytes()
        if len(rom) != ROM_SIZE or hashlib.sha1(rom).hexdigest() != ROM_SHA1:
            parser.error("requires the exact USA/Europe FireRed Rev 1 ROM")
        entries, matched, unmatched = collect_entries(args.unstripped, rom)
        print(f"{len(entries)} ranges; {matched} matched bytes; {unmatched} unmatched bytes")
    else:
        if len(args.outputs) != 3:
            parser.error("build requires input.so output.so manifest.bin")
        build(args.unstripped, args.rom, *args.outputs)


if __name__ == "__main__":
    main()
