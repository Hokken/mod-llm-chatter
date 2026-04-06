/*
 * mod-llm-chatter - Shared helpers used across multiple translation units
 */

#include "LLMChatterShared.h"

#include "LLMChatterConfig.h"
#include "Channel.h"
#include "ChannelMgr.h"
#include "Chat.h"
#include "Creature.h"
#include "DatabaseEnv.h"
#include "DBCStores.h"
#include "Group.h"
#include "Log.h"
#include "Map.h"
#include "Player.h"
#include "Playerbots.h"
#include "RandomPlayerbotMgr.h"
#include "World.h"
#include "WorldSession.h"

#include <algorithm>
#include <array>
#include <cctype>
#include <ctime>
#include <map>
#include <random>
#include <sstream>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace
{
constexpr uint8 PRIORITY_FILLER =
    static_cast<uint8>(LLMChatterPriorityBand::Filler);
constexpr uint8 PRIORITY_NORMAL =
    static_cast<uint8>(LLMChatterPriorityBand::Normal);
constexpr uint8 PRIORITY_HIGH =
    static_cast<uint8>(LLMChatterPriorityBand::High);
constexpr uint8 PRIORITY_HIGH_LOCAL = PRIORITY_HIGH + 1;
constexpr uint8 PRIORITY_CRITICAL =
    static_cast<uint8>(LLMChatterPriorityBand::Critical);

using DelayMember = uint32 LLMChatterConfig::*;

struct EventPriorityRule
{
    const char* eventType;
    uint8 priority;
};

struct ExactRangeDelayRule
{
    const char* eventType;
    DelayMember minMember;
    DelayMember maxMember;
};

struct ExactFixedDelayRule
{
    const char* eventType;
    DelayMember delayMember;
};

struct ExactLiteralDelayRule
{
    const char* eventType;
    uint32 delaySeconds;
};

struct PredicatePriorityRule
{
    bool (*matches)(const std::string& eventType);
    uint8 priority;
};

struct PredicateRangeDelayRule
{
    bool (*matches)(const std::string& eventType);
    DelayMember minMember;
    DelayMember maxMember;
};

struct PredicateFixedDelayRule
{
    bool (*matches)(const std::string& eventType);
    DelayMember delayMember;
};

bool IsBattlegroundEventType(const std::string& eventType)
{
    // All current battleground events use the bg_ prefix.
    // If that namespace grows beyond BG events later, switch this
    // helper to an explicit allow-list.
    return eventType.rfind("bg_", 0) == 0;
}

bool IsRaidEventType(const std::string& eventType)
{
    return eventType.rfind("raid_", 0) == 0;
}

bool IsStateCalloutEventType(const std::string& eventType)
{
    return eventType == "bot_group_low_health"
        || eventType == "bot_group_oom"
        || eventType == "bot_group_aggro_loss";
}

bool IsHolidayBoundaryEventType(
    const std::string& eventType)
{
    return eventType == "holiday_start"
        || eventType == "holiday_end";
}

bool IsQuestAcceptEventType(const std::string& eventType)
{
    return eventType == "bot_group_quest_accept"
        || eventType == "bot_group_quest_accept_batch";
}

bool IsZoneTransitionEventType(
    const std::string& eventType)
{
    return eventType == "bot_group_zone_transition"
        || eventType == "bot_group_subzone_change";
}

bool IsEmoteReactionEventType(
    const std::string& eventType)
{
    return eventType == "bot_group_emote_reaction"
        || eventType == "bot_group_emote_observer";
}

template <typename Rule, size_t N>
const Rule* FindExactRule(
    const std::array<Rule, N>& rules,
    const std::string& eventType)
{
    for (auto const& rule : rules)
        if (eventType == rule.eventType)
            return &rule;

    return nullptr;
}

template <typename Rule, size_t N>
const Rule* FindPredicateRule(
    const std::array<Rule, N>& rules,
    const std::string& eventType)
{
    for (auto const& rule : rules)
        if (rule.matches(eventType))
            return &rule;

    return nullptr;
}

uint32 RollConfiguredDelay(
    DelayMember minMember,
    DelayMember maxMember)
{
    return urand(
        sLLMChatterConfig->*minMember,
        sLLMChatterConfig->*maxMember);
}

constexpr std::array<EventPriorityRule, 33>
    kTierPriorityRules = {{
        {"bot_group_combat",        PRIORITY_CRITICAL},
        {"bot_group_spell_cast",    PRIORITY_CRITICAL},
        {"bot_group_nearby_object", PRIORITY_CRITICAL},
        {"weather_change",          PRIORITY_CRITICAL},
        {"transport_arrives",       PRIORITY_CRITICAL},
        {"bg_flag_picked_up",       PRIORITY_CRITICAL},
        {"bg_flag_dropped",         PRIORITY_CRITICAL},
        {"bg_flag_captured",        PRIORITY_CRITICAL},
        {"bg_flag_returned",        PRIORITY_CRITICAL},
        {"bg_node_contested",       PRIORITY_CRITICAL},
        {"bg_node_captured",        PRIORITY_CRITICAL},
        {"raid_boss_pull",          PRIORITY_CRITICAL},
        {"raid_boss_kill",          PRIORITY_CRITICAL},
        {"raid_boss_wipe",          PRIORITY_CRITICAL},
        {"bot_group_player_msg",    PRIORITY_HIGH_LOCAL},
        {"player_general_msg",      PRIORITY_HIGH},
        {"bot_group_death",         PRIORITY_HIGH},
        {"bot_group_wipe",          PRIORITY_HIGH},
        {"bot_group_join",          PRIORITY_HIGH},
        {"bot_group_join_batch",    PRIORITY_HIGH},
        {"bg_match_start",          PRIORITY_HIGH},
        {"bg_pvp_kill",             PRIORITY_HIGH},
        {"player_enters_zone",      PRIORITY_HIGH},
        {"bg_idle_chatter",         PRIORITY_FILLER},
        {"raid_idle_morale",        PRIORITY_FILLER},
        {"weather_ambient",         PRIORITY_FILLER},
        {"minor_event",             PRIORITY_FILLER},
        {"day_night_transition",    PRIORITY_FILLER},
        {"proximity_say",           PRIORITY_FILLER},
        {"proximity_conversation",  PRIORITY_FILLER},
        {"proximity_reply",         PRIORITY_NORMAL},
        {"proximity_player_say",
            PRIORITY_NORMAL},
        {"proximity_player_conversation",
            PRIORITY_NORMAL},
    }};

constexpr std::array<PredicatePriorityRule, 1>
    kTierPriorityPredicateRules = {{
        {IsStateCalloutEventType, PRIORITY_CRITICAL},
    }};

constexpr std::array<EventPriorityRule, 21>
    kLegacyPriorityRules = {{
        {"player_general_msg",       8},
        {"day_night_transition",     7},
        {"transport_arrives",        6},
        {"player_enters_zone",       6},
        {"weather_change",           5},
        {"bot_group_nearby_object",  5},
        {"weather_ambient",          3},
        {"bot_group_zone_transition", 3},
        {"bot_group_subzone_change", 3},
        {"holiday_start",            2},
        {"holiday_end",              2},
        {"minor_event",              2},
        {"bot_group_combat",         2},
        {"bot_group_join",           0},
        {"bot_group_join_batch",     0},
        {"raid_idle_morale",         0},
        {"proximity_say",           0},
        {"proximity_conversation",  0},
        {"proximity_reply",         1},
        {"proximity_player_say",          1},
        {"proximity_player_conversation", 1},
    }};

constexpr std::array<PredicatePriorityRule, 1>
    kLegacyPriorityPredicateRules = {{
        {IsStateCalloutEventType, 2},
    }};

struct TierDelayRule
{
    uint8 minimumPriority;
    DelayMember minMember;
    DelayMember maxMember;
};

constexpr std::array<TierDelayRule, 4>
    kTierDelayRules = {{
        {
            PRIORITY_CRITICAL,
            &LLMChatterConfig::_priorityReactRangeCriticalMin,
            &LLMChatterConfig::_priorityReactRangeCriticalMax,
        },
        {
            PRIORITY_HIGH,
            &LLMChatterConfig::_priorityReactRangeHighMin,
            &LLMChatterConfig::_priorityReactRangeHighMax,
        },
        {
            PRIORITY_NORMAL,
            &LLMChatterConfig::_priorityReactRangeNormalMin,
            &LLMChatterConfig::_priorityReactRangeNormalMax,
        },
        {
            PRIORITY_FILLER,
            &LLMChatterConfig::_priorityReactRangeFillerMin,
            &LLMChatterConfig::_priorityReactRangeFillerMax,
        },
    }};

constexpr std::array<ExactRangeDelayRule, 4>
    kLegacyExactRangeDelayRules = {{
        {
            "day_night_transition",
            &LLMChatterConfig::_reactRangeDayNightMin,
            &LLMChatterConfig::_reactRangeDayNightMax,
        },
        {
            "weather_change",
            &LLMChatterConfig::_reactRangeWeatherMin,
            &LLMChatterConfig::_reactRangeWeatherMax,
        },
        {
            "weather_ambient",
            &LLMChatterConfig::_reactRangeWeatherAmbientMin,
            &LLMChatterConfig::_reactRangeWeatherAmbientMax,
        },
        {
            "transport_arrives",
            &LLMChatterConfig::_reactRangeTransportMin,
            &LLMChatterConfig::_reactRangeTransportMax,
        },
    }};

constexpr std::array<PredicateRangeDelayRule, 2>
    kLegacyPredicateRangeDelayRules = {{
        {
            IsHolidayBoundaryEventType,
            &LLMChatterConfig::_reactRangeHolidayMin,
            &LLMChatterConfig::_reactRangeHolidayMax,
        },
        {
            IsQuestAcceptEventType,
            &LLMChatterConfig::_reactRangeQuestAcceptMin,
            &LLMChatterConfig::_reactRangeQuestAcceptMax,
        },
    }};

constexpr std::array<ExactFixedDelayRule, 18>
    kLegacyExactFixedDelayRules = {{
        {"bot_group_join",             &LLMChatterConfig::_reactDelayJoin},
        {
            "bot_group_join_batch",
            &LLMChatterConfig::_reactDelayJoinBatch,
        },
        {"bot_group_kill",             &LLMChatterConfig::_reactDelayKill},
        {"bot_group_wipe",             &LLMChatterConfig::_reactDelayWipe},
        {"bot_group_death",            &LLMChatterConfig::_reactDelayDeath},
        {"bot_group_loot",             &LLMChatterConfig::_reactDelayLoot},
        {"bot_group_combat",           &LLMChatterConfig::_reactDelayCombat},
        {
            "bot_group_player_msg",
            &LLMChatterConfig::_reactDelayPlayerMsg,
        },
        {
            "bot_group_levelup",
            &LLMChatterConfig::_reactDelayLevelUp,
        },
        {
            "bot_group_quest_objectives",
            &LLMChatterConfig::_reactDelayQuestObjectives,
        },
        {
            "bot_group_quest_complete",
            &LLMChatterConfig::_reactDelayQuestComplete,
        },
        {
            "bot_group_achievement",
            &LLMChatterConfig::_reactDelayAchievement,
        },
        {
            "bot_group_spell_cast",
            &LLMChatterConfig::_reactDelaySpellCast,
        },
        {
            "bot_group_resurrect",
            &LLMChatterConfig::_reactDelayResurrect,
        },
        {
            "bot_group_corpse_run",
            &LLMChatterConfig::_reactDelayCorpseRun,
        },
        {
            "bot_group_dungeon_entry",
            &LLMChatterConfig::_reactDelayDungeonEntry,
        },
        {
            "bot_group_nearby_object",
            &LLMChatterConfig::_reactDelayNearbyObject,
        },
        {
            "player_general_msg",
            &LLMChatterConfig::_reactDelayGeneralMsg,
        },
    }};

constexpr std::array<PredicateFixedDelayRule, 5>
    kLegacyPredicateFixedDelayRules = {{
        {
            IsZoneTransitionEventType,
            &LLMChatterConfig::_reactDelayZoneTransition,
        },
        {
            IsStateCalloutEventType,
            &LLMChatterConfig::_reactDelayStateCallout,
        },
        {
            IsBattlegroundEventType,
            &LLMChatterConfig::_reactDelayBGEvent,
        },
        {
            IsRaidEventType,
            // Preserve the historical shared BG/Raid delay bucket.
            &LLMChatterConfig::_reactDelayBGEvent,
        },
        {
            IsEmoteReactionEventType,
            &LLMChatterConfig::_reactDelayEmote,
        },
    }};

constexpr std::array<ExactLiteralDelayRule, 3>
    kLegacyExactLiteralDelayRules = {{
        {"player_enters_zone", 2},
        {"proximity_player_say", 1},
        {"proximity_player_conversation", 1},
    }};

std::string GetBotRoleName(Player* player)
{
    if (!player)
        return "dps";

    PlayerbotAI* ai = GET_PLAYERBOT_AI(player);
    if (!ai)
        return "dps";

    if (PlayerbotAI::IsTank(player))
        return "tank";
    if (PlayerbotAI::IsHeal(player))
        return "healer";
    if (PlayerbotAI::IsRanged(player))
        return "ranged_dps";
    return "melee_dps";
}

uint8 GetTierPriority(const std::string& eventType)
{
    if (const auto* predicateRule = FindPredicateRule(
            kTierPriorityPredicateRules,
            eventType))
        return predicateRule->priority;

    if (const auto* exactRule = FindExactRule(
            kTierPriorityRules,
            eventType))
        return exactRule->priority;

    return PRIORITY_NORMAL;
}

uint8 GetLegacyPriority(const std::string& eventType)
{
    if (const auto* predicateRule = FindPredicateRule(
            kLegacyPriorityPredicateRules,
            eventType))
        return predicateRule->priority;

    if (const auto* exactRule = FindExactRule(
            kLegacyPriorityRules,
            eventType))
        return exactRule->priority;

    // Historical default for most group and battleground event
    // producers was inline priority 1.
    return 1;
}

uint32 GetTierReactionDelaySeconds(
    const std::string& eventType)
{
    uint8 priority = GetTierPriority(eventType);

    for (auto const& rule : kTierDelayRules)
        if (priority >= rule.minimumPriority)
            return RollConfiguredDelay(
                rule.minMember,
                rule.maxMember);

    return RollConfiguredDelay(
        &LLMChatterConfig::_priorityReactRangeFillerMin,
        &LLMChatterConfig::_priorityReactRangeFillerMax);
}

uint32 GetLegacyReactionDelaySeconds(
    const std::string& eventType)
{
    if (const auto* exactRangeRule = FindExactRule(
            kLegacyExactRangeDelayRules,
            eventType))
        return RollConfiguredDelay(
            exactRangeRule->minMember,
            exactRangeRule->maxMember);

    if (const auto* predicateRangeRule = FindPredicateRule(
            kLegacyPredicateRangeDelayRules,
            eventType))
        return RollConfiguredDelay(
            predicateRangeRule->minMember,
            predicateRangeRule->maxMember);

    if (const auto* exactFixedRule = FindExactRule(
            kLegacyExactFixedDelayRules,
            eventType))
        return sLLMChatterConfig->*(exactFixedRule->delayMember);

    if (const auto* literalFixedRule = FindExactRule(
            kLegacyExactLiteralDelayRules,
            eventType))
        return literalFixedRule->delaySeconds;

    if (const auto* predicateFixedRule = FindPredicateRule(
            kLegacyPredicateFixedDelayRules,
            eventType))
        return sLLMChatterConfig->*(predicateFixedRule->delayMember);

    return RollConfiguredDelay(
        &LLMChatterConfig::_reactRangeDefaultMin,
        &LLMChatterConfig::_reactRangeDefaultMax);
}

const char* GetQualityColor(uint8 quality)
{
    switch (quality)
    {
        case 0: return "9d9d9d";
        case 1: return "ffffff";
        case 2: return "1eff00";
        case 3: return "0070dd";
        case 4: return "a335ee";
        case 5: return "ff8000";
        default: return "ffffff";
    }
}

std::string ConvertItemLinks(const std::string& text)
{
    std::string result = text;
    size_t pos = 0;

    while ((pos = result.find("[[item:", pos)) != std::string::npos)
    {
        size_t endPos = result.find("]]", pos);
        if (endPos == std::string::npos)
            break;

        std::string content = result.substr(pos + 7, endPos - pos - 7);
        size_t firstColon = content.find(':');
        size_t lastColon = content.rfind(':');

        if (firstColon != std::string::npos
            && lastColon != std::string::npos
            && firstColon != lastColon)
        {
            std::string idStr = content.substr(0, firstColon);
            std::string name =
                content.substr(
                    firstColon + 1,
                    lastColon - firstColon - 1);
            std::string qualityStr = content.substr(lastColon + 1);

            try
            {
                uint32 itemId = std::stoul(idStr);
                uint8 quality =
                    static_cast<uint8>(std::stoul(qualityStr));
                std::ostringstream link;
                link << "|cff" << GetQualityColor(quality)
                     << "|Hitem:" << itemId
                     << ":0:0:0:0:0:0:0:0|h[" << name
                     << "]|h|r";
                result.replace(pos, endPos - pos + 2, link.str());
                pos += link.str().length();
            }
            catch (...)
            {
                pos = endPos + 2;
            }
        }
        else
        {
            pos = endPos + 2;
        }
    }

    return result;
}

std::string ConvertQuestLinks(const std::string& text)
{
    std::string result = text;
    size_t pos = 0;

    while ((pos = result.find("[[quest:", pos)) != std::string::npos)
    {
        size_t endPos = result.find("]]", pos);
        if (endPos == std::string::npos)
            break;

        std::string content = result.substr(pos + 8, endPos - pos - 8);
        size_t firstColon = content.find(':');
        size_t lastColon = content.rfind(':');

        if (firstColon != std::string::npos
            && lastColon != std::string::npos
            && firstColon != lastColon)
        {
            std::string idStr = content.substr(0, firstColon);
            std::string name =
                content.substr(
                    firstColon + 1,
                    lastColon - firstColon - 1);
            std::string levelStr = content.substr(lastColon + 1);

            try
            {
                uint32 questId = std::stoul(idStr);
                uint32 level = std::stoul(levelStr);
                std::ostringstream link;
                link << "|cffffff00|Hquest:" << questId << ":"
                     << level << "|h[" << name << "]|h|r";
                result.replace(pos, endPos - pos + 2, link.str());
                pos += link.str().length();
            }
            catch (...)
            {
                pos = endPos + 2;
            }
        }
        else
        {
            pos = endPos + 2;
        }
    }

    return result;
}

std::string ConvertNpcLinks(const std::string& text)
{
    std::string result = text;
    size_t pos = 0;

    while ((pos = result.find("[[npc:", pos)) != std::string::npos)
    {
        size_t endPos = result.find("]]", pos);
        if (endPos == std::string::npos)
            break;

        std::string content = result.substr(pos + 6, endPos - pos - 6);
        size_t colonPos = content.find(':');

        if (colonPos != std::string::npos)
        {
            std::string name = content.substr(colonPos + 1);
            std::string coloredName = "|cff00ff00" + name + "|r";
            result.replace(pos, endPos - pos + 2, coloredName);
            pos += coloredName.length();
        }
        else
        {
            pos = endPos + 2;
        }
    }

    return result;
}

std::string ConvertSpellLinks(const std::string& text)
{
    std::string result = text;
    size_t pos = 0;

    while ((pos = result.find("[[spell:", pos)) != std::string::npos)
    {
        size_t endPos = result.find("]]", pos);
        if (endPos == std::string::npos)
            break;

        std::string content = result.substr(pos + 8, endPos - pos - 8);
        size_t colonPos = content.find(':');

        if (colonPos != std::string::npos)
        {
            std::string idStr = content.substr(0, colonPos);
            std::string name = content.substr(colonPos + 1);

            try
            {
                uint32 spellId = std::stoul(idStr);
                std::ostringstream link;
                link << "|cff71d5ff|Hspell:" << spellId << "|h["
                     << name << "]|h|r";
                result.replace(pos, endPos - pos + 2, link.str());
                pos += link.str().length();
            }
            catch (...)
            {
                pos = endPos + 2;
            }
        }
        else
        {
            pos = endPos + 2;
        }
    }

    return result;
}

uint32 LookupTextEmoteId(const std::string& emoteName)
{
    static const std::unordered_map<std::string, uint32> emoteMap = {
        {"agree", TEXT_EMOTE_AGREE},
        {"amaze", TEXT_EMOTE_AMAZE},
        {"angry", TEXT_EMOTE_ANGRY},
        {"apologize", TEXT_EMOTE_APOLOGIZE},
        {"applaud", TEXT_EMOTE_APPLAUD},
        {"bashful", TEXT_EMOTE_BASHFUL},
        {"beckon", TEXT_EMOTE_BECKON},
        {"beg", TEXT_EMOTE_BEG},
        {"bite", TEXT_EMOTE_BITE},
        {"bleed", TEXT_EMOTE_BLEED},
        {"blink", TEXT_EMOTE_BLINK},
        {"blush", TEXT_EMOTE_BLUSH},
        {"bonk", TEXT_EMOTE_BONK},
        {"bored", TEXT_EMOTE_BORED},
        {"bounce", TEXT_EMOTE_BOUNCE},
        {"brb", TEXT_EMOTE_BRB},
        {"bow", TEXT_EMOTE_BOW},
        {"burp", TEXT_EMOTE_BURP},
        {"bye", TEXT_EMOTE_BYE},
        {"cackle", TEXT_EMOTE_CACKLE},
        {"cheer", TEXT_EMOTE_CHEER},
        {"chicken", TEXT_EMOTE_CHICKEN},
        {"chuckle", TEXT_EMOTE_CHUCKLE},
        {"clap", TEXT_EMOTE_CLAP},
        {"confused", TEXT_EMOTE_CONFUSED},
        {"congratulate", TEXT_EMOTE_CONGRATULATE},
        {"cough", TEXT_EMOTE_COUGH},
        {"cower", TEXT_EMOTE_COWER},
        {"crack", TEXT_EMOTE_CRACK},
        {"cringe", TEXT_EMOTE_CRINGE},
        {"cry", TEXT_EMOTE_CRY},
        {"curious", TEXT_EMOTE_CURIOUS},
        {"curtsey", TEXT_EMOTE_CURTSEY},
        {"dance", TEXT_EMOTE_DANCE},
        {"drink", TEXT_EMOTE_DRINK},
        {"drool", TEXT_EMOTE_DROOL},
        {"eat", TEXT_EMOTE_EAT},
        {"eye", TEXT_EMOTE_EYE},
        // farewell not in 3.3.5a
        {"fart", TEXT_EMOTE_FART},
        {"fidget", TEXT_EMOTE_FIDGET},
        {"flex", TEXT_EMOTE_FLEX},
        {"frown", TEXT_EMOTE_FROWN},
        {"gasp", TEXT_EMOTE_GASP},
        {"gaze", TEXT_EMOTE_GAZE},
        {"giggle", TEXT_EMOTE_GIGGLE},
        {"glare", TEXT_EMOTE_GLARE},
        {"gloat", TEXT_EMOTE_GLOAT},
        {"greet", TEXT_EMOTE_GREET},
        {"grin", TEXT_EMOTE_GRIN},
        {"groan", TEXT_EMOTE_GROAN},
        {"grovel", TEXT_EMOTE_GROVEL},
        {"guffaw", TEXT_EMOTE_GUFFAW},
        {"hail", TEXT_EMOTE_HAIL},
        {"happy", TEXT_EMOTE_HAPPY},
        {"hello", TEXT_EMOTE_HELLO},
        {"hug", TEXT_EMOTE_HUG},
        {"hungry", TEXT_EMOTE_HUNGRY},
        {"kiss", TEXT_EMOTE_KISS},
        {"kneel", TEXT_EMOTE_KNEEL},
        {"laugh", TEXT_EMOTE_LAUGH},
        {"laydown", TEXT_EMOTE_LAYDOWN},
        // massage not in 3.3.5a
        {"moan", TEXT_EMOTE_MOAN},
        {"moon", TEXT_EMOTE_MOON},
        {"mourn", TEXT_EMOTE_MOURN},
        {"no", TEXT_EMOTE_NO},
        {"nod", TEXT_EMOTE_NOD},
        {"nosepick", TEXT_EMOTE_NOSEPICK},
        {"panic", TEXT_EMOTE_PANIC},
        {"peer", TEXT_EMOTE_PEER},
        {"plead", TEXT_EMOTE_PLEAD},
        {"point", TEXT_EMOTE_POINT},
        {"poke", TEXT_EMOTE_POKE},
        {"pray", TEXT_EMOTE_PRAY},
        {"ready", TEXT_EMOTE_READY},
        {"roar", TEXT_EMOTE_ROAR},
        {"rude", TEXT_EMOTE_RUDE},
        {"salute", TEXT_EMOTE_SALUTE},
        {"scratch", TEXT_EMOTE_SCRATCH},
        {"sexy", TEXT_EMOTE_SEXY},
        {"shake", TEXT_EMOTE_SHAKE},
        {"shout", TEXT_EMOTE_SHOUT},
        {"shrug", TEXT_EMOTE_SHRUG},
        {"shy", TEXT_EMOTE_SHY},
        {"sigh", TEXT_EMOTE_SIGH},
        {"sit", TEXT_EMOTE_SIT},
        {"sleep", TEXT_EMOTE_SLEEP},
        {"snarl", TEXT_EMOTE_SNARL},
        {"spit", TEXT_EMOTE_SPIT},
        {"stare", TEXT_EMOTE_STARE},
        {"surprised", TEXT_EMOTE_SURPRISED},
        {"surrender", TEXT_EMOTE_SURRENDER},
        {"talk", TEXT_EMOTE_TALK},
        {"talkex", TEXT_EMOTE_TALKEX},
        {"talkq", TEXT_EMOTE_TALKQ},
        {"tap", TEXT_EMOTE_TAP},
        {"thank", TEXT_EMOTE_THANK},
        {"threaten", TEXT_EMOTE_THREATEN},
        {"tired", TEXT_EMOTE_TIRED},
        {"victory", TEXT_EMOTE_VICTORY},
        {"wave", TEXT_EMOTE_WAVE},
        {"welcome", TEXT_EMOTE_WELCOME},
        {"whine", TEXT_EMOTE_WHINE},
        {"whistle", TEXT_EMOTE_WHISTLE},
        {"work", TEXT_EMOTE_WORK},
        {"yawn", TEXT_EMOTE_YAWN},
        {"boggle", TEXT_EMOTE_BOGGLE},
        {"calm", TEXT_EMOTE_CALM},
        {"cold", TEXT_EMOTE_COLD},
        {"comfort", TEXT_EMOTE_COMFORT},
        {"cuddle", TEXT_EMOTE_CUDDLE},
        {"duck", TEXT_EMOTE_DUCK},
        {"insult", TEXT_EMOTE_INSULT},
        {"introduce", TEXT_EMOTE_INTRODUCE},
        {"jk", TEXT_EMOTE_JK},
        {"lick", TEXT_EMOTE_LICK},
        {"listen", TEXT_EMOTE_LISTEN},
        {"lost", TEXT_EMOTE_LOST},
        {"mock", TEXT_EMOTE_MOCK},
        {"ponder", TEXT_EMOTE_PONDER},
        {"pounce", TEXT_EMOTE_POUNCE},
        {"praise", TEXT_EMOTE_PRAISE},
        {"purr", TEXT_EMOTE_PURR},
        {"puzzle", TEXT_EMOTE_PUZZLE},
        {"raise", TEXT_EMOTE_RAISE},
        {"shimmy", TEXT_EMOTE_SHIMMY},
        {"shiver", TEXT_EMOTE_SHIVER},
        {"shoo", TEXT_EMOTE_SHOO},
        {"slap", TEXT_EMOTE_SLAP},
        {"smirk", TEXT_EMOTE_SMIRK},
        {"sniff", TEXT_EMOTE_SNIFF},
        {"snub", TEXT_EMOTE_SNUB},
        {"soothe", TEXT_EMOTE_SOOTHE},
        {"stink", TEXT_EMOTE_STINK},
        {"taunt", TEXT_EMOTE_TAUNT},
        {"tease", TEXT_EMOTE_TEASE},
        {"thirsty", TEXT_EMOTE_THIRSTY},
        {"veto", TEXT_EMOTE_VETO},
        {"snicker", TEXT_EMOTE_SNICKER},
        {"stand", TEXT_EMOTE_STAND},
        {"tickle", TEXT_EMOTE_TICKLE},
        {"violin", TEXT_EMOTE_VIOLIN},
        {"smile", TEXT_EMOTE_SMILE},
        {"rasp", TEXT_EMOTE_RASP},
        {"pity", TEXT_EMOTE_PITY},
        {"growl", TEXT_EMOTE_GROWL},
        {"bark", TEXT_EMOTE_BARK},
        {"scared", TEXT_EMOTE_SCARED},
        {"flop", TEXT_EMOTE_FLOP},
        {"love", TEXT_EMOTE_LOVE},
        {"moo", TEXT_EMOTE_MOO},
        {"commend", TEXT_EMOTE_COMMEND},
        {"train", TEXT_EMOTE_TRAIN},
        {"helpme", TEXT_EMOTE_HELPME},
        {"incoming", TEXT_EMOTE_INCOMING},
        {"charge", TEXT_EMOTE_CHARGE},
        {"flee", TEXT_EMOTE_FLEE},
        {"attacktarget", TEXT_EMOTE_ATTACKMYTARGET},
        {"oom", TEXT_EMOTE_OOM},
        {"follow", TEXT_EMOTE_FOLLOW},
        {"wait", TEXT_EMOTE_WAIT},
        {"healme", TEXT_EMOTE_HEALME},
        {"openfire", TEXT_EMOTE_OPENFIRE},
        {"flirt", TEXT_EMOTE_FLIRT},
        {"joke", TEXT_EMOTE_JOKE},
        {"golfclap", TEXT_EMOTE_GOLFCLAP},
        {"wink", TEXT_EMOTE_WINK},
        {"pat", TEXT_EMOTE_PAT},
        {"serious", TEXT_EMOTE_SERIOUS},
        {"goodluck", TEXT_EMOTE_GOODLUCK},
        {"blame", TEXT_EMOTE_BLAME},
        {"blank", TEXT_EMOTE_BLANK},
        {"brandish", TEXT_EMOTE_BRANDISH},
        {"breath", TEXT_EMOTE_BREATH},
        {"disagree", TEXT_EMOTE_DISAGREE},
        {"doubt", TEXT_EMOTE_DOUBT},
        {"embarrass", TEXT_EMOTE_EMBARRASS},
        {"encourage", TEXT_EMOTE_ENCOURAGE},
        {"enemy", TEXT_EMOTE_ENEMY},
        {"eyebrow", TEXT_EMOTE_EYEBROW},
        {"toast", TEXT_EMOTE_TOAST},
        {"fail", TEXT_EMOTE_FAIL},
        {"highfive", TEXT_EMOTE_HIGHFIVE},
        {"absent", TEXT_EMOTE_ABSENT},
        {"arm", TEXT_EMOTE_ARM},
        {"awe", TEXT_EMOTE_AWE},
        {"backpack", TEXT_EMOTE_BACKPACK},
        {"badfeeling", TEXT_EMOTE_BADFEELING},
        {"challenge", TEXT_EMOTE_CHALLENGE},
        {"chug", TEXT_EMOTE_CHUG},
        {"ding", TEXT_EMOTE_DING},
        {"facepalm", TEXT_EMOTE_FACEPALM},
        {"faint", TEXT_EMOTE_FAINT},
        {"go", TEXT_EMOTE_GO},
        {"going", TEXT_EMOTE_GOING},
        {"glower", TEXT_EMOTE_GLOWER},
        {"headache", TEXT_EMOTE_HEADACHE},
        {"hiccup", TEXT_EMOTE_HICCUP},
        {"hiss", TEXT_EMOTE_HISS},
        {"holdhand", TEXT_EMOTE_HOLDHAND},
        {"hurry", TEXT_EMOTE_HURRY},
        {"idea", TEXT_EMOTE_IDEA},
        {"jealous", TEXT_EMOTE_JEALOUS},
        {"luck", TEXT_EMOTE_LUCK},
        {"map", TEXT_EMOTE_MAP},
        {"mercy", TEXT_EMOTE_MERCY},
        {"mutter", TEXT_EMOTE_MUTTER},
        {"nervous", TEXT_EMOTE_NERVOUS},
        {"offer", TEXT_EMOTE_OFFER},
        {"pet", TEXT_EMOTE_PET},
        {"pinch", TEXT_EMOTE_PINCH},
        {"proud", TEXT_EMOTE_PROUD},
        {"promise", TEXT_EMOTE_PROMISE},
        {"pulse", TEXT_EMOTE_PULSE},
        {"punch", TEXT_EMOTE_PUNCH},
        {"pout", TEXT_EMOTE_POUT},
        {"regret", TEXT_EMOTE_REGRET},
        {"revenge", TEXT_EMOTE_REVENGE},
        {"rolleyes", TEXT_EMOTE_ROLLEYES},
        {"ruffle", TEXT_EMOTE_RUFFLE},
        {"sad", TEXT_EMOTE_SAD},
        {"scoff", TEXT_EMOTE_SCOFF},
        {"scold", TEXT_EMOTE_SCOLD},
        {"scowl", TEXT_EMOTE_SCOWL},
        {"search", TEXT_EMOTE_SEARCH},
        {"shakefist", TEXT_EMOTE_SHAKEFIST},
        {"shifty", TEXT_EMOTE_SHIFTY},
        {"shudder", TEXT_EMOTE_SHUDDER},
        {"signal", TEXT_EMOTE_SIGNAL},
        {"silence", TEXT_EMOTE_SILENCE},
        {"sing", TEXT_EMOTE_SING},
        {"smack", TEXT_EMOTE_SMACK},
        {"sneak", TEXT_EMOTE_SNEAK},
        {"sneeze", TEXT_EMOTE_SNEEZE},
        {"snort", TEXT_EMOTE_SNORT},
        {"squeal", TEXT_EMOTE_SQUEAL},
        {"suspicious", TEXT_EMOTE_SUSPICIOUS},
        {"think", TEXT_EMOTE_THINK},
        {"truce", TEXT_EMOTE_TRUCE},
        {"twiddle", TEXT_EMOTE_TWIDDLE},
        {"warn", TEXT_EMOTE_WARN},
        {"snap", TEXT_EMOTE_SNAP},
        {"charm", TEXT_EMOTE_CHARM},
        {"coverears", TEXT_EMOTE_COVEREARS},
        {"crossarms", TEXT_EMOTE_CROSSARMS},
        {"look", TEXT_EMOTE_LOOK},
        {"object", TEXT_EMOTE_OBJECT},
        {"sweat", TEXT_EMOTE_SWEAT},
        {"yw", TEXT_EMOTE_YW},
    };

    auto it = emoteMap.find(emoteName);
    if (it != emoteMap.end())
        return it->second;

    return 0;
}
}

