/*
 * mod-llm-chatter - world reactivity
 *
 * Owns:
 *   - LLMChatterReactivityPlayerScript (achievement, quest,
 *     level and login records for real players)
 *   - llm_reactivity_inbox writes
 *   - delivery of llm_reactivity_letters rows through the mail
 *     system, online or offline
 *   - the fresh-rumor lookup used by proximity scans: an
 *     in-memory set refreshed by one async query, so the world
 *     thread never waits on the database
 *
 * Triggers live in their own table rather than
 * llm_chatter_events: startup expires every pending event, and
 * a letter earned just before a restart must not be lost.
 */

#include "LLMChatterReactivity.h"

#include "LLMChatterConfig.h"
#include "LLMChatterShared.h"

#include "AchievementMgr.h"
#include "AsyncCallbackProcessor.h"
#include "CharacterCache.h"
#include "DatabaseEnv.h"
#include "Item.h"
#include "Log.h"
#include "Mail.h"
#include "ObjectAccessor.h"
#include "ObjectGuid.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "QueryCallback.h"
#include "QuestDef.h"
#include "ScriptMgr.h"
#include "SharedDefines.h"

#include <algorithm>
#include <array>
#include <cstdlib>
#include <sstream>
#include <string>
#include <unordered_set>
#include <utility>
#include <vector>

namespace
{

// Letters sent per tick; the rest wait for the next poll.
constexpr uint32 LETTERS_PER_TICK = 5;

// Skills the bridge can write about. It maps them to names.
constexpr std::array<uint32, 14> PROFESSION_SKILLS = {
    SKILL_ALCHEMY, SKILL_BLACKSMITHING, SKILL_ENCHANTING,
    SKILL_ENGINEERING, SKILL_HERBALISM, SKILL_INSCRIPTION,
    SKILL_JEWELCRAFTING, SKILL_LEATHERWORKING, SKILL_MINING,
    SKILL_SKINNING, SKILL_TAILORING, SKILL_COOKING,
    SKILL_FIRST_AID, SKILL_FISHING};

bool IsReactivityEnabled()
{
    return sLLMChatterConfig
        && sLLMChatterConfig->IsEnabled()
        && (sLLMChatterConfig->_lettersEnable
            || sLLMChatterConfig->_rumorsEnable);
}

bool IsRealPlayer(Player* player)
{
    return player && !IsPlayerBot(player);
}

std::string BuildSkillsJson(Player* player)
{
    std::string json = "{";
    bool first = true;
    for (uint32 skill : PROFESSION_SKILLS)
    {
        if (!player->HasSkill(skill))
            continue;
        if (!first)
            json += ",";
        first = false;
        json += "\"" + std::to_string(skill) + "\":"
            + std::to_string(
                player->GetPureSkillValue(skill));
    }
    return json + "}";
}

// The facts the bridge cannot read from saved character rows:
// live profession points and skills are only written at save.
std::string BuildPlayerFactsJson(Player* player)
{
    return std::string("{\"level\":")
        + std::to_string(player->GetLevel())
        + ",\"team\":\""
        + (player->GetTeamId(true) == TEAM_ALLIANCE
            ? "Alliance" : "Horde")
        + "\",\"free_professions\":"
        + std::to_string(
            player->GetFreePrimaryProfessionPoints())
        + ",\"skills\":" + BuildSkillsJson(player) + "}";
}

void RecordDeed(
    char const* kind, Player* player, uint32 triggerId,
    std::string const& extraData)
{
    CharacterDatabase.Execute(
        "INSERT INTO llm_reactivity_inbox "
        "(kind, player_guid, trigger_id, extra_data) "
        "VALUES ('" + std::string(kind) + "', "
        + std::to_string(player->GetGUID().GetCounter())
        + ", " + std::to_string(triggerId)
        + ", '" + EscapeString(extraData) + "')");
}

class LLMChatterReactivityPlayerScript : public PlayerScript
{
public:
    LLMChatterReactivityPlayerScript()
        : PlayerScript(
              "LLMChatterReactivityPlayerScript",
              {PLAYERHOOK_ON_LOGIN,
               PLAYERHOOK_ON_LEVEL_CHANGED,
               PLAYERHOOK_ON_PLAYER_COMPLETE_QUEST,
               PLAYERHOOK_ON_ACHI_COMPLETE}) {}

