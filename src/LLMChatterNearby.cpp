/*
 * mod-llm-chatter - nearby object and creature ownership
 */

#include "LLMChatterNearby.h"

#include "LLMChatterConfig.h"
#include "LLMChatterGroup.h"
#include "LLMChatterShared.h"

#include "CellImpl.h"
#include "DatabaseEnv.h"
#include "DBCStores.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "Group.h"
#include "Player.h"
#include "World.h"
#include "WorldSession.h"
#include "WorldSessionMgr.h"

#include <algorithm>
#include <ctime>
#include <list>
#include <map>
#include <random>
#include <set>
#include <string>
#include <vector>

struct NearbyGameObjectCheck
{
    WorldObject const* _obj;
    float _range;

    NearbyGameObjectCheck(
        WorldObject const* obj, float range)
        : _obj(obj), _range(range) {}

    WorldObject const& GetFocusObject() const
    {
        return *_obj;
    }

    bool operator()(GameObject* go)
    {
        return go
            && _obj->IsWithinDistInMap(go, _range)
            && go->isSpawned()
            && go->GetGOInfo();
    }
};

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

static std::map<std::string, time_t> _goNameCooldowns;
static std::map<std::string, time_t> _nearbyCooldownCache;

static bool IsOnNearbyCooldown(
    const std::string& cooldownKey,
    uint32 cooldownSeconds)
{
    return IsEventOnCooldown(
        _nearbyCooldownCache,
        cooldownKey,
        cooldownSeconds);
}

static void SetNearbyCooldown(
    const std::string& cooldownKey)
{
    SetEventCooldown(
        _nearbyCooldownCache,
        cooldownKey);
}

static const char* GetGoTypeName(
    GameobjectTypes type)
{
    switch (type)
    {
        case GAMEOBJECT_TYPE_CHEST:
            return "Chest";
        case GAMEOBJECT_TYPE_GENERIC:
            return "Landmark";
        case GAMEOBJECT_TYPE_SPELL_FOCUS:
            return "SpellFocus";
        case GAMEOBJECT_TYPE_TEXT:
            return "Book";
        case GAMEOBJECT_TYPE_GOOBER:
            return "World Object";
        case GAMEOBJECT_TYPE_QUESTGIVER:
            return "Quest Board";
        case GAMEOBJECT_TYPE_MAILBOX:
            return "Mailbox";
        case GAMEOBJECT_TYPE_MEETINGSTONE:
            return "Meeting Stone";
        case GAMEOBJECT_TYPE_SPELLCASTER:
            return "Portal";
        case GAMEOBJECT_TYPE_MO_TRANSPORT:
            return "Transport";
        case GAMEOBJECT_TYPE_FISHINGHOLE:
            return "Fishing School";
        default:
            return nullptr;
    }
}

static uint8 GetGatheringType(GameObject* go)
{
    if (!go || !go->GetGOInfo())
        return 0;

    uint32 lockId = go->GetGOInfo()->GetLockId();
    if (!lockId)
        return 0;

    LockEntry const* lock =
        sLockStore.LookupEntry(lockId);
    if (!lock)
        return 0;

    for (uint8 i = 0; i < MAX_LOCK_CASE; ++i)
    {
        if (lock->Type[i] != 2)
            continue;
        uint32 skill = lock->Index[i];
        if (skill == LOCKTYPE_HERBALISM)
            return 1;
        if (skill == LOCKTYPE_MINING)
            return 2;
    }

    return 0;
}

static bool IsInterestingGameObject(GameObject* go)
{
    if (!go || !go->GetGOInfo())
        return false;

    if (go->GetGOInfo()->IconName == "Point")
        return false;
    if (go->HasFlag(GAMEOBJECT_FLAGS,
            GO_FLAG_NOT_SELECTABLE))
        return false;

    static const std::set<GameobjectTypes> blacklist = {
        GAMEOBJECT_TYPE_TRAP,
        GAMEOBJECT_TYPE_FLAGSTAND,
        GAMEOBJECT_TYPE_FLAGDROP,
        GAMEOBJECT_TYPE_CAPTURE_POINT,
        GAMEOBJECT_TYPE_DO_NOT_USE,
        GAMEOBJECT_TYPE_DO_NOT_USE_2,
        GAMEOBJECT_TYPE_CAMERA,
        GAMEOBJECT_TYPE_MAP_OBJECT,
        GAMEOBJECT_TYPE_AURA_GENERATOR,
        GAMEOBJECT_TYPE_GUARDPOST,
        GAMEOBJECT_TYPE_DUEL_ARBITER,
        GAMEOBJECT_TYPE_AREADAMAGE,
        GAMEOBJECT_TYPE_BINDER,
        GAMEOBJECT_TYPE_DESTRUCTIBLE_BUILDING,
        GAMEOBJECT_TYPE_TRAPDOOR,
        GAMEOBJECT_TYPE_BUTTON,
        GAMEOBJECT_TYPE_SUMMONING_RITUAL,
        GAMEOBJECT_TYPE_DUNGEON_DIFFICULTY,
        GAMEOBJECT_TYPE_MINI_GAME,
        GAMEOBJECT_TYPE_GUILD_BANK,
        GAMEOBJECT_TYPE_FISHINGNODE,
        GAMEOBJECT_TYPE_CHAIR,
        GAMEOBJECT_TYPE_DOOR,
        GAMEOBJECT_TYPE_BARBER_CHAIR,
    };

    return blacklist.count(go->GetGoType()) == 0;
}

