/*
 * mod-llm-chatter - proximity chatter domain
 */

#include "LLMChatterProximity.h"

#include "LLMChatterBossDialogue.h"
#include "LLMChatterConfig.h"
#include "LLMChatterShared.h"

#include "CellImpl.h"
#include "Creature.h"
#include "DBCStores.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "Group.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Playerbots.h"
#include "RandomPlayerbotMgr.h"
#include "ScriptedCreature.h"
#include "Map.h"
#include "World.h"
#include "WorldSession.h"
#include "WorldSessionMgr.h"

#include <algorithm>
#include <cctype>
#include <ctime>
#include <list>
#include <map>
#include <random>
#include <string>
#include <vector>

namespace
{
struct NearbyCreatureCheck
{
    WorldObject const* _obj;
    float _range;

    NearbyCreatureCheck(
        WorldObject const* obj, float range)
        : _obj(obj), _range(range) {}

    WorldObject const& GetFocusObject() const
    {
        return *_obj;
    }

    bool operator()(Unit* unit)
    {
        if (!unit || !unit->IsAlive())
            return false;
        if (!unit->ToCreature())
            return false;
        return _obj->IsWithinDistInMap(unit, _range);
    }
};

struct NearbyBotCheck
{
    WorldObject const* _obj;
    float _range;

    NearbyBotCheck(
        WorldObject const* obj, float range)
        : _obj(obj), _range(range) {}

    bool operator()(Player* other)
    {
        return other && other->IsInWorld()
            && _obj->IsWithinDistInMap(other, _range);
    }
};

struct ProximityCandidate
{
    bool isNPC = false;
    Player* bot = nullptr;
    Creature* npc = nullptr;
    uint32 id = 0;
    uint32 entry = 0;
    std::string name;
    std::string role;
    std::string className;
    std::string raceName;
    std::string subName;
};

struct ProximityParticipant
{
    uint32 id = 0;
    bool isNPC = false;
    std::string name;
};

struct ProximityScene
{
    uint32 sceneId = 0;
    uint32 playerGuid = 0;
    uint32 zoneId = 0;
    uint32 mapId = 0;
    uint32 instanceId = 0;
    std::vector<ProximityParticipant> participants;
    uint32 lastSpeakerId = 0;
    bool lastSpeakerIsNPC = false;
    std::string lastSpeakerName;
    std::string lastMessage;
    time_t lastActivity = 0;
    uint8 replyCount = 0;
    bool pendingReply = false;
    bool replyEligible = false;

