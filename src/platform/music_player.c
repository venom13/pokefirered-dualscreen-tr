// Portable MP2K sequencer adapted from Goldoire/pokeemerald-dualscreen
// and gradenGnostic/pokeemerald-multiplatform. See THIRD_PARTY_NOTICES.md.
#ifdef PORTABLE
#include "global.h"
#include "gba/m4a_internal.h"
#include "m4a.h"

extern void *const gMPlayJumpTableTemplate[];
extern const u8 gClockTable[];

#define FLOOR_DIV_POW2(a, b) ((a) >> __builtin_ctz(b))

static void ChnVolSetAsm(struct SoundChannel *chan, struct MusicPlayerTrack *track);

void SoundMainBTM(void *ptr)
{
    memset(ptr, 0, 0x40);
}

void RealClearChain(void *ptr)
{
    struct SoundChannel *chan = ptr;
    struct MusicPlayerTrack *track = chan->track;
    if (track == NULL)
        return;
    struct SoundChannel *next = chan->nextChannelPointer;
    struct SoundChannel *prev = chan->prevChannelPointer;
    if (prev != NULL)
        prev->nextChannelPointer = next;
    else
        track->chan = next;
    if (next != NULL)
        next->prevChannelPointer = prev;
    chan->track = NULL;
}

u8 ConsumeTrackByte(struct MusicPlayerTrack *track) {
    u8 *ptr = track->cmdPtr++;
    return *ptr;
}

void MPlayJumpTableCopy(MPlayFunc *mplayJumpTable) {
    for (u32 i = 0; i < 36; i++) {
        mplayJumpTable[i] = (MPlayFunc)gMPlayJumpTableTemplate[i];
    }
}

// Ends the current track. (Fine as in the Italian musical word, not English)
void ply_fine(struct MusicPlayerInfo *unused, struct MusicPlayerTrack *track) {
    for (struct SoundChannel *chan = track->chan; chan != NULL; chan = chan->nextChannelPointer) {
        if (chan->statusFlags & 0xC7) {
            chan->statusFlags |= 0x40;
        }
        RealClearChain(chan);
    }
    track->flags = 0;
}

// Sets the track's cmdPtr to the specified address.
void ply_goto(struct MusicPlayerInfo *unused, struct MusicPlayerTrack *track) {
    u8 *addr;
    memcpy(&addr, track->cmdPtr, sizeof(u8 *));
    track->cmdPtr = addr;

}

// Sets the track's cmdPtr to the specified address after backing up its current position.
void ply_patt(struct MusicPlayerInfo *unused, struct MusicPlayerTrack *track) {
    u8 level = track->patternLevel;
    if (level < 3) {
        track->patternStack[level] = track->cmdPtr + sizeof(u8 *);
        track->patternLevel++;
        ply_goto(unused, track);
    } else {
        // Stop playing this track, as an indication to the music programmer that they need to quit
        // nesting patterns so darn much.
        ply_fine(unused, track);
    }
}

// Marks the end of the current pattern, if there is one, by resetting the pattern to the
// most recently saved value.
void ply_pend(struct MusicPlayerInfo *unused, struct MusicPlayerTrack *track) {
    if (track->patternLevel != 0) {
        u8 index = --track->patternLevel;
        track->cmdPtr = track->patternStack[index];
    }
}

// Loops back until a REPT event has been reached the specified number of times
void ply_rept(struct MusicPlayerInfo *unused, struct MusicPlayerTrack *track) {
    if (*track->cmdPtr == 0) {
        // "Repeat 0 times" == loop forever
        track->cmdPtr++;
        ply_goto(unused, track);
    } else {
        u8 repeatCount = ++track->repN;
        if (repeatCount < ConsumeTrackByte(track)) {
            ply_goto(unused, track);
        } else {
            track->repN = 0;
            track->cmdPtr += sizeof(u8 *);
        }
    }
}

// Sets the note priority for new notes in this track.
void ply_prio(struct MusicPlayerInfo *unused, struct MusicPlayerTrack *track) {
    track->priority = ConsumeTrackByte(track);
}

// Sets the BPM of all tracks to the specified tempo (in beats per half-minute, because 255 as a max tempo
// kinda sucks but 510 is plenty).
void ply_tempo(struct MusicPlayerInfo *player, struct MusicPlayerTrack *track) {
    u16 bpm = ConsumeTrackByte(track);
    bpm *= 2;
    player->tempoD = bpm;
    player->tempoI = (bpm * player->tempoU) / 256;
}

