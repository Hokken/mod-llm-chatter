/*
 * mod-llm-chatter - proximity chatter domain
 */

#include "LLMChatterProximity.h"

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
    if (bot->GetMapId() != player->GetMapId())
        return false;
    if (!player->IsWithinDistInMap(bot, radius))
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
    if (cr->IsPet() || cr->IsTotem()
        || cr->IsGuardian())
        return false;
    if (cr->IsPlayer() || cr->IsInCombat())
        return false;
    if (cr->IsHostileTo(player))
        return false;

    CreatureTemplate const* tmpl =
        cr->GetCreatureTemplate();
    if (!tmpl)
        return false;
    if (cr->GetName().empty())
        return false;

    switch (tmpl->type)
    {
        case CREATURE_TYPE_CRITTER:
        case CREATURE_TYPE_BEAST:
        case CREATURE_TYPE_MECHANICAL:
        case CREATURE_TYPE_ELEMENTAL:
        case CREATURE_TYPE_GAS_CLOUD:
        case CREATURE_TYPE_NON_COMBAT_PET:
        case CREATURE_TYPE_TOTEM:
            return false;
        default:
            break;
    }

    if (cr->IsGuard())
        return true;

    uint32 npcFlags =
        cr->GetUInt32Value(UNIT_NPC_FLAGS);
    if (npcFlags
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
            | UNIT_NPC_FLAG_QUESTGIVER))
        return true;

    return tmpl->type == CREATURE_TYPE_HUMANOID;
}

WorldObject* ResolveParticipantObject(
    Player* player,
    ProximityParticipant const& participant)
{
    if (!player || !player->IsInWorld())
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
    if (bot->GetMapId() != player->GetMapId())
        return nullptr;
    return bot;
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
        + JsonEscape(GetClassName(bot->getClass()))
        + "\",\"race\":\""
        + JsonEscape(GetRaceName(bot->getRace()))
        + "\",\"role\":\"bot\"}";
}

std::string BuildNPCParticipantJson(Creature* cr)
{
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
            cr->GetCreatureTemplate()->SubName)
        + "\"}";
}

std::string BuildParticipantJson(
    ProximityCandidate const& candidate)
{
    if (candidate.isNPC && candidate.npc)
        return BuildNPCParticipantJson(
            candidate.npc);

    if (candidate.bot)
        return BuildBotParticipantJson(
            candidate.bot);

    return "{}";
}

std::string BuildParticipantsJson(
    std::vector<ProximityCandidate> const& candidates)
{
    std::string json = "[";
    for (size_t i = 0; i < candidates.size(); ++i)
    {
        if (i > 0)
            json += ",";
        json += BuildParticipantJson(candidates[i]);
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
    std::string key = std::to_string(
        player->GetGUID().GetCounter())
        + ":"
        + std::to_string(player->GetZoneId());
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

    std::string key = std::to_string(
        player->GetGUID().GetCounter())
        + ":"
        + std::to_string(player->GetZoneId());
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
    ProximityCandidate const& candidate)
{
    return std::string(candidate.isNPC ? "npc:" : "bot:")
        + std::to_string(candidate.id);
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
            GetClassName(bot->getClass());
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
    return std::string("{")
        + "\"player_guid\":"
        + std::to_string(
            player->GetGUID().GetCounter())
        + ",\"player_name\":\""
        + JsonEscape(player->GetName())
        + "\",\"zone_id\":"
        + std::to_string(player->GetZoneId())
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
        + BuildParticipantsJson(speakers)
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
        GetEntityCooldownKey(first);
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
        GetEntityCooldownKey(first);

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
            GetEntityCooldownKey(s));
}

