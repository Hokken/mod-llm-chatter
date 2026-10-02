/* mod-llm-chatter - battleground match and final-delivery ownership */
#include "LLMChatterBGDelivery.h"
#include "LLMChatterAB.h"
#include "LLMChatterConfig.h"
#include "LLMChatterJsonFields.h"
#include "LLMChatterShared.h"
#include "Battleground.h"
#include "Group.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Playerbots.h"
#include "Random.h"
#include "Timer.h"

#include <chrono>
#include <map>
#include <mutex>

namespace
{
struct MatchIdentity
{
    std::string token;
    uint32 type;
    uint32 map;
    bool abEnabled;
};
std::mutex _matchesMutex;
std::map<uint32, MatchIdentity> _matches;

std::string NewToken()
{
    // Process nonce plus serial: restart and same-ID instance reuse are
    // distinct. Random values are identity entropy, not gameplay tuning.
    static std::string const nonce = std::to_string(
        std::chrono::system_clock::now().time_since_epoch().count())
        + "-" + std::to_string(rand32()) + "-" + std::to_string(rand32());
    static uint64 serial = 0; // caller holds _matchesMutex
    return nonce + "-" + std::to_string(++serial);
}

bool ReadId(LLMChatterJson::Members const& fields, char const* key,
    uint64& value)
{
    return LLMChatterJson::UInt(fields, key, value) && value <= UINT32_MAX;
}
}

bool BGEventUsesABSnapshot(std::string const& eventType)
{
    return eventType == "bg_node_captured" || eventType == "bg_node_contested"
        || eventType == "bg_idle_chatter" || eventType == "bg_score_milestone";
}

void EnsureBGDeliveryLifetime(Battleground* bg)
{
    if (!bg || !bg->isBattleground())
        return;
    std::lock_guard<std::mutex> lock(_matchesMutex);
    auto it = _matches.find(bg->GetInstanceID());
    bool abEnabled = sLLMChatterConfig->_bgABEnable;
    if (it == _matches.end()
        || (bg->GetBgTypeID(true) == BATTLEGROUND_AB
            && it->second.abEnabled != abEnabled))
        _matches[bg->GetInstanceID()] = {
            NewToken(), uint32(bg->GetBgTypeID(true)), bg->GetMapId(), abEnabled};
}

void ResetBGDeliveryLifetime(uint32 instanceId)
{
    std::lock_guard<std::mutex> lock(_matchesMutex);
    _matches.erase(instanceId);
}

Player* GetBGChatterRecipient(Battleground* bg, Player* subject)
{
    if (!bg || !subject || !subject->GetGroup())
        return nullptr;
    auto eligible = [&](Player* player)
    {
        return player && player->IsInWorld() && !IsPlayerBot(player)
            && player->GetBattleground() == bg
            && player->GetBgTeamId() == subject->GetBgTeamId();
    };
    if (eligible(subject))
        return subject;
    for (GroupReference* ref = subject->GetGroup()->GetFirstMember();
        ref; ref = ref->next())
        if (eligible(ref->GetSource()))
            return ref->GetSource();
    return nullptr;
}

void AppendBGDeliveryContext(Battleground* bg, Player* subject,
    std::string& json)
{
    Player* recipient = GetBGChatterRecipient(bg, subject);
    if (!recipient)
        return; // existing BG markers make this fail closed at delivery
    MatchIdentity identity;
    {
        std::lock_guard<std::mutex> lock(_matchesMutex);
        auto it = _matches.find(bg->GetInstanceID());
        if (it == _matches.end())
            return; // only lifecycle hooks may create an identity
        identity = it->second;
    }
    LLMChatterJson::Members fields;
    if (!LLMChatterJson::ReadObject(json, fields))
        return;
    Group* group = recipient->GetGroup();
    uint64 groupId = group->GetGUID().GetCounter();
    uint64 stored = 0;
    for (char const* key : {"group_id", "raid_group_id"})
        if (fields.count(key) && (!ReadId(fields, key, stored)
            || (stored && stored != groupId)))
            return;
    // Rebuild from borrowed raw values to normalize without duplicate keys.
    std::map<std::string, std::string> values;
    for (auto const& [key, value] : fields)
        values[key] = std::string(value);
    values["is_battleground"] = "true";
    values["bg_match_token"] = "\"" + identity.token + "\"";
    values["bg_observed_ms"] = std::to_string(GetTimeMS().count());
    values["bg_recipient_guid"] = std::to_string(
        recipient->GetGUID().GetCounter());
    values["bg_instance_id"] = std::to_string(bg->GetInstanceID());
    values["bg_type_id"] = std::to_string(identity.type);
    values["bg_map_id"] = std::to_string(identity.map);
    values["group_id"] = std::to_string(groupId);
    values["player_subgroup"] = std::to_string(
        group->GetMemberGroup(recipient->GetGUID()));
    values["team"] = recipient->GetBgTeamId() == TEAM_ALLIANCE
        ? "\"Alliance\"" : "\"Horde\"";
    json = "{";
    for (auto const& [key, value] : values)
    {
        if (json.size() > 1)
            json += ",";
        json += "\"" + JsonEscape(key) + "\":" + value;
    }
    json += "}";
}