static int GetGoInterestScore(GameObject* go)
{
    static const std::set<GameobjectTypes> high = {
        GAMEOBJECT_TYPE_SPELL_FOCUS,
        GAMEOBJECT_TYPE_TEXT,
        GAMEOBJECT_TYPE_GENERIC,
        GAMEOBJECT_TYPE_GOOBER,
        GAMEOBJECT_TYPE_CHEST,
        GAMEOBJECT_TYPE_CHAIR,
    };

    if (high.count(go->GetGoType()))
        return 2;
    return 1;
}

static bool IsInterestingCreature(
    Creature* cr, Player* bot)
{
    if (!cr || !cr->IsAlive())
        return false;

    if (cr->IsPet() || cr->IsTotem()
        || cr->IsGuardian())
        return false;
    if (cr->IsInCombat())
        return false;
    if (cr->IsPlayer())
        return false;

    CreatureTemplate const* tmpl =
        cr->GetCreatureTemplate();
    if (!tmpl)
        return false;

    uint32 cType = tmpl->type;
    if (cType == CREATURE_TYPE_TOTEM
        || cType == CREATURE_TYPE_NON_COMBAT_PET
        || cType == CREATURE_TYPE_GAS_CLOUD
        || cType == CREATURE_TYPE_NOT_SPECIFIED
        || cType == CREATURE_TYPE_MECHANICAL)
        return false;

    uint32 npcFlags =
        cr->GetUInt32Value(UNIT_NPC_FLAGS);
    uint32 rank = tmpl->rank;

    if (rank == 4)
        return true;
    if (npcFlags
        & (UNIT_NPC_FLAG_FLIGHTMASTER
            | UNIT_NPC_FLAG_INNKEEPER
            | UNIT_NPC_FLAG_QUESTGIVER
            | UNIT_NPC_FLAG_TRAINER
            | UNIT_NPC_FLAG_TRAINER_CLASS
            | UNIT_NPC_FLAG_TRAINER_PROFESSION
            | UNIT_NPC_FLAG_VENDOR
            | UNIT_NPC_FLAG_VENDOR_AMMO
            | UNIT_NPC_FLAG_VENDOR_FOOD
            | UNIT_NPC_FLAG_VENDOR_POISON
            | UNIT_NPC_FLAG_VENDOR_REAGENT))
        return true;

    if (cType == CREATURE_TYPE_CRITTER
        || cType == CREATURE_TYPE_BEAST)
        return true;

    if (cType == CREATURE_TYPE_HUMANOID
        && !tmpl->SubName.empty())
        return true;

    return false;
}

static int GetCreatureInterestScore(Creature* cr)
{
    CreatureTemplate const* tmpl =
        cr->GetCreatureTemplate();
    uint32 rank = tmpl->rank;
    uint32 npcFlags =
        cr->GetUInt32Value(UNIT_NPC_FLAGS);

    if (rank == 4)
        return 3;
    if (npcFlags
        & (UNIT_NPC_FLAG_FLIGHTMASTER
            | UNIT_NPC_FLAG_INNKEEPER
            | UNIT_NPC_FLAG_QUESTGIVER
            | UNIT_NPC_FLAG_TRAINER
            | UNIT_NPC_FLAG_TRAINER_CLASS
            | UNIT_NPC_FLAG_TRAINER_PROFESSION
            | UNIT_NPC_FLAG_VENDOR
            | UNIT_NPC_FLAG_VENDOR_AMMO
            | UNIT_NPC_FLAG_VENDOR_FOOD
            | UNIT_NPC_FLAG_VENDOR_POISON
            | UNIT_NPC_FLAG_VENDOR_REAGENT))
        return 2;

    return 1;
}

