/*
 * mod-llm-chatter - group duel domain
 *
 * Owns:
 *   - LLMChatterDuelPlayerScript (duel start and end)
 *   - bot_group_duel_start / bot_group_duel_end events
 *
 * A duel qualifies when at least one duellist is in a
 * group with a real player and bots. Group bots that
 * watch the duel react as well as bot duellists.
 */

#include "LLMChatterConfig.h"
#include "LLMChatterGroupInternal.h"
#include "LLMChatterShared.h"

#include "Group.h"
#include "Player.h"
#include "ScriptMgr.h"

#include <ctime>
#include <mutex>
#include <string>
#include <unordered_map>
#include <vector>

namespace
{

enum class DuelEventKind : uint8
{
    Start = 0,
    End = 1,
};

std::unordered_map<uint64, time_t> _duelCooldowns;
std::mutex _duelCooldownMutex;

bool IsDuelChatterEnabled()
{
    return sLLMChatterConfig
        && sLLMChatterConfig->IsEnabled()
        && sLLMChatterConfig->_useGroupChatter
        && sLLMChatterConfig->_duelChatterEnable;
}

bool TryConsumeDuelCooldown(
    uint32 groupId, DuelEventKind kind, time_t now)
{
    std::lock_guard<std::mutex> lock(
        _duelCooldownMutex);

    // Opportunistic pruning keeps the map bounded.
    time_t maxAge = static_cast<time_t>(
        sLLMChatterConfig->_duelCooldown);
    for (auto it = _duelCooldowns.begin();
         it != _duelCooldowns.end(); )
    {
        if (now - it->second > maxAge)
            it = _duelCooldowns.erase(it);
        else
            ++it;
    }

    uint64 key = (static_cast<uint64>(groupId) << 8)
        | static_cast<uint8>(kind);
    auto it = _duelCooldowns.find(key);
    if (it != _duelCooldowns.end()
        && (now - it->second) < maxAge)
        return false;
    _duelCooldowns[key] = now;
    return true;
}

Group* GetQualifyingDuelGroup(Player* player)
{
    if (!player)
        return nullptr;
    if (player->InBattleground() || player->InArena())
        return nullptr;
    Group* group = player->GetGroup();
    if (!group || !GroupHasRealPlayer(group))
        return nullptr;
    return group;
}

// A group bot that can see at least one duellist.
// Bot duellists are candidates too.
Player* SelectDuelReactor(
    Group* group, Player* a, Player* b)
{
    std::vector<Player*> candidates;
    for (GroupReference* itr =
             group->GetFirstMember();
         itr != nullptr; itr = itr->next())
    {
        Player* member = itr->GetSource();
        if (!member || !IsPlayerBot(member)
            || !member->IsAlive())
            continue;
        if (IsPvPEnemyPerceivable(member, a)
            || IsPvPEnemyPerceivable(member, b))
            candidates.push_back(member);
    }
    if (candidates.empty())
        return nullptr;
    return candidates[urand(0, candidates.size() - 1)];
}

// The reactor knows itself and its own party members.
// Anyone else is known only if the reactor can see them,
// so a stealthed outsider is never identified.
bool IsDuellistKnownTo(
    Player* reactor, Player* duellist, Group* group)
{
    if (!reactor || !duellist)
        return false;
    if (reactor == duellist
        || duellist->GetGroup() == group)
        return true;
    return IsPvPEnemyPerceivable(reactor, duellist);
}

std::string BuildDuellistFields(
    char const* prefix, Player* duellist,
    Group* group, Player* reactor)
{
    std::string p(prefix);
    bool inGroup = duellist->GetGroup() == group;
    std::string json =
        "\"" + p + "_guid\":"
        + std::to_string(
            duellist->GetGUID().GetCounter())
        + ",\"" + p + "_in_group\":"
        + std::string(inGroup ? "true" : "false")
        + ",\"" + p + "_is_real_player\":"
        + std::string(
            (inGroup && !IsPlayerBot(duellist))
                ? "true" : "false");

    if (!IsDuellistKnownTo(reactor, duellist, group))
        return json + ",\"" + p
            + "_identity_known\":false";

    return json
        + ",\"" + p + "_identity_known\":true"
        + ",\"" + p + "_name\":\""
        + JsonEscape(duellist->GetName()) + "\""
        + ",\"" + p + "_race\":"
        + std::to_string(duellist->getRace())
        + ",\"" + p + "_class\":"
        + std::to_string(duellist->getClass())
        + ",\"" + p + "_level\":"
        + std::to_string(duellist->GetLevel());
}

char const* GetReactorRole(
    Player* reactor, Player* winner, Player* loser)
{
    if (reactor == winner)
        return "winner";
    if (reactor == loser)
        return "loser";
    return "spectator";
}

void QueueDuelEvent(
    char const* eventType, Group* group,
    Player* first, Player* second,
    std::string const& outcome,
    Player* initiator)
{
    uint32 chance = (std::string(eventType)
            == "bot_group_duel_start")
        ? sLLMChatterConfig->_duelStartChance
        : sLLMChatterConfig->_duelEndChance;
    if (urand(1, 100) > chance)
        return;

    Player* reactor =
        SelectDuelReactor(group, first, second);
    if (!reactor)
        return;

    uint32 groupId = group->GetGUID().GetCounter();
    DuelEventKind kind = outcome.empty()
        ? DuelEventKind::Start : DuelEventKind::End;
    if (!TryConsumeDuelCooldown(
            groupId, kind, time(nullptr)))
        return;

    bool isEnd = !outcome.empty();
    // For end events `first` is the winner and
    // `second` the loser.
    std::string role = isEnd
        ? GetReactorRole(reactor, first, second)
        : ((reactor == first || reactor == second)
            ? "duellist" : "spectator");

    uint32 botGuid = reactor->GetGUID().GetCounter();
    std::string botName = reactor->GetName();

    std::string extraData = "{"
        + BuildBotIdentityFields(reactor) + ","
        "\"group_id\":" +
            std::to_string(groupId) + ","
        + BuildDuellistFields(
            isEnd ? "winner" : "duellist_a",
            first, group, reactor) + ","
        + BuildDuellistFields(
            isEnd ? "loser" : "duellist_b",
            second, group, reactor) + ","
        "\"reactor_role\":\"" + role + "\",";
    if (isEnd)
        extraData += "\"outcome\":\"" + outcome
            + "\",";
    if (initiator
        && IsDuellistKnownTo(reactor, initiator, group))
        extraData += "\"initiator_name\":\""
            + JsonEscape(initiator->GetName())
            + "\",";
    extraData += BuildBotStateJson(reactor) + "}";

    extraData = EscapeString(extraData);

    QueueChatterEvent(
        eventType,
        "player",
        reactor->GetZoneId(),
        reactor->GetMapId(),
        GetChatterEventPriority(eventType),
        "",
        botGuid,
        botName,
        0,
        (isEnd && IsDuellistKnownTo(
                reactor, second, group))
            ? second->GetName() : "",
        0,
        extraData,
        GetReactionDelaySeconds(eventType),
        60,
        false
    );
}

// Queue for each distinct qualifying group among the
// duellists (both may share one group).
void QueueDuelEventForGroups(
    char const* eventType,
    Player* first, Player* second,
    std::string const& outcome,
    Player* initiator)
{
    Group* g1 = GetQualifyingDuelGroup(first);
    Group* g2 = GetQualifyingDuelGroup(second);
    if (g1)
        QueueDuelEvent(
            eventType, g1, first, second,
            outcome, initiator);
    if (g2 && g2 != g1)
        QueueDuelEvent(
            eventType, g2, first, second,
            outcome, initiator);
}

} // namespace

