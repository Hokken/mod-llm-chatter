#ifndef MOD_LLM_CHATTER_VOICE_H
#define MOD_LLM_CHATTER_VOICE_H

#include "Define.h"
#include "ObjectGuid.h"

#include <string>

class Player;
class Unit;

// Voice mailbox (TTS). The worldserver only records lines the bound
// listener actually received; the host agent synthesizes and plays.
enum LLMChatterVoiceChannel : uint32
{
    VOICE_CHANNEL_NONE  = 0x00,
    VOICE_CHANNEL_SAY   = 0x01,
    VOICE_CHANNEL_YELL  = 0x02,
    VOICE_CHANNEL_MSAY  = 0x04,
    VOICE_CHANNEL_PARTY = 0x08,
};

uint32 ParseVoiceChannels(std::string const& configured);

// Called from config load: bumps the listener generation and
// republishes presence so rows from older runs, sessions or bindings
// can never match.
void ResetVoice();

// One call per logical send, after the line went out. Transport
// helpers (SendPartyMessageInstant) never call this; their callers do.
// messageId 0 means the line has no llm_chatter_messages row. Returns
// true when a voice row was queued.
bool RecordVoiceLine(Unit* speaker, LLMChatterVoiceChannel channel,
    std::string const& text, uint32 messageId);

// After a voiced, queued line for which delivery turned the bot toward
// a target: the bot looks away once that line's audio completed.
// facing is the orientation the bot was told to turn to: the turn is a
// spline, so the bot's own orientation only reaches it on a later tick.
void NoteVoiceFacing(Player* bot, uint32 messageId, float facing);

// Delivery channel name ("say", "yell", "party") to its voice channel;
// VOICE_CHANNEL_NONE for channels that are never voiced.
LLMChatterVoiceChannel VoiceChannelForDelivery(std::string const& channel);

// True when a bot's facing for a line on this channel should wait for
// its audio to start (FaceAtVoice); false with voice or the channel off.
bool IsVoiceFacingDeferred(LLMChatterVoiceChannel channel);

// A voiced, queued line's deferred facing: applied once when its audio
// starts, dropped if it never plays.
void NotePendingFacing(Player* bot, uint32 messageId, ObjectGuid target);

// Cheap gate for callers: false when voice or this channel is off, so
// no voice-specific copies are made.
bool IsVoiceChannelWanted(LLMChatterVoiceChannel channel);

// Bot say/yell can be vetoed or rewritten inside Player::Say/Yell, so
// arm before the call and take after it: Take yields the text that was
// actually broadcast, or false when nothing was. channel is SAY or YELL.
bool ArmVoiceChatCapture(Player* bot, LLMChatterVoiceChannel channel,
    std::string const& message);
bool TakeVoiceChatCapture(std::string& broadcastText);

void AddLLMChatterVoiceScripts();

#endif