void HandleProximityPlayerSayNewScene(
    Player* player, std::string const& safeMsg)
{
    if (!player || !player->IsInWorld())
        return;
    if (player->IsInCombat() || player->IsMounted()
        || player->IsFlying())
        return;

    Map* map = player->GetMap();
    if (!map || map->IsRaid() || map->IsDungeon()
        || map->IsBattleground())
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
            [](ProximityCandidate const& c)
            {
                return IsEventOnCooldown(
                    _entityCooldowns,
                    GetEntityCooldownKey(c),
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

    // Check if the player has a target that matches
    // a candidate — if so, that entity should be the
    // primary responder.
    ProximityCandidate const* targetCandidate =
        nullptr;
    ObjectGuid selGuid =
        player->GetGuidValue(UNIT_FIELD_TARGET);
    if (selGuid)
    {
        for (auto const& c : nonParty)
        {
            if (c.isNPC && c.npc
                && c.npc->GetGUID() == selGuid)
            {
                targetCandidate = &c;
                break;
            }
            if (!c.isNPC && c.bot
                && c.bot->GetGUID() == selGuid)
            {
                targetCandidate = &c;
                break;
            }
        }
    }

    std::string addressedName =
        targetCandidate
            ? targetCandidate->name
            : std::string();

    std::shuffle(
        candidates.begin(), candidates.end(),
        _rng);

    bool wantsConversation =
        candidates.size() >= 2
        && urand(1, 100)
            <= sLLMChatterConfig
                   ->_proxChatterConversationChance;

    if (wantsConversation)
    {
        size_t participantCount = std::min<size_t>(
            candidates.size(), 3);
        std::vector<ProximityCandidate> speakers(
            candidates.begin(),
            candidates.begin() + participantCount);

        // If player has a targeted candidate,
        // ensure it is the first speaker.
        if (targetCandidate)
        {
            bool found = false;
            for (size_t i = 0; i < speakers.size();
                 ++i)
            {
                if (speakers[i].id
                        == targetCandidate->id
                    && speakers[i].isNPC
                        == targetCandidate->isNPC)
                {
                    std::swap(speakers[0],
                              speakers[i]);
                    found = true;
                    break;
                }
            }
            if (!found)
                speakers[0] = *targetCandidate;
        }

        // Ensure at least one non-party speaker.
        bool hasNonParty = false;
        for (auto const& s : speakers)
        {
            if (s.isNPC
                || !IsSameGroup(
                    s.bot, playerGroup))
            {
                hasNonParty = true;
                break;
            }
        }
        if (!hasNonParty && !nonParty.empty())
        {
            // Swap last speaker with a random
            // non-party candidate.
            std::shuffle(
                nonParty.begin(), nonParty.end(),
                _rng);
            speakers.back() = nonParty.front();
        }

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
            addressedName);
        return;
    }

    // Single speaker — prefer player's target,
    // then any non-party candidate.
    ProximityCandidate chosen;
    if (targetCandidate)
    {
        chosen = *targetCandidate;
    }
    else
    {
        std::shuffle(
            nonParty.begin(), nonParty.end(),
            _rng);
        chosen = nonParty.front();
    }
    std::vector<ProximityCandidate> speaker = {
        chosen};
    QueuePlayerSayProximityEvent(
        player,
        "proximity_player_say",
        speaker,
        candidates,
        1,
        safeMsg,
        addressedName);
}

void MaybeQueueProximityScene(Player* player)
{
    if (!player || !player->IsInWorld())
        return;
    if (player->IsInCombat() || player->IsMounted()
        || player->IsFlying())
        return;

    Map* map = player->GetMap();
    if (!map || map->IsRaid() || map->IsDungeon()
        || map->IsBattleground())
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

    std::shuffle(
        candidates.begin(), candidates.end(),
        _rng);

    bool playerAddressed =
        urand(1, 100)
        <= sLLMChatterConfig
               ->_proxChatterPlayerAddressChance;
    bool wantsConversation =
        candidates.size() >= 2
        && urand(1, 100)
            <= sLLMChatterConfig
                   ->_proxChatterConversationChance;

    if (wantsConversation)
    {
        size_t participantCount = std::min<size_t>(
            candidates.size(), 3);
        std::vector<ProximityCandidate> speakers(
            candidates.begin(),
            candidates.begin() + participantCount);

        // If all speakers are party bots, skip —
        // idle party chat already handles that.
        Group* playerGroup = player->GetGroup();
        bool allPartyBots = playerGroup != nullptr;
        for (auto const& s : speakers)
        {
            if (s.isNPC
                || !IsSameGroup(s.bot, playerGroup))
            {
                allPartyBots = false;
                break;
            }
        }
        if (allPartyBots)
            return;

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

    // Filter to non-party candidates only — party
    // chatter owns grouped-bot conversations.
    Group* grp = player->GetGroup();
    std::vector<ProximityCandidate> nonParty;
    for (auto const& c : candidates)
    {
        if (c.isNPC
            || !IsSameGroup(c.bot, grp))
            nonParty.push_back(c);
    }
    if (nonParty.empty())
        return;

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
    if (!player)
        return nullptr;

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

        ProximityParticipant responder;
        responder.id = scene.lastSpeakerId;
        responder.isNPC = scene.lastSpeakerIsNPC;
        responder.name = scene.lastSpeakerName;
        WorldObject* target =
            ResolveParticipantObject(
                player, responder);
        if (!target)
            continue;
        if (!player->IsWithinDistInMap(target, 40.0f))
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
    if (trimmed.size()
        > sLLMChatterConfig->_maxMessageLength)
    {
        trimmed.resize(
            sLLMChatterConfig->_maxMessageLength);
    }
    return trimmed;
}
} // namespace

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
    Player* player, uint32 type,
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

    EvictExpiredScenes();

    std::string safeMsg = TrimChatMessage(msg);
    if (safeMsg.empty())
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
        + "\",\"zone_name\":\""
        + JsonEscape(
            GetAreaNameForLocale(
                player->GetZoneId()))
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
    uint32 zoneId, uint32 botGuid,
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
        auto& ids = _playerScenes[playerGuid];
        if (std::find(
                ids.begin(), ids.end(), eventId)
            == ids.end())
            ids.push_back(eventId);
    }

    ObjectGuid playerObjGuid =
        ObjectGuid::Create<HighGuid::Player>(
            playerGuid);
    Player* player =
        ObjectAccessor::FindPlayer(playerObjGuid);
    if (player && player->IsInWorld())
        scene.mapId = player->GetMapId();

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