class LLMChatterDuelPlayerScript : public PlayerScript
{
public:
    LLMChatterDuelPlayerScript()
        : PlayerScript(
              "LLMChatterDuelPlayerScript",
              {PLAYERHOOK_ON_DUEL_START,
               PLAYERHOOK_ON_DUEL_END}) {}

    void OnPlayerDuelStart(
        Player* player1, Player* player2) override
    {
        if (!IsDuelChatterEnabled()
            || !player1 || !player2)
            return;

        Player* initiator = player1->duel
            ? player1->duel->Initiator : nullptr;
        QueueDuelEventForGroups(
            "bot_group_duel_start",
            player1, player2, "", initiator);
    }

    void OnPlayerDuelEnd(
        Player* winner, Player* loser,
        DuelCompleteType type) override
    {
        if (!IsDuelChatterEnabled()
            || !winner || !loser)
            return;

        // Only duels that actually started get an end
        // reaction. StartTime is 0 for a declined or
        // unaccepted challenge (DuelHandler sets it on
        // accept) and in the future during the countdown.
        if (!loser->duel
            || loser->duel->StartTime == 0
            || time(nullptr) < loser->duel->StartTime)
            return;

        std::string outcome;
        switch (type)
        {
            case DUEL_WON:
                outcome = "won";
                break;
            case DUEL_FLED:
                outcome = "fled";
                break;
            default:
                outcome = "interrupted";
                break;
        }

        QueueDuelEventForGroups(
            "bot_group_duel_end",
            winner, loser, outcome, nullptr);
    }
};

void AddLLMChatterDuelScripts()
{
    new LLMChatterDuelPlayerScript();
}
