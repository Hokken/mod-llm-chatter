/*
 * mod-llm-chatter - group player/combat hook ownership
 *
 * This file owns the remaining free-function
 * implementations behind LLMChatterGroupPlayerScript,
 * plus the shared zone/state polling helpers that are
 * still part of the group domain.
 */

#include "LLMChatterConfig.h"
#include "LLMChatterBG.h"
#include "LLMChatterGroup.h"
#include "LLMChatterGroupInternal.h"
#include "LLMChatterProximity.h"
#include "LLMChatterShared.h"

#include "AchievementMgr.h"
#include "Battleground.h"
#include "Chat.h"
#include "DatabaseEnv.h"
#include "DBCStores.h"
#include "Group.h"
#include "Log.h"
#include "ObjectAccessor.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "Playerbots.h"
#include "Spell.h"
#include "World.h"
#include "WorldSessionMgr.h"

#include <algorithm>
#include <ctime>
#include <set>
#include <string>
#include <vector>

namespace
{

void QueueStateCallout(
    Player* bot, Group* group,
    const char* eventType, uint32 groupId)
{
    if (!bot->IsAlive())
        return;

    std::string botName = bot->GetName();
    uint32 botGuid =
        bot->GetGUID().GetCounter();

    std::string targetName = "";
    Unit* victim = bot->GetVictim();
    if (victim)
        targetName = victim->GetName();

    std::string aggroTarget = "";
    if (victim && victim->GetVictim()
        && victim->GetVictim() != bot)
    {
        aggroTarget =
            victim->GetVictim()->GetName();
    }

    if (sLLMChatterConfig->_preCacheEnable
        && sLLMChatterConfig
               ->_preCacheStateEnable
        && group)
    {
        std::string category;
        std::string evtStr(eventType);
        if (evtStr == "bot_group_low_health")
            category = "state_low_health";
        else if (evtStr == "bot_group_oom")
            category = "state_oom";
        else if (evtStr == "bot_group_aggro_loss")
            category = "state_aggro_loss";

        if (!category.empty())
        {
            std::string cachedMsg, cachedEmote;
            if (TryConsumeCachedReaction(
                    groupId, botGuid,
                    category,
                    cachedMsg, cachedEmote))
            {
                std::string tgt =
                    (category == "state_aggro_loss")
                    ? targetName : "";
                ResolvePlaceholders(
                    cachedMsg, tgt, "", "");
                SendPartyMessageInstant(
                    bot, group,
                    cachedMsg, cachedEmote);
                RecordCachedChatHistory(
                    groupId, botGuid,
                    botName, cachedMsg);
                return;
            }
            if (!sLLMChatterConfig
                    ->_preCacheFallbackToLive)
                return;
        }
    }

    std::string extraData = "{"
        "\"bot_guid\":" +
            std::to_string(botGuid) + ","
        "\"bot_name\":\"" +
            JsonEscape(botName) + "\","
        "\"group_id\":" +
            std::to_string(groupId) + ","
        "\"target_name\":\"" +
            JsonEscape(targetName) + "\","
        "\"aggro_target\":\"" +
            JsonEscape(aggroTarget) + "\","
        + BuildBotStateJson(bot) + "}";

    if (bot->InBattleground())
    {
        Battleground* bg =
            bot->GetBattleground();
        if (bg)
            AppendBGContext(bg, bot, extraData);
    }

    extraData = EscapeString(extraData);

    QueueChatterEvent(
        eventType,
        "player",
        bot->GetZoneId(),
        bot->GetMapId(),
        GetChatterEventPriority(eventType),
        std::string("state:") + eventType + ":"
            + std::to_string(botGuid),
        botGuid,
        botName,
        0,
        "",
        0,
        extraData,
        GetReactionDelaySeconds(eventType),
        60,
        false
    );
}

} // namespace

void HandleGroupCreatureKillImpl(
    Player* killer, Creature* killed)
{
    if (!sLLMChatterConfig
        || !sLLMChatterConfig->IsEnabled()
        || !sLLMChatterConfig->_useGroupChatter)
        return;

    if (!killer || !killed)
        return;

    if (killer->InBattleground())
        return;

    Group* group = killer->GetGroup();
    if (!group)
        return;

    if (!GroupHasRealPlayer(group))
        return;

    Player* reactor = nullptr;
    if (IsPlayerBot(killer))
        reactor = killer;
    else
        reactor = GetRandomBotInGroup(group);

    if (!reactor)
        return;

    CreatureTemplate const* tmpl =
        killed->GetCreatureTemplate();
    if (!tmpl)
        return;

    uint32 rank = tmpl->rank;
    bool isBoss = (rank == 3)
        || (tmpl->type_flags
            & CREATURE_TYPE_FLAG_BOSS_MOB)
        || killed->IsDungeonBoss()
        || _namedBossEntries.count(
            killed->GetEntry());
    bool isRare = (rank == 2 || rank == 4);
    bool isNormal = !isBoss && !isRare;

    uint32 groupId =
        group->GetGUID().GetCounter();

    time_t now = time(nullptr);
    if (isNormal)
    {
        auto it =
            _groupKillCooldowns.find(groupId);
        if (it != _groupKillCooldowns.end()
            && (now - it->second)
               < (time_t)sLLMChatterConfig
                   ->_groupKillCooldown)
            return;
    }

    if (isNormal && urand(1, 100)
        > sLLMChatterConfig
            ->_groupKillChanceNormal)
        return;

    _groupKillCooldowns[groupId] = now;

    uint32 botGuid =
        reactor->GetGUID().GetCounter();
    std::string botName = reactor->GetName();
    std::string creatureName = killed->GetName();
    uint32 creatureEntry = killed->GetEntry();

    std::string extraData = "{"
        + BuildBotIdentityFields(reactor) + ","
        "\"creature_name\":\"" +
            JsonEscape(creatureName) + "\","
        "\"creature_entry\":" +
            std::to_string(creatureEntry) + ","
        "\"is_boss\":" +
            std::string(
                isBoss ? "true" : "false") + ","
        "\"is_rare\":" +
            std::string(
                isRare ? "true" : "false") + ","
        "\"is_normal\":" +
            std::string(
                isNormal ? "true" : "false") + ","
        "\"group_id\":" +
            std::to_string(groupId) + ","
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
        creatureName,
        creatureEntry,
        extraData,
        GetReactionDelaySeconds("bot_group_kill"),
        120,
        false
    );
}

