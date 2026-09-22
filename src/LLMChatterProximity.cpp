/*
 * mod-llm-chatter - proximity chatter domain
 */

#include "LLMChatterProximity.h"

#include "LLMChatterBossDialogue.h"
#include "LLMChatterConfig.h"
#include "LLMChatterGroup.h"
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
#include "Util.h"
#include "Map.h"
#include "World.h"
#include "WorldSession.h"
#include "WorldSessionMgr.h"

#include <algorithm>
#include <cctype>
#include <ctime>
#include <list>
#include <map>
#include <mutex>
#include <random>
#include <set>
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
static std::map<std::string, time_t>
    _directedEmoteCooldowns;
static std::map<std::string, time_t>
    _directedBotEmoteCooldowns;
static std::mutex _proximityCooldownMutex;
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

enum class DirectedReactorScope
{
    NPCOnly,
    NPCsAndUngroupedBots
};

bool IsProximityCooldownActive(
    std::map<std::string, time_t> const& cooldowns,
    std::string const& key, uint32 cooldownSeconds,
    bool checkPersisted);

std::string GetEntityCooldownKey(
    Player const* player,
    ProximityCandidate const& candidate);

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

bool IsInstanceProximityMap(Map const* map)
{
    return map && (map->IsDungeon() || map->IsRaid());
}

bool IsEligibleProximityAnchor(Player* player)
{
    return player && player->IsInWorld()
        && player->IsAlive()
        && !player->IsInCombat()
        && !player->IsFlying()
        && IsProximityMapAllowed(player->GetMap());
}

bool IsEligibleAmbientProximityAnchor(Player* player)
{
    return IsEligibleProximityAnchor(player)
        && !player->IsMounted();
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
    Player* player, Player* bot, float radius,
    bool allowMounted)
{
    if (!player || !bot)
        return false;
    if (!IsPlayerBot(bot))
        return false;
    if (player->GetTeamId() != bot->GetTeamId())
        return false;
    if (!bot->IsInWorld() || !bot->IsAlive())
        return false;
    if (bot->IsInCombat()
        || (!allowMounted && bot->IsMounted())
        || bot->IsFlying())
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
    if (IsLLMChatterInternalCreature(cr)
        || cr->HasUnitFlag(UNIT_FLAG_NOT_SELECTABLE))
        return false;
    if (cr->HasUnitState(UNIT_STATE_DIED)
        || cr->HasDynamicFlag(UNIT_DYNFLAG_DEAD))
        return false;
    if (!player->IsWithinDistInMap(cr, radius))
        return false;
    if (!player->CanSeeOrDetect(cr)
        || !player->IsWithinLOSInMap(cr))
        return false;
    if (cr->IsPet() || cr->IsTotem()
        || cr->IsGuardian())
        return false;
    if (cr->IsPlayer() || cr->IsInCombat())
        return false;
    CreatureTemplate const* tmpl =
        cr->GetCreatureTemplate();
    if (!tmpl)
        return false;
    if (!cr->GetSpawnId())
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
                return !StringEqualI(
                        candidate.name, selected.name)
                    && CanShareProximityScene(
                        candidate, selected);
            });
        if (compatible)
            speakers.push_back(candidate);
    }

    return speakers;
}

bool IsSameCandidate(
    ProximityCandidate const& left,
    ProximityCandidate const& right)
{
    return left.isNPC == right.isNPC
        && left.id == right.id;
}

uint32 RollDirectedExtraReactorCount(
    size_t available, uint32 callerMaxExtras,
    bool requireAtLeastOne)
{
    uint32 maxCount = std::min<uint32>(
        static_cast<uint32>(available),
        std::min<uint32>(
            callerMaxExtras,
            std::min<uint32>(
                sLLMChatterConfig
                    ->_proxDirectedMaxExtraReactors,
                sLLMChatterConfig
                    ->_proxDirectedMaxLines - 1)));
    uint32 minimumCount = requireAtLeastOne ? 1 : 0;
    if (maxCount < minimumCount)
        return 0;

    if (requireAtLeastOne)
    {
        auto const& witnessWeights =
            sLLMChatterConfig
                ->_proxDirectedWitnessReactorWeights;
        uint32 witnessMax = std::min<uint32>(maxCount, 2u);
        uint32 totalWeight = 0;
        for (uint32 count = 1;
             count <= witnessMax; ++count)
        {
            totalWeight += witnessWeights[count - 1];
        }
        uint32 roll = urand(1, totalWeight);
        uint32 cumulative = 0;
        for (uint32 count = 1;
             count <= witnessMax; ++count)
        {
            cumulative += witnessWeights[count - 1];
            if (roll <= cumulative)
                return count;
        }
        return 1;
    }

    auto const& weights =
        sLLMChatterConfig
            ->_proxDirectedExtraReactorWeights;

    uint32 totalWeight = 0;
    for (uint32 count = minimumCount;
         count <= maxCount; ++count)
        totalWeight += weights[count];
    if (totalWeight == 0)
        return minimumCount;

    uint32 roll = urand(1, totalWeight);
    uint32 cumulative = 0;
    for (uint32 count = minimumCount;
         count <= maxCount; ++count)
    {
        cumulative += weights[count];
        if (roll <= cumulative)
            return count;
    }

    return 0;
}