std::string ValidateBGDelivery(Player* speaker, std::string const& channel,
    std::string const& owner, std::string const& eventType,
    uint32 eventMapId, uint32 rowGroupId, std::string const& json)
{
    using namespace LLMChatterJson;
    Members fields;
    bool parsed = ReadObject(json, fields);
    // Location alone is not a BG contract: ordinary loot, resurrection,
    // travel and social Party rows retain their existing delivery policy.
    bool bgRow = owner == "bg" || channel == "battleground"
        || eventType.compare(0, 3, "bg_") == 0
        || (parsed && (fields.count("bg_match_token")
            || fields.count("bg_instance_id") || fields.count("bg_type_id")
            || fields.count("ab_state")
            || (fields.count("is_battleground")
                && fields.at("is_battleground") == "true")));
    if (!bgRow)
        return {};
    if (!sLLMChatterConfig->IsEnabled() || !sLLMChatterConfig->_bgChatterEnable)
        return "bg_disabled";
    if (!parsed)
        return "bg_contract_invalid";
    uint64 instance = 0, type = 0, map = 0, recipientId = 0;
    uint64 groupId = 0, subgroup = 0, observed = 0, raidGroup = 0;
    std::string token, team;
    if (!String(fields, "bg_match_token", token) || token.empty()
        || !String(fields, "team", team)
        || (team != "Alliance" && team != "Horde")
        || !ReadId(fields, "bg_instance_id", instance) || !instance
        || !ReadId(fields, "bg_type_id", type)
        || !ReadId(fields, "bg_map_id", map) || map != eventMapId
        || !ReadId(fields, "bg_recipient_guid", recipientId) || !recipientId
        || !ReadId(fields, "group_id", groupId) || !groupId
        || !ReadId(fields, "player_subgroup", subgroup) || subgroup >= 8
        || !UInt(fields, "bg_observed_ms", observed))
        return "bg_contract_missing";
    if ((fields.count("raid_group_id")
            && (!ReadId(fields, "raid_group_id", raidGroup)
                || (raidGroup && raidGroup != groupId)))
        || (rowGroupId && rowGroupId != groupId))
        return "bg_group_conflict";
    {
        std::lock_guard<std::mutex> lock(_matchesMutex);
        auto it = _matches.find(static_cast<uint32>(instance));
        if (it == _matches.end() || it->second.token != token
            || it->second.type != type || it->second.map != map)
            return "bg_match_changed";
    }
    uint64 now = GetTimeMS().count();
    // Only rows carrying AB base facts use the AB budget; their staleness
    // is also caught by the revision checks below. Incidental rows in AB
    // carry no base facts (option C) and use the generic BG budget.
    bool abSnapshot = type == BATTLEGROUND_AB && fields.count("ab_state");
    uint32 ageSec = eventType == "bg_match_end"
        ? sLLMChatterConfig->_bgMatchEndMaxAgeSec
        : abSnapshot ? sLLMChatterConfig->_bgABFactualMaxAgeSec
        : sLLMChatterConfig->_bgFactualMaxAgeSec;
    if (observed > now || now - observed > uint64(ageSec) * 1000)
        return "bg_facts_expired";
    if (!speaker || !speaker->IsInWorld() || !IsPlayerBot(speaker))
        return "bg_speaker_unavailable";
    Player* recipient = ObjectAccessor::FindPlayer(
        ObjectGuid::Create<HighGuid::Player>(static_cast<uint32>(recipientId)));
    if (!recipient || !recipient->IsInWorld() || IsPlayerBot(recipient))
        return "bg_recipient_unavailable";
    Battleground* bg = speaker->GetBattleground();
    TeamId expectedTeam = team == "Alliance" ? TEAM_ALLIANCE : TEAM_HORDE;
    if (!bg || recipient->GetBattleground() != bg
        || bg->GetInstanceID() != instance || bg->GetMapId() != map
        || bg->GetBgTypeID(true) != type
        || speaker->GetMapId() != map || recipient->GetMapId() != map
        || !speaker->GetMap() || speaker->GetMap() != recipient->GetMap()
        || speaker->GetMap()->GetInstanceId() != instance
        || speaker->GetBgTeamId() != expectedTeam
        || recipient->GetBgTeamId() != expectedTeam)
        return "bg_match_or_team_changed";
    Group* group = speaker->GetGroup();
    if (!group || group != recipient->GetGroup()
        || group->GetGUID().GetCounter() != groupId)
        return "bg_group_changed";
    if (channel == "party")
    {
        if (group->GetMemberGroup(speaker->GetGUID()) != subgroup
            || group->GetMemberGroup(recipient->GetGUID()) != subgroup)
            return "bg_subgroup_changed";
    }
    else if (channel != "battleground")
        return "bg_channel_invalid";
    bool arrival = eventType == "bot_group_join_batch"
        || eventType == "bg_match_start";
    if (eventType == "bg_match_end")
    {
        if (bg->GetStatus() != STATUS_WAIT_LEAVE)
            return "bg_status_changed";
    }
    else if (bg->GetStatus() != STATUS_IN_PROGRESS
        && !(arrival && bg->GetStatus() == STATUS_WAIT_JOIN))
        return "bg_status_changed";
    // The node prompt exposes only this objective, never the full snapshot.
    if (type == BATTLEGROUND_AB
        && (eventType == "bg_node_captured" || eventType == "bg_node_contested"))
        return sLLMChatterConfig->_bgABEnable && IsABNodeEventCurrent(bg, json)
            ? "" : "bg_ab_node_changed";
    auto ab = fields.find("ab_state");
    if (ab != fields.end())
    {
        // Old incidental prose may already contain base facts. Discard it
        // at the contract boundary rather than exempting old generated text.
        if (!BGEventUsesABSnapshot(eventType))
            return "bg_ab_context_unexpected";
        if (type != BATTLEGROUND_AB || !sLLMChatterConfig->_bgABEnable
            || !IsABSnapshotCurrent(bg, ab->second, now, ageSec))
            return "bg_ab_state_changed";
    }
    return {};
}
