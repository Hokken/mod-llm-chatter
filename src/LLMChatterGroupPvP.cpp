/*
 * mod-llm-chatter - group overworld PvP domain
 *
 * Owns:
 *   - opposing-faction enemy resolution (players and
 *     their pets; real players and playerbots alike)
 *   - the identity visibility gate for PvP payloads
 *   - PvP reactor selection and enemy JSON fields
 *   - PvP per-group and per-enemy cooldowns
 *   - PvP pull and player-kill entry points
 *
 * Battlegrounds and arenas are excluded; they have
 * their own domain in LLMChatterBG.cpp.
 */

#include "LLMChatterConfig.h"
#include "LLMChatterGroupInternal.h"
#include "LLMChatterShared.h"

#include "Group.h"
#include "Player.h"
#include "Unit.h"
// After Unit.h: Formulas.h uses Unit without declaring it.
#include "Formulas.h"

#include <algorithm>
#include <ctime>
#include <mutex>
#include <string>
#include <unordered_map>
#include <vector>

namespace
{

// Cooldown maps keyed by group and event kind, and by
// group, enemy, and event kind. Hooks run on map worker
// threads, so both maps share one mutex.
std::unordered_map<uint64, time_t> _pvpGroupCooldowns;
std::unordered_map<uint64, time_t> _pvpEnemyCooldowns;
std::mutex _pvpCooldownMutex;
time_t _pvpLastPrune = 0;

constexpr time_t PVP_PRUNE_INTERVAL = 600;

uint64 MakeGroupKindKey(
    uint32 groupId, PvPEventKind kind)
{
    return (static_cast<uint64>(groupId) << 8)
        | static_cast<uint8>(kind);
}

uint64 MakeEnemyKindKey(
    uint32 groupId, uint32 enemyGuid,
    PvPEventKind kind)
{
    // 24 bits of enemy GUID keep the key unique for
    // any realistic character GUID range.
    return (static_cast<uint64>(groupId) << 32)
        | (static_cast<uint64>(
               enemyGuid & 0xFFFFFF) << 8)
        | static_cast<uint8>(kind);
}

void PrunePvPCooldownsLocked(time_t now)
{
    if (now - _pvpLastPrune < PVP_PRUNE_INTERVAL)
        return;
    _pvpLastPrune = now;

    time_t maxAge = static_cast<time_t>(std::max(
        sLLMChatterConfig->_pvpCooldown,
        sLLMChatterConfig->_pvpEnemyCooldown));

    auto prune = [now, maxAge](auto& m)
    {
        for (auto it = m.begin(); it != m.end(); )
        {
            if (now - it->second > maxAge)
                it = m.erase(it);
            else
                ++it;
        }
    };
    prune(_pvpGroupCooldowns);
    prune(_pvpEnemyCooldowns);
}

bool IsQualifyingPvPGroup(
    Player* member, Group*& outGroup)
{
    outGroup = nullptr;
    if (!member)
        return false;
    if (member->InBattleground()
        || member->InArena())
        return false;

    Group* group = member->GetGroup();
    if (!group || !GroupHasRealPlayer(group))
        return false;

    outGroup = group;
    return true;
}

bool IsPvPChatterEnabled()
{
    return sLLMChatterConfig
        && sLLMChatterConfig->IsEnabled()
        && sLLMChatterConfig->_useGroupChatter
        && sLLMChatterConfig->_pvpChatterEnable;
}

} // namespace

// ============================================================
// Enemy resolution and visibility
// ============================================================

Player* ResolveOpposingFactionPlayer(
    Player* member, Unit* unit)
{
    if (!member || !unit)
        return nullptr;

    Player* enemy =
        unit->GetCharmerOrOwnerPlayerOrPlayerItself();
    if (!enemy || enemy == member)
        return nullptr;

    if (enemy->GetTeamId() == member->GetTeamId())
        return nullptr;

    if (member->InBattleground() || member->InArena()
        || enemy->InBattleground()
        || enemy->InArena())
        return nullptr;

    if (member->duel
        && member->duel->Opponent == enemy)
        return nullptr;

    return enemy;
}

bool IsPvPEnemyPerceivable(
    Player* reactor, Unit* unit)
{
    return IsUnitPerceivableBy(reactor, unit);
}