std::vector<ProximityCandidate> SelectDirectedReactors(
    Player* player,
    std::vector<ProximityCandidate> const& candidates,
    ProximityCandidate const& addressed,
    ProximityCandidate const* preferred,
    DirectedReactorScope scope,
    uint32 callerMaxExtras,
    bool requireAtLeastOne)
{
    std::vector<ProximityCandidate> eligible;
    if (scope == DirectedReactorScope::NPCsAndUngroupedBots
        && !player)
    {
        return eligible;
    }

    for (ProximityCandidate const& candidate : candidates)
    {
        if (IsSameCandidate(candidate, addressed)
            || StringEqualI(candidate.name, addressed.name)
            || !CanShareProximityScene(candidate, addressed))
        {
            continue;
        }

        if (scope == DirectedReactorScope::NPCOnly
            && !candidate.isNPC)
        {
            continue;
        }

        if (scope
                == DirectedReactorScope::NPCsAndUngroupedBots)
        {
            if (!candidate.isNPC
                && (!candidate.bot
                    || IsSameGroup(
                        candidate.bot, player->GetGroup())
                    || player->GetTeamId()
                        != candidate.bot->GetTeamId()))
            {
                continue;
            }
            if (IsProximityCooldownActive(
                    _entityCooldowns,
                    GetEntityCooldownKey(player, candidate),
                    sLLMChatterConfig
                        ->_proxChatterEntityCooldown,
                    false))
            {
                continue;
            }
        }
        eligible.push_back(candidate);
    }

    for (size_t i = 0; i < eligible.size(); ++i)
    {
        size_t other = urand(
            static_cast<uint32>(i),
            static_cast<uint32>(eligible.size() - 1));
        std::swap(eligible[i], eligible[other]);
    }

    uint32 count =
        RollDirectedExtraReactorCount(
            eligible.size(), callerMaxExtras,
            requireAtLeastOne);
    std::vector<ProximityCandidate> selected;
    if (count == 0)
        return selected;

    bool preferredTypeAllowed = preferred
        && (scope
                == DirectedReactorScope::NPCsAndUngroupedBots
            || preferred->isNPC);
    if (preferredTypeAllowed
        && !IsSameCandidate(*preferred, addressed))
    {
        auto it = std::find_if(
            eligible.begin(), eligible.end(),
            [preferred](ProximityCandidate const& candidate)
            {
                return IsSameCandidate(
                    candidate, *preferred);
            });
        if (it != eligible.end())
        {
            selected.push_back(*it);
            eligible.erase(it);
        }
    }

    for (ProximityCandidate const& candidate : eligible)
    {
        if (selected.size() >= count)
            break;
        bool compatible = std::all_of(
            selected.begin(), selected.end(),
            [&candidate](
                ProximityCandidate const& other)
            {
                return !StringEqualI(
                        candidate.name, other.name)
                    && CanShareProximityScene(
                        candidate, other);
            });
        if (compatible)
            selected.push_back(candidate);
    }

    return selected;
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

size_t FindNameWithBoundary(
    std::string const& messageLower,
    std::string const& nameLower,
    size_t start = 0)
{
    if (messageLower.empty() || nameLower.empty())
        return std::string::npos;

    size_t pos = messageLower.find(nameLower, start);
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
            return pos;

        pos = messageLower.find(
            nameLower, pos + 1);
    }

    return std::string::npos;
}

std::vector<std::string> ExtractNameTokens(
    std::string const& value)
{
    std::vector<std::string> tokens;
    std::string current;
    for (unsigned char c : value)
    {
        if (std::isalnum(c) != 0)
        {
            current += static_cast<char>(
                std::tolower(c));
        }
        else if (!current.empty())
        {
            tokens.push_back(current);
            current.clear();
        }
    }
    if (!current.empty())
        tokens.push_back(current);
    return tokens;
}