    bool IsExpired() const
    {
        uint32 expiry =
            sLLMChatterConfig
                ? sLLMChatterConfig
                      ->_proxChatterReplyWindowSeconds
                : 30;
        return time(nullptr) - lastActivity
            > static_cast<time_t>(expiry);
    }
};

static std::map<std::string, time_t> _entityCooldowns;
static std::map<std::string, std::pair<time_t, uint32>>
    _zoneFatigue;
static std::map<uint32, ProximityScene> _activeScenes;
static std::map<uint32, std::vector<uint32>> _playerScenes;
static std::mt19937 _rng(std::random_device{}());

enum class DirectedSayResult
{
    NotDirected,
    Queued,
    Suppressed
};

bool IsProximityMapAllowed(Map const* map)
{
    if (!map || map->IsBattlegroundOrArena())
        return false;
    if (map->IsRaid())
        return sLLMChatterConfig
            && sLLMChatterConfig
                   ->_proxChatterEnableInRaids;
    if (map->IsDungeon())
        return sLLMChatterConfig
            && sLLMChatterConfig
                   ->_proxChatterEnableInDungeons;
    return true;
}

bool IsEligibleProximityAnchor(Player* player)
{
    return player && player->IsInWorld()
        && player->IsAlive()
        && !player->IsInCombat()
        && !player->IsMounted()
        && !player->IsFlying()
        && IsProximityMapAllowed(player->GetMap());
}

std::string GetNPCDisposition(
    Creature const* creature, Player const* player)
{
    if (!creature || !player)
        return "neutral";

    ReputationRank reaction =
        creature->GetReactionTo(player);
    if (reaction <= REP_HOSTILE)
        return "hostile";
    if (reaction == REP_UNFRIENDLY)
        return "unfriendly";
    if (reaction == REP_NEUTRAL)
        return "neutral";
    return "friendly";
}

std::string GetCreatureRankLabel(
    CreatureTemplate const* creatureTemplate)
{
    if (!creatureTemplate)
        return "normal";

    switch (creatureTemplate->rank)
    {
        case CREATURE_ELITE_ELITE:
            return "elite";
        case CREATURE_ELITE_RAREELITE:
            return "rare elite";
        case CREATURE_ELITE_WORLDBOSS:
            return "world boss";
        case CREATURE_ELITE_RARE:
            return "rare";
        default:
            return "normal";
    }
}

std::string GetCreatureTypeLabel(
    CreatureTemplate const* creatureTemplate)
{
    if (!creatureTemplate)
        return "unknown";

    switch (creatureTemplate->type)
    {
        case CREATURE_TYPE_BEAST:
            return "beast";
        case CREATURE_TYPE_DRAGONKIN:
            return "dragonkin";
        case CREATURE_TYPE_DEMON:
            return "demon";
        case CREATURE_TYPE_ELEMENTAL:
            return "elemental";
        case CREATURE_TYPE_GIANT:
            return "giant";
        case CREATURE_TYPE_UNDEAD:
            return "undead";
        case CREATURE_TYPE_HUMANOID:
            return "humanoid";
        case CREATURE_TYPE_CRITTER:
            return "critter";
        case CREATURE_TYPE_MECHANICAL:
            return "mechanical";
        case CREATURE_TYPE_NOT_SPECIFIED:
            return "not specified";
        case CREATURE_TYPE_TOTEM:
            return "totem";
        case CREATURE_TYPE_NON_COMBAT_PET:
            return "non-combat pet";
        case CREATURE_TYPE_GAS_CLOUD:
            return "gas cloud";
        default:
            return "unknown";
    }
}

enum class ProximityNPCQualification
{
    None,
    Guard,
    FunctionalNPC,
    Humanoid,
    ConfiguredEntry
};

bool HasConversationalNPCFlags(Creature const* creature)
{
    if (!creature)
        return false;

    uint32 npcFlags = creature->GetNpcFlags();
    return npcFlags
        & (UNIT_NPC_FLAG_VENDOR
            | UNIT_NPC_FLAG_VENDOR_AMMO
            | UNIT_NPC_FLAG_VENDOR_FOOD
            | UNIT_NPC_FLAG_VENDOR_POISON
            | UNIT_NPC_FLAG_VENDOR_REAGENT
            | UNIT_NPC_FLAG_TRAINER
            | UNIT_NPC_FLAG_TRAINER_CLASS
            | UNIT_NPC_FLAG_TRAINER_PROFESSION
            | UNIT_NPC_FLAG_INNKEEPER
            | UNIT_NPC_FLAG_FLIGHTMASTER
            | UNIT_NPC_FLAG_QUESTGIVER);
}

ProximityNPCQualification GetProximityNPCQualification(
    Creature const* creature)
{
    if (!creature || !sLLMChatterConfig)
        return ProximityNPCQualification::None;

    CreatureTemplate const* creatureTemplate =
        creature->GetCreatureTemplate();
    if (!creatureTemplate)
        return ProximityNPCQualification::None;

    uint32 entry = creature->GetEntry();
    if (sLLMChatterConfig->IsProximitySpeakerDenied(entry))
        return ProximityNPCQualification::None;
    if (IsLLMChatterBoss(creature))
        return ProximityNPCQualification::None;
    if (creature->IsGuard())
        return ProximityNPCQualification::Guard;
    if (HasConversationalNPCFlags(creature))
        return ProximityNPCQualification::FunctionalNPC;
    if (creatureTemplate->type == CREATURE_TYPE_HUMANOID)
        return ProximityNPCQualification::Humanoid;
    if (sLLMChatterConfig->IsProximitySpeakerAllowed(entry))
        return ProximityNPCQualification::ConfiguredEntry;
    return ProximityNPCQualification::None;
}

std::string GetProximityNPCQualificationLabel(
    ProximityNPCQualification qualification)
{
    switch (qualification)
    {
        case ProximityNPCQualification::Guard:
            return "guard";
        case ProximityNPCQualification::FunctionalNPC:
            return "functional NPC";
        case ProximityNPCQualification::Humanoid:
            return "humanoid";
        case ProximityNPCQualification::ConfiguredEntry:
            return "configured entry";
        default:
            return "";
    }
}

bool IsSameGroup(Player* left, Group* group)
{
    if (!left || !group)
        return false;

    Group* botGroup = left->GetGroup();
    if (!botGroup)
        return false;

    return botGroup->GetGUID() == group->GetGUID();
}

bool IsEligibleProximityBot(
    Player* player, Player* bot, float radius)
{
    if (!player || !bot)
        return false;
    if (!IsPlayerBot(bot))
        return false;
    if (!bot->IsInWorld() || !bot->IsAlive())
        return false;
    if (bot->IsInCombat() || bot->IsMounted()
        || bot->IsFlying())
        return false;
    if (HasUnsafeChatterFacingMotion(bot))
        return false;
    if (bot->GetMap() != player->GetMap())
        return false;
    if (!player->IsWithinDistInMap(bot, radius))
        return false;
    if (!player->IsWithinLOSInMap(bot))
        return false;

    WorldSession* session = bot->GetSession();
    if (session && session->PlayerLoading())
        return false;

    return true;
}

bool IsEligibleProximityNPC(
    Player* player, Creature* cr, float radius)
{
    if (!player || !cr || !cr->IsAlive())
        return false;
    if (!player->IsWithinDistInMap(cr, radius))
        return false;
    if (!player->IsWithinLOSInMap(cr))
        return false;
    if (cr->IsPet() || cr->IsTotem()
        || cr->IsGuardian())
        return false;
    if (cr->IsPlayer() || cr->IsInCombat())
        return false;
    if (HasUnsafeChatterFacingMotion(cr))
        return false;

    CreatureTemplate const* tmpl =
        cr->GetCreatureTemplate();
    if (!tmpl)
        return false;
    if (!cr->GetSpawnId())
        return false;
    if (cr->GetName().empty())
        return false;
    return GetProximityNPCQualification(cr)
        != ProximityNPCQualification::None;
}

WorldObject* ResolveParticipantObject(
    Player* player,
    ProximityParticipant const& participant)
{
    if (!player || !player->IsInWorld()
        || !player->IsAlive())
        return nullptr;

    if (participant.isNPC)
        return FindCreatureBySpawnId(
            player->GetMap(), participant.id);

    ObjectGuid guid =
        ObjectGuid::Create<HighGuid::Player>(
            participant.id);
    Player* bot = ObjectAccessor::FindPlayer(guid);
    if (!bot || !bot->IsInWorld())
        return nullptr;
    if (bot->GetMap() != player->GetMap())
        return nullptr;
    return bot;
}

WorldObject* GetCandidateObject(
    ProximityCandidate const& candidate)
{
    if (candidate.isNPC)
        return candidate.npc;
    return candidate.bot;
}

Unit* GetCandidateUnit(
    ProximityCandidate const& candidate)
{
    if (candidate.isNPC)
        return candidate.npc;
    return candidate.bot;
}

bool CanShareProximityScene(
    ProximityCandidate const& left,
    ProximityCandidate const& right)
{
    Unit* leftUnit = GetCandidateUnit(left);
    Unit* rightUnit = GetCandidateUnit(right);
    if (!leftUnit || !rightUnit)
        return false;

    return !leftUnit->IsHostileTo(rightUnit)
        && !rightUnit->IsHostileTo(leftUnit);
}

std::vector<ProximityCandidate> SelectCompatibleSpeakers(
    std::vector<ProximityCandidate> const& candidates,
    ProximityCandidate const* preferred,
    size_t maximum)
{
    std::vector<ProximityCandidate> speakers;
    if (preferred)
        speakers.push_back(*preferred);

    for (ProximityCandidate const& candidate : candidates)
    {
        if (speakers.size() >= maximum)
            break;
        if (preferred
            && candidate.id == preferred->id
            && candidate.isNPC == preferred->isNPC)
            continue;

        bool compatible = std::all_of(
            speakers.begin(), speakers.end(),
            [&candidate](
                ProximityCandidate const& selected)
            {
                return CanShareProximityScene(
                    candidate, selected);
            });
        if (compatible)
            speakers.push_back(candidate);
    }

    return speakers;
}

std::string ToLowerAscii(std::string value)
{
    std::transform(
        value.begin(), value.end(), value.begin(),
        [](unsigned char c)
        {
            return static_cast<char>(
                std::tolower(c));
        });
    return value;
}

bool IsAsciiNameChar(char c)
{
    unsigned char uc =
        static_cast<unsigned char>(c);
    return std::isalnum(uc) != 0;
}

bool ContainsNameWithBoundary(
    std::string const& messageLower,
    std::string const& nameLower)
{
    if (messageLower.empty() || nameLower.empty())
        return false;

    size_t pos = messageLower.find(nameLower);
    while (pos != std::string::npos)
    {
        bool beforeOk =
            pos == 0
            || !IsAsciiNameChar(
                messageLower[pos - 1]);
        size_t end = pos + nameLower.size();
        bool afterOk =
            end >= messageLower.size()
            || !IsAsciiNameChar(
                messageLower[end]);
        if (beforeOk && afterOk)
            return true;

        pos = messageLower.find(
            nameLower, pos + 1);
    }

    return false;
}

std::string FirstNameToken(
    std::string const& name)
{
    size_t end = name.find_first_of(" \t\r\n");
    if (end == std::string::npos)
        return name;
    return name.substr(0, end);
}

ProximityCandidate const* FindSelectedCandidate(
    Player* player,
    std::vector<ProximityCandidate> const& candidates)
{
    if (!player)
        return nullptr;

    ObjectGuid selGuid =
        player->GetGuidValue(UNIT_FIELD_TARGET);
    if (!selGuid)
        return nullptr;

    for (auto const& c : candidates)
    {
        if (c.isNPC && c.npc
            && c.npc->GetGUID() == selGuid)
            return &c;
        if (!c.isNPC && c.bot
            && c.bot->GetGUID() == selGuid)
            return &c;
    }

    return nullptr;
}

ProximityCandidate const* FindNamedCandidate(
    Player* player,
    std::vector<ProximityCandidate> const& candidates,
    std::string const& message)
{
    if (!player || message.empty())
        return nullptr;

    std::string msgLower = ToLowerAscii(message);

    auto findBest = [&](
        bool firstTokenOnly) -> ProximityCandidate const*
    {
        ProximityCandidate const* best = nullptr;
        float bestDist = 1e9f;

        for (auto const& c : candidates)
        {
            std::string matchName =
                firstTokenOnly
                    ? FirstNameToken(c.name)
                    : c.name;
            if (matchName.size() < 3)
                continue;

            std::string nameLower =
                ToLowerAscii(matchName);
            if (!ContainsNameWithBoundary(
                    msgLower, nameLower))
                continue;

            WorldObject* obj =
                GetCandidateObject(c);
            if (!obj)
                continue;

            float dist =
                player->GetDistance(obj);
            if (!best || dist < bestDist)
            {
                best = &c;
                bestDist = dist;
            }
        }

        return best;
    };

    ProximityCandidate const* fullName =
        findBest(false);
    if (fullName)
        return fullName;

    return findBest(true);
}

void EvictExpiredScenes()
{
    for (auto it = _activeScenes.begin();
         it != _activeScenes.end();)
    {
        if (it->second.IsExpired())
        {
            auto pit =
                _playerScenes.find(
                    it->second.playerGuid);
            if (pit != _playerScenes.end())
            {
                auto& ids = pit->second;
                ids.erase(
                    std::remove(
                        ids.begin(), ids.end(),
                        it->first),
                    ids.end());
                if (ids.empty())
                    _playerScenes.erase(pit);
            }
            it = _activeScenes.erase(it);
        }
        else
            ++it;
    }
}

void AddSceneParticipant(
    ProximityScene& scene, uint32 id,
    bool isNPC, std::string const& name)
{
    for (ProximityParticipant const& participant :
         scene.participants)
    {
        if (participant.id == id
            && participant.isNPC == isNPC)
            return;
    }

    ProximityParticipant participant;
    participant.id = id;
    participant.isNPC = isNPC;
    participant.name = name;
    scene.participants.push_back(participant);
}

std::string BuildBotParticipantJson(Player* bot)
{
    return std::string("{")
        + "\"name\":\""
        + JsonEscape(bot->GetName()) + "\","
        + "\"is_npc\":false,"
        + "\"bot_guid\":"
        + std::to_string(
            bot->GetGUID().GetCounter())
        + ",\"class\":\""
        + JsonEscape(GetChatterClassName(bot->getClass()))
        + "\",\"race\":\""
        + JsonEscape(GetRaceName(bot->getRace()))
        + "\",\"role\":\"bot\"}";
}

std::string BuildNPCParticipantJson(
    Creature* cr, Player* player)
{
    CreatureTemplate const* creatureTemplate =
        cr->GetCreatureTemplate();
    return std::string("{")
        + "\"name\":\""
        + JsonEscape(cr->GetName()) + "\","
        + "\"is_npc\":true,"
        + "\"npc_entry\":"
        + std::to_string(cr->GetEntry())
        + ",\"npc_spawn_id\":"
        + std::to_string(cr->GetSpawnId())
        + ",\"role\":\""
        + JsonEscape(GetCreatureRoleName(cr))
        + "\",\"sub_name\":\""
        + JsonEscape(
            creatureTemplate->SubName)
        + "\",\"disposition\":\""
        + JsonEscape(
            GetNPCDisposition(cr, player))
        + "\",\"rank\":\""
        + JsonEscape(
            GetCreatureRankLabel(creatureTemplate))
        + "\",\"creature_type\":\""
        + JsonEscape(
            GetCreatureTypeLabel(creatureTemplate))
        + "\",\"qualification\":\""
        + JsonEscape(
            GetProximityNPCQualificationLabel(
                GetProximityNPCQualification(cr)))
        + "\"}";
}

std::string BuildParticipantJson(
    ProximityCandidate const& candidate,
    Player* player)
{
    if (candidate.isNPC && candidate.npc)
        return BuildNPCParticipantJson(
            candidate.npc, player);

    if (candidate.bot)
        return BuildBotParticipantJson(
            candidate.bot);

    return "{}";
}

std::string BuildParticipantsJson(
    std::vector<ProximityCandidate> const& candidates,
    Player* player)
{
    std::string json = "[";
    for (size_t i = 0; i < candidates.size(); ++i)
    {
        if (i > 0)
            json += ",";
        json += BuildParticipantJson(
            candidates[i], player);
    }
    json += "]";
    return json;
}

std::string GetAreaNameForLocale(uint32 areaId)
{
    AreaTableEntry const* area =
        sAreaTableStore.LookupEntry(areaId);
    if (!area)
        return "";

    uint8 locale = sWorld->GetDefaultDbcLocale();
    char const* name = area->area_name[locale];
    if (!name || !*name)
        name = area->area_name[LOCALE_enUS];
    return name ? name : "";
}

uint32 ComputeEffectiveChance(Player* player)
{
    uint32 chance =
        sLLMChatterConfig->_proxChatterChance;
    if (!player)
        return chance;

    uint32 windowSeconds = std::max<uint32>(
        sLLMChatterConfig->_proxChatterEntityCooldown,
        sLLMChatterConfig->_proxChatterScanInterval
            * 3);
    Map* map = player->GetMap();
    std::string key = std::to_string(
        player->GetGUID().GetCounter())
        + ":" + std::to_string(player->GetMapId())
        + ":" + std::to_string(
            map ? map->GetInstanceId() : 0);
    time_t now = time(nullptr);
    auto& state = _zoneFatigue[key];

    if (state.first == 0
        || now - state.first
            > static_cast<time_t>(windowSeconds))
    {
        state.first = now;
        state.second = 0;
        return chance;
    }

    if (state.second
        <= sLLMChatterConfig
               ->_proxChatterZoneFatigueThreshold)
        return chance;

    uint32 overflow = state.second
        - sLLMChatterConfig
              ->_proxChatterZoneFatigueThreshold;
    uint32 decay = overflow
        * sLLMChatterConfig
              ->_proxChatterZoneFatigueDecay;
    return decay >= chance ? 0 : chance - decay;
}

void NoteZoneTrigger(Player* player)
{
    if (!player)
        return;

    Map* map = player->GetMap();
    std::string key = std::to_string(
        player->GetGUID().GetCounter())
        + ":" + std::to_string(player->GetMapId())
        + ":" + std::to_string(
            map ? map->GetInstanceId() : 0);
    auto& state = _zoneFatigue[key];
    state.first = time(nullptr);
    ++state.second;
}

void EvictExpiredProximityCooldowns()
{
    time_t now = time(nullptr);
    time_t entityCutoff = static_cast<time_t>(
        sLLMChatterConfig
            ->_proxChatterEntityCooldown);
    uint32 zoneWindow = std::max<uint32>(
        sLLMChatterConfig
            ->_proxChatterEntityCooldown,
        sLLMChatterConfig
                ->_proxChatterScanInterval
            * 3);
    time_t zoneCutoff =
        static_cast<time_t>(zoneWindow);

    for (auto it = _entityCooldowns.begin();
         it != _entityCooldowns.end();)
    {
        if (now - it->second > entityCutoff)
            it = _entityCooldowns.erase(it);
        else
            ++it;
    }

    for (auto it = _zoneFatigue.begin();
         it != _zoneFatigue.end();)
    {
        if (now - it->second.first > zoneCutoff)
            it = _zoneFatigue.erase(it);
        else
            ++it;
    }
}

std::string GetEntityCooldownKey(
    Player const* player,
    ProximityCandidate const& candidate)
{
    Map const* map = player ? player->GetMap() : nullptr;
    return std::string(candidate.isNPC ? "npc:" : "bot:")
        + std::to_string(player ? player->GetMapId() : 0)
        + ":" + std::to_string(
            map ? map->GetInstanceId() : 0)
        + ":" + std::to_string(candidate.id);
}

void CollectNearbyBots(
    Player* player, float radius,
    std::vector<ProximityCandidate>& out)
{
    std::list<Player*> nearbyPlayers;
    NearbyBotCheck check(player, radius);
    Acore::PlayerListSearcher<NearbyBotCheck>
        searcher(player, nearbyPlayers, check);
    Cell::VisitObjects(player, searcher, radius);

    for (Player* bot : nearbyPlayers)
    {
        if (!IsEligibleProximityBot(
                player, bot, radius))
            continue;

        ProximityCandidate candidate;
        candidate.bot = bot;
        candidate.id =
            bot->GetGUID().GetCounter();
        candidate.entry = 0;
        candidate.name = bot->GetName();
        candidate.className =
            GetChatterClassName(bot->getClass());
        candidate.raceName =
            GetRaceName(bot->getRace());
        out.push_back(candidate);
    }
}

void CollectNearbyNPCs(
    Player* player, float radius,
    std::vector<ProximityCandidate>& out)
{
    std::list<Creature*> creatures;
    NearbyCreatureCheck check(player, radius);
    Acore::CreatureListSearcher<
        NearbyCreatureCheck>
        searcher(player, creatures, check);
    Cell::VisitObjects(player, searcher, radius);

    for (Creature* creature : creatures)
    {
        if (!IsEligibleProximityNPC(
                player, creature, radius))
            continue;

        ProximityCandidate candidate;
        candidate.isNPC = true;
        candidate.npc = creature;
        candidate.id = creature->GetSpawnId();
        candidate.entry = creature->GetEntry();
        candidate.name = creature->GetName();
        candidate.role =
            GetCreatureRoleName(creature);
        candidate.subName =
            creature->GetCreatureTemplate()->SubName;
        out.push_back(candidate);
    }
}

void DeduplicateCandidates(
    std::vector<ProximityCandidate>& candidates)
{
    std::map<std::string, size_t> chosen;
    for (size_t i = 0; i < candidates.size(); ++i)
    {
        std::string key =
            (candidates[i].isNPC ? "npc:" : "bot:")
            + std::to_string(candidates[i].id);
        chosen[key] = i;
    }

    std::vector<ProximityCandidate> deduped;
    deduped.reserve(chosen.size());
    for (auto const& pair : chosen)
        deduped.push_back(
            candidates[pair.second]);
    candidates.swap(deduped);
}

std::string BuildNearbyNamesJson(
    std::vector<ProximityCandidate> const& allCandidates,
    std::vector<ProximityCandidate> const& speakers)
{
    std::set<uint32> speakerIds;
    for (auto const& s : speakers)
        speakerIds.insert(s.id);

    std::string json = "[";
    size_t count = 0;
    for (auto const& c : allCandidates)
    {
        if (speakerIds.count(c.id))
            continue;
        if (count >= 4)
            break;
        if (count > 0)
            json += ",";
        json += "\"" + JsonEscape(c.name) + "\"";
        ++count;
    }
    json += "]";
    return json;
}

std::string BuildBaseEventJson(
    Player* player,
    std::vector<ProximityCandidate> const& speakers,
    std::vector<ProximityCandidate> const& allCandidates,
    bool playerAddressed,
    uint32 maxLines)
{
    Map* map = player->GetMap();
    uint32 instanceId = map ? map->GetInstanceId() : 0;
    char const* rawMapName =
        map ? map->GetMapName() : nullptr;
    return std::string("{")
        + "\"player_guid\":"
        + std::to_string(
            player->GetGUID().GetCounter())
        + ",\"player_name\":\""
        + JsonEscape(player->GetName())
        + "\",\"zone_id\":"
        + std::to_string(player->GetZoneId())
        + ",\"map_id\":"
        + std::to_string(player->GetMapId())
        + ",\"instance_id\":"
        + std::to_string(instanceId)
        + ",\"map_name\":\""
        + JsonEscape(rawMapName ? rawMapName : "")
        + "\",\"is_dungeon\":"
        + std::string(
            map && map->IsDungeon()
                ? "true" : "false")
        + ",\"is_raid\":"
        + std::string(
            map && map->IsRaid()
                ? "true" : "false")
        + ",\"zone_name\":\""
        + JsonEscape(
            GetAreaNameForLocale(
                player->GetZoneId()))
        + "\",\"subzone_name\":\""
        + JsonEscape(
            GetAreaNameForLocale(
                player->GetAreaId()))
        + "\",\"player_addressed\":"
        + std::string(
            playerAddressed ? "true" : "false")
        + ",\"nearby_names\":"
        + BuildNearbyNamesJson(
            allCandidates, speakers)
        + ",\"line_delay_seconds\":"
        + std::to_string(
            sLLMChatterConfig
                ->_proxChatterConversationLineDelay)
        + ",\"max_lines\":"
        + std::to_string(maxLines)
        + ",\"participants\":"
        + BuildParticipantsJson(speakers, player)
        + "}";
}

void QueueProximityEvent(
    Player* player, char const* eventType,
    std::vector<ProximityCandidate> const& speakers,
    std::vector<ProximityCandidate> const& allCandidates,
    bool playerAddressed, uint32 maxLines)
{
    if (!player || speakers.empty())
        return;

    ProximityCandidate const& first = speakers[0];
    std::string cooldownKey =
        GetEntityCooldownKey(player, first);
    if (IsEventOnCooldown(
            _entityCooldowns,
            cooldownKey,
            sLLMChatterConfig
                ->_proxChatterEntityCooldown))
        return;

    std::string json = BuildBaseEventJson(
        player, speakers, allCandidates,
        playerAddressed, maxLines);
    std::string escaped = EscapeString(json);

    QueueChatterEvent(
        eventType,
        "player",
        player->GetZoneId(),
        player->GetMapId(),
        GetChatterEventPriority(eventType),
        cooldownKey,
        first.isNPC ? 0 : first.id,
        first.name,
        player->GetGUID().GetCounter(),
        player->GetName(),
        first.entry,
        escaped,
        GetReactionDelaySeconds(eventType),
        sLLMChatterConfig
            ->_eventExpirationSeconds,
        false);

    SetEventCooldown(_entityCooldowns, cooldownKey);
    NoteZoneTrigger(player);
}

void QueuePlayerSayProximityEvent(
    Player* player, char const* eventType,
    std::vector<ProximityCandidate> const& speakers,
    std::vector<ProximityCandidate> const& allCandidates,
    uint32 maxLines,
    std::string const& playerMessage,
    std::string const& addressedName)
{
    if (!player || speakers.empty())
        return;

    ProximityCandidate const& first = speakers[0];

    std::string json = BuildBaseEventJson(
        player, speakers, allCandidates,
        true, maxLines);

    // Inject player_message and optional
    // addressed_name before closing brace.
    std::string extra =
        ",\"player_message\":\""
        + JsonEscape(playerMessage) + "\"";
    if (!addressedName.empty())
        extra += ",\"addressed_name\":\""
            + JsonEscape(addressedName) + "\"";
    if (!json.empty() && json.back() == '}')
        json.insert(json.size() - 1, extra);

    std::string escaped = EscapeString(json);
    std::string cooldownKey =
        GetEntityCooldownKey(player, first);

    QueueChatterEvent(
        eventType,
        "player",
        player->GetZoneId(),
        player->GetMapId(),
        GetChatterEventPriority(eventType),
        cooldownKey,
        first.isNPC ? 0 : first.id,
        first.name,
        player->GetGUID().GetCounter(),
        player->GetName(),
        first.entry,
        escaped,
        GetReactionDelaySeconds(eventType),
        sLLMChatterConfig
            ->_eventExpirationSeconds,
        false);

    // Set cooldown on speakers (not checked here,
    // but prevents ambient scan from re-using them).
    for (auto const& s : speakers)
        SetEventCooldown(
            _entityCooldowns,
            GetEntityCooldownKey(player, s));
}

bool HasNearbySelectedUnit(
    Player* player, float radius)
{
    if (!player)
        return false;

    ObjectGuid selectedGuid =
        player->GetGuidValue(UNIT_FIELD_TARGET);
    if (!selectedGuid)
        return false;

    Unit* selected = ObjectAccessor::GetUnit(
        *player, selectedGuid);
    return selected && selected != player
        && selected->GetMap() == player->GetMap()
        && player->IsWithinDistInMap(
            selected, radius);
}

DirectedSayResult QueueDirectedPlayerSayProximityEvent(
    Player* player, std::string const& safeMsg)
{
    if (!IsEligibleProximityAnchor(player)
        || safeMsg.empty())
        return DirectedSayResult::Suppressed;

    float radius = static_cast<float>(
        sLLMChatterConfig
            ->_proxChatterPlayerSayScanRadius);
    std::vector<ProximityCandidate> candidates;
    CollectNearbyBots(player, radius, candidates);
    CollectNearbyNPCs(player, radius, candidates);
    DeduplicateCandidates(candidates);

    Group* playerGroup = player->GetGroup();
    std::vector<ProximityCandidate> nonParty;
    for (auto const& c : candidates)
    {
        if (c.isNPC
            || !IsSameGroup(c.bot, playerGroup))
            nonParty.push_back(c);
    }
    ProximityCandidate const* directed =
        FindNamedCandidate(
            player, nonParty, safeMsg);
    if (!directed)
        directed = FindSelectedCandidate(
            player, nonParty);

    if (!directed)
    {
        return HasNearbySelectedUnit(player, radius)
            ? DirectedSayResult::Suppressed
            : DirectedSayResult::NotDirected;
    }

    std::vector<ProximityCandidate> speaker = {
        *directed};
    QueuePlayerSayProximityEvent(
        player,
        "proximity_player_say",
        speaker,
        candidates,
        1,
        safeMsg,
        directed->name);
    return DirectedSayResult::Queued;
}

void HandleProximityPlayerSayNewScene(
    Player* player, std::string const& safeMsg)
{
    if (!IsEligibleProximityAnchor(player))
        return;

    float radius = static_cast<float>(
        sLLMChatterConfig
            ->_proxChatterPlayerSayScanRadius);
    std::vector<ProximityCandidate> candidates;
    CollectNearbyBots(player, radius, candidates);
    CollectNearbyNPCs(player, radius, candidates);
    DeduplicateCandidates(candidates);

    // Filter out cooled-down candidates BEFORE
    // speaker selection so we never silently drop
    // a player-initiated /say when others are free.
    candidates.erase(
        std::remove_if(
            candidates.begin(), candidates.end(),
            [player](ProximityCandidate const& c)
            {
                return IsEventOnCooldown(
                    _entityCooldowns,
                    GetEntityCooldownKey(player, c),
                    sLLMChatterConfig
                        ->_proxChatterEntityCooldown);
            }),
        candidates.end());

    if (candidates.empty())
        return;

    // Partition into party bots vs non-party
    // (NPCs + non-grouped bots).
    Group* playerGroup = player->GetGroup();
    std::vector<ProximityCandidate> nonParty;
    for (auto const& c : candidates)
    {
        if (c.isNPC
            || !IsSameGroup(c.bot, playerGroup))
            nonParty.push_back(c);
    }

    // If zero non-party candidates, skip — party
    // chatter owns grouped-bot-only conversations.
    if (nonParty.empty())
        return;

    std::shuffle(
        candidates.begin(), candidates.end(),
        _rng);
    std::shuffle(
        nonParty.begin(), nonParty.end(),
        _rng);

    std::vector<ProximityCandidate> speakers =
        SelectCompatibleSpeakers(
            candidates, &nonParty.front(), 3);

    bool wantsConversation =
        speakers.size() >= 2
        && urand(1, 100)
            <= sLLMChatterConfig
                   ->_proxChatterConversationChance;

    if (wantsConversation)
    {
        uint32 maxLines = std::clamp<uint32>(
            sLLMChatterConfig
                ->_proxChatterMaxConversationLines,
            2, 4);
        QueuePlayerSayProximityEvent(
            player,
            "proximity_player_conversation",
            speakers,
            candidates,
            maxLines,
            safeMsg,
            "");
        return;
    }

    std::vector<ProximityCandidate> speaker = {
        nonParty.front()};
    QueuePlayerSayProximityEvent(
        player,
        "proximity_player_say",
        speaker,
        candidates,
        1,
        safeMsg,
        "");
}

void MaybeQueueProximityScene(Player* player)
{
    if (!IsEligibleProximityAnchor(player))
        return;

    uint32 effectiveChance =
        ComputeEffectiveChance(player);
    if (effectiveChance == 0
        || urand(1, 100) > effectiveChance)
        return;

    float radius = static_cast<float>(
        sLLMChatterConfig
            ->_proxChatterScanRadius);
    std::vector<ProximityCandidate> candidates;
    CollectNearbyBots(player, radius, candidates);
    CollectNearbyNPCs(player, radius, candidates);
    DeduplicateCandidates(candidates);

    if (candidates.empty())
        return;

    Group* playerGroup = player->GetGroup();
    std::vector<ProximityCandidate> nonParty;
    for (auto const& candidate : candidates)
    {
        if (candidate.isNPC
            || !IsSameGroup(
                candidate.bot, playerGroup))
        {
            nonParty.push_back(candidate);
        }
    }
    if (nonParty.empty())
        return;

    std::shuffle(
        candidates.begin(), candidates.end(),
        _rng);
    std::shuffle(
        nonParty.begin(), nonParty.end(),
        _rng);

    std::vector<ProximityCandidate> speakers =
        SelectCompatibleSpeakers(
            candidates, &nonParty.front(), 3);

    bool playerAddressed =
        urand(1, 100)
        <= sLLMChatterConfig
               ->_proxChatterPlayerAddressChance;
    bool wantsConversation =
        speakers.size() >= 2
        && urand(1, 100)
            <= sLLMChatterConfig
                   ->_proxChatterConversationChance;

    if (wantsConversation)
    {
        uint32 maxLines = std::clamp<uint32>(
            sLLMChatterConfig
                ->_proxChatterMaxConversationLines,
            2, 4);
        QueueProximityEvent(
            player,
            "proximity_conversation",
            speakers,
            candidates,
            playerAddressed,
            maxLines);
        return;
    }

    std::vector<ProximityCandidate> speaker = {
        nonParty.front()};
    QueueProximityEvent(
        player,
        "proximity_say",
        speaker,
        candidates,
        playerAddressed,
        1);
}

ProximityScene* FindBestScene(Player* player)
{
    if (!IsEligibleProximityAnchor(player))
        return nullptr;

    Map* map = player->GetMap();
    uint32 instanceId = map ? map->GetInstanceId() : 0;
    float replyRadius = static_cast<float>(
        sLLMChatterConfig
            ->_proxChatterPlayerSayScanRadius);

    auto it = _playerScenes.find(
        player->GetGUID().GetCounter());
    if (it == _playerScenes.end())
        return nullptr;

    ProximityScene* best = nullptr;
    for (uint32 sceneId : it->second)
    {
        auto sceneIt = _activeScenes.find(sceneId);
        if (sceneIt == _activeScenes.end())
            continue;

        ProximityScene& scene = sceneIt->second;
        if (scene.IsExpired() || scene.pendingReply)
            continue;
        if (!scene.replyEligible)
            continue;
        if (scene.replyCount
            >= sLLMChatterConfig
                   ->_proxChatterReplyMaxTurns)
            continue;
        if (scene.mapId != player->GetMapId())
            continue;
        if (scene.instanceId != instanceId)
            continue;

        ProximityParticipant responder;
        responder.id = scene.lastSpeakerId;
        responder.isNPC = scene.lastSpeakerIsNPC;
        responder.name = scene.lastSpeakerName;
        WorldObject* target =
            ResolveParticipantObject(
                player, responder);
        if (!target)
            continue;
        bool eligible = responder.isNPC
            ? IsEligibleProximityNPC(
                player, target->ToCreature(), replyRadius)
            : IsEligibleProximityBot(
                player, target->ToPlayer(), replyRadius);
        if (!eligible)
            continue;

        if (!best
            || scene.lastActivity
                > best->lastActivity)
            best = &scene;
    }

    return best;
}

std::string TrimChatMessage(
    std::string const& msg)
{
    size_t start =
        msg.find_first_not_of(" \t\r\n");
    if (start == std::string::npos)
        return "";

    size_t end =
        msg.find_last_not_of(" \t\r\n");
    std::string trimmed =
        msg.substr(start, end - start + 1);
    // UTF-8 safe clamp: never split a multi-byte character
    return NormalizeChatTextForDb(
        trimmed, sLLMChatterConfig->_maxMessageLength);
}
} // namespace