bool IsPlayerBot(Player* player)
{
    if (!player)
        return false;

    PlayerbotAI* ai = GET_PLAYERBOT_AI(player);
    return ai != nullptr;
}

Creature* FindCreatureBySpawnId(
    Map* map, uint32 spawnId)
{
    if (!map || !spawnId)
        return nullptr;

    auto bounds =
        map->GetCreatureBySpawnIdStore()
            .equal_range(spawnId);
    for (auto itr = bounds.first;
         itr != bounds.second; ++itr)
    {
        Creature* creature = itr->second;
        if (creature && creature->IsInWorld())
            return creature;
    }

    return nullptr;
}

std::string GetCreatureRoleName(Creature* creature)
{
    if (!creature || !creature->GetCreatureTemplate())
        return "NPC";

    if (creature->IsGuard())
        return "Guard";

    uint32 npcFlags =
        creature->GetUInt32Value(UNIT_NPC_FLAGS);
    if (npcFlags & UNIT_NPC_FLAG_FLIGHTMASTER)
        return "Flight Master";
    if (npcFlags & UNIT_NPC_FLAG_INNKEEPER)
        return "Innkeeper";
    if (npcFlags & UNIT_NPC_FLAG_QUESTGIVER)
        return "Quest Giver";
    if (npcFlags
        & (UNIT_NPC_FLAG_TRAINER
            | UNIT_NPC_FLAG_TRAINER_CLASS
            | UNIT_NPC_FLAG_TRAINER_PROFESSION))
    {
        return "Trainer";
    }
    if (npcFlags
        & (UNIT_NPC_FLAG_VENDOR
            | UNIT_NPC_FLAG_VENDOR_AMMO
            | UNIT_NPC_FLAG_VENDOR_FOOD
            | UNIT_NPC_FLAG_VENDOR_POISON
            | UNIT_NPC_FLAG_VENDOR_REAGENT))
    {
        return "Vendor";
    }

    CreatureTemplate const* tmpl =
        creature->GetCreatureTemplate();
    if (tmpl->rank == CREATURE_ELITE_RARE
        || tmpl->rank == CREATURE_ELITE_RAREELITE)
    {
        return "Rare Creature";
    }

    switch (tmpl->type)
    {
        case CREATURE_TYPE_CRITTER:
            return "Critter";
        case CREATURE_TYPE_BEAST:
            return "Beast";
        default:
            return "NPC";
    }
}