Player* SelectPvPReactor(
    Group* group, Player* exclude,
    Unit* enemyUnit, bool requireAlive)
{
    if (!group || !enemyUnit
        || !enemyUnit->IsInWorld())
        return nullptr;

    std::vector<Player*> perceiving;
    std::vector<Player*> sameMap;
    for (GroupReference* itr =
             group->GetFirstMember();
         itr != nullptr; itr = itr->next())
    {
        Player* member = itr->GetSource();
        if (!member || member == exclude
            || !IsPlayerBot(member))
            continue;
        if (requireAlive && !member->IsAlive())
            continue;
        if (!member->IsInMap(enemyUnit))
            continue;

        if (IsPvPEnemyPerceivable(member, enemyUnit))
            perceiving.push_back(member);
        else
            sameMap.push_back(member);
    }

    std::vector<Player*> const& pool =
        !perceiving.empty() ? perceiving : sameMap;
    if (pool.empty())
        return nullptr;
    return pool[urand(0, pool.size() - 1)];
}

std::string GetPerceivedPvPEnemyName(
    Player* reactor, PvPEnemyRef const& ref)
{
    if (!ref.enemy)
        return "";
    if (IsPvPEnemyPerceivable(reactor, ref.enemy))
        return ref.enemy->GetName();
    if (ref.viaPet && ref.unit
        && ref.unit != ref.enemy
        && IsPvPEnemyPerceivable(reactor, ref.unit))
        return ref.unit->GetName();
    return "";
}

char const* DetectPvPInitiator(
    Player* member, Player* enemy)
{
    if (!member || !enemy)
        return "unknown";

    Unit* enemyVictim = enemy->GetVictim();
    Player* enemyTarget = enemyVictim
        ? enemyVictim
              ->GetCharmerOrOwnerPlayerOrPlayerItself()
        : nullptr;
    bool enemyOnGroup = enemyTarget
        && enemyTarget->GetGroup()
        && enemyTarget->GetGroup()
               == member->GetGroup();

    Unit* memberVictim = member->GetVictim();
    Player* memberTarget = memberVictim
        ? memberVictim
              ->GetCharmerOrOwnerPlayerOrPlayerItself()
        : nullptr;
    bool memberOnEnemy = (memberTarget == enemy);

    if (enemyOnGroup && !memberOnEnemy)
        return "enemy";
    if (memberOnEnemy && !enemyOnGroup)
        return "group";
    return "unknown";
}

std::string BuildPvPEnemyFields(
    Player* reactor, Player* reference,
    PvPEnemyRef const& ref, char const* initiator)
{
    std::string json =
        "\"enemy_kind\":\"player\","
        "\"via_pet\":"
        + std::string(ref.viaPet ? "true" : "false")
        + ",\"initiator\":\""
        + std::string(initiator ? initiator : "unknown")
        + "\"";

    if (ref.viaPet && ref.unit
        && ref.unit != ref.enemy
        && IsPvPEnemyPerceivable(reactor, ref.unit))
    {
        json += ",\"enemy_pet_name\":\""
            + JsonEscape(ref.unit->GetName()) + "\"";
    }

    if (!ref.enemy
        || !IsPvPEnemyPerceivable(reactor, ref.enemy))
    {
        json += ",\"enemy_identity_known\":false";
        return json;
    }

    Player* enemy = ref.enemy;
    uint8 enemyLevel = enemy->GetLevel();
    uint8 refLevel = reference
        ? reference->GetLevel() : enemyLevel;
    int32 levelGap = static_cast<int32>(enemyLevel)
        - static_cast<int32>(refLevel);
    bool isGray = enemyLevel
        <= Acore::XP::GetGrayLevel(refLevel);

    json +=
        ",\"enemy_identity_known\":true"
        ",\"enemy_guid\":"
        + std::to_string(
            enemy->GetGUID().GetCounter())
        + ",\"enemy_name\":\""
        + JsonEscape(enemy->GetName()) + "\""
        + ",\"enemy_race\":"
        + std::to_string(enemy->getRace())
        + ",\"enemy_class\":"
        + std::to_string(enemy->getClass())
        + ",\"enemy_gender\":"
        + std::to_string(enemy->getGender())
        + ",\"enemy_level\":"
        + std::to_string(enemyLevel)
        + ",\"enemy_faction\":\""
        + std::string(
            enemy->GetTeamId() == TEAM_ALLIANCE
                ? "Alliance" : "Horde")
        + "\""
        + ",\"enemy_is_bot\":"
        + std::string(
            IsPlayerBot(enemy) ? "true" : "false")
        + ",\"level_gap\":"
        + std::to_string(levelGap)
        + ",\"is_gray_kill\":"
        + std::string(isGray ? "true" : "false");
    return json;
}