bool IsCandidateTokenExcluded(
    ProximityCandidate const& candidate,
    std::string const& token)
{
    if (token.size() < 3
        || sLLMChatterConfig
            ->IsDirectedNameStopword(token))
    {
        return true;
    }

    std::vector<std::string> subNameTokens =
        ExtractNameTokens(candidate.subName);
    return std::find(
        subNameTokens.begin(), subNameTokens.end(),
        token) != subNameTokens.end();
}

bool IsUniqueCandidateToken(
    std::vector<ProximityCandidate> const& candidates,
    ProximityCandidate const& owner,
    std::string const& token)
{
    for (ProximityCandidate const& candidate : candidates)
    {
        if (IsSameCandidate(candidate, owner))
            continue;
        std::vector<std::string> tokens =
            ExtractNameTokens(candidate.name);
        if (std::find(
                tokens.begin(), tokens.end(), token)
            != tokens.end())
        {
            return false;
        }
    }
    return true;
}

bool IsExplicitVocativeNameUse(
    std::string const& messageLower,
    size_t position, size_t length)
{
    size_t before = position;
    while (before > 0
        && std::isspace(static_cast<unsigned char>(
            messageLower[before - 1])) != 0)
    {
        --before;
    }
    if (before > 0
        && (messageLower[before - 1] == ','
            || messageLower[before - 1] == ':'))
    {
        return true;
    }

    size_t after = position + length;
    size_t next = messageLower.find_first_not_of(
        " \t\r\n", after);
    return next != std::string::npos
        && (messageLower[next] == ','
            || messageLower[next] == ':');
}

struct NamedCandidateMatch
{
    ProximityCandidate const* candidate = nullptr;
    bool vocative = false;
};

bool IsProximityCooldownActive(
    std::map<std::string, time_t> const& cooldowns,
    std::string const& key, uint32 cooldownSeconds,
    bool checkPersisted)
{
    bool found = false;
    bool active = false;
    {
        std::lock_guard<std::mutex> lock(
            _proximityCooldownMutex);
        auto it = cooldowns.find(key);
        if (it != cooldowns.end())
        {
            found = true;
            active = time(nullptr) - it->second
                < static_cast<time_t>(cooldownSeconds);
        }
    }

    return found
        ? active
        : checkPersisted
            && IsPersistedEventOnCooldown(
                key, cooldownSeconds);
}

void SetProximityCooldown(
    std::map<std::string, time_t>& cooldowns,
    std::string const& key)
{
    std::lock_guard<std::mutex> lock(
        _proximityCooldownMutex);
    cooldowns[key] = time(nullptr);
}

bool TryReserveProximityCooldown(
    std::map<std::string, time_t>& cooldowns,
    std::string const& key, uint32 cooldownSeconds)
{
    std::lock_guard<std::mutex> lock(
        _proximityCooldownMutex);
    time_t now = time(nullptr);
    auto it = cooldowns.find(key);
    if (it != cooldowns.end()
        && now - it->second
            < static_cast<time_t>(cooldownSeconds))
    {
        return false;
    }
    cooldowns[key] = now;
    return true;
}

struct SelectedCandidateMatch
{
    ProximityCandidate const* candidate = nullptr;
    bool suppress = false;
    char const* reason = nullptr;
};

SelectedCandidateMatch FindSelectedCandidate(
    Player* player,
    std::vector<ProximityCandidate> const& candidates)
{
    if (!player)
        return {};

    ObjectGuid selGuid =
        player->GetGuidValue(UNIT_FIELD_TARGET);
    if (!selGuid)
        return {};

    Unit* selected = ObjectAccessor::GetUnit(
        *player, selGuid);
    if (!selected || selected == player
        || !selected->IsAlive())
    {
        return {};
    }

    if (Player* selectedPlayer = selected->ToPlayer())
    {
        if (!IsPlayerBot(selectedPlayer))
        {
            return {
                nullptr, true, "selected_living_player",
            };
        }

        if (IsSameGroup(
                selectedPlayer, player->GetGroup()))
        {
            return {
                nullptr, true, "selected_party_bot",
            };
        }

        for (auto const& candidate : candidates)
        {
            if (!candidate.isNPC && candidate.bot
                && candidate.bot->GetGUID() == selGuid)
            {
                return {&candidate, false, nullptr};
            }
        }

        // A non-party playerbot that is currently ineligible
        // is ignored like any other non-speaking target.
        return {};
    }

    Creature* selectedCreature =
        selected->ToCreature();
    if (!selectedCreature)
        return {};

    if (IsLLMChatterBoss(selectedCreature))
    {
        return {
            nullptr, true, "selected_boss_not_routed",
        };
    }

    if (GetProximityNPCQualification(
            selectedCreature)
        == ProximityNPCQualification::None)
    {
        return {};
    }

    for (auto const& c : candidates)
    {
        if (c.isNPC && c.npc
            && c.npc->GetGUID() == selGuid)
        {
            return {&c, false, nullptr};
        }
    }

    return {
        nullptr, true, "selected_npc_ineligible",
    };
}

