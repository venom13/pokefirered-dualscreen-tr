// Portable stereo mixer for FireRed's MP2K player. The envelope and reverb
// follow the original driver; SDL replaces GBA DMA and hardware scanline waits.
#ifdef PORTABLE
#include "global.h"
#include "gba/m4a_internal.h"
#include "platform.h"
#include "cgb_audio.h"

extern const s8 gDeltaEncodingTable[];

static bool32 TickEnvelope(struct SoundChannel *chan)
{
    u8 status = chan->statusFlags;
    u32 volume = chan->envelopeVolume;

    if (!(status & SOUND_CHANNEL_SF_ON))
        return FALSE;
    if (status & SOUND_CHANNEL_SF_START)
    {
        if ((status & SOUND_CHANNEL_SF_STOP) || chan->wav == NULL
         || chan->count >= chan->wav->size)
            goto stop;
        chan->count = chan->wav->size - chan->count;
        chan->fw = 0;
        volume = 0;
        status = SOUND_CHANNEL_SF_ENV_ATTACK;
        if ((chan->wav->status & 0xC000) && chan->wav->loopStart < chan->wav->size)
            status |= SOUND_CHANNEL_SF_LOOP;
    }
    else if (status & SOUND_CHANNEL_SF_IEC)
    {
        if (chan->pseudoEchoLength == 0 || --chan->pseudoEchoLength == 0)
            goto stop;
        return TRUE;
    }

    if (status & SOUND_CHANNEL_SF_STOP)
    {
        volume = volume * chan->release >> 8;
        if (volume <= chan->pseudoEchoVolume)
            goto echo;
    }
    else if ((status & SOUND_CHANNEL_SF_ENV) == SOUND_CHANNEL_SF_ENV_DECAY)
    {
        volume = volume * chan->decay >> 8;
        if (volume <= chan->sustain)
        {
            volume = chan->sustain;
            if (volume == 0)
                goto echo;
            status--;
        }
    }
    else if ((status & SOUND_CHANNEL_SF_ENV) == SOUND_CHANNEL_SF_ENV_ATTACK)
    {
        volume += chan->attack;
        if (volume >= 255)
        {
            volume = 255;
            status--;
        }
    }
    goto done;
echo:
    volume = chan->pseudoEchoVolume;
    if (volume == 0)
        goto stop;
    status |= SOUND_CHANNEL_SF_IEC;
done:
    chan->envelopeVolume = volume;
    chan->statusFlags = status;
    return TRUE;
stop:
    chan->statusFlags = 0;
    return FALSE;
}

struct SampleCache
{
    u32 block;
    s8 samples[64];
};

static s8 ReadSample(const struct WaveData *wav, u32 index, struct SampleCache *cache)
{
    if (wav->type == 0)
        return wav->data[index];

    // Cry headers count decoded samples. Each complete or partial 64-sample
    // block occupies 33 bytes. Cache belongs to this voice, never another cry.
    u32 block = index / 64;
    if (cache->block != block)
    {
        const u8 *src = (const u8 *)wav->data + block * 33;
        s8 value = *src++;
        cache->samples[0] = value;
        cache->samples[1] = value += gDeltaEncodingTable[*src++ & 15];
        for (u32 i = 2; i < 64; i += 2)
        {
            u8 delta = *src++;
            cache->samples[i] = value += gDeltaEncodingTable[delta >> 4];
            cache->samples[i + 1] = value += gDeltaEncodingTable[delta & 15];
        }
        cache->block = block;
    }
    return cache->samples[index % 64];
}

