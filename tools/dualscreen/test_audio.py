#!/usr/bin/env python3
"""Run the built ARMv7 audio engine and game songs without a device or a ROM.

Requires unicorn and pyelftools, plus an unstripped local libmain.so. Android
and SDL output calls are intercepted; the sequencer, mixer, and game assets are
the actual APK code/data. No game state or save is changed.
"""
import argparse
import math
from pathlib import Path
import re
import struct

from elftools.elf.elffile import ELFFile
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import (
    UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
    UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_C1_C0_2,
    UC_ARM_REG_FPEXC,
)

ROOT = Path(__file__).resolve().parents[2]
BASE, STUBS, STOP, STACK = 0x10000000, 0x70000000, 0x71000000, 0x72000000


class Engine:
    def __init__(self, path):
        self.uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
        self.skipped = False
        self.real_output = False
        self.frames = []
        self.hooks = {}
        with path.open('rb') as source:
            elf = ELFFile(source)
            assert elf['e_machine'] == 'EM_ARM'
            segments = [s for s in elf.iter_segments() if s['p_type'] == 'PT_LOAD']
            size = max(s['p_vaddr'] + s['p_memsz'] for s in segments)
            self.uc.mem_map(BASE, (size + 4095) & ~4095)
            for segment in segments:
                self.uc.mem_write(BASE + segment['p_vaddr'], segment.data())
            self.symbols = {
                s.name: BASE + s['st_value']
                for s in elf.get_section_by_name('.symtab').iter_symbols()
                if s['st_shndx'] != 'SHN_UNDEF'
            }
            self.uc.mem_map(STUBS, 0x10000)
            imports = {}
            for section in elf.iter_sections():
                if section['sh_type'] != 'SHT_REL':
                    continue
                symbols = elf.get_section(section['sh_link'])
                for reloc in section.iter_relocations():
                    address = BASE + reloc['r_offset']
                    addend = self.u32(address)
                    kind = reloc['r_info_type']
                    if kind == 23:  # R_ARM_RELATIVE
                        value = BASE + addend
                    else:
                        symbol = symbols.get_symbol(reloc['r_info_sym'])
                        if symbol['st_shndx'] == 'SHN_UNDEF':
                            if symbol.name not in imports:
                                target = STUBS + len(imports) * 4
                                imports[symbol.name] = target
                                self.hooks[target] = symbol.name
                                self.uc.mem_write(target, b'\x1e\xff\x2f\xe1')  # bx lr
                            target = imports[symbol.name]
                        else:
                            target = BASE + symbol['st_value']
                        if kind == 2:  # R_ARM_ABS32
                            value = target + addend
                        elif kind in (21, 22):  # GLOB_DAT / JUMP_SLOT
                            value = target
                        elif kind == 3:
                            value = target + addend - address
                        else:
                            raise AssertionError(f'Unhandled ARM relocation {kind}')
                    self.write32(address, value)
        self.uc.mem_map(STOP, 4096)
        self.uc.mem_map(STACK, 0x200000)
        self.uc.reg_write(UC_ARM_REG_C1_C0_2, 0xF << 20)
        self.uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
        for name in ('Platform_SkipAudioFrame', 'Platform_QueueAudio'):
            self.hooks[self.symbols[name] & ~1] = name
        # Only intercept known boundaries, leaving the audio code untouched.
        self.uc.hook_add(UC_HOOK_CODE, self.intercept, begin=STUBS, end=STUBS + 0xFFFF)
        for name in ('Platform_SkipAudioFrame', 'Platform_QueueAudio'):
            address = self.symbols[name] & ~1
            self.uc.hook_add(UC_HOOK_CODE, self.intercept, begin=address, end=address)

    def u32(self, address):
        return struct.unpack('<I', self.uc.mem_read(address, 4))[0]

    def write32(self, address, value):
        self.uc.mem_write(address, struct.pack('<I', value & 0xFFFFFFFF))

    def intercept(self, uc, address, size, data):
        name = self.hooks[address]
        a, b, c = [uc.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2)]
        result = 0
        if name == 'Platform_QueueAudio' and self.real_output:
            return  # Execute the real volume/resampling path into SDL_QueueAudio.
        if name == 'Platform_SkipAudioFrame':
            result = int(self.skipped)
        elif name == 'Platform_QueueAudio':
            assert b == 701 * 2 * 4, b
            samples = struct.unpack('<1402f', uc.mem_read(a, b))
            assert all(math.isfinite(x) and -1 <= x <= 1 for x in samples)
            self.frames.append(samples)
        elif name == 'SDL_QueueAudio':
            assert a == 1 and c % 8 == 0
            samples = struct.unpack(f'<{c // 4}f', uc.mem_read(b, c))
            assert all(math.isfinite(x) and -1 <= x <= 1 for x in samples)
            self.frames.append(samples)
        elif name in ('memcpy', 'memmove', '__memcpy_chk', '__memmove_chk') or name.startswith('__aeabi_memcpy'):
            uc.mem_write(a, bytes(uc.mem_read(b, c)))
            result = a
        elif name in ('memset', '__memset_chk'):
            uc.mem_write(a, bytes([b & 255]) * c)
            result = a
        elif name.startswith('__aeabi_memclr'):
            uc.mem_write(a, bytes(b))
        elif name.startswith('__aeabi_memset'):
            uc.mem_write(a, bytes([c & 255]) * b)
        elif name in ('puts', 'printf', '__android_log_print', 'SDL_Log'):
            pass
        else:
            raise AssertionError(f'Unexpected external call: {name}')
        uc.reg_write(UC_ARM_REG_R0, result)
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

    def call(self, name, *args):
        for reg, value in zip((UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3), args):
            self.uc.reg_write(reg, value & 0xFFFFFFFF)
        sp = STACK + 0x1FFF00
        for i, value in enumerate(args[4:]):
            self.write32(sp + i * 4, value)
        self.uc.reg_write(UC_ARM_REG_SP, sp)
        self.uc.reg_write(UC_ARM_REG_LR, STOP)
        self.uc.emu_start(self.symbols[name], STOP, timeout=10_000_000)
        assert self.uc.reg_read(UC_ARM_REG_PC) == STOP, f'{name} did not return'
        return self.uc.reg_read(UC_ARM_REG_R0)

    def tick(self, frames):
        for _ in range(frames):
            # FireRed's VCount submits the previous mix, then VBlank mixes.
            self.call('m4aSoundVSync')
            self.call('m4aSoundMain')

    def reset(self):
        self.skipped = False
        self.call('m4aSoundInit')
        self.frames.clear()
        assert self.u32(self.symbols['gSoundInfo']) == 0x68736D53

    def check_boot(self):
        # Stop at the first input read: AgbMain must have completed sound/heap/
        # callback initialization without waiting for a nonexistent GBA scanline.
        address = self.symbols['Platform_GetKeyInput'] & ~1
        hook = self.uc.hook_add(UC_HOOK_CODE, lambda uc, *_: uc.emu_stop(), begin=address, end=address)
        self.uc.reg_write(UC_ARM_REG_SP, STACK + 0x1FFF00)
        self.uc.reg_write(UC_ARM_REG_LR, STOP)
        self.uc.emu_start(self.symbols['AgbMain'], STOP, timeout=10_000_000)
        self.uc.hook_del(hook)
        assert self.uc.reg_read(UC_ARM_REG_PC) == address, 'AgbMain did not reach its game loop'
        assert self.u32(self.symbols['gSoundInfo']) == 0x68736D53
        print('AgbMain: reached the game loop with sound initialized', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('library', type=Path)
    parser.add_argument('--all-songs', action='store_true')
    parser.add_argument('--song-frames', type=int, default=120)
    args = parser.parse_args()
    engine = Engine(args.library)
    engine.check_boot()
    assert not engine.call('IsPokemonCryPlaying', 0)
    engine.call('m4aMPlayStop', 0)
    songs = {
        name: int(number) for name, number in re.findall(
            r'^#define\s+(\w+)\s+(\d+)\b',
            (ROOT / 'include/constants/songs.h').read_text(), re.M)
    }
    names = [n for n in songs if n.startswith(('MUS_', 'SE_')) and songs[n] > 0] if args.all_songs else [
        'MUS_TITLE', 'MUS_PALLET', 'MUS_VIRIDIAN_FOREST', 'MUS_VS_WILD', 'SE_SELECT', 'SE_WIN_OPEN',
    ]
    for name in names:
        assert name in songs, name
        engine.reset()
        engine.call('m4aSongNumStart', songs[name])
        engine.tick(args.song_frames)
        peak = max(abs(x) for frame in engine.frames for x in frame)
        assert peak > 0.001, (name, 'silent')
        print(f'{name}: {len(engine.frames)} stereo frames, peak {peak:.3f}', flush=True)

    # Normal, fainting and reversed move cries exercise compressed sample
    # boundaries and the completion check that was disabled with the old stubs.
    for species in (1, 4, 7, 25, 129, 150, 277):
        for mode in (0, 4, 5, 9):
            engine.reset()
            engine.call('PlayCryInternal', species, 0, 120, 10, mode)
            engine.tick(2)
            player = engine.u32(engine.symbols['gMPlay_PokemonCry'])
            assert engine.call('IsPokemonCryPlaying', player), (species, mode, 'never started')
            engine.tick(178)
            peak = max(abs(x) for frame in engine.frames for x in frame)
            assert peak > 0.001, (species, mode, 'silent cry')
            assert not engine.call('IsPokemonCryPlaying', player), (species, mode, 'never finished')
        print(f'Cry species {species}: normal, reverse and faint checks passed', flush=True)

    engine.reset()
    engine.call('m4aSongNumStart', songs['MUS_VS_WILD'])
    engine.call('PlayCryInternal', 1, -63, 120, 10, 0)
    engine.call('PlayCryInternal', 25, 63, 120, 10, 4)
    engine.call('m4aSongNumStart', songs['SE_SELECT'])
    engine.tick(120)
    assert max(abs(x) for frame in engine.frames for x in frame) > 0.001

    # A skipped fast-forward frame must advance neither player nor DMA cycle.
    before = engine.u32(engine.symbols['gMPlayInfo_BGM'] + 16)
    dma = bytes(engine.uc.mem_read(engine.symbols['gSoundInfo'] + 4, 1))
    count = len(engine.frames)
    engine.skipped = True
    engine.tick(8)
    assert len(engine.frames) == count
    assert engine.u32(engine.symbols['gMPlayInfo_BGM'] + 16) == before
    assert bytes(engine.uc.mem_read(engine.symbols['gSoundInfo'] + 4, 1)) == dma
    engine.skipped = False
    engine.tick(8)
    assert len(engine.frames) == count + 8

    # Pausing the driver must stop output, then resume on the same live song.
    engine.call('m4aSoundVSyncOff')
    count = len(engine.frames)
    engine.tick(4)
    assert len(engine.frames) == count
    engine.call('m4aSoundVSyncOn')
    engine.tick(4)
    assert len(engine.frames) == count + 4

    # Reinitialization (soft reset) must be safe, with no stale cry pointers.
    for _ in range(3):
        engine.reset()
        engine.tick(4)
        assert all(x == 0 for frame in engine.frames for x in frame)

    # Exercise the SDL host's real volume and fast-forward resampler as well.
    engine.real_output = True
    engine.write32(engine.symbols['sdlAudioDevice'], 1)

    def output(volume, speed=1, sped_up=False):
        engine.reset()
        engine.uc.mem_write(engine.symbols['sPlatformSettings'] + 5, bytes([volume]))
        engine.uc.mem_write(engine.symbols['sPlatformSettings'] + 12, bytes([sped_up]))
        engine.uc.mem_write(engine.symbols['timeScale'], struct.pack('<d', speed))
        engine.call('m4aSongNumStart', songs['MUS_TITLE'])
        engine.tick(12)
        return [sample for frame in engine.frames for sample in frame]

    full = output(10)
    half = output(5)
    muted = output(0)
    assert max(abs(x) for x in full) > 0.001
    assert all(abs(a * 0.5 - b) < 1e-6 for a, b in zip(full, half))
    assert all(x == 0 for x in muted)
    assert output(10, 4, False) == full
    for speed in (2, 3, 4):
        accelerated = output(10, speed, True)
        assert len(accelerated) == 12 * (701 // speed) * 2
        assert max(abs(x) for x in accelerated) > 0.001
    print('SDL output: volume 0/50/100%, normal music and 2x/3x/4x resampling passed.')
    print('Audio initialization, non-silent output, fast-forward and reset checks passed.')


if __name__ == '__main__':
    main()
