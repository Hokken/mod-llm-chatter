/*
 * mod-llm-chatter - safe pre-aggro boss dialogue
 */

#include "LLMChatterBossDialogue.h"

#include "LLMChatterConfig.h"
#include "LLMChatterProximity.h"
#include "LLMChatterShared.h"

#include "CellImpl.h"
#include "Creature.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "WorldSession.h"
#include "WorldSessionMgr.h"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <ctime>
#include <list>
#include <map>
#include <mutex>
#include <sstream>
#include <string>
#include <vector>

namespace
{
struct NearbyBossCheck
{
    WorldObject const* focus;
    float radius;

    NearbyBossCheck(WorldObject const* object, float range)
        : focus(object), radius(range) {}

    WorldObject const& GetFocusObject() const
    {
        return *focus;
    }

    bool operator()(Creature* creature)
    {
        return creature && creature->IsAlive()
            && !IsLLMChatterInternalCreature(creature)
            && IsLLMChatterBoss(creature)
            && focus->IsWithinDistInMap(creature, radius);
    }
};

struct BossPresenceState
{
    uint32 linesQueued = 0;
    uint64 presenceId = 0;
    time_t lastEligibleAt = 0;
    time_t nextOpportunityAt = 0;
};

std::map<std::string, BossPresenceState> _bossPresenceStates;
std::map<std::string, time_t> _bossDirectedCooldowns;
std::map<std::string, time_t> _bossPendingUntil;
std::map<uint32, time_t> _bossPlayerScanTimes;
std::map<std::string, time_t> _bossDirectedScanTimes;
std::mutex _bossDialogueStateMutex;
time_t _nextBossStateEviction = 0;
uint32 _lastBossScanPlayerGuid = 0;

bool IsBossMapAllowed(Map const* map)
{
    if (!map || map->IsBattlegroundOrArena())
        return false;
    if (map->IsRaid())
        return sLLMChatterConfig->_proxChatterEnableInRaids;
    return map->IsDungeon()
        && sLLMChatterConfig->_proxChatterEnableInDungeons;
}

bool IsBossAnchorEligible(Player* player)
{
    return IsProximityAnchorEligible(player)
        && IsBossMapAllowed(player->GetMap());
}

float GetBossAggroDistance(
    Player* player, Creature* creature);
void MaybeEvictExpiredBossDialogueState(time_t now);

float GetBossSafeDistance(
    Player* player, Creature* creature)
{
    if (!player || !creature)
        return 0.0f;

    return GetBossAggroDistance(player, creature)
        + static_cast<float>(
            sLLMChatterConfig->_proxBossAggroSafetyMargin);
}

float GetBossAggroDistance(
    Player* player, Creature* creature)
{
    if (!player || !creature)
        return 0.0f;
    return creature->GetAggroRange(player)
        + std::max(0.0f, creature->m_CombatDistance);
}

std::string GetBossPresenceKey(Creature* creature)
{
    Map* map = creature ? creature->GetMap() : nullptr;
    return "boss:auto:"
        + std::to_string(
            creature ? creature->GetMapId() : 0)
        + ":" + std::to_string(
            map ? map->GetInstanceId() : 0)
        + ":" + std::to_string(
            creature ? creature->GetSpawnId() : 0);
}

std::string GetBossDirectedCooldownKey(
    Player* player, Creature* creature)
{
    Map* map = player ? player->GetMap() : nullptr;
    return std::to_string(
        player ? player->GetGUID().GetCounter() : 0)
        + ":" + std::to_string(
            player ? player->GetMapId() : 0)
        + ":" + std::to_string(
            map ? map->GetInstanceId() : 0)
        + ":" + std::to_string(
            creature ? creature->GetSpawnId() : 0);
}

std::string GetBossPlayerMapKey(Player* player)
{
    Map* map = player ? player->GetMap() : nullptr;
    return std::to_string(
        player ? player->GetGUID().GetCounter() : 0)
        + ":" + std::to_string(
            player ? player->GetMapId() : 0)
        + ":" + std::to_string(
            map ? map->GetInstanceId() : 0);
}

std::string NormalizeName(std::string const& value)
{
    std::string normalized;
    normalized.reserve(value.size());
    bool pendingSpace = false;
    for (unsigned char character : value)
    {
        if (std::isalnum(character))
        {
            if (pendingSpace && !normalized.empty())
                normalized += ' ';
            normalized += static_cast<char>(
                std::tolower(character));
            pendingSpace = false;
        }
        else
        {
            pendingSpace = true;
        }
    }
    return normalized;
}

enum class BossNameMatch
{
    None,
    FirstToken,
    Full
};

BossNameMatch GetBossNameMatch(
    std::string const& normalizedMessage,
    Creature* creature)
{
    if (!creature)
        return BossNameMatch::None;

    std::string normalizedName =
        NormalizeName(creature->GetName());
    if (!normalizedName.empty()
        && normalizedMessage.find(
            " " + normalizedName + " ")
            != std::string::npos)
        return BossNameMatch::Full;

    size_t firstSpace = normalizedName.find(' ');
    std::string firstName = normalizedName.substr(
        0, firstSpace);
    if (firstName.size() >= 3
        && normalizedMessage.find(
            " " + firstName + " ")
            != std::string::npos)
        return BossNameMatch::FirstToken;
    return BossNameMatch::None;
}

void CollectNearbyBosses(
    Player* player, float radius,
    std::vector<Creature*>& bosses,
    bool requireEligible = true)
{
    std::list<Creature*> creatures;
    NearbyBossCheck check(player, radius);
    Acore::CreatureListSearcher<NearbyBossCheck> searcher(
        player, creatures, check);
    Cell::VisitObjects(player, searcher, radius);

    for (Creature* creature : creatures)
    {
        if (!requireEligible
            || IsBossDialogueSpeakerEligible(
                player, creature, radius))
            bosses.push_back(creature);
    }

    std::sort(
        bosses.begin(), bosses.end(),
        [player](Creature* left, Creature* right)
        {
            return player->GetDistance(left)
                < player->GetDistance(right);
        });
}

std::string GetBossRank(Creature const* creature)
{
    CreatureTemplate const* creatureTemplate =
        creature ? creature->GetCreatureTemplate() : nullptr;
    if (!creatureTemplate)
        return "boss";
    if (creatureTemplate->rank == CREATURE_ELITE_WORLDBOSS)
        return "world boss";
    if (creatureTemplate->rank == CREATURE_ELITE_RAREELITE)
        return "rare elite";
    if (creatureTemplate->rank == CREATURE_ELITE_ELITE)
        return "elite";
    return "boss";
}

std::string BuildBossEventJson(
    Player* player, Creature* boss,
    std::string const& trigger,
    std::string const& playerMessage)
{
    Map* map = player->GetMap();
    CreatureTemplate const* creatureTemplate =
        boss->GetCreatureTemplate();
    char const* rawMapName = map ? map->GetMapName() : nullptr;
    uint32 distance = static_cast<uint32>(
        std::ceil(player->GetDistance(boss)));
    float aggroDistance = GetBossAggroDistance(
        player, boss);
    uint32 safeDistance = static_cast<uint32>(
        std::ceil(GetBossSafeDistance(player, boss)));

    std::ostringstream json;
    json << "{\"player_guid\":"
         << player->GetGUID().GetCounter()
         << ",\"player_name\":\""
         << JsonEscape(player->GetName())
         << "\",\"zone_id\":" << player->GetZoneId()
         << ",\"zone_name\":\""
         << JsonEscape(GetZoneName(player->GetZoneId()))
         << "\",\"subzone_name\":\""
         << JsonEscape(GetZoneName(player->GetAreaId()))
         << "\",\"map_id\":" << player->GetMapId()
         << ",\"instance_id\":"
         << (map ? map->GetInstanceId() : 0)
         << ",\"map_name\":\""
         << JsonEscape(rawMapName ? rawMapName : "")
         << "\",\"is_dungeon\":"
         << (map && map->IsDungeon() ? "true" : "false")
         << ",\"is_raid\":"
         << (map && map->IsRaid() ? "true" : "false")
         << ",\"encounter_state\":\"pre_aggro\""
         << ",\"trigger\":\"" << JsonEscape(trigger)
         << "\",\"player_message\":\""
         << JsonEscape(playerMessage)
         << "\",\"distance\":" << distance
         << ",\"safe_distance\":" << safeDistance
         << ",\"boss\":{\"name\":\""
         << JsonEscape(boss->GetName())
         << "\",\"entry\":" << boss->GetEntry()
         << ",\"spawn_id\":" << boss->GetSpawnId()
         << ",\"role\":\""
         << JsonEscape(GetCreatureRoleName(boss))
         << "\",\"sub_name\":\""
         << JsonEscape(
                creatureTemplate
                    ? creatureTemplate->SubName : "")
         << "\",\"disposition\":\"hostile\""
         << ",\"rank\":\""
         << JsonEscape(GetBossRank(boss))
         << "\"}}";
    std::ostringstream safetyMetadata;
    safetyMetadata
        << ",\"aggro_distance\":"
        << static_cast<uint32>(std::ceil(aggroDistance))
        << ",\"safety_margin\":"
        << sLLMChatterConfig->_proxBossAggroSafetyMargin;
    std::string result = json.str();
    result.insert(result.size() - 1, safetyMetadata.str());
    return result;
}

void QueueBossDialogueEvent(
    Player* player, Creature* boss,
    char const* eventType,
    std::string const& playerMessage,
    std::string const& cooldownKey,
    uint32 automaticLineNumber,
    uint64 presenceId)
{
    std::string json = BuildBossEventJson(
        player, boss, eventType, playerMessage);
    if (automaticLineNumber > 0)
    {
        std::string lineMetadata =
            ",\"automatic_line_number\":"
            + std::to_string(automaticLineNumber);
        json.insert(json.size() - 1, lineMetadata);
    }
    if (presenceId > 0)
    {
        std::string presenceMetadata =
            ",\"presence_id\":"
            + std::to_string(presenceId);
        json.insert(json.size() - 1, presenceMetadata);
    }
    QueueChatterEvent(
        eventType,
        "player",
        player->GetZoneId(),
        player->GetMapId(),
        GetChatterEventPriority(eventType),
        cooldownKey,
        0,
        boss->GetName(),
        player->GetGUID().GetCounter(),
        player->GetName(),
        boss->GetEntry(),
        EscapeString(json),
        1,
        15,
        false);
}

uint32 GetRandomBossDelay(uint32 minimum, uint32 maximum)
{
    minimum = std::max<uint32>(1, minimum);
    maximum = std::max(minimum, maximum);
    return urand(minimum, maximum);
}

uint32 GetBossRepeatChance(uint32 linesQueued)
{
    uint32 chance = std::min<uint32>(
        100, sLLMChatterConfig->_proxBossRepeatChance);
    uint32 minimumChance = std::min(
        chance,
        std::min<uint32>(
            100,
            sLLMChatterConfig->_proxBossRepeatChanceFloor));
    uint32 decay = std::min<uint32>(
        100, sLLMChatterConfig->_proxBossRepeatChanceDecay);
    for (uint32 line = 1; line < linesQueued; ++line)
        chance = std::max(
            minimumChance, chance * decay / 100);
    return chance;
}

void ResetBossPresenceState(
    BossPresenceState& state, time_t now)
{
    state = BossPresenceState{};
    state.presenceId = static_cast<uint64>(now);
    state.lastEligibleAt = now;
}

bool TryScheduleBossApproach(
    Creature* boss, uint32& automaticLineNumber,
    uint64& presenceId)
{
    automaticLineNumber = 0;
    presenceId = 0;
    std::string presenceKey = GetBossPresenceKey(boss);
    uint32 resetSeconds = std::max<uint32>(
        1, sLLMChatterConfig->_proxBossPresenceReset);

    std::lock_guard<std::mutex> lock(
        _bossDialogueStateMutex);
    time_t now = time(nullptr);
    MaybeEvictExpiredBossDialogueState(now);
    BossPresenceState& state =
        _bossPresenceStates[presenceKey];
    if (state.lastEligibleAt == 0
        || now - state.lastEligibleAt
            > static_cast<time_t>(resetSeconds))
        ResetBossPresenceState(state, now);
    else
        state.lastEligibleAt = now;
    presenceId = state.presenceId;

    if (state.nextOpportunityAt == 0)
    {
        state.nextOpportunityAt = now
            + static_cast<time_t>(GetRandomBossDelay(
                sLLMChatterConfig->_proxBossInitialDelayMin,
                sLLMChatterConfig->_proxBossInitialDelayMax));
        return false;
    }

    uint32 maximumLines =
        sLLMChatterConfig->_proxBossMaxAutomaticLines;
    bool reachedConfiguredLimit =
        !sLLMChatterConfig->_proxBossUnlimitedAutomaticLines
        && (maximumLines == 0
            || state.linesQueued >= maximumLines);
    if (reachedConfiguredLimit
        || now < state.nextOpportunityAt)
        return false;

    state.nextOpportunityAt = now
        + static_cast<time_t>(GetRandomBossDelay(
            sLLMChatterConfig->_proxBossRepeatDelayMin,
            sLLMChatterConfig->_proxBossRepeatDelayMax));
    if (state.linesQueued > 0
        && urand(1, 100)
            > GetBossRepeatChance(state.linesQueued))
        return false;

    automaticLineNumber = ++state.linesQueued;
    return true;
}

uint64 PostponeBossApproach(Creature* boss)
{
    std::lock_guard<std::mutex> lock(
        _bossDialogueStateMutex);
    time_t now = time(nullptr);
    std::string presenceKey = GetBossPresenceKey(boss);
    BossPresenceState& state =
        _bossPresenceStates[presenceKey];
    uint32 resetSeconds = std::max<uint32>(
        1, sLLMChatterConfig->_proxBossPresenceReset);
    if (state.lastEligibleAt == 0
        || now - state.lastEligibleAt
            > static_cast<time_t>(resetSeconds))
        ResetBossPresenceState(state, now);
    else
        state.lastEligibleAt = now;
    state.nextOpportunityAt = now
        + static_cast<time_t>(GetRandomBossDelay(
            sLLMChatterConfig->_proxBossRepeatDelayMin,
            sLLMChatterConfig->_proxBossRepeatDelayMax));
    return state.presenceId;
}

void EvictExpiredBossDialogueState(time_t now)
{
    auto evictCooldowns = [now](
        std::map<std::string, time_t>& cooldowns,
        uint32 lifetime)
    {
        for (auto it = cooldowns.begin(); it != cooldowns.end();)
        {
            if (now - it->second
                > static_cast<time_t>(lifetime))
                it = cooldowns.erase(it);
            else
                ++it;
        }
    };
    evictCooldowns(
        _bossDirectedCooldowns,
        sLLMChatterConfig->_proxBossDirectedReplyCooldown);
    uint32 presenceResetSeconds = std::max<uint32>(
        1, sLLMChatterConfig->_proxBossPresenceReset);
    for (auto it = _bossPresenceStates.begin();
         it != _bossPresenceStates.end();)
    {
        if (now - it->second.lastEligibleAt
            > static_cast<time_t>(presenceResetSeconds))
            it = _bossPresenceStates.erase(it);
        else
            ++it;
    }
    for (auto it = _bossPendingUntil.begin();
         it != _bossPendingUntil.end();)
    {
        if (it->second <= now)
            it = _bossPendingUntil.erase(it);
        else
            ++it;
    }

    time_t scanLifetime = std::max<time_t>(
        60,
        static_cast<time_t>(
            sLLMChatterConfig
                ->_proxBossApproachCheckInterval) * 4);
    for (auto it = _bossPlayerScanTimes.begin();
         it != _bossPlayerScanTimes.end();)
    {
        if (now - it->second > scanLifetime)
            it = _bossPlayerScanTimes.erase(it);
        else
            ++it;
    }

    time_t directedScanLifetime = std::max<time_t>(
        60,
        static_cast<time_t>(
            sLLMChatterConfig
                ->_proxBossDirectedScanCooldown) * 4);
    for (auto it = _bossDirectedScanTimes.begin();
         it != _bossDirectedScanTimes.end();)
    {
        if (now - it->second > directedScanLifetime)
            it = _bossDirectedScanTimes.erase(it);
        else
            ++it;
    }
}

void MaybeEvictExpiredBossDialogueState(time_t now)
{
    if (now < _nextBossStateEviction)
        return;
    EvictExpiredBossDialogueState(now);
    _nextBossStateEviction = now + 60;
}

bool TryBeginBossPlayerScan(
    uint32 playerGuid, uint32 intervalSeconds)
{
    std::lock_guard<std::mutex> lock(
        _bossDialogueStateMutex);
    time_t now = time(nullptr);
    MaybeEvictExpiredBossDialogueState(now);

    intervalSeconds = std::max<uint32>(
        1, intervalSeconds);
    auto found = _bossPlayerScanTimes.find(playerGuid);
    if (found != _bossPlayerScanTimes.end()
        && now - found->second
            < static_cast<time_t>(intervalSeconds))
        return false;

    _bossPlayerScanTimes[playerGuid] = now;
    return true;
}

bool TryBeginBossDirectedScan(
    std::string const& playerMapKey,
    uint32 cooldownSeconds)
{
    std::lock_guard<std::mutex> lock(
        _bossDialogueStateMutex);
    time_t now = time(nullptr);
    MaybeEvictExpiredBossDialogueState(now);

    cooldownSeconds = std::max<uint32>(
        1, cooldownSeconds);
    auto found = _bossDirectedScanTimes.find(playerMapKey);
    if (found != _bossDirectedScanTimes.end()
        && now - found->second
            < static_cast<time_t>(cooldownSeconds))
        return false;

    _bossDirectedScanTimes[playerMapKey] = now;
    return true;
}

bool IsBossDialogueBlocked(
    std::map<std::string, time_t> const& cooldowns,
    std::string const& cooldownKey,
    uint32 cooldownSeconds,
    time_t now)
{
    auto pending = _bossPendingUntil.find(cooldownKey);
    if (pending != _bossPendingUntil.end()
        && pending->second > now)
        return true;

    auto cooldown = cooldowns.find(cooldownKey);
    return cooldown != cooldowns.end()
        && now - cooldown->second
            < static_cast<time_t>(cooldownSeconds);
}

bool TryReserveBossDialogue(
    std::map<std::string, time_t>& cooldowns,
    std::string const& cooldownKey,
    uint32 cooldownSeconds)
{
    {
        std::lock_guard<std::mutex> lock(
            _bossDialogueStateMutex);
        time_t now = time(nullptr);
        MaybeEvictExpiredBossDialogueState(now);
        if (IsBossDialogueBlocked(
                cooldowns, cooldownKey,
                cooldownSeconds, now))
            return false;
    }

    if (IsPersistedEventOnCooldown(
            cooldownKey, cooldownSeconds))
        return false;

    std::lock_guard<std::mutex> lock(
        _bossDialogueStateMutex);
    time_t now = time(nullptr);
    MaybeEvictExpiredBossDialogueState(now);
    if (IsBossDialogueBlocked(
            cooldowns, cooldownKey,
            cooldownSeconds, now))
        return false;

    _bossPendingUntil[cooldownKey] = now + 15;
    SetEventCooldown(cooldowns, cooldownKey);
    return true;
}
} // namespace