void HandleGroupPlayerKilledByCreatureImpl(
    Creature* killer, Player* killed)
{
    if (!sLLMChatterConfig
        || !sLLMChatterConfig->IsEnabled()
        || !sLLMChatterConfig->_useGroupChatter)
        return;

    if (!killed)
        return;

    Group* group = killed->GetGroup();
    if (!group)
        return;

    if (!GroupHasRealPlayer(group))
        return;

    uint32 groupId =
        group->GetGUID().GetCounter();
    time_t now = time(nullptr);

    {
        bool allDead = true;
        uint32 memberCount = 0;
        for (GroupReference* itr =
                 group->GetFirstMember();
             itr != nullptr;
             itr = itr->next())
        {
            Player* member =
                itr->GetSource();
            if (!member)
                continue;
            memberCount++;
            if (member->IsAlive())
            {
                allDead = false;
                break;
            }
        }

        if (allDead
            && memberCount
               >= sLLMChatterConfig
                   ->_wipeMinGroupSize)
        {
            auto wit =
                _groupWipeCooldowns
                    .find(groupId);
            if (wit
                != _groupWipeCooldowns.end()
                && (now - wit->second)
                   < (time_t)
                       sLLMChatterConfig
                           ->_groupWipeCooldown)
            {
                return;
            }

            if (urand(1, 100)
                > sLLMChatterConfig
                    ->_groupWipeChance)
                return;

            _groupWipeCooldowns[groupId] =
                now;

            Player* wipeReactor =
                GetRandomBotInGroup(group);
            if (!wipeReactor)
                return;

            uint32 wrGuid =
                wipeReactor->GetGUID()
                    .GetCounter();
            std::string wrName =
                wipeReactor->GetName();
            std::string kName =
                killer
                    ? killer->GetName()
                    : "";
            uint32 kEntry =
                killer
                    ? killer->GetEntry()
                    : 0;

            std::string wipeData = "{"
                + BuildBotIdentityFields(
                    wipeReactor) + ","
                "\"group_id\":" +
                    std::to_string(
                        groupId) + ","
                "\"killer_name\":\"" +
                    JsonEscape(
                        kName) + "\","
                "\"killer_entry\":" +
                    std::to_string(
                        kEntry) + ","
                + BuildBotStateJson(wipeReactor)
                + "}";

            wipeData =
                EscapeString(wipeData);

            QueueChatterEvent(
                "bot_group_wipe",
                "player",
                killed->GetZoneId(),
                killed->GetMapId(),
                GetChatterEventPriority(
                    "bot_group_wipe"),
                "",
                wrGuid,
                wrName,
                0,
                kName,
                kEntry,
                wipeData,
                GetReactionDelaySeconds(
                    "bot_group_wipe"),
                120,
                false
            );

            return;
        }
    }

    auto it = _groupDeathCooldowns.find(groupId);
    if (it != _groupDeathCooldowns.end()
        && (now - it->second)
           < (time_t)sLLMChatterConfig
               ->_groupDeathCooldown)
        return;

    if (urand(1, 100)
        > sLLMChatterConfig->_groupDeathChance)
        return;

    _groupDeathCooldowns[groupId] = now;

    Player* reactor = GetRandomBotInGroup(
        group, killed);
    if (!reactor)
        return;

    uint32 reactorGuid =
        reactor->GetGUID().GetCounter();
    std::string reactorName =
        reactor->GetName();

    bool isPlayerDeath =
        !IsPlayerBot(killed);
    uint32 deadGuid =
        killed->GetGUID().GetCounter();
    std::string deadName =
        killed->GetName();
    std::string killerName =
        killer ? killer->GetName() : "";
    uint32 killerEntry =
        killer ? killer->GetEntry() : 0;

    std::string extraData = "{"
        + BuildBotIdentityFields(reactor) + ","
        "\"dead_name\":\"" +
            JsonEscape(deadName) + "\","
        "\"dead_guid\":" +
            std::to_string(deadGuid) + ","
        "\"killer_name\":\"" +
            JsonEscape(killerName) + "\","
        "\"killer_entry\":" +
            std::to_string(killerEntry) + ","
        "\"group_id\":" +
            std::to_string(groupId) + ","
        "\"is_player_death\":" +
            std::string(
                isPlayerDeath
                    ? "true" : "false") + ","
        + BuildBotStateJson(reactor) + "}";

    if (reactor->InBattleground())
    {
        Battleground* bg =
            reactor->GetBattleground();
        if (bg)
            AppendBGContext(
                bg, reactor, extraData);
    }

    extraData = EscapeString(extraData);

    QueueChatterEvent(
        "bot_group_death",
        "player",
        killed->GetZoneId(),
        killed->GetMapId(),
        GetChatterEventPriority("bot_group_death"),
        "",
        reactorGuid,
        reactorName,
        0,
        killerName,
        killerEntry,
        extraData,
        GetReactionDelaySeconds("bot_group_death"),
        120,
        false
    );
}

void HandleGroupLootEventImpl(
    Player* player, Item* item)
{
    if (!sLLMChatterConfig
        || !sLLMChatterConfig->IsEnabled()
        || !sLLMChatterConfig->_useGroupChatter)
        return;

    if (!player)
        return;

    Group* group = player->GetGroup();
    if (!group)
        return;

    if (!GroupHasRealPlayer(group))
        return;

    Map* lMap = player->GetMap();
    if (lMap && lMap->IsBattleground())
        return;

    bool isBot = IsPlayerBot(player);

    if (!item)
        return;
    ItemTemplate const* tmpl =
        item->GetTemplate();
    if (!tmpl)
        return;

    uint8 quality = tmpl->Quality;

    if (lMap && lMap->IsRaid() && quality < 4)
        return;

    if (quality < 2)
        return;
    std::string itemName = tmpl->Name1;
    uint32 itemEntry = item->GetEntry();

    uint32 chance;
    if (quality == 2)
        chance = sLLMChatterConfig
            ->_groupLootChanceGreen;
    else if (quality == 3)
        chance = sLLMChatterConfig
            ->_groupLootChanceBlue;
    else
        chance = 100;

    if (urand(1, 100) > chance)
        return;

    uint32 groupId =
        group->GetGUID().GetCounter();

    time_t now = time(nullptr);
    if (quality < 4)
    {
        auto it =
            _groupLootCooldowns.find(groupId);
        if (it != _groupLootCooldowns.end()
            && (now - it->second)
               < (time_t)sLLMChatterConfig
                   ->_groupLootCooldown)
            return;
    }

    _groupLootCooldowns[groupId] = now;

    std::string looterName = player->GetName();

    Player* reactor = nullptr;
    if (!isBot)
    {
        reactor = GetRandomBotInGroup(group);
    }
    else if (urand(0, 1) == 0)
    {
        reactor =
            GetRandomBotInGroup(group, player);
        if (!reactor)
            reactor = player;
    }
    else
    {
        reactor = player;
    }

    if (!reactor)
        return;

    uint32 reactorGuid =
        reactor->GetGUID().GetCounter();
    std::string reactorName = reactor->GetName();

    std::string extraData = "{"
        + BuildBotIdentityFields(reactor) + ","
        "\"is_bot\":1,"
        "\"looter_name\":\"" +
            JsonEscape(looterName) + "\","
        "\"item_name\":\"" +
            JsonEscape(itemName) + "\","
        "\"item_entry\":" +
            std::to_string(itemEntry) + ","
        "\"item_quality\":" +
            std::to_string(quality) + ","
        "\"group_id\":" +
            std::to_string(groupId)
        + "," + BuildBotStateJson(reactor)
        + "}";

    extraData = EscapeString(extraData);

    QueueChatterEvent(
        "bot_group_loot",
        "player",
        reactor->GetZoneId(),
        reactor->GetMapId(),
        GetChatterEventPriority("bot_group_loot"),
        "",
        reactorGuid,
        reactorName,
        0,
        itemName,
        itemEntry,
        extraData,
        GetReactionDelaySeconds("bot_group_loot"),
        120,
        false
    );
}

