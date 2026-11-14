/*
 * mod-llm-chatter - group awareness for non-party speech
 *
 * See LLMChatterGroupAwareness.h for the contract.
 */

#include "LLMChatterGroupAwareness.h"

#include "LLMChatterConfig.h"
#include "LLMChatterGroupGuard.h"
#include "LLMChatterShared.h"

#include "Group.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"

#include <cstdio>
#include <ctime>
#include <map>
#include <mutex>
#include <utility>

namespace
{

std::mutex _awarenessMutex;
std::string _epoch;
uint64 _nextRev = 0;
std::map<uint32, uint64> _groupRev;
std::map<std::pair<uint32, uint32>, time_t> _memberSince;

constexpr size_t kMaxListedMembers = 4;

// Caller holds _awarenessMutex.
std::string const& EpochLocked()
{
    if (_epoch.empty())
    {
        uint64 value =
            ((static_cast<uint64>(rand32()) << 32) | rand32())
            ^ static_cast<uint64>(time(nullptr));
        char buf[17];
        std::snprintf(buf, sizeof(buf), "%016llx",
            static_cast<unsigned long long>(value));
        _epoch = buf;
    }
    return _epoch;
}

// Caller holds _awarenessMutex. A group seen for the first time
// in this process (including one restored after a relog or a
// restart, which fires no add hook) draws a fresh revision.
uint64 ObserveRevLocked(uint32 groupId)
{
    auto it = _groupRev.find(groupId);
    if (it != _groupRev.end())
        return it->second;
    uint64 rev = ++_nextRev;
    _groupRev[groupId] = rev;
    return rev;
}

// Caller holds _awarenessMutex. Unknown memberships start "now":
// nothing from before the first observation counts as known.
time_t ObserveMemberSinceLocked(uint32 groupId, uint32 botGuid)
{
    auto key = std::make_pair(groupId, botGuid);
    auto it = _memberSince.find(key);
    if (it != _memberSince.end())
        return it->second;
    time_t now = time(nullptr);
    _memberSince[key] = now;
    return now;
}

std::string GroupFingerprint(Group const* group)
{
    std::vector<std::pair<std::uint32_t, std::uint8_t>> slots;
    for (auto const& slot : group->GetMemberSlots())
        slots.emplace_back(slot.guid.GetCounter(), slot.group);
    return LLMChatterGroupGuard::Fingerprint(std::move(slots));
}

LLMChatterGroupGuard::Guard LiveGuard(Player* bot)
{
    LLMChatterGroupGuard::Guard guard;
    Group* group = bot ? bot->GetGroup() : nullptr;
    std::lock_guard<std::mutex> lock(_awarenessMutex);
    guard.epoch = EpochLocked();
    if (!group)
        return guard;
    guard.groupId = group->GetGUID().GetCounter();
    guard.rev = ObserveRevLocked(guard.groupId);
    guard.fp = GroupFingerprint(group);
    return guard;
}

std::string BoolJson(bool value)
{
    return value ? "true" : "false";
}

} // namespace

void NoteGroupMemberAdded(Group* group, ObjectGuid guid)
{
    if (!group)
        return;
    uint32 groupId = group->GetGUID().GetCounter();
    std::lock_guard<std::mutex> lock(_awarenessMutex);
    _groupRev[groupId] = ++_nextRev;
    if (guid)
        _memberSince[{groupId, guid.GetCounter()}] = time(nullptr);
}

void NoteGroupMemberRemoved(Group* group, ObjectGuid guid)
{
    if (!group)
        return;
    uint32 groupId = group->GetGUID().GetCounter();
    std::lock_guard<std::mutex> lock(_awarenessMutex);
    _groupRev[groupId] = ++_nextRev;
    if (guid)
        _memberSince.erase({groupId, guid.GetCounter()});
}

void NoteGroupDisbanded(Group* group)
{
    if (!group)
        return;
    uint32 groupId = group->GetGUID().GetCounter();
    std::lock_guard<std::mutex> lock(_awarenessMutex);
    // A later observation of this id draws a fresh, never-used
    // revision from the global counter.
    _groupRev.erase(groupId);
    for (auto it = _memberSince.begin(); it != _memberSince.end();)
    {
        if (it->first.first == groupId)
            it = _memberSince.erase(it);
        else
            ++it;
    }
}

