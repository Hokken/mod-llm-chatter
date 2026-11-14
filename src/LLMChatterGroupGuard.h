#ifndef MOD_LLM_CHATTER_GROUP_GUARD_H
#define MOD_LLM_CHATTER_GROUP_GUARD_H

/*
 * mod-llm-chatter - speaker group membership guard (pure part)
 *
 * Standard library only, so the comparison and the extra_data
 * reader can be unit-tested outside the server build
 * (tools/tests/cpp/test_group_guard.cpp).
 *
 * A queued line remembers which group its speaker was in when
 * the line was written: the process epoch, the group id (0 when
 * ungrouped), the group's membership revision and a fingerprint
 * of the group's (member, subgroup) slots. Delivery recomputes
 * the same values live and drops the line on any difference.
 */

#include "LLMChatterJsonFields.h"

#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace LLMChatterGroupGuard
{

struct Guard
{
    std::string epoch;
    std::uint64_t groupId = 0;
    std::uint64_t rev = 0;
    std::string fp;
};

enum class ReadResult
{
    Absent,     // no speaker_groups entry for this bot: no check
    Malformed,  // an entry exists but cannot be read: drop
    Ok
};

// Reads extra_data.speaker_groups["<botGuid>"].
inline ReadResult ReadSpeakerGuard(
    std::string_view extraData, std::uint32_t botGuid, Guard& out)
{
    out = Guard();
    if (extraData.empty() || !botGuid)
        return ReadResult::Absent;

    LLMChatterJson::Members top;
    if (!LLMChatterJson::ReadObject(extraData, top))
        return ReadResult::Absent;
    auto groupsIt = top.find("speaker_groups");
    if (groupsIt == top.end())
        return ReadResult::Absent;

    LLMChatterJson::Members groups;
    if (!LLMChatterJson::ReadObject(groupsIt->second, groups))
        return ReadResult::Malformed;
    auto entryIt = groups.find(std::to_string(botGuid));
    if (entryIt == groups.end())
        return ReadResult::Absent;

    LLMChatterJson::Members entry;
    if (!LLMChatterJson::ReadObject(entryIt->second, entry)
        || !LLMChatterJson::String(entry, "e", out.epoch)
        || out.epoch.empty()
        || !LLMChatterJson::UInt(entry, "g", out.groupId))
        return ReadResult::Malformed;
    if (out.groupId != 0
        && (!LLMChatterJson::UInt(entry, "rev", out.rev)
            || !LLMChatterJson::String(entry, "fp", out.fp)))
        return ReadResult::Malformed;
    return ReadResult::Ok;
}

// True when the stored guard still describes the live state.
inline bool GuardMatches(Guard const& stored, Guard const& live)
{
    if (stored.epoch != live.epoch
        || stored.groupId != live.groupId)
        return false;
    if (stored.groupId == 0)
        return true;
    return stored.rev == live.rev && stored.fp == live.fp;
}

// Order-independent fingerprint of (member guid, subgroup) slots:
// FNV-1a 64 over the sorted pairs, as 16 hex digits.
inline std::string Fingerprint(
    std::vector<std::pair<std::uint32_t, std::uint8_t>> slots)
{
    std::sort(slots.begin(), slots.end());
    std::uint64_t hash = 1469598103934665603ULL;
    auto mix = [&hash](std::uint8_t byte)
    {
        hash ^= byte;
        hash *= 1099511628211ULL;
    };
    for (auto const& slot : slots)
    {
        for (int shift = 0; shift < 32; shift += 8)
            mix(static_cast<std::uint8_t>(slot.first >> shift));
        mix(slot.second);
    }
    char buf[17];
    std::snprintf(buf, sizeof(buf), "%016llx",
        static_cast<unsigned long long>(hash));
    return buf;
}

// {"e":"...","g":N[,"rev":N,"fp":"..."]}
inline std::string GuardJson(Guard const& guard)
{
    std::string json = "{\"e\":\"" + guard.epoch
        + "\",\"g\":" + std::to_string(guard.groupId);
    if (guard.groupId != 0)
        json += ",\"rev\":" + std::to_string(guard.rev)
            + ",\"fp\":\"" + guard.fp + "\"";
    json += "}";
    return json;
}

// Event extra_data key recording the lowest sequence dropped for a
// group change. Delivery writes it on the event row, so it also
// stops rows the bridge commits later (a General follow-up or
// extended turn generated while the dropped line was pending).
constexpr char const* kGroupDropSeqKey = "group_drop_seq";

// True when an earlier line of this row's event was dropped for a
// group change: the row would answer a line nobody heard.
inline bool RowFollowsGroupDrop(
    std::string_view extraData, std::uint32_t sequence)
{
    if (extraData.empty())
        return false;
    LLMChatterJson::Members top;
    std::uint64_t dropSeq = 0;
    return LLMChatterJson::ReadObject(extraData, top)
        && LLMChatterJson::UInt(top, kGroupDropSeqKey, dropSeq)
        && sequence > dropSeq;
}

} // namespace LLMChatterGroupGuard

#endif // MOD_LLM_CHATTER_GROUP_GUARD_H