std::string EscapeString(const std::string& str)
{
    std::string result = str;
    size_t pos = 0;

    while ((pos = result.find('\\', pos)) != std::string::npos)
    {
        result.replace(pos, 1, "\\\\");
        pos += 2;
    }

    pos = 0;
    while ((pos = result.find('\'', pos)) != std::string::npos)
    {
        result.replace(pos, 1, "''");
        pos += 2;
    }

    return result;
}

std::string JsonEscape(const std::string& str)
{
    std::string result;
    result.reserve(str.size() * 2);

    for (char c : str)
    {
        switch (c)
        {
            case '"':
                result += "\\\"";
                break;
            case '\\':
                result += "\\\\";
                break;
            case '\n':
                result += "\\n";
                break;
            case '\r':
                result += "\\r";
                break;
            case '\t':
                result += "\\t";
                break;
            default:
                result += c;
                break;
        }
    }

    return result;
}

std::string GetClassName(uint8 classId)
{
    switch (classId)
    {
        case CLASS_WARRIOR: return "Warrior";
        case CLASS_PALADIN: return "Paladin";
        case CLASS_HUNTER: return "Hunter";
        case CLASS_ROGUE: return "Rogue";
        case CLASS_PRIEST: return "Priest";
        case CLASS_DEATH_KNIGHT: return "Death Knight";
        case CLASS_SHAMAN: return "Shaman";
        case CLASS_MAGE: return "Mage";
        case CLASS_WARLOCK: return "Warlock";
        case CLASS_DRUID: return "Druid";
        default: return "Unknown";
    }
}