NamedCandidateMatch FindNamedCandidate(
    Player* player,
    std::vector<ProximityCandidate> const& candidates,
    std::string const& message)
{
    if (!player || message.empty())
        return {};

    std::string msgLower = ToLowerAscii(message);

    auto findBest = [&](bool fullName)
        -> NamedCandidateMatch
    {
        NamedCandidateMatch best;
        float bestDist = 1e9f;

        for (auto const& c : candidates)
        {
            std::vector<std::string> identifiers;
            if (fullName)
            {
                bool ambiguous = std::any_of(
                    candidates.begin(), candidates.end(),
                    [&c](ProximityCandidate const& other)
                    {
                        return !IsSameCandidate(c, other)
                            && StringEqualI(c.name, other.name);
                    });
                if (!ambiguous)
                    identifiers.push_back(
                        ToLowerAscii(c.name));
            }
            else
            {
                for (std::string const& token :
                     ExtractNameTokens(c.name))
                {
                    if (!IsCandidateTokenExcluded(c, token)
                        && IsUniqueCandidateToken(
                            candidates, c, token))
                    {
                        identifiers.push_back(token);
                    }
                }
            }

            WorldObject* obj =
                GetCandidateObject(c);
            if (!obj)
                continue;

            for (std::string const& identifier : identifiers)
            {
                if (identifier.size() < 3)
                    continue;
                size_t position = FindNameWithBoundary(
                    msgLower, identifier);
                if (position == std::string::npos)
                    continue;

                bool vocative = false;
                for (size_t occurrence = position;
                     occurrence != std::string::npos;
                     occurrence = FindNameWithBoundary(
                         msgLower, identifier,
                         occurrence + 1))
                {
                    if (IsExplicitVocativeNameUse(
                            msgLower, occurrence,
                            identifier.size()))
                    {
                        vocative = true;
                        break;
                    }
                }
                float dist = player->GetDistance(obj);
                if (!best.candidate
                    || (vocative && !best.vocative)
                    || (vocative == best.vocative
                        && dist < bestDist))
                {
                    best.candidate = &c;
                    best.vocative = vocative;
                    bestDist = dist;
                }
            }
        }

        return best;
    };

    NamedCandidateMatch fullName = findBest(true);
    if (fullName.candidate)
        return fullName;

    return findBest(false);
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
    char const* gender = "unknown";
    if (cr->getGender() == GENDER_MALE)
        gender = "male";
    else if (cr->getGender() == GENDER_FEMALE)
        gender = "female";
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
        + "\",\"gender\":\""
        + gender
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
    Map* map = player ? player->GetMap() : nullptr;
    bool instanceMap = IsInstanceProximityMap(map);
    uint32 chance = instanceMap
        ? sLLMChatterConfig->_proxChatterInstanceChance
        : sLLMChatterConfig->_proxChatterOutdoorChance;
    if (!player)
        return chance;

    uint32 scanInterval = instanceMap
        ? sLLMChatterConfig
              ->_proxChatterInstanceScanInterval
        : sLLMChatterConfig
              ->_proxChatterOutdoorScanInterval;
    uint32 windowSeconds = std::max<uint32>(
        sLLMChatterConfig->_proxChatterEntityCooldown,
        scanInterval * 3);
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
        std::max(
            sLLMChatterConfig
                ->_proxChatterOutdoorScanInterval,
            sLLMChatterConfig
                ->_proxChatterInstanceScanInterval)
            * 3);
    time_t zoneCutoff =
        static_cast<time_t>(zoneWindow);

    {
        std::lock_guard<std::mutex> lock(
            _proximityCooldownMutex);
        for (auto it = _entityCooldowns.begin();
             it != _entityCooldowns.end();)
        {
            if (now - it->second > entityCutoff)
                it = _entityCooldowns.erase(it);
            else
                ++it;
        }

        time_t emoteCutoff = static_cast<time_t>(
            sLLMChatterConfig
                ->_emoteNPCVerbalCooldown);
        for (auto it = _directedEmoteCooldowns.begin();
             it != _directedEmoteCooldowns.end();)
        {
            if (now - it->second > emoteCutoff)
                it = _directedEmoteCooldowns.erase(it);
            else
                ++it;
        }

        time_t botEmoteCutoff = static_cast<time_t>(
            sLLMChatterConfig
                ->_emoteMirrorCooldown) * 2;
        for (auto it = _directedBotEmoteCooldowns.begin();
             it != _directedBotEmoteCooldowns.end();)
        {
            if (now - it->second > botEmoteCutoff)
                it = _directedBotEmoteCooldowns.erase(it);
            else
                ++it;
        }
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

ProximityCandidate BuildBotCandidate(Player* bot)
{
    ProximityCandidate candidate;
    candidate.bot = bot;
    candidate.id = bot->GetGUID().GetCounter();
    candidate.entry = 0;
    candidate.name = bot->GetName();
    candidate.className =
        GetChatterClassName(bot->getClass());
    candidate.raceName =
        GetRaceName(bot->getRace());
    return candidate;
}

void CollectNearbyBots(
    Player* player, float radius,
    std::vector<ProximityCandidate>& out,
    bool allowMounted)
{
    std::list<Player*> nearbyPlayers;
    NearbyBotCheck check(player, radius);
    Acore::PlayerListSearcher<NearbyBotCheck>
        searcher(player, nearbyPlayers, check);
    Cell::VisitObjects(player, searcher, radius);

    for (Player* bot : nearbyPlayers)
    {
        if (!IsEligibleProximityBot(
                player, bot, radius, allowMounted))
            continue;

        out.push_back(BuildBotCandidate(bot));
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
    std::vector<ProximityCandidate> const& speakers,
    ProximityCandidate const* additionallyExcluded = nullptr)
{
    std::set<std::pair<bool, uint32>> speakerIds;
    for (auto const& s : speakers)
        speakerIds.emplace(s.isNPC, s.id);
    if (additionallyExcluded)
    {
        speakerIds.emplace(
            additionallyExcluded->isNPC,
            additionallyExcluded->id);
    }

    std::string json = "[";
    size_t count = 0;
    std::set<std::string> includedNames;
    for (auto const& c : allCandidates)
    {
        if (speakerIds.count({c.isNPC, c.id}))
            continue;
        if (!includedNames.insert(
                ToLowerAscii(c.name)).second)
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
    uint32 maxLines,
    ProximityCandidate const* additionallyExcluded = nullptr)
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
            allCandidates, speakers,
            additionallyExcluded)
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
    if (IsProximityCooldownActive(
            _entityCooldowns,
            cooldownKey,
            sLLMChatterConfig
                ->_proxChatterEntityCooldown,
            true))
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

    SetProximityCooldown(
        _entityCooldowns, cooldownKey);
    NoteZoneTrigger(player);
}

void QueuePlayerSayProximityEvent(
    Player* player, char const* eventType,
    std::vector<ProximityCandidate> const& speakers,
    std::vector<ProximityCandidate> const& allCandidates,
    uint32 maxLines,
    std::string const& playerMessage,
    std::string const& addressedName,
    std::string const& interactionMode,
    uint32 expirySeconds)
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
    if (!interactionMode.empty())
        extra += ",\"interaction_mode\":\""
            + JsonEscape(interactionMode) + "\"";
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
        expirySeconds,
        false);

    // Set cooldown on speakers (not checked here,
    // but prevents ambient scan from re-using them).
    for (auto const& s : speakers)
        SetProximityCooldown(
            _entityCooldowns,
            GetEntityCooldownKey(player, s));
}