    void OnPlayerLogin(Player* player) override
    {
        if (IsReactivityEnabled() && IsRealPlayer(player))
            RecordDeed(
                "login", player, 0,
                BuildPlayerFactsJson(player));
    }

    void OnPlayerLevelChanged(
        Player* player, uint8 /*oldLevel*/) override
    {
        if (IsReactivityEnabled() && IsRealPlayer(player))
            RecordDeed(
                "level", player, player->GetLevel(),
                BuildPlayerFactsJson(player));
    }

    void OnPlayerCompleteQuest(
        Player* player, Quest const* quest) override
    {
        if (quest && IsReactivityEnabled()
            && IsRealPlayer(player))
            RecordDeed(
                "quest", player, quest->GetQuestId(),
                BuildPlayerFactsJson(player));
    }

    void OnPlayerAchievementComplete(
        Player* player,
        AchievementEntry const* achievement) override
    {
        if (achievement && IsReactivityEnabled()
            && IsRealPlayer(player))
            RecordDeed(
                "achievement", player, achievement->ID,
                BuildPlayerFactsJson(player));
    }
};

// "entry:count,entry:count" as written by the bridge.
std::vector<std::pair<uint32, uint32>> ParseLetterItems(
    std::string const& items)
{
    std::vector<std::pair<uint32, uint32>> parsed;
    std::stringstream stream(items);
    std::string part;
    while (std::getline(stream, part, ','))
    {
        size_t colon = part.find(':');
        if (colon == std::string::npos)
            continue;
        uint32 entry = static_cast<uint32>(
            std::strtoul(part.c_str(), nullptr, 10));
        uint32 count = static_cast<uint32>(std::strtoul(
            part.c_str() + colon + 1, nullptr, 10));
        if (entry && count)
            parsed.emplace_back(entry, count);
    }
    return parsed;
}

void AttachLetterItems(
    MailDraft& draft, CharacterDatabaseTransaction trans,
    Player const* receiver,
    std::vector<std::pair<uint32, uint32>> const& items,
    uint32 letterId, uint32& attached)
{
    for (auto const& [entry, count] : items)
    {
        ItemTemplate const* proto =
            sObjectMgr->GetItemTemplate(entry);
        if (!proto)
        {
            LOG_WARN(
                "module",
                "LLMChatter: letter {} names unknown item {}",
                letterId, entry);
            continue;
        }

        uint32 left = count;
        uint32 stack = std::max<uint32>(
            1, proto->GetMaxStackSize());
        while (left && attached < MAX_MAIL_ITEMS)
        {
            uint32 size = std::min(left, stack);
            Item* item = Item::CreateItem(
                entry, size, receiver);
            if (!item)
                break;
            item->SaveToDB(trans);
            draft.AddItem(item);
            left -= size;
            ++attached;
        }
    }
}

void MarkLetter(uint32 letterId, char const* status)
{
    CharacterDatabase.Execute(
        "UPDATE llm_reactivity_letters SET status = '"
        + std::string(status) + "' WHERE id = "
        + std::to_string(letterId));
}

void SendLetter(
    uint32 letterId, uint32 playerGuid,
    std::string const& senderType, uint32 senderId,
    std::string const& subject, std::string const& body,
    std::string const& items)
{
    ObjectGuid receiverGuid =
        ObjectGuid::Create<HighGuid::Player>(playerGuid);
    if (!sCharacterCache->GetCharacterCacheByGuid(receiverGuid))
    {
        MarkLetter(letterId, "failed");
        return;
    }

    // Claimed outside the transaction, before it is queued: the
    // commit is asynchronous and the next poll must not see this
    // row as ready. A crash here leaves it unsent rather than sent
    // twice; the bridge retires rows left in this state.
    CharacterDatabase.DirectExecute(
        "UPDATE llm_reactivity_letters SET status = 'sending' "
        "WHERE status = 'ready' AND id = "
        + std::to_string(letterId));

    Player* online =
        ObjectAccessor::FindConnectedPlayer(receiverGuid);
    MailSender sender(
        senderType == "bot" ? MAIL_NORMAL : MAIL_CREATURE,
        senderId);
    MailDraft draft(subject, body);

    CharacterDatabaseTransaction trans =
        CharacterDatabase.BeginTransaction();
    uint32 attached = 0;
    AttachLetterItems(
        draft, trans, online, ParseLetterItems(items),
        letterId, attached);
    if (!attached)
    {
        // A letter always carries a gift. Nothing was attached,
        // so the transaction holds nothing worth committing.
        MarkLetter(letterId, "failed");
        return;
    }

    draft.SendMailTo(
        trans, MailReceiver(online, playerGuid), sender);
    trans->Append(
        "UPDATE llm_reactivity_letters SET status = 'sent', "
        "sent_at = NOW() WHERE id = {}", letterId);
    CharacterDatabase.CommitTransaction(trans);
}

} // namespace