std::string GetRaceName(uint8 raceId)
{
    switch (raceId)
    {
        case RACE_HUMAN: return "Human";
        case RACE_ORC: return "Orc";
        case RACE_DWARF: return "Dwarf";
        case RACE_NIGHTELF: return "Night Elf";
        case RACE_UNDEAD_PLAYER: return "Undead";
        case RACE_TAUREN: return "Tauren";
        case RACE_GNOME: return "Gnome";
        case RACE_TROLL: return "Troll";
        case RACE_BLOODELF: return "Blood Elf";
        case RACE_DRAENEI: return "Draenei";
        default: return "Unknown";
    }
}

std::string GetZoneName(uint32 zoneId)
{
    if (AreaTableEntry const* area =
            sAreaTableStore.LookupEntry(zoneId))
    {
        uint8 locale = sWorld->GetDefaultDbcLocale();
        char const* n = area->area_name[locale];
        std::string zoneName = n ? n : "";
        if (zoneName.empty())
        {
            n = area->area_name[LOCALE_enUS];
            zoneName = n ? n : "";
        }
        if (!zoneName.empty())
            return zoneName;
    }

    return "Unknown Zone";
}

std::string BuildBotIdentityFields(
    Player* player, bool includeRoles)
{
    if (!player)
    {
        LOG_ERROR(
            "module",
            "LLMChatter: BuildBotIdentityFields called with null player");

        std::string json =
            "\"bot_guid\":0,"
            "\"bot_name\":\"Unknown\","
            "\"bot_class\":0,"
            "\"bot_race\":0,"
            "\"bot_gender\":0,"
            "\"bot_level\":0";

        if (includeRoles)
            json += ",\"role\":\"dps\"";

        return json;
    }

    std::string json =
        "\"bot_guid\":" +
            std::to_string(
                player->GetGUID().GetCounter())
        + ",\"bot_name\":\""
        + JsonEscape(player->GetName()) + "\","
        + "\"bot_class\":"
        + std::to_string(player->getClass())
        + ",\"bot_race\":"
        + std::to_string(player->getRace())
        + ",\"bot_gender\":"
        + std::to_string(player->getGender())
        + ",\"bot_level\":"
        + std::to_string(player->GetLevel());

    if (includeRoles)
        json += ",\"role\":\""
            + GetBotRoleName(player) + "\"";

    return json;
}