void HandleGroupPlayerEnterCombatImpl(
    Player* player, Unit* enemy)
{
    if (!sLLMChatterConfig
        || !sLLMChatterConfig->IsEnabled()
        || !sLLMChatterConfig->_useGroupChatter)
        return;

    if (!player || !enemy)
        return;

    if (!IsPlayerBot(player))
        return;

    Group* group = player->GetGroup();
    if (!group)
        return;

    if (!GroupHasRealPlayer(group))
        return;

    Creature* creature = enemy->ToCreature();
    if (!creature)
        return;

    CreatureTemplate const* tmpl =
        creature->GetCreatureTemplate();
    if (!tmpl)
        return;

    uint32 rank = tmpl->rank;
    bool isBoss = (rank == 3)
        || (tmpl->type_flags
            & CREATURE_TYPE_FLAG_BOSS_MOB);
    bool isElite = (rank >= 1);
    bool isNormal = !isBoss && !isElite;

    uint32 groupId =
        group->GetGUID().GetCounter();

    time_t now = time(nullptr);
    if (!isBoss)
    {
        uint32 cooldownSec = isElite
            ? sLLMChatterConfig->_groupKillCooldown
                / 2
            : sLLMChatterConfig->_groupKillCooldown;
        auto it =
            _groupCombatCooldowns.find(groupId);
        if (it != _groupCombatCooldowns.end()
            && (now - it->second)
               < (time_t)cooldownSec)
            return;
    }

    uint32 chance;
    if (isBoss)
        chance = sLLMChatterConfig
            ->_combatChanceBoss;
    else if (isElite)
        chance = sLLMChatterConfig
            ->_combatChanceElite;
    else
        chance = sLLMChatterConfig
            ->_combatChanceNormal;
    if (urand(1, 100) > chance)
        return;

    _groupCombatCooldowns[groupId] = now;

    uint32 botGuid =
        player->GetGUID().GetCounter();
    std::string botName = player->GetName();
    std::string creatureName =
        creature->GetName();

    if (sLLMChatterConfig->_preCacheEnable
        && sLLMChatterConfig
               ->_preCacheCombatEnable)
    {
        std::string cachedMsg, cachedEmote;
        if (TryConsumeCachedReaction(
                groupId, botGuid,
                "combat_pull",
                cachedMsg, cachedEmote))
        {
            ResolvePlaceholders(
                cachedMsg, creatureName,
                "", "");
            SendPartyMessageInstant(
                player, group,
                cachedMsg, cachedEmote);
            RecordCachedChatHistory(
                groupId, botGuid,
                botName, cachedMsg);
            return;
        }
        if (!sLLMChatterConfig
                ->_preCacheFallbackToLive)
            return;
    }

    std::string extraData = "{"
        + BuildBotIdentityFields(player) + ","
        "\"creature_name\":\"" +
            JsonEscape(creatureName) + "\","
        "\"creature_entry\":" +
            std::to_string(
                creature->GetEntry()) + ","
        "\"is_boss\":" +
            std::string(
                isBoss ? "1" : "0") + ","
        "\"is_elite\":" +
            std::string(
                isElite ? "1" : "0") + ","
        "\"group_id\":" +
            std::to_string(groupId) + ","
        + BuildBotStateJson(player) + "}";

    if (player->InBattleground())
    {
        Battleground* bg =
            player->GetBattleground();
        if (bg)
            AppendBGContext(
                bg, player, extraData);
    }

    extraData = EscapeString(extraData);

    QueueChatterEvent(
        "bot_group_combat",
        "player",
        player->GetZoneId(),
        player->GetMapId(),
        GetChatterEventPriority("bot_group_combat"),
        "",
        botGuid,
        botName,
        0,
        creatureName,
        creature->GetEntry(),
        extraData,
        GetReactionDelaySeconds("bot_group_combat"),
        30,
        false
    );
}

void HandleGroupPlayerBeforeSendChatMessageImpl(
    Player* player, uint32& type,
    std::string& msg)
{
    HandleProximityPlayerSay(player, type, msg);

    if (type != CHAT_MSG_PARTY
        && type != CHAT_MSG_PARTY_LEADER)
        return;

    if (!sLLMChatterConfig->IsEnabled()
        || !sLLMChatterConfig->_useGroupChatter)
        return;

    if (!player || msg.empty())
        return;

    {
        bool hasUnderscore = false;
        bool allCapsOrSep = true;
        for (char c : msg)
        {
            if (c == '_')
                hasUnderscore = true;
            else if (c != ' ' && c != '\t'
                && c != '\n' && c != '\r'
                && !(c >= 'A' && c <= 'Z'))
            {
                allCapsOrSep = false;
                break;
            }
        }
        if (hasUnderscore && allCapsOrSep)
            return;
    }

    if (msg.size() > 2 && msg[0] == '|'
        && msg[1] == 'c')
    {
        std::string stripped = msg;
        size_t start, end;
        while ((start = stripped.find("|c"))
               != std::string::npos
            && (end = stripped.find("|r", start))
               != std::string::npos)
        {
            stripped.erase(start,
                end - start + 2);
        }
        stripped.erase(0,
            stripped.find_first_not_of(" \t"));
        if (!stripped.empty())
        {
            stripped.erase(
                stripped.find_last_not_of(
                    " \t") + 1);
        }
        if (stripped.empty())
            return;
    }

    if (IsPlayerBot(player))
        return;

    Group* group = player->GetGroup();
    if (!group)
        return;

    uint32 groupId =
        group->GetGUID().GetCounter();

    bool hasBotInGroup = false;
    for (GroupReference* itr =
             group->GetFirstMember();
         itr != nullptr; itr = itr->next())
    {
        if (Player* member = itr->GetSource())
        {
            if (IsPlayerBot(member))
            {
                hasBotInGroup = true;
                break;
            }
        }
    }
    if (!hasBotInGroup)
        return;

    std::string playerName = player->GetName();
    uint32 playerGuid =
        player->GetGUID().GetCounter();

    std::string safeMsg = msg;
    size_t firstChar = safeMsg.find_first_not_of(
        " \t\n\r");
    if (firstChar == std::string::npos)
        return;
    if (firstChar > 0)
        safeMsg = safeMsg.substr(firstChar);
    size_t lastChar = safeMsg.find_last_not_of(
        " \t\n\r");
    if (lastChar != std::string::npos)
        safeMsg = safeMsg.substr(0, lastChar + 1);
    if (safeMsg.empty())
        return;
    if (safeMsg.size()
        > sLLMChatterConfig->_maxMessageLength)
        safeMsg = safeMsg.substr(
            0,
            sLLMChatterConfig->_maxMessageLength);

    if (IsLikelyPlayerbotControlCommand(
            safeMsg))
    {
        return;
    }

    CharacterDatabase.Execute(
        "INSERT INTO llm_group_chat_history "
        "(group_id, speaker_guid, speaker_name,"
        " is_bot, message) "
        "VALUES ({}, {}, '{}', 0, '{}')",
        groupId, playerGuid,
        EscapeString(playerName),
        EscapeString(safeMsg));

    time_t now = time(nullptr);
    auto it =
        _groupPlayerMsgCooldowns.find(groupId);
    if (it != _groupPlayerMsgCooldowns.end()
        && (now - it->second)
           < (time_t)sLLMChatterConfig
               ->_groupPlayerMsgCooldown)
        return;

    _groupPlayerMsgCooldowns[groupId] = now;

    std::string extraData = "{"
        "\"player_name\":\"" +
            JsonEscape(playerName) + "\","
        "\"player_gender\":" +
            std::to_string(player->getGender()) + ","
        "\"player_message\":\"" +
            JsonEscape(safeMsg) + "\","
        "\"group_id\":" +
            std::to_string(groupId) +
        "}";

    extraData = EscapeString(extraData);

    QueueChatterEvent(
        "bot_group_player_msg",
        "player",
        player->GetZoneId(),
        player->GetMapId(),
        GetChatterEventPriority(
            "bot_group_player_msg"),
        "",
        player->GetGUID().GetCounter(),
        playerName,
        0,
        "",
        0,
        extraData,
        GetReactionDelaySeconds(
            "bot_group_player_msg"),
        60,
        false
    );
}