bool IsBossDialogueEntryDenied(uint32 creatureEntry)
{
    return sLLMChatterConfig
        && sLLMChatterConfig
            ->IsProximityBossSpeakerDenied(creatureEntry);
}

bool IsBossDialogueSpeakerEligible(
    Player* player, Creature* creature, float radius)
{
    if (!IsBossAnchorEligible(player) || !creature)
        return false;
    if (!creature->IsAlive() || creature->IsInCombat())
        return false;
    if (IsLLMChatterInternalCreature(creature)
        || creature->HasUnitState(UNIT_STATE_DIED)
        || creature->HasDynamicFlag(UNIT_DYNFLAG_DEAD))
        return false;
    if (!creature->GetSpawnId()
        || !IsLLMChatterBoss(creature)
        || IsBossDialogueEntryDenied(creature->GetEntry()))
        return false;
    if (creature->GetMap() != player->GetMap())
        return false;
    if (!creature->IsHostileTo(player))
        return false;
    if (!player->IsWithinDistInMap(creature, radius))
        return false;
    if (!player->CanSeeOrDetect(creature)
        || !player->IsWithinLOSInMap(creature)
        || !creature->CanSeeOrDetect(player))
        return false;

    return player->GetDistance(creature)
        > GetBossSafeDistance(player, creature);
}