bool IsEventOnCooldown(
    std::map<std::string, time_t>& cooldownCache,
    const std::string& cooldownKey,
    uint32 cooldownSeconds)
{
    auto it = cooldownCache.find(cooldownKey);
    if (it != cooldownCache.end())
    {
        time_t now = time(nullptr);
        if (now - it->second < cooldownSeconds)
            return true;
    }

    QueryResult result = CharacterDatabase.Query(
        "SELECT 1 FROM llm_chatter_events "
        "WHERE cooldown_key = '{}' AND created_at > "
        "DATE_SUB(NOW(), INTERVAL {} SECOND) LIMIT 1",
        cooldownKey, cooldownSeconds);

    return static_cast<bool>(result);
}

void SetEventCooldown(
    std::map<std::string, time_t>& cooldownCache,
    const std::string& cooldownKey)
{
    cooldownCache[cooldownKey] = time(nullptr);
}

bool CanSpeakInGeneralChannel(Player* bot)
{
    if (!bot || !bot->IsInWorld())
        return false;

    // Ensure the bot is joined to the correct
    // General channel for its current zone.
    // Bots present when the server starts never
    // trigger OnPlayerUpdateZone, so without this
    // they would never be in any General channel.
    EnsureBotInGeneralChannel(bot);

    uint32 zoneId = bot->GetZoneId();
    AreaTableEntry const* area =
        sAreaTableStore.LookupEntry(zoneId);
    if (!area)
        return false;

    char const* zn =
        area->area_name[sWorld->GetDefaultDbcLocale()];
    std::string zoneName = zn ? zn : "";
    if (zoneName.empty())
    {
        zn = area->area_name[LOCALE_enUS];
        zoneName = zn ? zn : "";
    }
    if (zoneName.empty())
        return false;

    ChannelMgr* cMgr =
        ChannelMgr::forTeam(bot->GetTeamId());
    if (!cMgr)
        return false;

    for (auto const& [key, channel] :
         cMgr->GetChannels())
    {
        if (!channel)
            continue;
        if (channel->GetChannelId()
            != ChatChannelId::GENERAL)
            continue;
        if (channel->GetName().find(zoneName)
            == std::string::npos)
            continue;

        return bot->IsInChannel(channel);
    }

    return false;
}

std::string ConvertAllLinks(const std::string& text)
{
    std::string result = text;
    result = ConvertItemLinks(result);
    result = ConvertQuestLinks(result);
    result = ConvertSpellLinks(result);
    result = ConvertNpcLinks(result);
    return result;
}