bool QueuePlayerEmoteProximityEvent(
    Player* player,
    ProximityCandidate const& addressed,
    std::vector<ProximityCandidate> const& speakers,
    std::vector<ProximityCandidate> const& allCandidates,
    std::string const& emoteName,
    uint32 textEmote,
    uint32 mirrorEmote,
    std::string const& interactionMode,
    bool addressedSpeaks)
{
    if (!player || speakers.empty())
        return false;

    uint32 maxLines = speakers.size() > 1
        ? sLLMChatterConfig->_proxDirectedMaxLines
        : 1;
    std::string json = BuildBaseEventJson(
        player, speakers, allCandidates,
        true, maxLines, &addressed);
    std::string extra =
        ",\"interaction\":\"emote\""
        ",\"player_emote\":\""
        + JsonEscape(emoteName)
        + "\",\"player_emote_id\":"
        + std::to_string(textEmote)
        + ",\"mirror_emote\":\""
        + JsonEscape(
            mirrorEmote
                ? GetTextEmoteName(mirrorEmote)
                : "")
        + "\""
        + ",\"addressed_name\":\""
        + JsonEscape(addressed.name)
        + "\",\"addressed_participant\":"
        + BuildParticipantJson(addressed, player)
        + ",\"addressed_speaks\":"
        + std::string(
            addressedSpeaks ? "true" : "false")
        + ",\"interaction_mode\":\""
        + JsonEscape(interactionMode) + "\"";
    if (!json.empty() && json.back() == '}')
        json.insert(json.size() - 1, extra);

    QueueChatterEvent(
        "proximity_player_emote",
        "player",
        player->GetZoneId(),
        player->GetMapId(),
        GetChatterEventPriority(
            "proximity_player_emote"),
        GetEntityCooldownKey(player, addressed),
        addressed.isNPC ? 0 : addressed.id,
        addressed.name,
        player->GetGUID().GetCounter(),
        player->GetName(),
        addressed.entry,
        EscapeString(json),
        GetReactionDelaySeconds(
            "proximity_player_emote"),
        sLLMChatterConfig
            ->_proxDirectedExpirySeconds,
        false);

    for (ProximityCandidate const& speaker : speakers)
    {
        SetProximityCooldown(
            _entityCooldowns,
            GetEntityCooldownKey(player, speaker));
    }
    return true;
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
    CollectNearbyBots(player, radius, candidates, true);
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
    NamedCandidateMatch named =
        FindNamedCandidate(player, nonParty, safeMsg);
    SelectedCandidateMatch selectedMatch =
        FindSelectedCandidate(player, nonParty);
    bool explicitNamedOverride =
        named.candidate && named.vocative;
    if (selectedMatch.suppress
        && !explicitNamedOverride)
    {
        if (sLLMChatterConfig->IsDebugLog())
        {
            LOG_DEBUG(
                "module",
                "LLMChatter: suppressing proximity /say fallback for "
                "player {} because {}",
                player->GetName(),
                selectedMatch.reason
                    ? selectedMatch.reason : "selected_target");
        }
        return DirectedSayResult::Suppressed;
    }
    ProximityCandidate const* selected =
        selectedMatch.suppress
            ? nullptr : selectedMatch.candidate;
    ProximityCandidate const* directed =
        selected && (!named.candidate || !named.vocative)
            ? selected : named.candidate;

    auto isEligibleDirectedTarget =
        [player, radius](
            ProximityCandidate const* candidate)
        {
            return candidate
                && (candidate->isNPC
                    || IsProximityDirectedPlayerbotEligible(
                        player, candidate->bot, radius));
        };

    if (explicitNamedOverride
        && !isEligibleDirectedTarget(named.candidate))
    {
        if (isEligibleDirectedTarget(selected))
            directed = selected;
        else
            return DirectedSayResult::Suppressed;
    }

    if (!directed)
    {
        if (sLLMChatterConfig->IsDebugLog())
        {
            LOG_DEBUG(
                "module",
                "LLMChatter: proximity /say for player {} has "
                "no directed target; "
                "reason=directed_target_not_resolved",
                player->GetName());
        }
        return DirectedSayResult::NotDirected;
    }
    if (!isEligibleDirectedTarget(directed))
        return DirectedSayResult::Suppressed;

    std::vector<ProximityCandidate> speakers = {
        *directed,
    };
    if (directed->isNPC)
    {
        std::vector<ProximityCandidate> extras =
            SelectDirectedReactors(
                player, candidates, *directed,
                directed == selected
                    ? named.candidate : selected,
                DirectedReactorScope::NPCOnly,
                sLLMChatterConfig
                    ->_proxDirectedMaxExtraReactors,
                false);
        speakers.insert(
            speakers.end(),
            extras.begin(), extras.end());
    }
    else
    {
        std::vector<ProximityCandidate> extras =
            SelectDirectedReactors(
                player, candidates, *directed,
                directed == selected
                    ? named.candidate : selected,
                DirectedReactorScope::NPCsAndUngroupedBots,
                sLLMChatterConfig
                    ->_proxDirectedBotMaxParticipants - 1,
                false);
        speakers.insert(
            speakers.end(),
            extras.begin(), extras.end());
    }

    bool conversation = speakers.size() > 1;
    std::string interactionMode = directed->isNPC
        && conversation
        && urand(1, 100)
            <= sLLMChatterConfig
                   ->_proxDirectedNPCAsideChance
        ? "npc_aside" : "player_inclusive";
    uint32 maxLines = conversation
        ? sLLMChatterConfig->_proxDirectedMaxLines
        : 1;
    QueuePlayerSayProximityEvent(
        player,
        conversation
            ? "proximity_player_conversation"
            : "proximity_player_say",
        speakers,
        candidates,
        maxLines,
        safeMsg,
        directed->name,
        interactionMode,
        sLLMChatterConfig
            ->_proxDirectedExpirySeconds);
    return DirectedSayResult::Queued;
}