void CheckBossProximityDialogue()
{
    if (!sLLMChatterConfig
        || !sLLMChatterConfig->IsEnabled()
        || !sLLMChatterConfig->_useEventSystem
        || !sLLMChatterConfig->_proxChatterEnable
        || !sLLMChatterConfig->_proxBossDialogueEnable)
        return;

    float radius = static_cast<float>(
        sLLMChatterConfig->_proxBossApproachMaxRadius);
    if (radius <= 0.0f)
        return;
    WorldSessionMgr::SessionMap const& sessions =
        sWorldSessionMgr->GetAllSessions();
    std::vector<Player*> players;
    for (auto const& pair : sessions)
    {
        WorldSession* session = pair.second;
        if (!session || session->PlayerLoading())
            continue;

        Player* player = session->GetPlayer();
        if (!player || IsPlayerBot(player)
            || !IsBossAnchorEligible(player))
            continue;
        players.push_back(player);
    }
    if (players.empty())
        return;

    size_t startIndex = 0;
    for (size_t index = 0; index < players.size(); ++index)
    {
        if (players[index]->GetGUID().GetCounter()
            == _lastBossScanPlayerGuid)
        {
            startIndex = (index + 1) % players.size();
            break;
        }
    }

    for (size_t offset = 0; offset < players.size(); ++offset)
    {
        Player* player = players[
            (startIndex + offset) % players.size()];
        if (!TryBeginBossPlayerScan(
                player->GetGUID().GetCounter(),
                sLLMChatterConfig
                    ->_proxBossApproachCheckInterval))
            continue;
        _lastBossScanPlayerGuid =
            player->GetGUID().GetCounter();

        std::vector<Creature*> bosses;
        CollectNearbyBosses(player, radius, bosses);
        if (bosses.empty())
            return;

        Creature* boss = bosses.front();
        uint32 automaticLineNumber = 0;
        uint64 presenceId = 0;
        if (!TryScheduleBossApproach(
                boss, automaticLineNumber,
                presenceId))
            return;

        std::string presenceKey =
            GetBossPresenceKey(boss);
        QueueBossDialogueEvent(
            player, boss,
            "proximity_boss_approach", "",
            presenceKey, automaticLineNumber,
            presenceId);
        return;
    }
}

