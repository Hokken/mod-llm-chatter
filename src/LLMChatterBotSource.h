#ifndef MOD_LLM_CHATTER_BOT_SOURCE_H
#define MOD_LLM_CHATTER_BOT_SOURCE_H

/*
 * mod-llm-chatter - chatter bot sourcing policy (pure part)
 *
 * Standard library only, so the policy can be unit-tested outside
 * the server build (tools/tests/cpp/test_bot_source.cpp).
 *
 * General and Guild chatter speakers come from two playerbot
 * registries: the random-bot holder and each real player's own
 * holder of alt bots (issue #98). AppendUniqueBot merges them
 * without duplicates; the first registry to add a GUID wins.
 * SampleBots draws a capped sample uniformly from the merged pool.
 *
 * ClassifySpeaker is the speaker rule shared by selection and by
 * delivery: only bots speak, and an alt bot speaks only while
 * LLMChatter.AltBots.Enable is on. Delivery re-checks it because a
 * queued line can outlive the speaker's bot session (logout and
 * relogin under client control, including as a self-bot) or the
 * config value (.reload config).
 */

#include <algorithm>
#include <cstddef>
#include <set>
#include <vector>

namespace LLMChatterBotSource
{

enum class SpeakerVerdict
{
    Ok,
    NotBot,       // a real player or a self-bot: never a speaker
    AltDisabled   // an alt bot while LLMChatter.AltBots.Enable = 0
};

inline SpeakerVerdict ClassifySpeaker(
    bool isPlayerBot, bool isRandomBot, bool altBotsEnabled)
{
    if (!isPlayerBot)
        return SpeakerVerdict::NotBot;
    if (!isRandomBot && !altBotsEnabled)
        return SpeakerVerdict::AltDisabled;
    return SpeakerVerdict::Ok;
}

// Drop reason logged and stored when delivery refuses a speaker.
inline char const* SpeakerDropReason(SpeakerVerdict verdict)
{
    switch (verdict)
    {
        case SpeakerVerdict::NotBot:
            return "speaker_not_bot";
        case SpeakerVerdict::AltDisabled:
            return "alt_bots_disabled";
        default:
            return "";
    }
}

// Appends `bot` unless it is null or `key` was already added.
template <typename Key, typename Bot>
inline bool AppendUniqueBot(
    std::vector<Bot*>& out, std::set<Key>& seen,
    Key const& key, Bot* bot)
{
    if (!bot || !seen.insert(key).second)
        return false;
    out.push_back(bot);
    return true;
}

// Uniform bounded sample: shuffles the whole pool, then keeps at most
// `cap` bots. Capping before shuffling would always keep the first
// registry's bots (and its lowest GUIDs) and never reach the rest.
template <typename Bot, typename Rng>
inline void SampleBots(std::vector<Bot*>& pool, std::size_t cap, Rng& rng)
{
    std::shuffle(pool.begin(), pool.end(), rng);
    if (pool.size() > cap)
        pool.resize(cap);
}

} // namespace LLMChatterBotSource

#endif