void HandleGroupPlayerLevelChangedImpl(
    Player* player, uint8 oldLevel)
{
    if (!sLLMChatterConfig
        || !sLLMChatterConfig->IsEnabled()
        || !sLLMChatterConfig->_useGroupChatter)
    {
        return;
    }

    if (!player)
    {
        return;
    }

    Group* group = player->GetGroup();
    if (!group)
    {
        return;
    }

    if (!GroupHasRealPlayer(group))
    {
        return;
    }

    {
        Map* lvlMap = player->GetMap();
        if (lvlMap
            && (lvlMap->IsRaid()
                || lvlMap->IsBattleground()))
            return;
    }

    uint8 newLevel = player->GetLevel();
    if (newLevel <= oldLevel)
    {
        return;
    }

    bool isBot = IsPlayerBot(player);

    Player* reactor = isBot
        ? GetRandomBotInGroup(group, player)
        : GetRandomBotInGroup(group);

    if (!reactor)
    {
        return;
    }

    uint32 groupId =
        group->GetGUID().GetCounter();
    uint32 botGuid =
        reactor->GetGUID().GetCounter();
    std::string botName = reactor->GetName();
    std::string playerName = player->GetName();

    std::string extraData = "{"
        "\"bot_guid\":" +
            std::to_string(botGuid) + ","
        "\"bot_name\":\"" +
            JsonEscape(botName) + "\","
        "\"bot_class\":" +
            std::to_string(
                reactor->getClass()) + ","
        "\"bot_race\":" +
            std::to_string(
                reactor->getRace()) + ","
        "\"bot_gender\":" +
            std::to_string(
                reactor->getGender()) + ","
        "\"bot_level\":" +
            std::to_string(newLevel) + ","
        "\"old_level\":" +
            std::to_string(oldLevel) + ","
        "\"is_bot\":" +
            std::string(
                isBot ? "1" : "0") + ","
        "\"leveler_name\":\"" +
            JsonEscape(playerName) + "\","
        "\"group_id\":" +
            std::to_string(groupId) +
        "}";

    extraData = EscapeString(extraData);

    QueueChatterEvent(
        "bot_group_levelup",
        "player",
        reactor->GetZoneId(),
        reactor->GetMapId(),
        GetChatterEventPriority("bot_group_levelup"),
        "",
        botGuid,
        botName,
        0,
        "",
        0,
        extraData,
        GetReactionDelaySeconds("bot_group_levelup"),
        120,
        false
    );
}

bool HandleGroupPlayerBeforeQuestCompleteImpl(
    Player* player, uint32 questId)
{
    if (!sLLMChatterConfig
        || !sLLMChatterConfig->IsEnabled()
        || !sLLMChatterConfig->_useGroupChatter)
        return true;

    if (!player)
        return true;

    if (IsPlayerBot(player))
        return true;

    Group* group = player->GetGroup();
    if (!group)
        return true;

    if (!GroupHasRealPlayer(group))
        return true;

    {
        Map* qoMap = player->GetMap();
        if (qoMap && qoMap->IsBattleground())
            return true;
    }

    Quest const* quest =
        sObjectMgr->GetQuestTemplate(questId);
    if (!quest)
        return true;

    uint32 groupId =
        group->GetGUID().GetCounter();

    time_t now = time(nullptr);
    {
        auto it = _groupQuestObjCooldowns
            .find(groupId);
        if (it != _groupQuestObjCooldowns.end()
            && (now - it->second)
               < (time_t)sLLMChatterConfig
                   ->_groupQuestObjectiveCooldown)
            return true;
    }

    uint64 questKey =
        ((uint64)groupId << 32) | questId;
    {
        auto it =
            _questAcceptTimestamps.find(questKey);
        if (it != _questAcceptTimestamps.end()
            && (now - it->second)
               < (time_t)sLLMChatterConfig
                   ->_questObjSuppressWindow)
        {
            return true;
        }
    }

    if (urand(1, 100) >
        sLLMChatterConfig
            ->_groupQuestObjectiveChance)
        return true;

    _groupQuestObjCooldowns[groupId] = now;

    Player* reactor =
        GetRandomBotInGroup(group);

    if (!reactor)
        return true;

    uint32 botGuid =
        reactor->GetGUID().GetCounter();
    std::string botName = reactor->GetName();
    std::string playerName = player->GetName();
    std::string questName = quest->GetTitle();

    std::string extraData = "{"
        + BuildBotIdentityFields(reactor) + ","
        "\"quest_name\":\"" +
            JsonEscape(questName) + "\","
        "\"quest_id\":" +
            std::to_string(questId) + ","
        "\"completer_name\":\"" +
            JsonEscape(playerName) + "\","
        "\"quest_details\":\"" +
            JsonEscape(
                quest->GetDetails()
                    .substr(0, 200)) + "\","
        "\"quest_objectives\":\"" +
            JsonEscape(
                quest->GetObjectives()
                    .substr(0, 150)) + "\","
        "\"group_id\":" +
            std::to_string(groupId) +
        "}";

    extraData = EscapeString(extraData);

    QueueChatterEvent(
        "bot_group_quest_objectives",
        "player",
        reactor->GetZoneId(),
        reactor->GetMapId(),
        GetChatterEventPriority(
            "bot_group_quest_objectives"),
        "",
        botGuid,
        botName,
        0,
        questName,
        questId,
        extraData,
        GetReactionDelaySeconds(
            "bot_group_quest_objectives"),
        120,
        false
    );

    return true;
}

void HandleGroupPlayerCompleteQuestImpl(
    Player* player, Quest const* quest)
{
    if (!sLLMChatterConfig
        || !sLLMChatterConfig->IsEnabled()
        || !sLLMChatterConfig->_useGroupChatter)
    {
        return;
    }

    if (!player || !quest)
    {
        return;
    }

    if (IsPlayerBot(player))
        return;

    Group* group = player->GetGroup();
    if (!group)
    {
        return;
    }

    if (!GroupHasRealPlayer(group))
    {
        return;
    }

    {
        Map* qMap = player->GetMap();
        if (qMap && qMap->IsBattleground())
            return;
    }

    uint32 groupId =
        group->GetGUID().GetCounter();
    uint32 questId = quest->GetQuestId();

    uint64 questKey =
        ((uint64)groupId << 32) | questId;
    time_t now = time(nullptr);
    {
        auto it = _questCompleteCd.find(questKey);
        if (it != _questCompleteCd.end()
            && (now - it->second)
               < (time_t)sLLMChatterConfig
                   ->_questDeduplicationWindow)
        {
            return;
        }
        _questCompleteCd[questKey] = now;
    }

    if (urand(1, 100) >
        sLLMChatterConfig
            ->_groupQuestCompleteChance)
        return;

    Player* reactor =
        GetRandomBotInGroup(group);

    if (!reactor)
    {
        return;
    }

    uint32 botGuid =
        reactor->GetGUID().GetCounter();
    std::string botName = reactor->GetName();
    std::string playerName = player->GetName();
    std::string questName =
        quest->GetTitle();

    std::string extraData = "{"
        + BuildBotIdentityFields(reactor) + ","
        "\"completer_name\":\"" +
            JsonEscape(playerName) + "\","
        "\"quest_name\":\"" +
            JsonEscape(questName) + "\","
        "\"quest_id\":" +
            std::to_string(questId) + ","
        "\"quest_details\":\"" +
            JsonEscape(
                quest->GetDetails()
                    .substr(0, 200)) + "\","
        "\"quest_objectives\":\"" +
            JsonEscape(
                quest->GetObjectives()
                    .substr(0, 150)) + "\","
        "\"group_id\":" +
            std::to_string(groupId) +
        "}";

    extraData = EscapeString(extraData);

    QueueChatterEvent(
        "bot_group_quest_complete",
        "player",
        reactor->GetZoneId(),
        reactor->GetMapId(),
        GetChatterEventPriority(
            "bot_group_quest_complete"),
        "",
        botGuid,
        botName,
        0,
        questName,
        questId,
        extraData,
        GetReactionDelaySeconds(
            "bot_group_quest_complete"),
        120,
        false
    );
}