bool HandleBossProximityPlayerSay(
    Player* player, std::string const& message)
{
    if (!sLLMChatterConfig
        || !sLLMChatterConfig->_proxBossDialogueEnable
        || message.empty()
        || !IsBossAnchorEligible(player))
        return false;

    float radius = static_cast<float>(
        sLLMChatterConfig->_proxBossApproachMaxRadius);
    ObjectGuid selectedGuid =
        player->GetGuidValue(UNIT_FIELD_TARGET);
    Unit* selected = selectedGuid
        ? ObjectAccessor::GetUnit(*player, selectedGuid)
        : nullptr;
    Creature* selectedBoss = selected
        ? selected->ToCreature() : nullptr;
    bool selectedNearbyBoss = selectedBoss
        && !IsLLMChatterInternalCreature(selectedBoss)
        && IsLLMChatterBoss(selectedBoss)
        && selectedBoss->GetMap() == player->GetMap()
        && player->IsWithinDistInMap(selectedBoss, radius);
    std::string normalizedMessage =
        " " + NormalizeName(message) + " ";
    bool messageNamesSelectedBoss = selectedNearbyBoss
        && GetBossNameMatch(
            normalizedMessage, selectedBoss)
            != BossNameMatch::None;

    if (!TryBeginBossDirectedScan(
            GetBossPlayerMapKey(player),
            sLLMChatterConfig
                ->_proxBossDirectedScanCooldown))
        return messageNamesSelectedBoss;

    std::vector<Creature*> bosses;
    CollectNearbyBosses(
        player, radius, bosses, false);

    Creature* directedBoss = nullptr;
    std::vector<Creature*> firstTokenMatches;
    bool ambiguousFirstToken = false;
    for (Creature* boss : bosses)
    {
        BossNameMatch match = GetBossNameMatch(
            normalizedMessage, boss);
        if (match == BossNameMatch::Full)
        {
            if (!IsBossDialogueSpeakerEligible(
                    player, boss, radius))
                return true;
            directedBoss = boss;
            break;
        }
        if (match == BossNameMatch::FirstToken)
            firstTokenMatches.push_back(boss);
    }

    if (!directedBoss && !firstTokenMatches.empty())
    {
        uint32 matchedEntry =
            firstTokenMatches.front()->GetEntry();
        bool ambiguous = std::any_of(
            firstTokenMatches.begin(),
            firstTokenMatches.end(),
            [matchedEntry](Creature* boss)
            {
                return boss->GetEntry() != matchedEntry;
            });
        if (ambiguous)
            ambiguousFirstToken = true;
        else
        {
            Creature* boss = firstTokenMatches.front();
            if (!IsBossDialogueSpeakerEligible(
                    player, boss, radius))
                return true;
            directedBoss = boss;
        }
    }

    if (!directedBoss && selectedNearbyBoss)
    {
        if (!IsBossDialogueSpeakerEligible(
                player, selectedBoss, radius))
            return true;
        directedBoss = selectedBoss;
    }

    if (!directedBoss && ambiguousFirstToken)
        return true;
    if (!directedBoss)
        return false;

    std::string cooldownKey =
        GetBossDirectedCooldownKey(player, directedBoss);
    if (!TryReserveBossDialogue(
            _bossDirectedCooldowns,
            cooldownKey,
            sLLMChatterConfig
                ->_proxBossDirectedReplyCooldown))
        return true;

    uint64 presenceId = PostponeBossApproach(
        directedBoss);
    QueueBossDialogueEvent(
        player, directedBoss,
        "proximity_boss_player_say", message,
        cooldownKey, 0, presenceId);
    return true;
}
