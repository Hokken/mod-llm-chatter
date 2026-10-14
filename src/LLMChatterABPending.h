#ifndef MOD_LLM_CHATTER_AB_PENDING_H
#define MOD_LLM_CHATTER_AB_PENDING_H

#include <algorithm>
#include <array>
#include <cstdint>
#include <map>
#include <vector>

// Value-only scheduling policy; no game objects, SQL or random generator.
namespace LLMChatterAB
{
using Audience = std::uint64_t; // team/group/subgroup packed by the AB owner
struct Revision
{
    std::uint8_t node;
    std::uint64_t revision;
};

struct PendingNode
{
    bool active = false;
    std::uint8_t baseline = 0;
    bool baselineCaptured = false;
    std::uint64_t revision = 0;
    std::uint64_t firstMs = 0;
    std::uint64_t lastMs = 0;
    // Frozen at the first insertion attempt for this revision. New listeners
    // in an existing subgroup can hear retries; new subgroups get new changes.
    std::map<Audience, bool> receipts;
};

class PendingNodes
{
public:
    std::array<PendingNode, 5> nodes{};
    std::uint64_t nextAttemptMs = 0;
    std::uint8_t rotation = 0;

    void Record(std::uint8_t id, std::uint8_t previous, bool wasCaptured,
        std::uint8_t state, bool captured, std::uint64_t revision,
        std::uint64_t now)
    {
        auto& node = nodes[id];
        // A submitted earlier revision may still become visible. Do not
        // cancel its subsequent reversal as an entirely unsaid alarm.
        if (!node.active || !node.receipts.empty())
        {
            node = {};
            node.baseline = previous;
            node.baselineCaptured = wasCaptured;
            node.firstMs = now;
        }
        node.active = state != node.baseline || captured != node.baselineCaptured;
        node.lastMs = now;
        node.revision = revision;
        node.receipts.clear();
    }

    void Expire(std::uint64_t now, std::uint64_t maxAgeMs)
    {
        for (auto& node : nodes)
            if (node.active && now - node.lastMs > maxAgeMs)
                node = {};
    }

    std::vector<Revision> Select(std::uint64_t now, std::uint64_t cooldownMs,
        std::size_t limit)
    {
        if (now < nextAttemptMs)
            return {};
        std::vector<Revision> selected;
        for (std::uint8_t i = 0; i < nodes.size(); ++i)
            if (nodes[i].active)
                selected.push_back({i, nodes[i].revision});
        std::sort(selected.begin(), selected.end(), [&](auto a, auto b)
        {
            if (nodes[a.node].firstMs != nodes[b.node].firstMs)
                return nodes[a.node].firstMs < nodes[b.node].firstMs;
            return (a.node + 5 - rotation) % 5 < (b.node + 5 - rotation) % 5;
        });
        if (selected.size() > limit)
            selected.resize(limit);
        if (!selected.empty())
        {
            nextAttemptMs = now + cooldownMs; // includes failed chance rolls
            rotation = (selected.back().node + 1) % 5;
        }
        return selected;
    }

    void SetAudiences(std::vector<Revision> const& selected,
        std::vector<Audience> const& audiences)
    {
        for (auto item : selected)
            if (nodes[item.node].receipts.empty())
                for (auto audience : audiences)
                    nodes[item.node].receipts.emplace(audience, false);
    }

    std::vector<Revision> ForAudience(std::vector<Revision> const& selected,
        Audience audience) const
    {
        std::vector<Revision> result;
        for (auto item : selected)
        {
            auto const& receipts = nodes[item.node].receipts;
            auto it = receipts.find(audience);
            if (it != receipts.end() && !it->second)
                result.push_back(item);
        }
        return result;
    }

    void Acknowledge(Audience audience, std::vector<Revision> const& selected,
        bool success)
    {
        if (!success)
            return;
        for (auto item : selected)
        {
            auto& node = nodes[item.node];
            auto receipt = node.receipts.find(audience);
            if (!node.active || node.revision != item.revision
                || receipt == node.receipts.end())
                continue;
            receipt->second = true;
            if (std::all_of(node.receipts.begin(), node.receipts.end(),
                [](auto const& pair) { return pair.second; }))
                node = {};
        }
    }
};
}

#endif