void HandleGroupPlayerAchievementCompleteImpl(
    Player* player,
    AchievementEntry const* achievement)
{
    if (!sLLMChatterConfig
        || !sLLMChatterConfig->IsEnabled()
        || !sLLMChatterConfig->_useGroupChatter)
    {
        return;
    }

    if (!player || !achievement)
    {
        return;
    }

    Group* group = player->GetGroup();
    if (!group)
    {
        return;
    }

    if (!GroupHasRealPlayer(group))
    {
        return;
    }

    if (player->InBattleground())
    {
        Battleground* bg =
            player->GetBattleground();
        if (bg && bg->GetStatus()
                != STATUS_IN_PROGRESS)
            return;
    }

    bool isBot = IsPlayerBot(player);

    Player* reactor = isBot
        ? GetRandomBotInGroup(group, player)
        : GetRandomBotInGroup(group);

    if (!reactor)
    {
        return;
    }

    uint32 groupId =
        group->GetGUID().GetCounter();
    uint32 botGuid =
        reactor->GetGUID().GetCounter();
    std::string botName = reactor->GetName();
    std::string playerName = player->GetName();

    std::string achName =
        achievement->name[0]
            ? achievement->name[0] : "";
    uint32 achId = achievement->ID;

    std::string extraData = "{"
        + BuildBotIdentityFields(reactor) + ","
        "\"is_bot\":" +
            std::string(
                isBot ? "1" : "0") + ","
        "\"achiever_name\":\"" +
            JsonEscape(playerName) + "\","
        "\"achievement_name\":\"" +
            JsonEscape(achName) + "\","
        "\"achievement_id\":" +
            std::to_string(achId) + ","
        "\"group_id\":" +
            std::to_string(groupId) +
        "}";

    if (reactor->InBattleground())
    {
        Battleground* bg =
            reactor->GetBattleground();
        if (bg)
            AppendBGContext(
                bg, reactor, extraData);
    }

    extraData = EscapeString(extraData);

    QueueChatterEvent(
        "bot_group_achievement",
        "player",
        reactor->GetZoneId(),
        reactor->GetMapId(),
        GetChatterEventPriority(
            "bot_group_achievement"),
        "",
        botGuid,
        botName,
        0,
        achName,
        achId,
        extraData,
        GetReactionDelaySeconds(
            "bot_group_achievement"),
        120,
        false
    );
}

void HandleGroupPlayerSpellCastImpl(
    Player* player, Spell* spell)
{
    if (!sLLMChatterConfig
        || !sLLMChatterConfig->IsEnabled()
        || !sLLMChatterConfig->_useGroupChatter)
        return;

    if (!player || !spell)
        return;

    Group* group = player->GetGroup();
    if (!group)
        return;

    uint32 groupId =
        group->GetGUID().GetCounter();
    time_t now = time(nullptr);
    {
        auto it =
            _groupSpellCooldowns.find(groupId);
        if (it != _groupSpellCooldowns.end()
            && (now - it->second)
                < sLLMChatterConfig
                    ->_groupSpellCastCooldown)
            return;
    }

    if (!GroupHasRealPlayer(group))
        return;

    SpellInfo const* spellInfo =
        spell->GetSpellInfo();
    if (!spellInfo)
        return;

    if (spellInfo->IsPassive())
        return;

    if (spellInfo->HasAttribute(
            SPELL_ATTR0_DO_NOT_DISPLAY))
        return;

    if (spell->IsTriggered())
        return;

    if (!spellInfo->SpellName[0]
        || spellInfo->SpellName[0][0] == '\0')
        return;

    if (!IsPlayerBot(player)
        && spellInfo->IsPositive()
        && !spellInfo->HasAreaAuraEffect())
    {
        Unit* tgt =
            spell->m_targets.GetUnitTarget();
        if (!tgt || tgt == player)
            return;
    }

    std::string spellCategory;

    if (spellInfo->HasEffect(SPELL_EFFECT_RESURRECT)
        || spellInfo->HasEffect(
               SPELL_EFFECT_RESURRECT_NEW))
    {
        spellCategory = "resurrect";
    }
    else if (
        spellInfo->HasEffect(SPELL_EFFECT_HEAL)
        || spellInfo->HasEffect(
               SPELL_EFFECT_HEAL_MAX_HEALTH)
        || spellInfo->HasAura(
               SPELL_AURA_PERIODIC_HEAL))
    {
        Unit* target =
            spell->m_targets.GetUnitTarget();
        if (!target || target == player)
            return;

        Player* targetPlayer =
            target->ToPlayer();
        if (!targetPlayer)
            return;

        if (!targetPlayer->GetGroup()
            || targetPlayer->GetGroup()
                   != group)
            return;

        spellCategory = "heal";
    }
    else if (
        spellInfo->HasEffect(SPELL_EFFECT_DISPEL))
    {
        Unit* target =
            spell->m_targets.GetUnitTarget();
        if (!target || target == player)
            return;

        Player* targetPlayer =
            target->ToPlayer();
        if (!targetPlayer)
            return;

        if (!targetPlayer->GetGroup()
            || targetPlayer->GetGroup()
                   != group)
            return;

        spellCategory = "dispel";
    }
    else if (
        spellInfo->HasAura(
            SPELL_AURA_MOD_STUN)
        || spellInfo->HasAura(
               SPELL_AURA_MOD_ROOT)
        || spellInfo->HasAura(
               SPELL_AURA_MOD_FEAR)
        || spellInfo->HasAura(
               SPELL_AURA_MOD_CHARM)
        || spellInfo->HasAura(
               SPELL_AURA_MOD_CONFUSE))
    {
        spellCategory = "cc";
    }
    else if (spellInfo->IsPositive()
        && (spellInfo->HasAura(
                SPELL_AURA_SCHOOL_IMMUNITY)
            || spellInfo->HasAura(
                   SPELL_AURA_DAMAGE_IMMUNITY)
            || spellInfo->HasAura(
                   SPELL_AURA_MECHANIC_IMMUNITY)
            || spellInfo->HasAura(
                   SPELL_AURA_SCHOOL_ABSORB)
            || spellInfo->HasAura(
                   SPELL_AURA_MOD_DAMAGE_PERCENT_TAKEN)
            || spellInfo->HasAura(
                   SPELL_AURA_SPLIT_DAMAGE_PCT)
            || spellInfo->HasAura(
                   SPELL_AURA_SPLIT_DAMAGE_FLAT)))
    {
        spellCategory = "shield";
    }
    else if (spellInfo->IsPositive()
        && (spellInfo->HasAura(
                SPELL_AURA_MOD_STAT)
            || spellInfo->HasAura(
                SPELL_AURA_MOD_TOTAL_STAT_PERCENTAGE)
            || spellInfo->HasAura(
                SPELL_AURA_MOD_RESISTANCE)
            || spellInfo->HasAura(
                SPELL_AURA_MOD_ATTACK_POWER)
            || spellInfo->HasAura(
                SPELL_AURA_MOD_POWER_REGEN)
            || spellInfo->HasAura(
                SPELL_AURA_MOD_POWER_REGEN_PERCENT)
            || spellInfo->HasAura(
                SPELL_AURA_MOD_INCREASE_SPEED)
            || spellInfo->HasAura(
                SPELL_AURA_MOD_MELEE_HASTE)
            || spellInfo->HasAura(
                SPELL_AURA_HASTE_SPELLS)))
    {
        if (!spellInfo->HasAreaAuraEffect())
        {
            Unit* target =
                spell->m_targets.GetUnitTarget();
            if (!target || target == player)
                return;

            Player* targetPlayer =
                target->ToPlayer();
            if (!targetPlayer)
                return;

            if (!targetPlayer->GetGroup()
                || targetPlayer->GetGroup()
                       != group)
                return;
        }

        spellCategory = "buff";
    }
    else if (!spellInfo->IsPositive()
             && player->IsInCombat())
    {
        spellCategory = "offensive";
    }
    else if (spellInfo->IsPositive())
    {
        if (!spellInfo->HasAreaAuraEffect())
        {
            Unit* target =
                spell->m_targets.GetUnitTarget();
            if (!target || target == player)
                return;
            Player* targetPlayer =
                target->ToPlayer();
            if (!targetPlayer)
                return;
            if (!targetPlayer->GetGroup()
                || targetPlayer->GetGroup()
                       != group)
                return;
        }
        spellCategory = "support";
    }
    else
    {
        return;
    }

    if (spellCategory == "resurrect")
    {
        Map* rzMap = player->GetMap();
        if (rzMap && rzMap->IsBattleground())
        {
            uint32 rzChance =
                sLLMChatterConfig
                    ->_bgRezChance;
            if (urand(1, 100) > rzChance)
                return;
        }
    }
    else
    {
        uint32 numBots = CountBotsInGroup(group);
        uint32 effectiveChance =
            sLLMChatterConfig
                ->_groupSpellCastChance
            / std::max(numBots, 1u);
        if (effectiveChance < 1)
            effectiveChance = 1;
        if (urand(1, 100) > effectiveChance)
            return;
    }

    _groupSpellCooldowns[groupId] = now;

    bool casterIsBot = IsPlayerBot(player);
    Player* reactor = nullptr;
    if (casterIsBot)
        reactor = player;
    else
        reactor = GetRandomBotInGroup(group);

    if (!reactor)
        return;

    uint32 botGuid =
        reactor->GetGUID().GetCounter();
    std::string botName = reactor->GetName();
    std::string casterName = player->GetName();
    std::string spellName =
        spellInfo->SpellName[0]
            ? spellInfo->SpellName[0] : "";

    std::string targetName;
    bool isAreaBuff =
        spellInfo->HasAreaAuraEffect();
    Unit* spellTarget =
        spell->m_targets.GetUnitTarget();

    bool preferVictimTarget =
        (spellCategory == "offensive"
         || spellCategory == "cc");

    if (isAreaBuff)
    {
        targetName = "the group";
    }
    else if (spellTarget
             && (!preferVictimTarget
                 || spellTarget->GetGUID()
                        != player->GetGUID()))
    {
        targetName = spellTarget->GetName();
    }
    if (targetName.empty()
        && preferVictimTarget)
    {
        Unit* victim = player->GetVictim();
        if (victim)
            targetName = victim->GetName();
    }

    if (preferVictimTarget
        && targetName.empty())
        return;

    bool isSelfCast = (!preferVictimTarget
        && !isAreaBuff
        && spellTarget
        && spellTarget->GetGUID()
               == player->GetGUID());
    if (isSelfCast)
        return;

    std::string cacheKey;
    bool canUseCache = true;
    if (spellCategory == "offensive")
    {
        cacheKey = "spell_offensive";
        if (!casterIsBot)
            canUseCache = false;
    }
    else
    {
        cacheKey = "spell_support";
    }

    if (spellCategory != "resurrect"
        && canUseCache
        && sLLMChatterConfig->_preCacheEnable
        && sLLMChatterConfig
               ->_preCacheSpellEnable)
    {
        std::string cachedMsg, cachedEmote;
        if (TryConsumeCachedReaction(
                groupId, botGuid,
                cacheKey,
                cachedMsg, cachedEmote))
        {
            ResolvePlaceholders(
                cachedMsg, targetName,
                casterName, spellName);
            SendPartyMessageInstant(
                reactor, group,
                cachedMsg, cachedEmote);
            RecordCachedChatHistory(
                groupId, botGuid,
                botName, cachedMsg);
            return;
        }
        if (!sLLMChatterConfig
                ->_preCacheFallbackToLive)
            return;
    }

    std::string extraData = "{"
        + BuildBotIdentityFields(reactor) + ","
        "\"caster_name\":\"" +
            JsonEscape(casterName) + "\","
        "\"spell_name\":\"" +
            JsonEscape(spellName) + "\","
        "\"spell_category\":\"" +
            spellCategory + "\","
        "\"target_name\":\"" +
            JsonEscape(targetName) + "\","
        "\"group_id\":" +
            std::to_string(groupId) + ","
        + BuildBotStateJson(reactor) + "}";

    if (reactor->InBattleground())
    {
        Battleground* bg =
            reactor->GetBattleground();
        if (bg)
            AppendBGContext(
                bg, reactor, extraData);
    }

    extraData = EscapeString(extraData);

    QueueChatterEvent(
        "bot_group_spell_cast",
        "player",
        reactor->GetZoneId(),
        reactor->GetMapId(),
        GetChatterEventPriority(
            "bot_group_spell_cast"),
        "",
        botGuid,
        botName,
        0,
        casterName,
        0,
        extraData,
        GetReactionDelaySeconds(
            "bot_group_spell_cast"),
        120,
        false
    );
}