uint32 GetTextEmoteId(const std::string& emoteName)
{
    return LookupTextEmoteId(emoteName);
}

std::string GetTextEmoteName(uint32 emoteId)
{
    static const std::unordered_map<uint32, std::string>
        reverseMap = {
        {TEXT_EMOTE_AGREE,         "agree"},
        {TEXT_EMOTE_AMAZE,         "amaze"},
        {TEXT_EMOTE_ANGRY,         "angry"},
        {TEXT_EMOTE_APOLOGIZE,     "apologize"},
        {TEXT_EMOTE_APPLAUD,       "applaud"},
        {TEXT_EMOTE_BASHFUL,       "bashful"},
        {TEXT_EMOTE_BECKON,        "beckon"},
        {TEXT_EMOTE_BEG,           "beg"},
        {TEXT_EMOTE_BITE,          "bite"},
        {TEXT_EMOTE_BLEED,         "bleed"},
        {TEXT_EMOTE_BLINK,         "blink"},
        {TEXT_EMOTE_BLUSH,         "blush"},
        {TEXT_EMOTE_BONK,          "bonk"},
        {TEXT_EMOTE_BORED,         "bored"},
        {TEXT_EMOTE_BOUNCE,        "bounce"},
        {TEXT_EMOTE_BRB,           "brb"},
        {TEXT_EMOTE_BOW,           "bow"},
        {TEXT_EMOTE_BURP,          "burp"},
        {TEXT_EMOTE_BYE,           "bye"},
        {TEXT_EMOTE_CACKLE,        "cackle"},
        {TEXT_EMOTE_CHEER,         "cheer"},
        {TEXT_EMOTE_CHICKEN,       "chicken"},
        {TEXT_EMOTE_CHUCKLE,       "chuckle"},
        {TEXT_EMOTE_CLAP,          "clap"},
        {TEXT_EMOTE_CONFUSED,      "confused"},
        {TEXT_EMOTE_CONGRATULATE,  "congratulate"},
        {TEXT_EMOTE_COUGH,         "cough"},
        {TEXT_EMOTE_COWER,         "cower"},
        {TEXT_EMOTE_CRACK,         "crack"},
        {TEXT_EMOTE_CRINGE,        "cringe"},
        {TEXT_EMOTE_CRY,           "cry"},
        {TEXT_EMOTE_CURIOUS,       "curious"},
        {TEXT_EMOTE_CURTSEY,       "curtsey"},
        {TEXT_EMOTE_DANCE,         "dance"},
        {TEXT_EMOTE_DRINK,         "drink"},
        {TEXT_EMOTE_DROOL,         "drool"},
        {TEXT_EMOTE_EAT,           "eat"},
        {TEXT_EMOTE_EYE,           "eye"},
        {TEXT_EMOTE_FART,          "fart"},
        {TEXT_EMOTE_FIDGET,        "fidget"},
        {TEXT_EMOTE_FLEX,          "flex"},
        {TEXT_EMOTE_FROWN,         "frown"},
        {TEXT_EMOTE_GASP,          "gasp"},
        {TEXT_EMOTE_GAZE,          "gaze"},
        {TEXT_EMOTE_GIGGLE,        "giggle"},
        {TEXT_EMOTE_GLARE,         "glare"},
        {TEXT_EMOTE_GLOAT,         "gloat"},
        {TEXT_EMOTE_GREET,         "greet"},
        {TEXT_EMOTE_GRIN,          "grin"},
        {TEXT_EMOTE_GROAN,         "groan"},
        {TEXT_EMOTE_GROVEL,        "grovel"},
        {TEXT_EMOTE_GUFFAW,        "guffaw"},
        {TEXT_EMOTE_HAIL,          "hail"},
        {TEXT_EMOTE_HAPPY,         "happy"},
        {TEXT_EMOTE_HELLO,         "hello"},
        {TEXT_EMOTE_HUG,           "hug"},
        {TEXT_EMOTE_HUNGRY,        "hungry"},
        {TEXT_EMOTE_KISS,          "kiss"},
        {TEXT_EMOTE_KNEEL,         "kneel"},
        {TEXT_EMOTE_LAUGH,         "laugh"},
        {TEXT_EMOTE_LAYDOWN,       "laydown"},
        {TEXT_EMOTE_MOAN,          "moan"},
        {TEXT_EMOTE_MOON,          "moon"},
        {TEXT_EMOTE_MOURN,         "mourn"},
        {TEXT_EMOTE_NO,            "no"},
        {TEXT_EMOTE_NOD,           "nod"},
        {TEXT_EMOTE_NOSEPICK,      "nosepick"},
        {TEXT_EMOTE_PANIC,         "panic"},
        {TEXT_EMOTE_PEER,          "peer"},
        {TEXT_EMOTE_PLEAD,         "plead"},
        {TEXT_EMOTE_POINT,         "point"},
        {TEXT_EMOTE_POKE,          "poke"},
        {TEXT_EMOTE_PRAY,          "pray"},
        {TEXT_EMOTE_READY,         "ready"},
        {TEXT_EMOTE_ROAR,          "roar"},
        {TEXT_EMOTE_RUDE,          "rude"},
        {TEXT_EMOTE_SALUTE,        "salute"},
        {TEXT_EMOTE_SCRATCH,       "scratch"},
        {TEXT_EMOTE_SEXY,          "sexy"},
        {TEXT_EMOTE_SHAKE,         "shake"},
        {TEXT_EMOTE_SHOUT,         "shout"},
        {TEXT_EMOTE_SHRUG,         "shrug"},
        {TEXT_EMOTE_SHY,           "shy"},
        {TEXT_EMOTE_SIGH,          "sigh"},
        {TEXT_EMOTE_SIT,           "sit"},
        {TEXT_EMOTE_SLEEP,         "sleep"},
        {TEXT_EMOTE_SNARL,         "snarl"},
        {TEXT_EMOTE_SPIT,          "spit"},
        {TEXT_EMOTE_STARE,         "stare"},
        {TEXT_EMOTE_SURPRISED,     "surprised"},
        {TEXT_EMOTE_SURRENDER,     "surrender"},
        {TEXT_EMOTE_TALK,          "talk"},
        {TEXT_EMOTE_TALKEX,        "talkex"},
        {TEXT_EMOTE_TALKQ,         "talkq"},
        {TEXT_EMOTE_TAP,           "tap"},
        {TEXT_EMOTE_THANK,         "thank"},
        {TEXT_EMOTE_THREATEN,      "threaten"},
        {TEXT_EMOTE_TIRED,         "tired"},
        {TEXT_EMOTE_VICTORY,       "victory"},
        {TEXT_EMOTE_WAVE,          "wave"},
        {TEXT_EMOTE_WELCOME,       "welcome"},
        {TEXT_EMOTE_WHINE,         "whine"},
        {TEXT_EMOTE_WHISTLE,       "whistle"},
        {TEXT_EMOTE_WORK,          "work"},
        {TEXT_EMOTE_YAWN,          "yawn"},
        {TEXT_EMOTE_BOGGLE,        "boggle"},
        {TEXT_EMOTE_CALM,          "calm"},
        {TEXT_EMOTE_COLD,          "cold"},
        {TEXT_EMOTE_COMFORT,       "comfort"},
        {TEXT_EMOTE_CUDDLE,        "cuddle"},
        {TEXT_EMOTE_DUCK,          "duck"},
        {TEXT_EMOTE_INSULT,        "insult"},
        {TEXT_EMOTE_INTRODUCE,     "introduce"},
        {TEXT_EMOTE_JK,            "jk"},
        {TEXT_EMOTE_LICK,          "lick"},
        {TEXT_EMOTE_LISTEN,        "listen"},
        {TEXT_EMOTE_LOST,          "lost"},
        {TEXT_EMOTE_MOCK,          "mock"},
        {TEXT_EMOTE_PONDER,        "ponder"},
        {TEXT_EMOTE_POUNCE,        "pounce"},
        {TEXT_EMOTE_PRAISE,        "praise"},
        {TEXT_EMOTE_PURR,          "purr"},
        {TEXT_EMOTE_PUZZLE,        "puzzle"},
        {TEXT_EMOTE_RAISE,         "raise"},
        {TEXT_EMOTE_SHIMMY,        "shimmy"},
        {TEXT_EMOTE_SHIVER,        "shiver"},
        {TEXT_EMOTE_SHOO,          "shoo"},
        {TEXT_EMOTE_SLAP,          "slap"},
        {TEXT_EMOTE_SMIRK,         "smirk"},
        {TEXT_EMOTE_SNIFF,         "sniff"},
        {TEXT_EMOTE_SNUB,          "snub"},
        {TEXT_EMOTE_SOOTHE,        "soothe"},
        {TEXT_EMOTE_STINK,         "stink"},
        {TEXT_EMOTE_TAUNT,         "taunt"},
        {TEXT_EMOTE_TEASE,         "tease"},
        {TEXT_EMOTE_THIRSTY,       "thirsty"},
        {TEXT_EMOTE_VETO,          "veto"},
        {TEXT_EMOTE_SNICKER,       "snicker"},
        {TEXT_EMOTE_STAND,         "stand"},
        {TEXT_EMOTE_TICKLE,        "tickle"},
        {TEXT_EMOTE_VIOLIN,        "violin"},
        {TEXT_EMOTE_SMILE,         "smile"},
        {TEXT_EMOTE_RASP,          "rasp"},
        {TEXT_EMOTE_PITY,          "pity"},
        {TEXT_EMOTE_GROWL,         "growl"},
        {TEXT_EMOTE_BARK,          "bark"},
        {TEXT_EMOTE_SCARED,        "scared"},
        {TEXT_EMOTE_FLOP,          "flop"},
        {TEXT_EMOTE_LOVE,          "love"},
        {TEXT_EMOTE_MOO,           "moo"},
        {TEXT_EMOTE_COMMEND,       "commend"},
        {TEXT_EMOTE_TRAIN,         "train"},
        {TEXT_EMOTE_FLIRT,         "flirt"},
        {TEXT_EMOTE_JOKE,          "joke"},
        {TEXT_EMOTE_GOLFCLAP,      "golfclap"},
        {TEXT_EMOTE_WINK,          "wink"},
        {TEXT_EMOTE_PAT,           "pat"},
        {TEXT_EMOTE_SERIOUS,       "serious"},
        {TEXT_EMOTE_GOODLUCK,      "goodluck"},
        {TEXT_EMOTE_BLAME,         "blame"},
        {TEXT_EMOTE_BLANK,         "blank"},
        {TEXT_EMOTE_BRANDISH,      "brandish"},
        {TEXT_EMOTE_BREATH,        "breath"},
        {TEXT_EMOTE_DISAGREE,      "disagree"},
        {TEXT_EMOTE_DOUBT,         "doubt"},
        {TEXT_EMOTE_EMBARRASS,     "embarrass"},
        {TEXT_EMOTE_ENCOURAGE,     "encourage"},
        {TEXT_EMOTE_ENEMY,         "enemy"},
        {TEXT_EMOTE_EYEBROW,       "eyebrow"},
        {TEXT_EMOTE_TOAST,         "toast"},
        {TEXT_EMOTE_FAIL,          "fail"},
        {TEXT_EMOTE_HIGHFIVE,      "highfive"},
        {TEXT_EMOTE_MERCY,         "mercy"},
        {TEXT_EMOTE_SING,          "sing"},
        {TEXT_EMOTE_OBJECT,        "object"},
        {TEXT_EMOTE_YW,            "yw"},
        // IDs 381+ (text-only emotes)
        {TEXT_EMOTE_ABSENT,        "absent"},
        {TEXT_EMOTE_ARM,           "arm"},
        {TEXT_EMOTE_AWE,           "awe"},
        {TEXT_EMOTE_BACKPACK,      "backpack"},
        {TEXT_EMOTE_BADFEELING,    "badfeeling"},
        {TEXT_EMOTE_CHALLENGE,     "challenge"},
        {TEXT_EMOTE_CHUG,          "chug"},
        {TEXT_EMOTE_DING,          "ding"},
        {TEXT_EMOTE_FACEPALM,      "facepalm"},
        {TEXT_EMOTE_FAINT,         "faint"},
        {TEXT_EMOTE_GO,            "go"},
        {TEXT_EMOTE_GOING,         "going"},
        {TEXT_EMOTE_GLOWER,        "glower"},
        {TEXT_EMOTE_HEADACHE,      "headache"},
        {TEXT_EMOTE_HICCUP,        "hiccup"},
        {TEXT_EMOTE_HISS,          "hiss"},
        {TEXT_EMOTE_HOLDHAND,      "holdhand"},
        {TEXT_EMOTE_HURRY,         "hurry"},
        {TEXT_EMOTE_IDEA,          "idea"},
        {TEXT_EMOTE_JEALOUS,       "jealous"},
        {TEXT_EMOTE_LUCK,          "luck"},
        {TEXT_EMOTE_MAP,           "map"},
        {TEXT_EMOTE_MUTTER,        "mutter"},
        {TEXT_EMOTE_NERVOUS,       "nervous"},
        {TEXT_EMOTE_OFFER,         "offer"},
        {TEXT_EMOTE_PET,           "pet"},
        {TEXT_EMOTE_PINCH,         "pinch"},
        {TEXT_EMOTE_PROUD,         "proud"},
        {TEXT_EMOTE_PROMISE,       "promise"},
        {TEXT_EMOTE_PULSE,         "pulse"},
        {TEXT_EMOTE_PUNCH,         "punch"},
        {TEXT_EMOTE_POUT,          "pout"},
        {TEXT_EMOTE_REGRET,        "regret"},
        {TEXT_EMOTE_REVENGE,       "revenge"},
        {TEXT_EMOTE_ROLLEYES,      "rolleyes"},
        {TEXT_EMOTE_RUFFLE,        "ruffle"},
        {TEXT_EMOTE_SAD,           "sad"},
        {TEXT_EMOTE_SCOFF,         "scoff"},
        {TEXT_EMOTE_SCOLD,         "scold"},
        {TEXT_EMOTE_SCOWL,         "scowl"},
        {TEXT_EMOTE_SEARCH,        "search"},
        {TEXT_EMOTE_SHAKEFIST,     "shakefist"},
        {TEXT_EMOTE_SHIFTY,        "shifty"},
        {TEXT_EMOTE_SHUDDER,       "shudder"},
        {TEXT_EMOTE_SIGNAL,        "signal"},
        {TEXT_EMOTE_SILENCE,       "silence"},
        {TEXT_EMOTE_SMACK,         "smack"},
        {TEXT_EMOTE_SNEAK,         "sneak"},
        {TEXT_EMOTE_SNEEZE,        "sneeze"},
        {TEXT_EMOTE_SNORT,         "snort"},
        {TEXT_EMOTE_SQUEAL,        "squeal"},
        {TEXT_EMOTE_SUSPICIOUS,    "suspicious"},
        {TEXT_EMOTE_THINK,         "think"},
        {TEXT_EMOTE_TRUCE,         "truce"},
        {TEXT_EMOTE_TWIDDLE,       "twiddle"},
        {TEXT_EMOTE_WARN,          "warn"},
        {TEXT_EMOTE_SNAP,          "snap"},
        {TEXT_EMOTE_CHARM,         "charm"},
        {TEXT_EMOTE_COVEREARS,     "coverears"},
        {TEXT_EMOTE_CROSSARMS,     "crossarms"},
        {TEXT_EMOTE_LOOK,          "look"},
        {TEXT_EMOTE_SWEAT,         "sweat"},
    };
    auto it = reverseMap.find(emoteId);
    return (it != reverseMap.end())
        ? it->second : "wave";
}