void HandleProximityPlayerSayNewScene(
    Player* player, std::string const& safeMsg)
{
    if (!IsEligibleAmbientProximityAnchor(player))
        return;

    float radius = static_cast<float>(
        sLLMChatterConfig
            ->_proxChatterPlayerSayScanRadius);
    std::vector<ProximityCandidate> candidates;
    CollectNearbyBots(player, radius, candidates, false);
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
                return IsProximityCooldownActive(
                    _entityCooldowns,
                    GetEntityCooldownKey(player, c),
                    sLLMChatterConfig
                        ->_proxChatterEntityCooldown,
                    true);
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
            "",
            "",
            sLLMChatterConfig
                ->_proxDirectedExpirySeconds);
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
        "",
        "",
        sLLMChatterConfig
            ->_proxDirectedExpirySeconds);
}

void MaybeQueueProximityScene(Player* player)
{
    if (!IsEligibleAmbientProximityAnchor(player))
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
    CollectNearbyBots(player, radius, candidates, false);
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
    if (!IsEligibleAmbientProximityAnchor(player))
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
                player, target->ToPlayer(), replyRadius, true);
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
    Player* player, Player* bot, float radius,
    bool allowMounted)
{
    return IsEligibleProximityBot(
        player, bot, radius, allowMounted);
}