void HandleGroupPlayerResurrectImpl(
    Player* player)
{
    if (!sLLMChatterConfig
        || !sLLMChatterConfig->IsEnabled()
        || !sLLMChatterConfig
               ->_useGroupChatter)
        return;

    if (!player)
        return;

    if (player->InBattleground())
        return;

    if (!IsPlayerBot(player))
        return;

    Group* group = player->GetGroup();
    if (!group)
        return;

    if (!GroupHasRealPlayer(group))
        return;

    uint32 groupId =
        group->GetGUID().GetCounter();

    time_t now = time(nullptr);
    auto it =
        _groupResurrectCooldowns
            .find(groupId);
    if (it
        != _groupResurrectCooldowns.end()
        && (now - it->second)
           < (time_t)sLLMChatterConfig
               ->_groupResurrectCooldown)
        return;

    if (urand(1, 100)
        > sLLMChatterConfig
            ->_groupResurrectChance)
        return;

    _groupResurrectCooldowns[groupId] = now;

    uint32 botGuid =
        player->GetGUID().GetCounter();
    std::string botName =
        player->GetName();

    std::string extraData = "{"
        + BuildBotIdentityFields(player) + ","
        "\"group_id\":" +
            std::to_string(groupId) +
        "}";

    extraData = EscapeString(extraData);

    QueueChatterEvent(
        "bot_group_resurrect",
        "player",
        player->GetZoneId(),
        player->GetMapId(),
        GetChatterEventPriority(
            "bot_group_resurrect"),
        "",
        botGuid,
        botName,
        0,
        "",
        0,
        extraData,
        GetReactionDelaySeconds(
            "bot_group_resurrect"),
        120,
        false
    );
}