// ============================================================
// Cooldowns
// ============================================================

bool TryConsumePvPCooldown(
    uint32 groupId, uint32 enemyGuid,
    PvPEventKind kind, time_t now)
{
    std::lock_guard<std::mutex> lock(
        _pvpCooldownMutex);
    PrunePvPCooldownsLocked(now);

    uint64 groupKey = MakeGroupKindKey(groupId, kind);
    auto git = _pvpGroupCooldowns.find(groupKey);
    if (git != _pvpGroupCooldowns.end()
        && (now - git->second)
            < (time_t)sLLMChatterConfig->_pvpCooldown)
        return false;

    uint64 enemyKey = 0;
    if (enemyGuid)
    {
        enemyKey = MakeEnemyKindKey(
            groupId, enemyGuid, kind);
        auto eit = _pvpEnemyCooldowns.find(enemyKey);
        if (eit != _pvpEnemyCooldowns.end()
            && (now - eit->second)
                < (time_t)sLLMChatterConfig
                    ->_pvpEnemyCooldown)
            return false;
    }

    _pvpGroupCooldowns[groupKey] = now;
    if (enemyGuid)
        _pvpEnemyCooldowns[enemyKey] = now;
    return true;
}

void ClearPvPCooldownsForGroup(uint32 groupId)
{
    std::lock_guard<std::mutex> lock(
        _pvpCooldownMutex);
    for (auto it = _pvpGroupCooldowns.begin();
         it != _pvpGroupCooldowns.end(); )
    {
        if ((it->first >> 8) == groupId)
            it = _pvpGroupCooldowns.erase(it);
        else
            ++it;
    }
    for (auto it = _pvpEnemyCooldowns.begin();
         it != _pvpEnemyCooldowns.end(); )
    {
        if ((it->first >> 32) == groupId)
            it = _pvpEnemyCooldowns.erase(it);
        else
            ++it;
    }
}

// ============================================================
// PvP pull
// ============================================================

bool HandleGroupPvPEnterCombat(
    Player* player, Unit* enemyUnit)
{
    Player* enemy =
        ResolveOpposingFactionPlayer(player, enemyUnit);
    if (!enemy)
        return false;

    // From here on the enemy is an opposing-faction
    // player: never fall through to the creature path.
    if (!IsPvPChatterEnabled())
        return true;

    Group* group = nullptr;
    if (!IsQualifyingPvPGroup(player, group))
        return true;

    Player* reactor = nullptr;
    if (IsPlayerBot(player)
        && IsPvPEnemyPerceivable(player, enemy))
        reactor = player;
    else
        reactor = SelectPvPReactor(
            group, nullptr, enemy, true);

    // No anonymous pull: a hidden enemy stays hidden.
    if (!reactor
        || !IsPvPEnemyPerceivable(reactor, enemy))
        return true;

    if (urand(1, 100)
        > sLLMChatterConfig->_pvpCombatChance)
        return true;

    uint32 groupId = group->GetGUID().GetCounter();
    if (!TryConsumePvPCooldown(
            groupId,
            enemy->GetGUID().GetCounter(),
            PvPEventKind::Combat,
            time(nullptr)))
        return true;

    PvPEnemyRef ref;
    ref.enemy = enemy;
    ref.unit = enemyUnit;
    ref.viaPet = (enemyUnit != enemy);

    uint32 botGuid = reactor->GetGUID().GetCounter();
    std::string botName = reactor->GetName();
    std::string enemyName = enemy->GetName();

    std::string extraData = "{"
        + BuildBotIdentityFields(reactor) + ","
        "\"creature_name\":\"" +
            JsonEscape(enemyName) + "\","
        "\"creature_entry\":0,"
        "\"is_boss\":0,"
        "\"is_elite\":0,"
        "\"group_id\":" +
            std::to_string(groupId) + ","
        + BuildPvPEnemyFields(
            reactor, player, ref,
            DetectPvPInitiator(player, enemy))
        + ","
        + BuildBotStateJson(reactor) + "}";

    extraData = EscapeString(extraData);

    QueueChatterEvent(
        "bot_group_combat",
        "player",
        reactor->GetZoneId(),
        reactor->GetMapId(),
        GetChatterEventPriority("bot_group_combat"),
        "",
        botGuid,
        botName,
        0,
        enemyName,
        0,
        extraData,
        GetReactionDelaySeconds("bot_group_combat"),
        30,
        false
    );
    return true;
}

// ============================================================
// PvP kills and deaths
// ============================================================

