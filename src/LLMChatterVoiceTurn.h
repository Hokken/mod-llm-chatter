#ifndef MOD_LLM_CHATTER_VOICE_TURN_H
#define MOD_LLM_CHATTER_VOICE_TURN_H

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <utility>
#include <vector>

namespace LLMChatterVoice
{
constexpr float TWO_PI = 6.2831853071795864f;

// True while the bot still faces what delivery turned it toward: if
// the AI, a follow or another reply turned it since, leave it alone.
inline bool StillFacing(float current, float noted, float toleranceRad)
{
    return std::fabs(std::remainder(current - noted, TWO_PI))
        <= toleranceRad;
}

// Look away by a turn in [minRad, maxRad] to the left or right;
// unit01 picks within the range. Result wrapped into [0, 2pi).
inline float TurnAwayOrientation(float current, float minRad,
    float maxRad, float unit01, bool left)
{
    if (maxRad < minRad)
        std::swap(minRad, maxRad);
    float turn = minRad + (maxRad - minRad) * unit01;
    float result = std::fmod(current + (left ? turn : -turn), TWO_PI);
    if (result < 0.0f)
        result += TWO_PI;
    return result;
}

// Facing a bot was given for one voiced, queued message.
struct TurnNote
{
    std::uint32_t messageId = 0;
    std::uint32_t botGuid = 0;
    float orientation = 0.0f;
    std::uint64_t generation = 0;
    std::uint64_t noteMs = 0;
};

// Per-message notes, consumed exactly once by that message's terminal
// row. A bot's newest line supersedes its older notes, so only its
// last line can turn it, and only after that line completed.
class TurnNotes
{
public:
    // At the cap the oldest note is evicted (it simply never turns).
    void Note(TurnNote note, std::size_t cap)
    {
        if (!cap)
            return;
        _notes.erase(std::remove_if(_notes.begin(), _notes.end(),
            [&](TurnNote const& old)
            { return old.botGuid == note.botGuid; }), _notes.end());
        while (_notes.size() >= cap)
            _notes.erase(_notes.begin());
        _notes.push_back(note);
    }

    // Drops notes past their time-to-live or from another generation.
    void Prune(std::uint64_t nowMs, std::uint64_t ttlMs,
        std::uint64_t generation)
    {
        _notes.erase(std::remove_if(_notes.begin(), _notes.end(),
            [&](TurnNote const& note)
            {
                return note.generation != generation
                    || note.noteMs + ttlMs <= nowMs;
            }), _notes.end());
    }

    // A terminal row for messageId: the note is consumed either way, and
    // returned only when its audio really completed for the same
    // generation and bot.
    std::optional<TurnNote> OnTerminal(std::uint32_t messageId,
        bool played, std::uint64_t generation, std::uint32_t botGuid)
    {
        auto it = std::find_if(_notes.begin(), _notes.end(),
            [&](TurnNote const& note)
            { return note.messageId == messageId; });
        if (it == _notes.end())
            return std::nullopt;
        TurnNote note = *it;
        _notes.erase(it);
        if (!played || note.generation != generation
            || note.botGuid != botGuid)
            return std::nullopt;
        return note;
    }

    std::vector<std::uint32_t> Ids() const
    {
        std::vector<std::uint32_t> ids;
        ids.reserve(_notes.size());
        for (TurnNote const& note : _notes)
            ids.push_back(note.messageId);
        return ids;
    }

    bool Empty() const { return _notes.empty(); }
    std::size_t Size() const { return _notes.size(); }
    void Clear() { _notes.clear(); }

private:
    std::vector<TurnNote> _notes;
};

// A voiced line's facing, decided at send and applied at its audio
// start. Kept per message: two queued lines of one bot to different
// targets each turn at their own start; nothing supersedes them.
struct PendingFacing
{
    std::uint32_t messageId = 0;
    std::uint32_t botGuid = 0;
    std::uint64_t targetRaw = 0;
    std::uint64_t generation = 0;
    std::uint64_t noteMs = 0;
};

class PendingFacings
{
public:
    // At the cap the oldest pending facing is evicted (never applied).
    void Add(PendingFacing pending, std::size_t cap)
    {
        if (!cap)
            return;
        while (_pending.size() >= cap)
            _pending.erase(_pending.begin());
        _pending.push_back(pending);
    }

    void Prune(std::uint64_t nowMs, std::uint64_t ttlMs,
        std::uint64_t generation)
    {
        _pending.erase(std::remove_if(_pending.begin(), _pending.end(),
            [&](PendingFacing const& pending)
            {
                return pending.generation != generation
                    || pending.noteMs + ttlMs <= nowMs;
            }), _pending.end());
    }

    // Exactly once: the facing for messageId, removed as it is taken.
    std::optional<PendingFacing> Take(std::uint32_t messageId)
    {
        auto it = std::find_if(_pending.begin(), _pending.end(),
            [&](PendingFacing const& pending)
            { return pending.messageId == messageId; });
        if (it == _pending.end())
            return std::nullopt;
        PendingFacing pending = *it;
        _pending.erase(it);
        return pending;
    }

    std::vector<std::uint32_t> Ids() const
    {
        std::vector<std::uint32_t> ids;
        ids.reserve(_pending.size());
        for (PendingFacing const& pending : _pending)
            ids.push_back(pending.messageId);
        return ids;
    }

    bool Empty() const { return _pending.empty(); }
    std::size_t Size() const { return _pending.size(); }
    void Clear() { _pending.clear(); }

private:
    std::vector<PendingFacing> _pending;
};
}  // namespace LLMChatterVoice

#endif