bool IsProximityDirectedPlayerbotEligible(
    Player* player, Player* bot, float radius)
{
    if (!IsEligibleProximityAnchor(player)
        || !IsEligibleProximityBot(
            player, bot, radius, true))
    {
        return false;
    }
    if (IsSameGroup(bot, player->GetGroup()))
        return false;
    return player->GetTeamId() == bot->GetTeamId();
}

bool IsProximityPlayerbotEmoteRouteEnabled()
{
    return sLLMChatterConfig
        && sLLMChatterConfig->IsEnabled()
        && sLLMChatterConfig->_proxChatterEnable
        && sLLMChatterConfig->_useEventSystem
        && sLLMChatterConfig->_emoteReactionsEnable;
}

bool IsProximityNPCEligible(
    Player* player, Creature* creature, float radius)
{
    return IsEligibleProximityNPC(
        player, creature, radius);
}

void CheckProximityChatter(bool instanceMaps)
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
        Map* map = player->GetMap();
        bool playerInInstance =
            IsInstanceProximityMap(map);
        if (playerInInstance != instanceMaps)
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
    if (sLLMChatterConfig
            ->IsPlayerChatPrefixIgnored(safeMsg))
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
            ->_proxDirectedExpirySeconds,
        false);

    scene->pendingReply = true;
    scene->lastActivity = time(nullptr);
}

void HandleProximityPlayerEmote(
    Player* player, Creature* creature,
    uint32 textEmote, uint32 mirrorEmote)
{
    if (!sLLMChatterConfig
        || !sLLMChatterConfig->IsEnabled()
        || !sLLMChatterConfig->_proxChatterEnable
        || !sLLMChatterConfig->_useEventSystem
        || !sLLMChatterConfig->_emoteReactionsEnable
        || !player || IsPlayerBot(player)
        || !creature)
    {
        return;
    }
    if (IsCreatureEmoteScripted(creature, textEmote))
        return;
    if (!IsEligibleProximityAnchor(player))
        return;

    float radius = static_cast<float>(
        sLLMChatterConfig
            ->_proxChatterPlayerSayScanRadius);
    if (!IsEligibleProximityNPC(
            player, creature, radius))
    {
        return;
    }

    Map* map = player->GetMap();
    std::string pairKey =
        std::to_string(
            player->GetGUID().GetCounter())
        + ":" + std::to_string(player->GetMapId())
        + ":" + std::to_string(
            map ? map->GetInstanceId() : 0)
        + ":" + std::to_string(
            creature->GetSpawnId());
    if (IsProximityCooldownActive(
            _directedEmoteCooldowns,
            pairKey,
            sLLMChatterConfig
                ->_emoteNPCVerbalCooldown,
            false))
    {
        return;
    }
    if (urand(1, 100)
        > sLLMChatterConfig
              ->_emoteNPCVerbalReactionChance)
    {
        return;
    }

    std::vector<ProximityCandidate> candidates;
    CollectNearbyNPCs(player, radius, candidates);
    DeduplicateCandidates(candidates);
    auto addressedIt = std::find_if(
        candidates.begin(), candidates.end(),
        [creature](ProximityCandidate const& candidate)
        {
            return candidate.isNPC
                && candidate.npc == creature;
        });
    if (addressedIt == candidates.end())
        return;

    std::vector<ProximityCandidate> speakers = {
        *addressedIt,
    };
    std::vector<ProximityCandidate> extras =
        SelectDirectedReactors(
            player, candidates, *addressedIt, nullptr,
            DirectedReactorScope::NPCOnly,
            sLLMChatterConfig
                ->_proxDirectedMaxExtraReactors,
            false);
    speakers.insert(
        speakers.end(), extras.begin(), extras.end());

    std::string interactionMode =
        speakers.size() > 1
        && urand(1, 100)
            <= sLLMChatterConfig
                   ->_proxDirectedNPCAsideChance
        ? "npc_aside" : "player_inclusive";
    if (!TryReserveProximityCooldown(
            _directedEmoteCooldowns,
            pairKey,
            sLLMChatterConfig
                ->_emoteNPCVerbalCooldown))
    {
        return;
    }
    QueuePlayerEmoteProximityEvent(
        player, *addressedIt, speakers, candidates,
        GetTextEmoteName(textEmote),
        textEmote, mirrorEmote,
        interactionMode, true);
}