void CheckNearbyGameObjects()
{
    time_t now = time(nullptr);
    for (auto it = _goNameCooldowns.begin();
         it != _goNameCooldowns.end();)
    {
        if (now - it->second
            > (time_t)sLLMChatterConfig
                  ->_nearbyObjectNameCooldown)
        {
            it = _goNameCooldowns.erase(it);
        }
        else
        {
            ++it;
        }
    }

    EvictEmoteCooldowns();

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

        Group* group = player->GetGroup();
        if (!group || !GroupHasBots(group))
            continue;

        if (player->IsInCombat()
            || player->InBattleground()
            || player->IsMounted()
            || player->IsFlying())
            continue;

        std::vector<Player*> bots;
        bool groupInCombat = false;
        for (auto ref = group->GetFirstMember();
             ref; ref = ref->next())
        {
            Player* member = ref->GetSource();
            if (!member || !member->IsInWorld())
                continue;
            if (member->IsInCombat())
            {
                groupInCombat = true;
                break;
            }
            if (IsPlayerBot(member)
                && member->GetMapId()
                    == player->GetMapId())
            {
                bots.push_back(member);
            }
        }

        if (groupInCombat || bots.empty())
            continue;

        Player* bot = bots[urand(0, bots.size() - 1)];
        uint32 botZoneId = bot->GetZoneId();
        std::string cooldownKey = fmt::format(
            "nearby_obj:group:{}:zone:{}",
            group->GetGUID().GetCounter(),
            botZoneId);
        if (IsOnNearbyCooldown(
                cooldownKey,
                sLLMChatterConfig
                    ->_nearbyObjectCooldown))
            continue;

        if (urand(1, 100)
            > sLLMChatterConfig
                  ->_nearbyObjectChance)
            continue;

        float radius =
            (float)sLLMChatterConfig
                ->_nearbyObjectScanRadius;

        struct ScoredPOI
        {
            std::string name;
            std::string typeName;
            std::string subName;
            float distance;
            uint32 entry;
            uint32 spellFocusId;
            uint32 level;
            int score;
            bool isCreature;
        };

        std::vector<ScoredPOI> candidates;

        std::list<GameObject*> goList;
        NearbyGameObjectCheck goCheck(bot, radius);
        Acore::GameObjectListSearcher<
            NearbyGameObjectCheck>
            goSearcher(bot, goList, goCheck);
        Cell::VisitObjects(bot, goSearcher, radius);

        for (GameObject* go : goList)
        {
            if (!IsInterestingGameObject(go))
                continue;

            std::string goName =
                go->GetGOInfo()->name;
            if (goName.empty())
                continue;

            std::string nameCdKey =
                fmt::format("{}:{}",
                    bot->GetName(), goName);
            auto cdIt =
                _goNameCooldowns.find(nameCdKey);
            if (cdIt != _goNameCooldowns.end()
                && now - cdIt->second
                    < (time_t)sLLMChatterConfig
                          ->_nearbyObjectNameCooldown)
                continue;

            ScoredPOI sp;
            sp.name = goName;

            uint8 gather = GetGatheringType(go);
            if (gather == 1)
                sp.typeName = "Herb";
            else if (gather == 2)
                sp.typeName = "Ore Vein";
            else
            {
                const char* tn =
                    GetGoTypeName(go->GetGoType());
                if (!tn)
                    continue;
                sp.typeName = tn;
            }

            sp.subName = "";
            sp.distance = bot->GetDistance(go);
            sp.entry = go->GetEntry();
            sp.spellFocusId = 0;
            if (go->GetGoType()
                == GAMEOBJECT_TYPE_SPELL_FOCUS)
            {
                sp.spellFocusId =
                    go->GetGOInfo()
                        ->spellFocus.focusId;
            }
            sp.level = 0;
            sp.score = GetGoInterestScore(go);
            sp.isCreature = false;
            candidates.push_back(sp);
        }

        std::list<Creature*> crList;
        NearbyCreatureCheck crCheck(bot, radius);
        Acore::CreatureListSearcher<
            NearbyCreatureCheck>
            crSearcher(bot, crList, crCheck);
        Cell::VisitObjects(bot, crSearcher, radius);

        for (Creature* cr : crList)
        {
            if (!IsInterestingCreature(cr, bot))
                continue;

            std::string crName = cr->GetName();
            if (crName.empty())
                continue;

            std::string nameCdKey =
                fmt::format("{}:{}",
                    bot->GetName(), crName);
            auto cdIt =
                _goNameCooldowns.find(nameCdKey);
            if (cdIt != _goNameCooldowns.end()
                && now - cdIt->second
                    < (time_t)sLLMChatterConfig
                          ->_nearbyObjectNameCooldown)
                continue;

            ScoredPOI sp;
            sp.name = crName;
            sp.typeName = GetCreatureRoleName(cr);
            sp.subName =
                cr->GetCreatureTemplate()->SubName;
            sp.distance = bot->GetDistance(cr);
            sp.entry = cr->GetEntry();
            sp.spellFocusId = 0;
            sp.level = cr->GetLevel();
            sp.score = GetCreatureInterestScore(cr);
            sp.isCreature = true;
            candidates.push_back(sp);
        }

        {
            std::map<std::string, size_t> best;
            for (size_t i = 0;
                 i < candidates.size();
                 ++i)
            {
                auto bestIt =
                    best.find(candidates[i].name);
                if (bestIt == best.end())
                    best[candidates[i].name] = i;
                else if (
                    candidates[i].distance
                    < candidates[bestIt->second]
                          .distance)
                    bestIt->second = i;
            }

            std::vector<ScoredPOI> deduped;
            for (auto& [nm, idx] : best)
                deduped.push_back(candidates[idx]);
            candidates = std::move(deduped);
        }

        if (candidates.empty())
            continue;

        static std::mt19937 rng(std::random_device{}());
        std::shuffle(candidates.begin(),
            candidates.end(), rng);

        std::stable_sort(candidates.begin(),
            candidates.end(),
            [](const ScoredPOI& a,
               const ScoredPOI& b) {
                return a.score > b.score;
            });

        candidates.resize(1);

        std::string objectsJson = "[";
        for (size_t i = 0;
             i < candidates.size(); ++i)
        {
            auto& c = candidates[i];
            if (i > 0)
                objectsJson += ",";
            objectsJson += fmt::format(
                R"({{"name":"{}",)"
                R"("type":"{}",)"
                R"("sub_name":"{}",)"
                R"("distance_yards":{:.1f},)"
                R"("entry":{},)"
                R"("spell_focus_id":{},)"
                R"("level":{},)"
                R"("is_creature":{}}})",
                JsonEscape(c.name),
                JsonEscape(c.typeName),
                JsonEscape(c.subName),
                c.distance,
                c.entry,
                c.spellFocusId,
                c.level,
                c.isCreature ? "true" : "false");
        }
        objectsJson += "]";

        uint32 zoneId = bot->GetZoneId();
        uint32 areaId = bot->GetAreaId();
        uint32 mapId = bot->GetMapId();
        AreaTableEntry const* zone =
            sAreaTableStore.LookupEntry(zoneId);
        AreaTableEntry const* area =
            sAreaTableStore.LookupEntry(areaId);
        char const* zp = zone
            ? zone->area_name[
                sWorld->GetDefaultDbcLocale()]
            : nullptr;
        std::string zoneName = zp ? zp : "";
        char const* sp = area
            ? area->area_name[
                sWorld->GetDefaultDbcLocale()]
            : nullptr;
        std::string subzoneName = sp ? sp : "";
        bool inCity =
            zone
            && (zone->flags & AREA_FLAG_CAPITAL);
        bool inDungeon =
            bot->GetMap()
            && bot->GetMap()->IsDungeon();

        std::string extraJson =
            "{\"objects\":" + objectsJson + ","
            + BuildBotIdentityFields(bot) + ","
            + "\"group_id\":"
            + std::to_string(
                group->GetGUID().GetCounter())
            + ",\"zone_name\":\""
            + JsonEscape(zoneName)
            + "\",\"subzone_name\":\""
            + JsonEscape(subzoneName)
            + "\",\"in_city\":"
            + std::string(
                inCity ? "true" : "false")
            + ",\"in_dungeon\":"
            + std::string(
                inDungeon ? "true" : "false")
            + "}";

        extraJson = EscapeString(extraJson);

        auto& primary = candidates[0];
        uint32 facingTargetGuid =
            primary.isCreature
                ? primary.entry : 0;
        uint32 facingTargetEntry = primary.entry;
        std::string facingTargetName =
            primary.name;

        QueueChatterEvent(
            "bot_group_nearby_object",
            "player",
            zoneId,
            mapId,
            GetChatterEventPriority(
                "bot_group_nearby_object"),
            cooldownKey,
            bot->GetGUID().GetCounter(),
            bot->GetName(),
            facingTargetGuid,
            facingTargetName,
            facingTargetEntry,
            extraJson,
            GetReactionDelaySeconds(
                "bot_group_nearby_object"),
            sLLMChatterConfig
                ->_eventExpirationSeconds,
            false);

        SetNearbyCooldown(cooldownKey);
        for (auto& c : candidates)
        {
            std::string nameCd = fmt::format(
                "{}:{}",
                bot->GetName(), c.name);
            _goNameCooldowns[nameCd] = now;
        }
    }
}