void DeliverPendingReactivityLetters()
{
    if (!sLLMChatterConfig
        || !sLLMChatterConfig->_lettersEnable)
        return;

    QueryResult result = CharacterDatabase.Query(
        "SELECT id, player_guid, sender_type, sender_id, "
        "subject, body, items FROM llm_reactivity_letters "
        "WHERE status = 'ready' ORDER BY id LIMIT "
        + std::to_string(LETTERS_PER_TICK));
    if (!result)
        return;

    do
    {
        Field* fields = result->Fetch();
        SendLetter(
            fields[0].Get<uint32>(),
            fields[1].Get<uint32>(),
            fields[2].Get<std::string>(),
            fields[3].Get<uint32>(),
            fields[4].Get<std::string>(),
            fields[5].Get<std::string>(),
            fields[6].Get<std::string>());
    } while (result->NextRow());
}

namespace
{

// How often the fresh-rumor set is reloaded. A rumor the bridge has
// just unlocked waits at most this long, plus the bridge's own pass.
constexpr uint32 FRESH_RUMOR_REFRESH_MS = 10 * IN_MILLISECONDS;

// (player guid << 32) | zone id; zone 0 means anywhere. Read and
// written only on the world thread: the async callback runs from
// ProcessReadyCallbacks() in the world update.
std::unordered_set<uint64> _freshRumorZones;
QueryCallbackProcessor _freshRumorQueries;
bool _freshRumorQueryPending = false;
uint32 _lastFreshRumorRefresh = 0;

uint64 FreshRumorKey(uint32 playerGuid, uint32 zoneId)
{
    return (static_cast<uint64>(playerGuid) << 32) | zoneId;
}

} // namespace

void UpdateFreshRumorZones(uint32 now)
{
    _freshRumorQueries.ProcessReadyCallbacks();

    if (!sLLMChatterConfig || !sLLMChatterConfig->_rumorsEnable)
    {
        _freshRumorZones.clear();
        return;
    }
    if (_freshRumorQueryPending
        || now - _lastFreshRumorRefresh < FRESH_RUMOR_REFRESH_MS)
        return;

    _lastFreshRumorRefresh = now;
    _freshRumorQueryPending = true;
    _freshRumorQueries.AddCallback(
        CharacterDatabase.AsyncQuery(
            "SELECT player_guid, zone_id "
            "FROM llm_reactivity_fresh_rumor_zones")
        .WithCallback([](QueryResult result)
        {
            std::unordered_set<uint64> zones;
            if (result)
            {
                do
                {
                    Field* fields = result->Fetch();
                    zones.insert(FreshRumorKey(
                        fields[0].Get<uint32>(),
                        fields[1].Get<uint32>()));
                } while (result->NextRow());
            }
            _freshRumorZones.swap(zones);
            _freshRumorQueryPending = false;
        }));
}

bool HasFreshRumorHere(Player* player)
{
    if (!sLLMChatterConfig
        || !sLLMChatterConfig->_rumorsEnable
        || !player || _freshRumorZones.empty())
        return false;

    // Zone 0 marks a rumor that may be told anywhere.
    uint32 guid = player->GetGUID().GetCounter();
    return _freshRumorZones.count(FreshRumorKey(guid, 0))
        || _freshRumorZones.count(
            FreshRumorKey(guid, player->GetZoneId()));
}

void AddLLMChatterReactivityScripts()
{
    new LLMChatterReactivityPlayerScript();
}