void HandleGroupPlayerReleasedGhostImpl(
    Player* player)
{
    if (!sLLMChatterConfig
        || !sLLMChatterConfig->IsEnabled()
        || !sLLMChatterConfig
               ->_useGroupChatter)
        return;

    if (!player)
        return;

    Group* group = player->GetGroup();
    if (!group)
        return;

    if (!GroupHasRealPlayer(group))
        return;

    {
        Map* crMap = player->GetMap();
        if (crMap && crMap->IsBattleground())
            return;
    }

    uint32 groupId =
        group->GetGUID().GetCounter();

    time_t now = time(nullptr);
    auto it =
        _groupCorpseRunCooldowns
            .find(groupId);
    if (it
        != _groupCorpseRunCooldowns.end()
        && (now - it->second)
           < (time_t)sLLMChatterConfig
               ->_groupCorpseRunCooldown)
        return;

    if (urand(1, 100)
        > sLLMChatterConfig
            ->_groupCorpseRunChance)
        return;

    _groupCorpseRunCooldowns[groupId] = now;

    bool isPlayerDeath =
        !IsPlayerBot(player);
    std::string deadName =
        player->GetName();

    Player* reactor = isPlayerDeath
        ? GetRandomBotInGroup(group)
        : GetRandomBotInGroup(
              group, player);
    if (!reactor)
        return;

    uint32 botGuid =
        reactor->GetGUID().GetCounter();
    std::string botName =
        reactor->GetName();
    uint32 zoneId = player->GetZoneId();
    std::string zoneName =
        GetZoneName(zoneId);

    std::string extraData = "{"
        + BuildBotIdentityFields(reactor) + ","
        "\"group_id\":" +
            std::to_string(groupId) + ","
        "\"zone_id\":" +
            std::to_string(zoneId) + ","
        "\"zone_name\":\"" +
            JsonEscape(zoneName) + "\","
        "\"dead_name\":\"" +
            JsonEscape(deadName) + "\","
        "\"is_player_death\":" +
            std::string(
                isPlayerDeath
                    ? "true" : "false")
        + "}";

    extraData = EscapeString(extraData);

    QueueChatterEvent(
        "bot_group_corpse_run",
        "player",
        zoneId,
        player->GetMapId(),
        GetChatterEventPriority(
            "bot_group_corpse_run"),
        "",
        botGuid,
        botName,
        0,
        "",
        0,
        extraData,
        GetReactionDelaySeconds(
            "bot_group_corpse_run"),
        120,
        false
    );
}

void HandleGroupPlayerMapChangedImpl(
    Player* player)
{
    if (!sLLMChatterConfig
        || !sLLMChatterConfig->IsEnabled()
        || !sLLMChatterConfig
               ->_useGroupChatter)
        return;

    if (!player)
        return;

    if (!IsPlayerBot(player))
    {
        Map* map = player->GetMap();
        if (!map
            || (!map->IsDungeon()
                && !map->IsRaid()))
            return;

        Group* group = player->GetGroup();
        if (!group
            || !GroupHasBots(group))
            return;

        uint32 groupId =
            group->GetGUID().GetCounter();

        time_t now = time(nullptr);
        auto it =
            _groupDungeonCooldowns
                .find(groupId);
        if (it
            != _groupDungeonCooldowns.end()
            && (now - it->second)
               < (time_t)sLLMChatterConfig
                   ->_groupDungeonCooldown)
            return;

        if (urand(1, 100)
            > sLLMChatterConfig
                  ->_groupDungeonChance)
            return;

        _groupDungeonCooldowns[groupId] =
            now;

        uint32 mapId = map->GetId();
        std::string mapName =
            map->GetMapName()
                ? map->GetMapName() : "";
        bool isRaid = map->IsRaid();

        std::string extraData = "{"
            "\"group_id\":" +
                std::to_string(groupId) +
                ","
            "\"map_id\":" +
                std::to_string(mapId) + ","
            "\"map_name\":\"" +
                JsonEscape(mapName) + "\","
            "\"is_raid\":" +
                std::string(
                    isRaid
                        ? "true"
                        : "false") + ","
            "\"zone_id\":" +
                std::to_string(
                    player->GetZoneId()) +
            "}";

        extraData = EscapeString(extraData);

        QueueChatterEvent(
            "bot_group_dungeon_entry",
            "player",
            player->GetZoneId(),
            mapId,
            GetChatterEventPriority(
                "bot_group_dungeon_entry"),
            "",
            player->GetGUID()
                .GetRawValue(),
            player->GetName(),
            0,
            mapName,
            0,
            extraData,
            GetReactionDelaySeconds(
                "bot_group_dungeon_entry"),
            300,
            false
        );
        return;
    }

    Map* map = player->GetMap();
    if (!map
        || (!map->IsDungeon()
            && !map->IsBattleground()))
        return;

    Group* group = player->GetGroup();
    if (!group)
        return;

    if (!GroupHasRealPlayer(group))
        return;

    EnsureGroupJoinQueued(player, group);

    if (map->IsBattleground())
        return;
}

void HandleGroupPlayerTextEmoteImpl(
    Player* player, uint32 textEmote,
    ObjectGuid guid)
{
    if (!player)
        return;

    if (IsPlayerBot(player))
        return;

    if (s_ignoredEmotes.count(textEmote))
        return;
    if (s_combatCalloutEmotes.count(textEmote))
        return;
    if (!sLLMChatterConfig
        || !sLLMChatterConfig->IsEnabled())
        return;
    if (!sLLMChatterConfig->_emoteReactionsEnable)
        return;

    Group* group = player->GetGroup();

    EmoteTargetType tgtType = EMOTE_TGT_NONE;
    std::string targetName;
    uint32 npcRank = 0;
    uint32 npcType = 0;
    Player* cachedTargetPlayer = nullptr;
    Creature* cachedTargetCreature = nullptr;

    if (!guid.IsEmpty())
    {
        if (guid.IsPlayer())
        {
            Player* tgt =
                ObjectAccessor::FindPlayer(guid);
            if (tgt)
            {
                cachedTargetPlayer = tgt;
                targetName = tgt->GetName();
                if (tgt->GetGroup() == group)
                    tgtType = IsPlayerBot(tgt)
                        ? EMOTE_TGT_GROUP_BOT
                        : EMOTE_TGT_GROUP_PLAYER;
                else
                    tgtType =
                        EMOTE_TGT_EXT_PLAYER;
            }
        }
        else if (guid.IsCreature())
        {
            Creature* npc =
                ObjectAccessor::GetCreature(
                    *player, guid);
            if (npc)
            {
                tgtType = EMOTE_TGT_CREATURE;
                cachedTargetCreature = npc;
                targetName = npc->GetName();
                npcRank =
                    npc->GetCreatureTemplate()
                        ->rank;
                npcType =
                    npc->GetCreatureTemplate()
                        ->type;
            }
        }
    }

    if (sLLMChatterConfig->IsDebugLog())
        LOG_DEBUG("module",
            "LLMChatter: TextEmote {} "
            "tgtType={} target='{}'",
            textEmote,
            static_cast<int>(tgtType),
            targetName);

    // Creature mirror reactions are independent from
    // group observer chatter, so allow them even when
    // the player is solo or has no nearby bot audience.
    if (tgtType == EMOTE_TGT_CREATURE
        && cachedTargetCreature)
        HandleEmoteAtCreature(
            player, cachedTargetCreature,
            textEmote);

    if (!group || !GroupHasRealPlayer(group))
        return;

    constexpr float RANGE = 40.0f;
    std::vector<Player*> nearbyAliveBots;
    for (GroupReference* itr =
             group->GetFirstMember();
         itr; itr = itr->next())
    {
        Player* m = itr->GetSource();
        if (m && IsPlayerBot(m)
            && m->IsAlive()
            && m->GetDistance(player) <= RANGE)
            nearbyAliveBots.push_back(m);
    }
    if (nearbyAliveBots.empty())
        return;

    switch (tgtType)
    {
        case EMOTE_TGT_GROUP_BOT:
            if (cachedTargetPlayer)
                HandleEmoteAtGroupBot(
                    player, cachedTargetPlayer,
                    textEmote, group);
            break;
        case EMOTE_TGT_CREATURE:
            if (!player->IsInCombat())
                HandleEmoteObserver(
                    player, textEmote, group,
                    tgtType, targetName,
                    npcRank, npcType,
                    cachedTargetCreature
                        ? cachedTargetCreature
                              ->GetEntry()
                        : 0u,
                    cachedTargetCreature
                        ? cachedTargetCreature
                              ->GetCreatureTemplate()
                              ->SubName
                        : "",
                    nearbyAliveBots);
            break;
        case EMOTE_TGT_EXT_PLAYER:
        case EMOTE_TGT_NONE:
            if (!player->IsInCombat())
                HandleEmoteObserver(
                    player, textEmote, group,
                    tgtType, targetName,
                    npcRank, npcType,
                    0u, "",
                    nearbyAliveBots);
            break;
        case EMOTE_TGT_GROUP_PLAYER:
            break;
    }
}