static void MixChannel(struct SoundInfo *soundInfo, struct SoundChannel *chan, float *out)
{
    const struct WaveData *wav = chan->wav;
    struct SampleCache cache = {.block = (u32)-1};
    u32 volume = chan->envelopeVolume * (soundInfo->masterVolume + 1) >> 4;
    chan->envelopeVolumeRight = chan->rightVolume * volume >> 8;
    chan->envelopeVolumeLeft = chan->leftVolume * volume >> 8;
    float right = chan->envelopeVolumeRight / 32768.0f;
    float left = chan->envelopeVolumeLeft / 32768.0f;
    bool32 reverse = chan->type & 0x10;
    u32 loopLength = (chan->statusFlags & SOUND_CHANNEL_SF_LOOP) && !reverse
        ? wav->size - wav->loopStart : 0;
    // Fixed-rate drums still use the requested GBA mixing rate, not SDL's
    // higher output rate; otherwise restoring audio raises their pitch.
    float step = (chan->type & TONEDATA_TYPE_FIX)
        ? gPcmSamplesPerVBlankTable[soundInfo->freq - 1] * 59.7275f / PORTABLE_AUDIO_RATE
        : chan->frequency * soundInfo->divFreq;

    for (u32 i = 0; i < soundInfo->pcmSamplesPerVBlank; i++, out += 2)
    {
        u32 index = reverse ? chan->count - 1 : wav->size - chan->count;
        u32 next = reverse ? (index ? index - 1 : index) : index + 1;
        if (next >= wav->size)
            next = loopLength ? wav->loopStart : index;
        s32 a = ReadSample(wav, index, &cache);
        s32 b = ReadSample(wav, next, &cache);
        float sample = a + (b - a) * chan->fw;
        out[0] += sample * left;
        out[1] += sample * right;

        chan->fw += step;
        u32 advance = chan->fw;
        chan->fw -= advance;
        if (advance >= chan->count)
        {
            if (!loopLength)
            {
                chan->statusFlags = 0;
                return;
            }
            chan->count = loopLength - (advance - chan->count) % loopLength;
        }
        else
            chan->count -= advance;
    }
}

static float *CurrentBuffer(struct SoundInfo *soundInfo)
{
    u32 frame = soundInfo->pcmDmaCounter > 1
        ? soundInfo->pcmDmaPeriod - (soundInfo->pcmDmaCounter - 1) : 0;
    return soundInfo->pcmBuffer + frame * soundInfo->pcmSamplesPerVBlank * 2;
}

void SoundMain(void)
{
    struct SoundInfo *soundInfo = SOUND_INFO_PTR;
    if (soundInfo == NULL || soundInfo->ident != ID_NUMBER || Platform_SkipAudioFrame())
        return;
    soundInfo->ident++;
    if (soundInfo->MPlayMainHead != NULL)
        soundInfo->MPlayMainHead(soundInfo->musicPlayerHead);
    soundInfo->CgbSound();

    float *out = CurrentBuffer(soundInfo);
    float *next = soundInfo->pcmDmaCounter == 2
        ? soundInfo->pcmBuffer : out + soundInfo->pcmSamplesPerVBlank * 2;
    for (u32 i = 0; i < soundInfo->pcmSamplesPerVBlank * 2; i += 2)
    {
        float reverb = (out[i] + out[i + 1] + next[i] + next[i + 1])
            * (soundInfo->reverb / 512.0f);
        out[i] = out[i + 1] = reverb;
    }
    for (u32 i = 0; i < soundInfo->maxChans; i++)
        if (TickEnvelope(&soundInfo->chans[i]))
            MixChannel(soundInfo, &soundInfo->chans[i], out);
    cgb_audio_generate(soundInfo->pcmSamplesPerVBlank);
    soundInfo->ident = ID_NUMBER;
}

void m4aSoundVSync(void)
{
    struct SoundInfo *soundInfo = SOUND_INFO_PTR;
    if (soundInfo == NULL || soundInfo->ident != ID_NUMBER || Platform_SkipAudioFrame())
        return;
    float audio[PORTABLE_AUDIO_SAMPLES_PER_FRAME * 2];
    float *pcm = CurrentBuffer(soundInfo);
    float *cgb = cgb_get_buffer();
    for (u32 i = 0; i < soundInfo->pcmSamplesPerVBlank * 2; i++)
    {
        float sample = (pcm[i] + cgb[i]) * 0.5f;
        if (sample != sample)
            sample = 0;
        audio[i] = sample > 1 ? 1 : sample < -1 ? -1 : sample;
    }
    Platform_QueueAudio(audio, soundInfo->pcmSamplesPerVBlank * 2 * sizeof(float));
    if (soundInfo->pcmDmaCounter <= 1)
        soundInfo->pcmDmaCounter = soundInfo->pcmDmaPeriod;
    else
        soundInfo->pcmDmaCounter--;
}
#endif // PORTABLE