namespace
{

// A group member (or a group member's pet) killed an
// opposing-faction player.
void QueueGroupPvPKill(
    Player* groupKiller, PvPEnemyRef const& ref,
    bool killerIsPet)
{
    Group* group = nullptr;
    if (!IsQualifyingPvPGroup(groupKiller, group))
        return;

    Player* enemy = ref.enemy;
    if (!enemy)
        return;

    Player* reactor = nullptr;
    if (IsPlayerBot(groupKiller)
        && !killerIsPet
        && IsPvPEnemyPerceivable(groupKiller, enemy))
        reactor = groupKiller;
    else
        reactor = SelectPvPReactor(
            group, nullptr, enemy, true);
    if (!reactor)
        return;

    if (urand(1, 100)
        > sLLMChatterConfig->_pvpKillChance)
        return;

    uint32 groupId = group->GetGUID().GetCounter();
    if (!TryConsumePvPCooldown(
            groupId,
            enemy->GetGUID().GetCounter(),
            PvPEventKind::Kill,
            time(nullptr)))
        return;

    uint32 botGuid = reactor->GetGUID().GetCounter();
    std::string botName = reactor->GetName();
    std::string enemyName =
        GetPerceivedPvPEnemyName(reactor, ref);

    std::string extraData = "{"
        + BuildBotIdentityFields(reactor) + ","
        "\"creature_name\":\"" +
            JsonEscape(enemyName) + "\","
        "\"creature_entry\":0,"
        "\"is_boss\":false,"
        "\"is_rare\":false,"
        "\"is_normal\":false,"
        "\"killer_name\":\"" +
            JsonEscape(groupKiller->GetName()) + "\","
        "\"killer_is_pet\":" +
            std::string(
                killerIsPet ? "true" : "false") + ","
        "\"group_id\":" +
            std::to_string(groupId) + ","
        + BuildPvPEnemyFields(
            reactor, groupKiller, ref, "unknown")
        + ","
        + BuildBotStateJson(reactor) + "}";

    extraData = EscapeString(extraData);

    QueueChatterEvent(
        "bot_group_kill",
        "player",
        reactor->GetZoneId(),
        reactor->GetMapId(),
        GetChatterEventPriority("bot_group_kill"),
        "",
        botGuid,
        botName,
        0,
        enemyName,
        0,
        extraData,
        GetReactionDelaySeconds("bot_group_kill"),
        120,
        false
    );
}

void QueueGroupPvPDeath(
    Player* killed, PvPEnemyRef const& ref)
{
    Group* group = nullptr;
    if (!IsQualifyingPvPGroup(killed, group))
        return;

    QueueGroupDeathOrWipe(
        killed, group, "", 0, &ref);
}

} // namespace

void HandleGroupPvPKillImpl(
    Player* killer, Player* killed)
{
    if (!IsPvPChatterEnabled())
        return;
    if (!killer || !killed || killer == killed)
        return;

    // The killer's group gets a kill reaction.
    if (Player* enemy =
            ResolveOpposingFactionPlayer(
                killer, killed))
    {
        PvPEnemyRef ref;
        ref.enemy = enemy;
        ref.unit = killed;
        QueueGroupPvPKill(killer, ref, false);
    }

    // The victim's group gets a death reaction.
    if (Player* enemy =
            ResolveOpposingFactionPlayer(
                killed, killer))
    {
        PvPEnemyRef ref;
        ref.enemy = enemy;
        ref.unit = killer;
        QueueGroupPvPDeath(killed, ref);
    }
}

bool HandleGroupPetPvPKill(
    Creature* killer, Player* killed)
{
    if (!killer || !killed)
        return false;

    Player* owner =
        killer->GetCharmerOrOwnerPlayerOrPlayerItself();
    if (!owner)
        return false;

    // Owner on the victim's team: not overworld PvP,
    // keep the existing creature-death behavior.
    if (!ResolveOpposingFactionPlayer(killed, killer))
        return false;

    if (!IsPvPChatterEnabled())
        return true;

    // The pet owner's group gets a kill reaction.
    {
        PvPEnemyRef ref;
        ref.enemy = killed;
        ref.unit = killed;
        QueueGroupPvPKill(owner, ref, true);
    }

    // The victim's group gets a death reaction.
    {
        PvPEnemyRef ref;
        ref.enemy = owner;
        ref.unit = killer;
        ref.viaPet = true;
        QueueGroupPvPDeath(killed, ref);
    }
    return true;
}
