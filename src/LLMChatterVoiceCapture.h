#ifndef MOD_LLM_CHATTER_VOICE_CAPTURE_H
#define MOD_LLM_CHATTER_VOICE_CAPTURE_H

#include <cstdint>
#include <string>
#include <utility>

namespace LLMChatterVoice
{
// Learns what a bot say/yell really broadcast. Player::Say runs the
// OnPlayerCanUseChat hooks (which may veto or rewrite the text), then
// the chat filter, then sends. Our hook is required to run last, so
// Observe() sees the final text only when every earlier hook allowed
// it; the caller passes the filter verdict to Take().
struct ChatCapture
{
    bool armed = false;
    bool reached = false;
    std::uint32_t guid = 0;
    std::uint32_t type = 0;
    std::string text;

    void Arm(std::uint32_t speakerGuid, std::uint32_t chatType)
    {
        armed = true;
        reached = false;
        guid = speakerGuid;
        type = chatType;
        text.clear();
    }

    void Observe(std::uint32_t speakerGuid, std::uint32_t chatType,
        std::string const& msg)
    {
        if (!armed || speakerGuid != guid || chatType != type)
            return;
        reached = true;
        text = msg;
    }

    // Always disarms. True only if the line passed every hook and the
    // filter; out then holds the text as broadcast.
    bool Take(bool filtered, std::string& out)
    {
        bool sent = armed && reached && !filtered;
        if (sent)
            out = std::move(text);
        armed = false;
        reached = false;
        text.clear();
        return sent;
    }
};
}

#endif