std::string BuildBotStateJson(Player* player)
{
    if (!player)
        return "";

    float healthPct = player->GetHealthPct();
    bool inCombat = player->IsInCombat();

    int manaPctInt = -1;
    if (player->GetMaxPower(POWER_MANA) > 0)
        manaPctInt =
            static_cast<int>(player->GetPowerPct(POWER_MANA));

    PlayerbotAI* ai = GET_PLAYERBOT_AI(player);

    std::string targetName;
    Unit* victim = player->GetVictim();
    if (victim)
        targetName = victim->GetName();

    std::string botState = "non_combat";
    if (ai)
    {
        BotState state = ai->GetState();
        if (state == BOT_STATE_COMBAT)
            botState = "combat";
        else if (state == BOT_STATE_DEAD)
            botState = "dead";
    }

    return
        "\"bot_state\":{"
        "\"health_pct\":" +
            std::to_string(static_cast<int>(healthPct)) + ","
        "\"mana_pct\":" +
            std::to_string(manaPctInt) + ","
        "\"role\":\"" + GetBotRoleName(player) + "\","
        "\"in_combat\":" +
            std::string(
                inCombat ? "true" : "false")
            + ","
        "\"target\":\"" +
            JsonEscape(targetName) + "\","
        "\"bot_ai_state\":\"" + botState + "\""
        "}";
}

