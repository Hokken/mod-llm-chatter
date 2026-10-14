#ifndef MOD_LLM_CHATTER_AB_SCORE_H
#define MOD_LLM_CHATTER_AB_SCORE_H

#include <algorithm>
#include <array>
#include <charconv>
#include <cstdint>
#include <map>
#include <string_view>
#include <utility>
#include <vector>

namespace LLMChatterAB
{
inline std::vector<std::uint32_t> ParseMilestonePercents(std::string_view text)
{
    std::vector<std::uint32_t> result;
    for (;;)
    {
        auto comma = text.find(',');
        auto token = text.substr(0, comma);
        auto first = token.find_first_not_of(" \t\r\n");
        auto last = token.find_last_not_of(" \t\r\n");
        if (first == std::string_view::npos)
            return {30, 60, 90};
        token = token.substr(first, last - first + 1);
        std::uint32_t value = 0;
        auto parsed = std::from_chars(token.data(), token.data() + token.size(), value);
        if (parsed.ec != std::errc() || parsed.ptr != token.data() + token.size()
            || !value || value >= 100)
            return {30, 60, 90};
        result.push_back(value);
        if (comma == std::string_view::npos)
            break;
        text.remove_prefix(comma + 1);
    }
    std::sort(result.begin(), result.end());
    result.erase(std::unique(result.begin(), result.end()), result.end());
    return result;
}

inline std::map<std::uint32_t, bool> ScoreThresholds(std::uint32_t maximum,
    std::uint32_t warning, std::vector<std::uint32_t> const& percents)
{
    std::map<std::uint32_t, bool> result;
    for (auto percent : percents)
    {
        auto threshold = (std::uint64_t(maximum) * percent + 99) / 100;
        if (percent > 0 && percent < 100 && threshold > 0 && threshold < maximum)
            result[static_cast<std::uint32_t>(threshold)] = false;
    }
    if (warning > 0 && warning < maximum)
        result[warning] = true; // core warning wins a rounded collision
    return result;
}

struct ScorePending
{
    bool active = false;
    std::uint8_t team = 0;
    std::uint32_t threshold = 0;
    bool warning = false;
    std::uint64_t observedMs = 0;
    std::uint64_t revision = 0;
};

class ScoreTracker
{
public:
    ScorePending pending;
    std::uint64_t nextAttemptMs = 0;

    void Observe(std::uint32_t maximum, std::uint32_t warning,
        std::vector<std::uint32_t> const& percents,
        std::array<std::uint32_t, 2> const& scores, std::uint64_t now)
    {
        auto thresholds = ScoreThresholds(maximum, warning, percents);
        if (!_initialized || maximum != _maximum || thresholds != _thresholds)
        {
            // Late enable/target discovery/config change seeds reached values;
            // never replay already-crossed thresholds. Preserve serials so an
            // outstanding completion cannot acknowledge a new revision.
            _initialized = true;
            _maximum = maximum;
            _thresholds = std::move(thresholds);
            _highWater = scores;
            pending = {};
            return;
        }
        for (std::uint8_t team = 0; team < 2; ++team)
        {
            for (auto const& [value, isWarning] : _thresholds)
                if (value > _highWater[team] && value <= scores[team]
                    && (!pending.active || pending.observedMs != now
                        || value >= pending.threshold))
                    pending = {true, team, value, isWarning, now, ++_serial};
            _highWater[team] = std::max(_highWater[team], scores[team]);
        }
        if (scores[0] >= maximum || scores[1] >= maximum
            || (pending.active && scores[pending.team] < pending.threshold))
            pending.active = false;
    }

    bool TakeAttempt(std::uint64_t now, std::uint64_t cooldownMs,
        std::uint64_t maxAgeMs)
    {
        if (pending.active && now - pending.observedMs > maxAgeMs)
            pending.active = false;
        if (!pending.active || now < nextAttemptMs)
            return false;
        nextAttemptMs = now + cooldownMs;
        return true;
    }

    void Acknowledge(std::uint64_t revision, bool success)
    {
        if (success && pending.revision == revision)
            pending.active = false;
    }

private:
    bool _initialized = false;
    std::uint32_t _maximum = 0;
    std::map<std::uint32_t, bool> _thresholds;
    std::array<std::uint32_t, 2> _highWater{};
    std::uint64_t _serial = 0;
};

struct ObjectiveStatusClock
{
    std::uint64_t nextMs = 0;
    bool TakeOpportunity(std::uint64_t now, std::uint64_t intervalMs,
        bool nodePending, std::uint64_t recentNodeUntil)
    {
        if (!intervalMs || nodePending || now < recentNodeUntil || now < nextMs)
            return false;
        nextMs = now + intervalMs; // chance failure also spends this opportunity
        return true;
    }
};
}

#endif