void ply_keysh(struct MusicPlayerInfo *unused, struct MusicPlayerTrack *track) {
    track->keyShift = ConsumeTrackByte(track);
    track->flags |= 0xC;
}

void ply_voice(struct MusicPlayerInfo *player, struct MusicPlayerTrack *track) {
    u8 voice = *(track->cmdPtr++);
    struct ToneData *instrument = &player->tone[voice];
    track->tone = *instrument;

}

void ply_vol(struct MusicPlayerInfo *unused, struct MusicPlayerTrack *track) {
    track->vol = ConsumeTrackByte(track);
    track->flags |= 0x3;
}

void ply_pan(struct MusicPlayerInfo *unused, struct MusicPlayerTrack *track) {
    track->pan = ConsumeTrackByte(track) - 0x40;
    track->flags |= 0x3;
}

void ply_bend(struct MusicPlayerInfo *unused, struct MusicPlayerTrack *track) {
    track->bend = ConsumeTrackByte(track) - 0x40;
    track->flags |= 0xC;
}

void ply_bendr(struct MusicPlayerInfo *unused, struct MusicPlayerTrack *track) {
    track->bendRange = ConsumeTrackByte(track);
    track->flags |= 0xC;
}

void ply_lfodl(struct MusicPlayerInfo *unused, struct MusicPlayerTrack *track) {
    track->lfoDelay = ConsumeTrackByte(track);
}

void ply_modt(struct MusicPlayerInfo *unused, struct MusicPlayerTrack *track) {
    u8 type = ConsumeTrackByte(track);
    if (type != track->modT) {
        track->modT = type;
        track->flags |= 0xF;
    }
}

void ply_tune(struct MusicPlayerInfo *unused, struct MusicPlayerTrack *track) {
    track->tune = ConsumeTrackByte(track) - 0x40;
    track->flags |= 0xC;
}

void ply_port(struct MusicPlayerInfo *unused, struct MusicPlayerTrack *track) {
    // I'm really curious whether any games actually use this event...
    u8 offset = ConsumeTrackByte(track);
    REG_BASE[REG_OFFSET_NR10 + offset] = ConsumeTrackByte(track);

}