void QueueChatterEvent(
    const std::string& eventType,
    const std::string& eventScope,
    uint32 zoneId, uint32 mapId, uint8 priority,
    const std::string& cooldownKey,
    uint32 subjectGuid, const std::string& subjectName,
    uint32 targetGuid, const std::string& targetName,
    uint32 targetEntry, const std::string& extraData,
    uint32 reactAfterSeconds,
    uint32 expiresAfterSeconds,
    bool nullZeroNumeric)
{
    auto NumSql = [nullZeroNumeric](uint32 value)
    {
        if (nullZeroNumeric && value == 0)
            return std::string("NULL");
        return std::to_string(value);
    };

    // NOTE: extraData is written directly into a single-quoted SQL
    // string literal. Callers must pre-escape it for SQL.
    CharacterDatabase.Execute(
        "INSERT INTO llm_chatter_events "
        "(event_type, event_scope, zone_id, map_id, "
        "priority, cooldown_key, subject_guid, "
        "subject_name, target_guid, target_name, "
        "target_entry, extra_data, status, react_after, "
        "expires_at) "
        "VALUES ('{}', '{}', {}, {}, {}, '{}', "
        "{}, '{}', {}, '{}', {}, '{}', 'pending', "
        "DATE_ADD(NOW(), INTERVAL {} SECOND), "
        "DATE_ADD(NOW(), INTERVAL {} SECOND))",
        EscapeString(eventType),
        EscapeString(eventScope),
        NumSql(zoneId),
        NumSql(mapId),
        priority,
        EscapeString(cooldownKey),
        NumSql(subjectGuid),
        EscapeString(subjectName),
        NumSql(targetGuid),
        EscapeString(targetName),
        NumSql(targetEntry),
        extraData,
        reactAfterSeconds,
        expiresAfterSeconds);
}

void AppendRaidContext(
    Player* player, std::string& json)
{
    if (json.empty() || json.back() != '}')
    {
        return;
    }

    Group* group = player->GetGroup();
    if (!group || !group->isRaidGroup())
        return;

    uint8 playerSubGroup =
        group->GetMemberGroup(player->GetGUID());

    std::string partyGuids = "[";
    std::string raidGuids = "[";
    bool firstParty = true;
    bool firstRaid = true;

    for (GroupReference* itr =
             group->GetFirstMember();
         itr; itr = itr->next())
    {
        Player* member = itr->GetSource();
        if (!member || !IsPlayerBot(member))
            continue;

        uint8 sg = group->GetMemberGroup(
            member->GetGUID());
        uint32 guid =
            member->GetGUID().GetCounter();

        if (sg == playerSubGroup)
        {
            if (!firstParty)
                partyGuids += ",";
            partyGuids += std::to_string(guid);
            firstParty = false;
        }
        else
        {
            if (!firstRaid)
                raidGuids += ",";
            raidGuids += std::to_string(guid);
            firstRaid = false;
        }
    }

    partyGuids += "]";
    raidGuids += "]";

    json.pop_back();

    json += ","
        "\"in_raid\":true,"
        "\"raid_group_id\":" +
            std::to_string(
                group->GetGUID().GetCounter())
        + ","
        "\"player_subgroup\":" +
            std::to_string(playerSubGroup)
        + ","
        "\"party_bot_guids\":" + partyGuids + ","
        "\"raid_bot_guids\":" + raidGuids +
        "}";
}

bool GroupHasBots(Group* group)
{
    if (!group)
        return false;

    for (GroupReference* itr =
             group->GetFirstMember();
         itr; itr = itr->next())
    {
        Player* member = itr->GetSource();
        if (member && IsPlayerBot(member))
            return true;
    }

    return false;
}

Player* FindMentionedMember(
    Player* bot, Group* grp,
    const std::string& message)
{
    std::string msgLower = message;
    std::transform(
        msgLower.begin(), msgLower.end(),
        msgLower.begin(),
        [](unsigned char c) {
            return std::tolower(c);
        });

    for (GroupReference* itr =
             grp->GetFirstMember();
         itr; itr = itr->next())
    {
        Player* member = itr->GetSource();
        if (!member || member == bot)
            continue;

        std::string nameLower = member->GetName();
        std::transform(
            nameLower.begin(), nameLower.end(),
            nameLower.begin(),
            [](unsigned char c) {
                return std::tolower(c);
            });

        size_t pos = msgLower.find(nameLower);
        if (pos == std::string::npos)
            continue;

        // Word-boundary check: char before and
        // after must be non-alpha (handles
        // "Calwen's", etc.)
        bool leftOk =
            (pos == 0
             || !std::isalpha(
                    static_cast<unsigned char>(
                        msgLower[pos - 1])));
        size_t end = pos + nameLower.size();
        bool rightOk =
            (end >= msgLower.size()
             || !std::isalpha(
                    static_cast<unsigned char>(
                        msgLower[end])));

        if (leftOk && rightOk)
            return member;
    }
    return nullptr;
}

Player* FindNearbyDefenderBot(
    Player* intruder, uint32 zoneId,
    TeamId defenderTeam)
{
    if (!intruder || !intruder->IsInWorld())
        return nullptr;

    std::vector<Player*> candidates;

    auto allBots =
        sRandomPlayerbotMgr.GetAllBots();
    for (auto& pair : allBots)
    {
        Player* bot = pair.second;
        if (!bot || !bot->IsInWorld()
            || !bot->IsAlive())
            continue;

        WorldSession* session = bot->GetSession();
        if (session && session->PlayerLoading())
            continue;

        if (bot->GetZoneId() != zoneId)
            continue;
        if (bot->GetMapId() != intruder->GetMapId())
            continue;
        if (bot->GetTeamId() != defenderTeam)
            continue;
        if (bot->IsInCombat())
            continue;

        if (bot->GetDistance2d(intruder) > 300.0f)
            continue;

        candidates.push_back(bot);
    }

    if (candidates.empty())
        return nullptr;

    std::shuffle(
        candidates.begin(), candidates.end(),
        std::mt19937{std::random_device{}()});
    return candidates[0];
}

uint8 GetChatterEventPriority(
    const std::string& eventType)
{
    if (sLLMChatterConfig
        && sLLMChatterConfig->_prioritySystemEnable)
        return GetTierPriority(eventType);

    return GetLegacyPriority(eventType);
}

uint32 GetReactionDelaySeconds(
    const std::string& eventType)
{
    if (sLLMChatterConfig
        && sLLMChatterConfig->_prioritySystemEnable)
        return GetTierReactionDelaySeconds(eventType);

    return GetLegacyReactionDelaySeconds(eventType);
}

bool IsBGAllowedEmote(const std::string& emoteName)
{
    static const std::unordered_set<std::string> allowed = {
        "angry", "charge", "cheer", "flex",
        "roar", "salute", "shout", "threaten",
        "victory", "brandish", "challenge",
        "encourage", "enemy", "go", "incoming",
        "openfire", "attacktarget", "revenge",
        "shakefist", "warn", "ready", "taunt",
        "growl", "snarl", "glare", "gloat",
        "proud", "praise", "commend", "applaud",
        "congratulate", "highfive",
    };

    return allowed.count(emoteName) > 0;
}

void SendUnitTextEmote(Unit* unit, uint32 textEmoteId,
                       const std::string& targetName)
{
    if (!unit || !textEmoteId)
        return;

    EmotesTextEntry const* em =
        sEmotesTextStore.LookupEntry(textEmoteId);
    if (em)
    {
        uint32 emoteAnim = em->textid;
        switch (emoteAnim)
        {
            case EMOTE_STATE_SLEEP:
            case EMOTE_STATE_SIT:
            case EMOTE_STATE_KNEEL:
            case EMOTE_ONESHOT_NONE:
                break;
            case EMOTE_STATE_DANCE:
                unit->HandleEmoteCommand(
                    EMOTE_ONESHOT_DANCESPECIAL);
                break;
            default:
                unit->HandleEmoteCommand(emoteAnim);
                break;
        }
    }

    WorldPacket data(SMSG_TEXT_EMOTE,
                     20 + targetName.size() + 1);
    data << unit->GetGUID();
    data << uint32(textEmoteId);
    data << uint32(0);  // emoteNum
    // nameLen excludes null terminator (matches core
    // SMSG_TEXT_EMOTE serialization in ChatHandler.cpp)
    data << uint32(targetName.size());
    if (!targetName.empty())
        data.append(targetName.c_str(),
                    targetName.size() + 1);
    else
        data << uint8(0x00);
    unit->SendMessageToSet(&data, true);
}

void SendBotTextEmote(Player* bot, uint32 textEmoteId)
{
    SendUnitTextEmote(bot, textEmoteId);
}

void SendBotTextEmote(Player* bot, uint32 textEmoteId,
                      const std::string& targetName)
{
    SendUnitTextEmote(bot, textEmoteId, targetName);
}

void SendPartyMessageInstant(
    Player* bot, Group* group,
    const std::string& message,
    const std::string& emote)
{
    WorldPacket data;
    ChatHandler::BuildChatPacket(
        data,
        CHAT_MSG_PARTY,
        message,
        LANG_UNIVERSAL,
        CHAT_TAG_NONE,
        bot->GetGUID(),
        bot->GetName());

    int subGroup = -1;
    if (group->isRaidGroup())
        subGroup = group->GetMemberGroup(bot->GetGUID());

    group->BroadcastPacket(&data, false, subGroup);

    if (!emote.empty())
    {
        uint32 textEmoteId = LookupTextEmoteId(emote);
        if (textEmoteId)
            SendBotTextEmote(bot, textEmoteId);
    }
}