bool IsProximityAnchorEligible(Player* player)
{
    return IsEligibleProximityAnchor(player);
}

bool IsProximityPlayerbotEligible(
    Player* player, Player* bot, float radius)
{
    return IsEligibleProximityBot(
        player, bot, radius);
}

bool IsProximityNPCEligible(
    Player* player, Creature* creature, float radius)
{
    return IsEligibleProximityNPC(
        player, creature, radius);
}

void CheckProximityChatter()
{
    if (!sLLMChatterConfig
        || !sLLMChatterConfig->IsEnabled()
        || !sLLMChatterConfig->_proxChatterEnable
        || !sLLMChatterConfig->_useEventSystem)
        return;

    EvictExpiredScenes();
    EvictExpiredProximityCooldowns();

    WorldSessionMgr::SessionMap const& sessions =
        sWorldSessionMgr->GetAllSessions();
    for (auto const& pair : sessions)
    {
        WorldSession* session = pair.second;
        if (!session || session->PlayerLoading())
            continue;

        Player* player = session->GetPlayer();
        if (!player || !player->IsInWorld()
            || IsPlayerBot(player))
            continue;

        MaybeQueueProximityScene(player);
    }
}

void HandleProximityPlayerSay(
    Player* player, uint32 type, uint32 language,
    std::string const& msg)
{
    if (!sLLMChatterConfig
        || !sLLMChatterConfig->IsEnabled()
        || !sLLMChatterConfig->_proxChatterEnable
        || !sLLMChatterConfig->_useEventSystem)
        return;

    if (!player || IsPlayerBot(player)
        || type != CHAT_MSG_SAY)
        return;
    if (!IsEligibleProximityAnchor(player))
        return;

    // Ignore hidden addon traffic (DBM, Questie, ElvUI, ...);
    // it is real chat tagged LANG_ADDON, not player speech.
    if (language == LANG_ADDON)
    {
        LogIgnoredAddonChat(
            player, type, msg, "proximity");
        return;
    }

    EvictExpiredScenes();

    std::string safeMsg = TrimChatMessage(msg);
    if (safeMsg.empty())
        return;

    if (HandleBossProximityPlayerSay(player, safeMsg))
        return;

    DirectedSayResult directed =
        QueueDirectedPlayerSayProximityEvent(
            player, safeMsg);
    if (directed != DirectedSayResult::NotDirected)
        return;

    ProximityScene* scene = FindBestScene(player);
    if (!scene)
    {
        HandleProximityPlayerSayNewScene(
            player, safeMsg);
        return;
    }

    ProximityParticipant responder;
    responder.id = scene->lastSpeakerId;
    responder.isNPC = scene->lastSpeakerIsNPC;
    responder.name = scene->lastSpeakerName;
    WorldObject* target =
        ResolveParticipantObject(player, responder);
    if (!target)
        return;

    Map* map = player->GetMap();
    char const* rawMapName =
        map ? map->GetMapName() : nullptr;
    Creature* responderCreature =
        scene->lastSpeakerIsNPC
            ? target->ToCreature() : nullptr;
    CreatureTemplate const* responderTemplate =
        responderCreature
            ? responderCreature->GetCreatureTemplate()
            : nullptr;

    std::string json = std::string("{")
        + "\"scene_id\":"
        + std::to_string(scene->sceneId)
        + ",\"player_guid\":"
        + std::to_string(
            player->GetGUID().GetCounter())
        + ",\"player_name\":\""
        + JsonEscape(player->GetName())
        + "\",\"player_message\":\""
        + JsonEscape(safeMsg)
        + "\",\"zone_id\":"
        + std::to_string(player->GetZoneId())
        + ",\"map_id\":"
        + std::to_string(player->GetMapId())
        + ",\"instance_id\":"
        + std::to_string(
            map ? map->GetInstanceId() : 0)
        + ",\"map_name\":\""
        + JsonEscape(rawMapName ? rawMapName : "")
        + "\",\"is_dungeon\":"
        + std::string(
            map && map->IsDungeon()
                ? "true" : "false")
        + ",\"is_raid\":"
        + std::string(
            map && map->IsRaid()
                ? "true" : "false")
        + ",\"zone_name\":\""
        + JsonEscape(
            GetAreaNameForLocale(
                player->GetZoneId()))
        + "\",\"subzone_name\":\""
        + JsonEscape(
            GetAreaNameForLocale(
                player->GetAreaId()))
        + "\",\"turn_count\":"
        + std::to_string(scene->replyCount)
        + ",\"last_message\":\""
        + JsonEscape(scene->lastMessage)
        + "\",\"responder_name\":\""
        + JsonEscape(scene->lastSpeakerName)
        + "\",\"responder_is_npc\":"
        + std::string(
            scene->lastSpeakerIsNPC
                ? "true"
                : "false")
        + ",\"responder_bot_guid\":"
        + std::to_string(
            scene->lastSpeakerIsNPC
                ? 0
                : scene->lastSpeakerId)
        + ",\"responder_npc_spawn_id\":"
        + std::to_string(
            scene->lastSpeakerIsNPC
                ? scene->lastSpeakerId
                : 0)
        + ",\"responder_npc_entry\":"
        + std::to_string(
            responderCreature
                ? responderCreature->GetEntry() : 0)
        + ",\"responder_role\":\""
        + JsonEscape(
            responderCreature
                ? GetCreatureRoleName(
                    responderCreature) : "")
        + "\",\"responder_sub_name\":\""
        + JsonEscape(
            responderTemplate
                ? responderTemplate->SubName : "")
        + "\",\"responder_disposition\":\""
        + JsonEscape(
            responderCreature
                ? GetNPCDisposition(
                    responderCreature, player) : "")
        + "\",\"responder_rank\":\""
        + JsonEscape(
            responderTemplate
                ? GetCreatureRankLabel(
                    responderTemplate) : "")
        + "\",\"responder_creature_type\":\""
        + JsonEscape(
            responderTemplate
                ? GetCreatureTypeLabel(
                    responderTemplate) : "")
        + "\",\"responder_qualification\":\""
        + JsonEscape(
            responderCreature
                ? GetProximityNPCQualificationLabel(
                    GetProximityNPCQualification(
                        responderCreature)) : "")
        + "}";

    QueueChatterEvent(
        "proximity_reply",
        "player",
        player->GetZoneId(),
        player->GetMapId(),
        GetChatterEventPriority(
            "proximity_reply"),
        "",
        scene->lastSpeakerIsNPC
            ? 0
            : scene->lastSpeakerId,
        scene->lastSpeakerName,
        player->GetGUID().GetCounter(),
        player->GetName(),
        0,
        EscapeString(json),
        GetReactionDelaySeconds(
            "proximity_reply"),
        sLLMChatterConfig
            ->_eventExpirationSeconds,
        false);

    scene->pendingReply = true;
    scene->lastActivity = time(nullptr);
}