void MPlayMain(struct MusicPlayerInfo *player) {
    struct SoundInfo *mixer = (struct SoundInfo *)SOUND_INFO_PTR;

    if (player->ident != ID_NUMBER) {
        return;
    }
    player->ident = (ID_NUMBER + 1);

    if (player->MPlayMainNext != NULL) {
        player->MPlayMainNext(player->musicPlayerNext);
    }

    if (player->status & MUSICPLAYER_STATUS_PAUSE) {
        goto returnEarly;
    }
    FadeOutBody(player);
    if (player->status & MUSICPLAYER_STATUS_PAUSE) {
        goto returnEarly;
    }

    player->tempoC += player->tempoI;
    while (player->tempoC >= 150) {
        u16 trackBits = 0;

        for (u32 i = 0; i < player->trackCount; i++) {
            struct MusicPlayerTrack *currentTrack = player->tracks + i;
            struct SoundChannel *chan;
            if ((currentTrack->flags & MPT_FLG_EXIST) == 0) {
                continue;
            }
            trackBits |= (1 << i);

            chan = currentTrack->chan;
            while (chan != NULL) {
                if ((chan->statusFlags & SOUND_CHANNEL_SF_ON) == 0) {
                    ClearChain(chan);
                } else if (chan->gateTime != 0 && --chan->gateTime == 0) {
                    chan->statusFlags |= SOUND_CHANNEL_SF_STOP;
                }
                chan = chan->nextChannelPointer;
            }

            if (currentTrack->flags & MPT_FLG_START) {
                memset(currentTrack, 0, offsetof(struct MusicPlayerTrack, cmdPtr));
                currentTrack->flags = MPT_FLG_EXIST;
                currentTrack->bendRange = 2;
                currentTrack->volX = 64;
                currentTrack->lfoSpeed = 22;
                currentTrack->tone.type = 1;
            }

            while (currentTrack->wait == 0) {
                u8 event = *currentTrack->cmdPtr;
                if (event < 0x80) {
                    event = currentTrack->runningStatus;
                } else {
                    currentTrack->cmdPtr++;
                    if (event >= 0xBD) {
                        currentTrack->runningStatus = event;
                    }
                }

                if (event >= 0xCF) {
                    mixer->plynote(event - 0xCF, player, currentTrack);
                } else if (event >= 0xB1) {
                    void (*eventFunc)(struct MusicPlayerInfo *, struct MusicPlayerTrack *);
                    player->cmd = event - 0xB1;
                    eventFunc = mixer->MPlayJumpTable[player->cmd];
                    eventFunc(player, currentTrack);

                    if (currentTrack->flags == 0) {
                        goto nextTrack;
                    }
                } else {
                    currentTrack->wait = gClockTable[event - 0x80];
                }
            }

            currentTrack->wait--;

            if (currentTrack->lfoSpeed != 0 && currentTrack->mod != 0) {
                if (currentTrack->lfoDelayC != 0U) {
                    currentTrack->lfoDelayC--;
                    goto nextTrack;
                }

                currentTrack->lfoSpeedC += currentTrack->lfoSpeed;

                s8 r;
                if (currentTrack->lfoSpeedC >= 0x40U && currentTrack->lfoSpeedC < 0xC0U) {
                    r = 128 - currentTrack->lfoSpeedC;
                } else if (currentTrack->lfoSpeedC >= 0xC0U) {
                    // Unsigned -> signed casts where the value is out of range are implementation defined.
                    // Why not add a few extra lines to make behavior the same for literally everyone?
                    r = currentTrack->lfoSpeedC - 256;
                } else {
                    r = currentTrack->lfoSpeedC;
                }
                r = FLOOR_DIV_POW2(currentTrack->mod * r, 64);

                if (r != currentTrack->modM) {
                    currentTrack->modM = r;
                    if (currentTrack->modT == 0) {
                        currentTrack->flags |= MPT_FLG_PITCHG;
                    } else {
                        currentTrack->flags |= MPT_FLG_VOLCHG;
                    }
                }
            }

            nextTrack:;
        }

        player->clock++;
        if (trackBits == 0) {
            player->status = MUSICPLAYER_STATUS_PAUSE;
            goto returnEarly;
        }
        player->status = trackBits;
        player->tempoC -= 150;
    }

    u32 i = 0;

    do {
        struct MusicPlayerTrack *track = player->tracks + i;

        if ((track->flags & MPT_FLG_EXIST) == 0 || (track->flags & 0xF) == 0) {
            continue;
        }
        TrkVolPitSet((struct MusicPlayerInfo *)player, (struct MusicPlayerTrack *)track);
        for (struct SoundChannel *chan = track->chan; chan != NULL; chan = chan->nextChannelPointer) {
            if ((chan->statusFlags & 0xC7) == 0) {
                ClearChain(chan);
                continue;
            }
            u8 cgbType = chan->type & 0x7;
            if (track->flags & MPT_FLG_VOLCHG) {
                ChnVolSetAsm(chan, track);
                if (cgbType != 0) {
                    ((struct CgbChannel *)chan)->modify |= 1;
                }
            }
            if (track->flags & MPT_FLG_PITCHG) {
                s32 key = chan->key + (s8)track->keyM;
                if (key < 0) {
                    key = 0;
                }
                if (cgbType != 0) {
                    chan->frequency = mixer->MidiKeyToCgbFreq(cgbType, key, track->pitM);
                    ((struct CgbChannel *)chan)->modify |= 0x2;
                } else {
                    chan->frequency = MidiKeyToFreq((struct WaveData *)chan->wav, key, track->pitM);
                }
            }
        }
        track->flags &= ~0xF;
    }
    while(++i < player->trackCount);
returnEarly: ;
    player->ident = ID_NUMBER;
}

void TrackStop(struct MusicPlayerInfo *player, struct MusicPlayerTrack *track) {
    struct MusicPlayerTrack *mp2kTrack = (struct MusicPlayerTrack *)track;
    if (mp2kTrack->flags & 0x80) {
        for (struct SoundChannel *chan = mp2kTrack->chan; chan != NULL; chan = chan->nextChannelPointer) {
            if (chan->statusFlags != 0) {
                u8 cgbType = chan->type & 0x7;
                if (cgbType != 0) {
    struct SoundInfo *mixer = (struct SoundInfo *)SOUND_INFO_PTR;
                    mixer->CgbOscOff(cgbType);
                }
                chan->statusFlags = 0;
            }
            chan->track = NULL;
        }
        mp2kTrack->chan = NULL;
    }
}