bool HandleProximityPlayerbotEmote(
    Player* player, Player* bot,
    uint32 textEmote, uint32 mirrorEmote)
{
    if (!IsProximityPlayerbotEmoteRouteEnabled()
        || !player || IsPlayerBot(player) || !bot)
    {
        return false;
    }

    float radius = static_cast<float>(
        sLLMChatterConfig
            ->_proxChatterPlayerSayScanRadius);
    if (!IsProximityDirectedPlayerbotEligible(
            player, bot, radius))
    {
        return false;
    }

    Map* map = player->GetMap();
    std::string pairKey = "bot:"
        + std::to_string(
            player->GetGUID().GetCounter())
        + ":" + std::to_string(player->GetMapId())
        + ":" + std::to_string(
            map ? map->GetInstanceId() : 0)
        + ":" + std::to_string(
            bot->GetGUID().GetCounter());
    uint32 cooldownSeconds =
        sLLMChatterConfig->_emoteMirrorCooldown * 2;
    if (IsProximityCooldownActive(
            _directedBotEmoteCooldowns,
            pairKey, cooldownSeconds, false))
    {
        return false;
    }
    uint32 verbalRoll = urand(1, 100);
    bool addressedSpeaks = verbalRoll
        <= sLLMChatterConfig
               ->_emoteUngroupedBotVerbalReactionChance;
    uint32 witnessRoll = addressedSpeaks
        ? 0 : urand(1, 100);
    bool witnessSceneAccepted = !addressedSpeaks
        && witnessRoll
            <= sLLMChatterConfig
                   ->_emoteUngroupedBotWitnessReactionChance;
    if (sLLMChatterConfig->IsDebugLog())
    {
        LOG_DEBUG(
            "module",
            "LLMChatter: directed playerbot emote target={} "
            "verbal_roll={} addressed_speaks={} witness_roll={} "
            "witness_scene={}",
            bot->GetName(), verbalRoll, addressedSpeaks,
            witnessRoll, witnessSceneAccepted);
    }
    if (!addressedSpeaks && !witnessSceneAccepted)
    {
        return false;
    }

    std::vector<ProximityCandidate> candidates;
    CollectNearbyBots(player, radius, candidates, true);
    CollectNearbyNPCs(player, radius, candidates);
    DeduplicateCandidates(candidates);
    auto addressedIt = std::find_if(
        candidates.begin(), candidates.end(),
        [bot](ProximityCandidate const& candidate)
        {
            return !candidate.isNPC && candidate.bot
                && candidate.bot->GetGUID() == bot->GetGUID();
        });
    if (addressedIt == candidates.end())
        return false;

    std::vector<ProximityCandidate> speakers;
    if (addressedSpeaks)
        speakers.push_back(*addressedIt);

    std::vector<ProximityCandidate> extras =
        SelectDirectedReactors(
            player, candidates, *addressedIt, nullptr,
            DirectedReactorScope::NPCsAndUngroupedBots,
            sLLMChatterConfig
                ->_proxDirectedBotMaxParticipants - 1,
            !addressedSpeaks);
    speakers.insert(
        speakers.end(), extras.begin(), extras.end());
    if (speakers.empty())
    {
        if (sLLMChatterConfig->IsDebugLog())
        {
            LOG_DEBUG(
                "module",
                "LLMChatter: directed playerbot emote target={} "
                "has no eligible witness speakers",
                bot->GetName());
        }
        return false;
    }

    if (!TryReserveProximityCooldown(
            _directedBotEmoteCooldowns,
            pairKey, cooldownSeconds))
    {
        return false;
    }

    return QueuePlayerEmoteProximityEvent(
        player, *addressedIt, speakers, candidates,
        GetTextEmoteName(textEmote),
        textEmote, mirrorEmote,
        "player_inclusive", addressedSpeaks);
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