void RecordDeliveredProximityLine(
    uint32 eventId, uint32 playerGuid,
    uint32 zoneId, uint32 mapId,
    uint32 instanceId, uint32 botGuid,
    uint32 npcSpawnId, bool replyEligible,
    std::string const& speakerName,
    std::string const& message)
{
    if (!eventId || !playerGuid)
        return;

    EvictExpiredScenes();

    ProximityScene& scene = _activeScenes[eventId];
    bool wasPendingReply = scene.pendingReply;
    if (scene.sceneId == 0)
    {
        scene.sceneId = eventId;
        scene.playerGuid = playerGuid;
        scene.zoneId = zoneId;
        scene.mapId = mapId;
        scene.instanceId = instanceId;
        auto& ids = _playerScenes[playerGuid];
        if (std::find(
                ids.begin(), ids.end(), eventId)
            == ids.end())
            ids.push_back(eventId);
    }

    bool isNPC = npcSpawnId != 0;
    uint32 speakerId = isNPC ? npcSpawnId : botGuid;
    if (speakerId)
    {
        AddSceneParticipant(
            scene, speakerId, isNPC, speakerName);
        scene.lastSpeakerId = speakerId;
        scene.lastSpeakerIsNPC = isNPC;
        scene.lastSpeakerName = speakerName;
    }

    scene.lastMessage = message;
    scene.lastActivity = time(nullptr);
    scene.replyEligible = replyEligible;
    scene.pendingReply = false;
    if (wasPendingReply && scene.replyCount < 255)
        ++scene.replyCount;
}