void ChnVolSetAsm(struct SoundChannel *chan, struct MusicPlayerTrack *track) {
    s8 forcedPan = chan->rhythmPan;
    u32 rightVolume = (u8)(forcedPan + 128) * chan->velocity * track->volMR / 128 / 128;
    if (rightVolume > 0xFF) {
        rightVolume = 0xFF;
    }
    chan->rightVolume = rightVolume;

    u32 leftVolume = (u8)(127 - forcedPan) * chan->velocity * track->volML / 128 / 128;
    if (leftVolume > 0xFF) {
        leftVolume = 0xFF;
    }
    chan->leftVolume = leftVolume;
}

void ply_note(u32 clock, struct MusicPlayerInfo *player, struct MusicPlayerTrack *track) { // ply_note
    struct SoundInfo *mixer = (struct SoundInfo *)SOUND_INFO_PTR;

    // A note can be anywhere from 1 to 4 bytes long. First is always the note length...
    track->gateTime = gClockTable[clock];
    if (*track->cmdPtr < 0x80) {
        // Then the note name...
        track->key = *(track->cmdPtr++);
        if (*track->cmdPtr < 0x80) {
            // Then the velocity...
            track->velocity = *(track->cmdPtr++);
            if (*track->cmdPtr < 0x80) {
                // Then a number to add ticks to get exotic or more precise note lengths without TIE.
                track->gateTime += *(track->cmdPtr++);
            }
        }
    }

    // sp14
    s8 forcedPan = 0;
    // First r4, then r9
    struct ToneData *instrument = &track->tone;
    // sp8
    u8 key = track->key;
    u8 type = instrument->type;

    if (type & (TONEDATA_TYPE_RHY | TONEDATA_TYPE_SPL)) {
        u8 instrumentIndex;
        if (instrument->type & TONEDATA_TYPE_SPL) {
            instrumentIndex = instrument->keySplitTable[track->key];
        } else {
            instrumentIndex = track->key;
        }

        instrument = (struct ToneData *)instrument->wav + instrumentIndex;
        if (instrument->type & (TONEDATA_TYPE_RHY | TONEDATA_TYPE_SPL)) {
            return;
        }
        if (type & TONEDATA_TYPE_RHY) {
            if (instrument->pan_sweep & 0x80) {
                forcedPan = ((s8)(instrument->pan_sweep & 0x7F) - 0x40) * 2;
            }
            key = instrument->key;
        }
    }

    // sp10
    u32 priority = player->priority + track->priority;
    if (priority > 0xFF) {
        priority = 0xFF;
    }

    u8 cgbType = instrument->type & TONEDATA_TYPE_CGB;
    struct SoundChannel *chan;

    if (cgbType != 0) {
        if (mixer->cgbChans == NULL) {
            return;
        }
        // There's only one CgbChannel of a given type, so we don't need to loop to find it.
        chan = (struct SoundChannel *)(mixer->cgbChans + cgbType - 1);

        // If this channel is running and not stopped,
        if ((chan->statusFlags & SOUND_CHANNEL_SF_ON)
        && (chan->statusFlags & SOUND_CHANNEL_SF_STOP) == 0) {
            // then make sure this note is higher priority (or same priority but from a later track).
            if (chan->priority > priority || (chan->priority == priority && (uintptr_t)chan->track < (uintptr_t)track)) {
                return;
            }
        }
    } else {
        u32 p = priority;
        struct MusicPlayerTrack *t = track;
        bool32 foundStoppingChannel = FALSE;
        chan = NULL;
        u8 maxChans = mixer->maxChans;
        struct SoundChannel *currChan = mixer->chans;

        for (u32 i = 0; i < maxChans; i++, currChan++) {
            if ((currChan->statusFlags & SOUND_CHANNEL_SF_ON) == 0) {
                // Hey, we found a completely inactive channel! Let's use that.
                chan = currChan;
                break;
            }

            if (currChan->statusFlags & SOUND_CHANNEL_SF_STOP && !foundStoppingChannel) {
                // In the absence of a completely finalized channel, we can take over one that's about to
                // finalize. That's a tier above any channel that's currently playing a note.
                foundStoppingChannel = TRUE;
                p = currChan->priority;
                t = currChan->track;
                chan = currChan;
            } else if ((currChan->statusFlags & SOUND_CHANNEL_SF_STOP && foundStoppingChannel)
                   || ((currChan->statusFlags & SOUND_CHANNEL_SF_STOP) == 0 && !foundStoppingChannel)) {
                // The channel we're checking is on the same tier, so check the priority and track order
                if (currChan->priority < p) {
                    p = currChan->priority;
                    t = currChan->track;
                    chan = currChan;
                } else if (currChan->priority == p && (uintptr_t)currChan->track > (uintptr_t)t) {
                    t = currChan->track;
                    chan = currChan;
                } else if (currChan->priority == p && currChan->track == t) {
                    chan = currChan;
                }
            }
        }

    }

    if (chan == NULL) {
        return;
    }
    ClearChain(chan);

    chan->prevChannelPointer = NULL;
    chan->nextChannelPointer = track->chan;
    if (track->chan != NULL) {
        track->chan->prevChannelPointer = chan;
    }
    track->chan = chan;
    chan->track = track;

    track->lfoDelayC = track->lfoDelay;
    if (track->lfoDelay != 0) {
        ClearModM((struct MusicPlayerTrack *)track);
    }
    TrkVolPitSet((struct MusicPlayerInfo *)player, (struct MusicPlayerTrack *)track);

    chan->gateTime = track->gateTime;
    chan->midiKey = track->key;
    chan->velocity = track->velocity;
    chan->priority = priority;
    chan->key = key;
    chan->rhythmPan = forcedPan;
    chan->type = instrument->type;
    chan->wav = instrument->wav;
    chan->attack = instrument->attack;
    chan->decay = instrument->decay;
    chan->sustain = instrument->sustain;
    chan->release = instrument->release;
    chan->pseudoEchoVolume = track->pseudoEchoVolume;
    chan->pseudoEchoLength = track->pseudoEchoLength;
    ChnVolSetAsm(chan, track);

    // Avoid promoting keyShiftCalculated to u8 by splitting the addition into a separate statement
    s32 transposedKey = chan->key;
    transposedKey += (s8)track->keyM;
    if (transposedKey < 0) {
        transposedKey = 0;
    }

    if (cgbType != 0) {
        //struct CgbChannel *cgbChan = (struct CgbChannel *)chan;
        ((struct CgbChannel *)chan)->length = instrument->length;
        if (instrument->pan_sweep & 0x80 || (instrument->pan_sweep & 0x70) == 0) {
            ((struct CgbChannel *)chan)->sweep = 8;
        } else {
            ((struct CgbChannel *)chan)->sweep = instrument->pan_sweep;
        }

        chan->frequency = mixer->MidiKeyToCgbFreq(cgbType, transposedKey, track->pitM);
    } else {
        chan->count = track->unk_3C;
        chan->frequency = MidiKeyToFreq((struct WaveData *)chan->wav, transposedKey, track->pitM);
    }

    chan->statusFlags = SOUND_CHANNEL_SF_START;
    track->flags &= ~0xF;
}

void ply_endtie(struct MusicPlayerInfo *unused, struct MusicPlayerTrack *track) {
    u8 key = *track->cmdPtr;
    if (key < 0x80) {
        track->key = key;
        track->cmdPtr++;
    } else {
        key = track->key;
    }

    struct SoundChannel *chan = track->chan;
    while (chan != NULL) {
        if (chan->statusFlags & 0x83 && (chan->statusFlags & 0x40) == 0 && chan->midiKey == key) {
            chan->statusFlags |= 0x40;
            return;
        }
        chan = chan->nextChannelPointer;
    }
}

void ply_lfos(struct MusicPlayerInfo *unused, struct MusicPlayerTrack *track) {
    track->lfoSpeed = *(track->cmdPtr++);
    if (track->lfoSpeed == 0) {
        ClearModM((struct MusicPlayerTrack *)track);
    }
}

void ply_mod(struct MusicPlayerInfo *unused, struct MusicPlayerTrack *track) {
    track->mod = *(track->cmdPtr++);
    if (track->mod == 0) {
        ClearModM((struct MusicPlayerTrack *)track);
    }
}


#endif // PORTABLE