void HandleGroupPlayerUpdateZoneImpl(
    Player* player, uint32 newZone,
    uint32 newArea)
{
    if (!player || !sLLMChatterConfig)
        return;

    Group* grp = player->GetGroup();
    if (!grp)
        return;

    uint32 gId = grp->GetGUID().GetCounter();
    uint32 mapId = player->GetMapId();

    if (!IsPlayerBot(player))
    {
        CharacterDatabase.Execute(
            "UPDATE llm_group_bot_traits "
            "SET zone = {}, area = {}, map = {} "
            "WHERE group_id = {}",
            newZone, newArea, mapId, gId);
    }
    else
    {
        uint32 bGuid =
            player->GetGUID().GetCounter();
        CharacterDatabase.Execute(
            "UPDATE llm_group_bot_traits "
            "SET zone = {}, map = {} "
            "WHERE group_id = {} "
            "AND bot_guid = {}",
            newZone, mapId, gId, bGuid);
    }

    if (IsPlayerBot(player))
        return;

    if (!sLLMChatterConfig->_useGroupChatter)
        return;

    {
        Map* zMap = player->GetMap();
        if (zMap && zMap->IsBattleground())
            return;
    }

    Group* group = player->GetGroup();
    if (!group)
        return;

    if (!GroupHasRealPlayer(group))
        return;

    uint32 groupId = group->GetGUID().GetCounter();

    time_t now = time(nullptr);
    auto it = _groupZoneCooldowns.find(groupId);
    if (it != _groupZoneCooldowns.end()
        && (now - it->second)
           < (time_t)sLLMChatterConfig
               ->_groupZoneCooldown)
        return;

    if (urand(1, 100)
        > sLLMChatterConfig->_groupZoneChance)
        return;

    std::string zoneName = GetZoneName(newZone);
    if (zoneName.empty())
        return;

    _groupZoneCooldowns[groupId] = now;

    uint32 botGuid =
        player->GetGUID().GetCounter();
    std::string botName = player->GetName();

    std::string areaName;
    {
        AreaTableEntry const* areaEntry =
            sAreaTableStore.LookupEntry(newArea);
        if (areaEntry)
        {
            uint8 loc =
                sWorld->GetDefaultDbcLocale();
            char const* n =
                areaEntry->area_name[loc];
            areaName = n ? n : "";
            if (areaName.empty())
            {
                n = areaEntry
                    ->area_name[LOCALE_enUS];
                areaName = n ? n : "";
            }
        }
    }

    std::string extraData = "{"
        + BuildBotIdentityFields(player) + ","
        "\"group_id\":" +
            std::to_string(groupId) + ","
        "\"zone_id\":" +
            std::to_string(newZone) + ","
        "\"zone_name\":\"" +
            JsonEscape(zoneName) + "\","
        "\"area_id\":" +
            std::to_string(newArea) + ","
        "\"area_name\":\"" +
            JsonEscape(areaName) + "\""
        "}";

    extraData = EscapeString(extraData);

    QueueChatterEvent(
        "bot_group_zone_transition",
        "player",
        newZone,
        player->GetMapId(),
        GetChatterEventPriority(
            "bot_group_zone_transition"),
        "",
        botGuid,
        botName,
        0,
        zoneName,
        0,
        extraData,
        GetReactionDelaySeconds(
            "bot_group_zone_transition"),
        120,
        false
    );
}

void CheckGroupCombatStateImpl()
{
    if (!sLLMChatterConfig
        || !sLLMChatterConfig
            ->_stateCalloutEnabled)
        return;

    if (!sLLMChatterConfig->_useGroupChatter)
        return;

    time_t now = time(nullptr);
    WorldSessionMgr::SessionMap const& sessions =
        sWorldSessionMgr->GetAllSessions();
    std::set<uint32> visitedGroups;

    for (auto const& [id, session] : sessions)
    {
        Player* player =
            session->GetPlayer();
        if (!player
            || !player->IsInWorld())
            continue;
        if (IsPlayerBot(player))
            continue;

        Group* group = player->GetGroup();
        if (!group)
            continue;

        uint32 groupId =
            group->GetGUID().GetCounter();
        if (visitedGroups.count(groupId))
            continue;
        visitedGroups.insert(groupId);

        bool inBG = player->InBattleground();

        for (GroupReference* itr =
                 group->GetFirstMember();
             itr; itr = itr->next())
        {
            Player* bot = itr->GetSource();
            if (!bot || !IsPlayerBot(bot))
                continue;

            uint32 botGuid =
                bot->GetGUID().GetCounter();
            uint32 cd = sLLMChatterConfig
                ->_stateCalloutCooldown;
            uint32 chance = sLLMChatterConfig
                ->_stateCalloutChance;

            if (inBG)
            {
                cd *= 2;
                chance /= 2;
            }

            if (sLLMChatterConfig
                    ->_stateCalloutLowHealth)
            {
                float hp =
                    bot->GetHealthPct();
                if (hp > 0 && hp <=
                    sLLMChatterConfig
                        ->_lowHealthThreshold)
                {
                    auto it =
                        _botLowHealthCooldowns
                            .find(botGuid);
                    if (it ==
                        _botLowHealthCooldowns
                            .end()
                        || (now - it->second)
                            >= (time_t)cd)
                    {
                        if (urand(1, 100)
                            <= chance)
                        {
                            QueueStateCallout(
                                bot, group,
                                "bot_group_"
                                "low_health",
                                groupId);
                            _botLowHealthCooldowns
                                [botGuid] = now;
                        }
                    }
                }
            }

            if (sLLMChatterConfig
                    ->_stateCalloutOom)
            {
                if (bot->GetMaxPower(
                        POWER_MANA) > 0)
                {
                    float mp =
                        bot->GetPowerPct(
                            POWER_MANA);
                    if (mp <=
                        sLLMChatterConfig
                            ->_oomThreshold)
                    {
                        auto it =
                            _botOomCooldowns
                                .find(botGuid);
                        if (it ==
                            _botOomCooldowns
                                .end()
                            || (now - it->second)
                                >= (time_t)cd)
                        {
                            if (urand(1, 100)
                                <= chance)
                            {
                                QueueStateCallout(
                                    bot, group,
                                    "bot_group_"
                                    "oom",
                                    groupId);
                                _botOomCooldowns
                                    [botGuid] = now;
                            }
                        }
                    }
                }
            }

            if (!inBG
                && sLLMChatterConfig
                    ->_stateCalloutAggro
                && bot->IsInCombat())
            {
                PlayerbotAI* ai =
                    GET_PLAYERBOT_AI(bot);
                if (ai && PlayerbotAI
                        ::IsTank(bot))
                {
                    Unit* victim =
                        bot->GetVictim();
                    if (victim
                        && victim->GetVictim()
                        && victim->GetVictim()
                            != bot)
                    {
                        Player* threatened =
                            victim->GetVictim()
                                ->ToPlayer();
                        if (threatened
                            && group->IsMember(
                                threatened
                                    ->GetGUID()))
                        {
                            auto it =
                                _botAggroCooldowns
                                    .find(
                                        botGuid);
                            if (it ==
                                _botAggroCooldowns
                                    .end()
                                || (now
                                    - it->second)
                                    >= (time_t)cd)
                            {
                                if (urand(1, 100)
                                    <= chance)
                                {
                                    QueueStateCallout(
                                        bot,
                                        group,
                                        "bot_group"
                                        "_aggro_"
                                        "loss",
                                        groupId);
                                }
                                _botAggroCooldowns
                                    [botGuid]
                                        = now;
                            }
                        }
                    }
                }
            }
        }
    }
}