std::string BuildSpeakerGroupJson(Player* bot)
{
    Group* group = bot ? bot->GetGroup() : nullptr;
    if (!group)
        return "{}";

    uint32 groupId = group->GetGUID().GetCounter();
    uint32 botGuid = bot->GetGUID().GetCounter();
    std::string epoch;
    uint64 rev = 0;
    time_t memberSince = 0;
    {
        std::lock_guard<std::mutex> lock(_awarenessMutex);
        epoch = EpochLocked();
        rev = ObserveRevLocked(groupId);
        memberSince = ObserveMemberSinceLocked(groupId, botGuid);
    }

    bool isRaid = group->isRaidGroup();
    uint8 subgroup = group->GetMemberGroup(bot->GetGUID());
    float nearRadius = static_cast<float>(
        sLLMChatterConfig->_groupAwarenessNearbyRadius);

    std::string members = "[";
    size_t listed = 0;
    for (auto const& slot : group->GetMemberSlots())
    {
        if (listed >= kMaxListedMembers)
            break;
        if (slot.guid == bot->GetGUID())
            continue;
        if (isRaid && slot.group != subgroup)
            continue;
        Player* member =
            ObjectAccessor::FindConnectedPlayer(slot.guid);
        if (!member)
            continue;

        bool near = member->IsInWorld()
            && member->GetMap() == bot->GetMap()
            && member->GetInstanceId() == bot->GetInstanceId()
            && bot->IsWithinDistInMap(member, nearRadius);
        bool sameZone = member->IsInWorld()
            && member->GetZoneId() == bot->GetZoneId();

        if (listed > 0)
            members += ",";
        members += "{\"name\":\""
            + ChatterJsonEscape(member->GetName())
            + "\",\"is_player\":" + BoolJson(!IsPlayerBot(member))
            + ",\"near\":" + BoolJson(near)
            + ",\"same_zone\":" + BoolJson(sameZone) + "}";
        ++listed;
    }
    members += "]";

    Map* map = bot->GetMap();
    bool isInstance = map && (map->IsDungeon() || map->IsRaid());
    char const* mapName = map ? map->GetMapName() : nullptr;

    return std::string("{")
        + "\"group_id\":" + std::to_string(groupId)
        + ",\"epoch\":\"" + epoch + "\""
        + ",\"rev\":" + std::to_string(rev)
        + ",\"fp\":\"" + GroupFingerprint(group) + "\""
        + ",\"is_raid\":" + BoolJson(isRaid)
        + ",\"subgroup\":" + std::to_string(subgroup)
        + ",\"member_since\":"
        + std::to_string(static_cast<uint64>(memberSince))
        + ",\"with_real_player\":"
        + BoolJson(IsGroupedWithRealPlayer(bot))
        + ",\"self\":{\"map_id\":" + std::to_string(bot->GetMapId())
        + ",\"instance_id\":"
        + std::to_string(bot->GetInstanceId())
        + ",\"zone_id\":" + std::to_string(bot->GetZoneId())
        + ",\"area_id\":" + std::to_string(bot->GetAreaId())
        + ",\"zone_name\":\""
        + ChatterJsonEscape(GetAreaNameForLocale(bot->GetZoneId()))
        + "\",\"area_name\":\""
        + ChatterJsonEscape(GetAreaNameForLocale(bot->GetAreaId()))
        + "\",\"is_instance\":" + BoolJson(isInstance)
        + ",\"map_name\":\""
        + ChatterJsonEscape(isInstance && mapName ? mapName : "")
        + "\"}"
        + ",\"members\":" + members
        + "}";
}

std::string BuildSpeakerGroupsField(
    std::vector<Player*> const& speakers)
{
    std::string json = "\"speaker_groups\":{";
    bool first = true;
    for (Player* bot : speakers)
    {
        if (!bot || !IsPlayerBot(bot))
            continue;
        if (!first)
            json += ",";
        json += "\"" + std::to_string(bot->GetGUID().GetCounter())
            + "\":" + LLMChatterGroupGuard::GuardJson(LiveGuard(bot));
        first = false;
    }
    json += "}";
    return json;
}

std::string BuildBotGroupsField(std::vector<Player*> const& bots)
{
    std::string json = "\"bot_groups\":{";
    bool first = true;
    for (Player* bot : bots)
    {
        if (!bot || !IsPlayerBot(bot) || !bot->GetGroup())
            continue;
        if (!first)
            json += ",";
        json += "\"" + std::to_string(bot->GetGUID().GetCounter())
            + "\":" + BuildSpeakerGroupJson(bot);
        first = false;
    }
    json += "}";
    return json;
}

namespace
{

// Inserts `field` (a `"key":value` pair) into a compact JSON object
// string just before its closing brace.
void InsertJsonField(std::string& extraJson, std::string const& field)
{
    if (extraJson.size() < 2 || extraJson.back() != '}')
        return;
    bool emptyObject = extraJson.find_last_not_of(
        " \t\r\n", extraJson.size() - 2) == extraJson.find('{');
    extraJson.insert(extraJson.size() - 1,
        (emptyObject ? "" : ",") + field);
}

} // namespace

void AppendSpeakerGroups(
    std::string& extraJson,
    std::vector<Player*> const& speakers)
{
    InsertJsonField(extraJson, BuildSpeakerGroupsField(speakers));
}

void AppendCandidateGroups(
    std::string& extraJson,
    std::vector<Player*> const& candidates)
{
    InsertJsonField(extraJson, BuildBotGroupsField(candidates));
    InsertJsonField(extraJson, BuildSpeakerGroupsField(candidates));
}

char const* SpeakerGroupDropReason(
    std::string const& extraData, uint32 botGuid, Player* bot)
{
    if (!bot)
        return nullptr;

    LLMChatterGroupGuard::Guard stored;
    switch (LLMChatterGroupGuard::ReadSpeakerGuard(
        extraData, botGuid, stored))
    {
        case LLMChatterGroupGuard::ReadResult::Absent:
            return nullptr;
        case LLMChatterGroupGuard::ReadResult::Malformed:
            return "speaker_group_changed";
        case LLMChatterGroupGuard::ReadResult::Ok:
            break;
    }

    return LLMChatterGroupGuard::GuardMatches(stored, LiveGuard(bot))
        ? nullptr : "speaker_group_changed";
}
