/*
 * mod-llm-chatter - Shared helpers used across multiple translation units
 */

#include "LLMChatterShared.h"

#include "LLMChatterConfig.h"
#include "Chat.h"
#include "DatabaseEnv.h"
#include "DBCStores.h"
#include "Group.h"
#include "Log.h"
#include "Player.h"
#include "Playerbots.h"
#include "RandomPlayerbotMgr.h"
#include "WorldSession.h"

#include <algorithm>
#include <cctype>
#include <sstream>
#include <unordered_map>
#include <random>
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

uint8 GetTierPriority(const std::string& eventType)
{
    if (eventType == "bot_group_combat"
        || eventType == "bot_group_spell_cast"
        || IsStateCalloutEventType(eventType)
        || eventType == "bot_group_nearby_object"
        || eventType == "weather_change"
        || eventType == "transport_arrives"
        || eventType == "bg_flag_picked_up"
        || eventType == "bg_flag_dropped"
        || eventType == "bg_flag_captured"
        || eventType == "bg_flag_returned"
        || eventType == "bg_node_contested"
        || eventType == "bg_node_captured"
        || eventType == "raid_boss_pull"
        || eventType == "raid_boss_kill"
        || eventType == "raid_boss_wipe")
        return PRIORITY_CRITICAL;

    if (eventType == "bot_group_player_msg")
        return PRIORITY_HIGH_LOCAL;

    if (eventType == "player_general_msg"
        || eventType == "bot_group_death"
        || eventType == "bot_group_wipe"
        || eventType == "bg_match_start"
        || eventType == "bg_pvp_kill"
        || eventType == "player_enters_zone")
        return PRIORITY_HIGH;

    if (eventType == "bot_group_join"
        || eventType == "bot_group_join_batch"
        || eventType == "bg_idle_chatter"
        || eventType == "raid_idle_morale"
        || eventType == "weather_ambient"
        || eventType == "minor_event"
        || eventType == "day_night_transition")
        return PRIORITY_FILLER;

    return PRIORITY_NORMAL;
}

uint8 GetLegacyPriority(const std::string& eventType)
{
    if (eventType == "player_general_msg")
        return 8;
    if (eventType == "day_night_transition")
        return 7;
    if (eventType == "transport_arrives")
        return 6;
    if (eventType == "player_enters_zone")
        return 6;
    if (eventType == "weather_change"
        || eventType == "bot_group_nearby_object")
        return 5;
    if (eventType == "bot_group_discovery")
        return 4;
    if (eventType == "weather_ambient"
        || eventType == "bot_group_zone_transition")
        return 3;
    if (eventType == "bot_group_combat"
        || IsStateCalloutEventType(eventType)
        || eventType == "holiday_start"
        || eventType == "holiday_end"
        || eventType == "minor_event")
        return 2;
    if (eventType == "bot_group_join"
        || eventType == "bot_group_join_batch"
        || eventType == "raid_idle_morale")
        return 0;
    // Historical default for most group and battleground event
    // producers was inline priority 1.
    return 1;
}

uint32 GetTierReactionDelaySeconds(
    const std::string& eventType)
{
    uint8 priority = GetTierPriority(eventType);

    if (priority >= PRIORITY_CRITICAL)
        return urand(
            sLLMChatterConfig
                ->_priorityReactRangeCriticalMin,
            sLLMChatterConfig
                ->_priorityReactRangeCriticalMax);
    if (priority >= PRIORITY_HIGH)
        return urand(
            sLLMChatterConfig
                ->_priorityReactRangeHighMin,
            sLLMChatterConfig
                ->_priorityReactRangeHighMax);
    if (priority >= PRIORITY_NORMAL)
        return urand(
            sLLMChatterConfig
                ->_priorityReactRangeNormalMin,
            sLLMChatterConfig
                ->_priorityReactRangeNormalMax);
    return urand(
        sLLMChatterConfig
            ->_priorityReactRangeFillerMin,
        sLLMChatterConfig
            ->_priorityReactRangeFillerMax);
}

uint32 GetLegacyReactionDelaySeconds(
    const std::string& eventType)
{
    uint32 minDelay = 0;
    uint32 maxDelay = 0;

    if (eventType == "day_night_transition")
    {
        minDelay = sLLMChatterConfig
            ->_reactRangeDayNightMin;
        maxDelay = sLLMChatterConfig
            ->_reactRangeDayNightMax;
    }
    else if (eventType == "holiday_start"
        || eventType == "holiday_end")
    {
        minDelay = sLLMChatterConfig
            ->_reactRangeHolidayMin;
        maxDelay = sLLMChatterConfig
            ->_reactRangeHolidayMax;
    }
    else if (eventType == "weather_change")
    {
        minDelay = sLLMChatterConfig
            ->_reactRangeWeatherMin;
        maxDelay = sLLMChatterConfig
            ->_reactRangeWeatherMax;
    }
    else if (eventType == "weather_ambient")
    {
        minDelay = sLLMChatterConfig
            ->_reactRangeWeatherAmbientMin;
        maxDelay = sLLMChatterConfig
            ->_reactRangeWeatherAmbientMax;
    }
    else if (eventType == "transport_arrives")
    {
        minDelay = sLLMChatterConfig
            ->_reactRangeTransportMin;
        maxDelay = sLLMChatterConfig
            ->_reactRangeTransportMax;
    }
    else if (eventType == "bot_group_quest_accept"
        || eventType == "bot_group_quest_accept_batch")
    {
        minDelay = sLLMChatterConfig
            ->_reactRangeQuestAcceptMin;
        maxDelay = sLLMChatterConfig
            ->_reactRangeQuestAcceptMax;
    }
    else if (eventType == "bot_group_join")
        return sLLMChatterConfig->_reactDelayJoin;
    else if (eventType == "bot_group_join_batch")
        return sLLMChatterConfig->_reactDelayJoinBatch;
    else if (eventType == "bot_group_kill")
        return sLLMChatterConfig->_reactDelayKill;
    else if (eventType == "bot_group_wipe")
        return sLLMChatterConfig->_reactDelayWipe;
    else if (eventType == "bot_group_death")
        return sLLMChatterConfig->_reactDelayDeath;
    else if (eventType == "bot_group_loot")
        return sLLMChatterConfig->_reactDelayLoot;
    else if (eventType == "bot_group_combat")
        return sLLMChatterConfig->_reactDelayCombat;
    else if (eventType == "bot_group_player_msg")
        return sLLMChatterConfig->_reactDelayPlayerMsg;
    else if (eventType == "bot_group_levelup")
        return sLLMChatterConfig->_reactDelayLevelUp;
    else if (eventType == "bot_group_quest_objectives")
        return sLLMChatterConfig
            ->_reactDelayQuestObjectives;
    else if (eventType == "bot_group_quest_complete")
        return sLLMChatterConfig
            ->_reactDelayQuestComplete;
    else if (eventType == "bot_group_achievement")
        return sLLMChatterConfig->_reactDelayAchievement;
    else if (eventType == "bot_group_spell_cast")
        return sLLMChatterConfig->_reactDelaySpellCast;
    else if (eventType == "bot_group_resurrect")
        return sLLMChatterConfig->_reactDelayResurrect;
    else if (eventType == "bot_group_corpse_run")
        return sLLMChatterConfig->_reactDelayCorpseRun;
    else if (eventType == "bot_group_dungeon_entry")
        return sLLMChatterConfig->_reactDelayDungeonEntry;
    else if (eventType == "bot_group_zone_transition")
        return sLLMChatterConfig
            ->_reactDelayZoneTransition;
    else if (eventType == "bot_group_discovery")
    {
        return urand(
            sLLMChatterConfig->_reactDelayDiscoveryMin,
            sLLMChatterConfig->_reactDelayDiscoveryMax);
    }
    else if (eventType == "bot_group_nearby_object")
        return sLLMChatterConfig->_reactDelayNearbyObject;
    else if (IsStateCalloutEventType(eventType))
        return sLLMChatterConfig->_reactDelayStateCallout;
    else if (IsBattlegroundEventType(eventType))
        return sLLMChatterConfig->_reactDelayBGEvent;
    else if (IsRaidEventType(eventType))
        return sLLMChatterConfig->_reactDelayBGEvent;
    else if (eventType == "player_general_msg")
        return sLLMChatterConfig->_reactDelayGeneralMsg;
    else if (eventType == "player_enters_zone")
        return 2;
    else
    {
        minDelay = sLLMChatterConfig
            ->_reactRangeDefaultMin;
        maxDelay = sLLMChatterConfig
            ->_reactRangeDefaultMax;
    }

    return urand(minDelay, maxDelay);
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

    std::string role = "dps";
    PlayerbotAI* ai = GET_PLAYERBOT_AI(player);
    if (ai)
    {
        if (PlayerbotAI::IsTank(player))
            role = "tank";
        else if (PlayerbotAI::IsHeal(player))
            role = "healer";
        else if (PlayerbotAI::IsRanged(player))
            role = "ranged_dps";
        else
            role = "melee_dps";
    }

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
        "\"role\":\"" + role + "\","
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

void SendBotTextEmote(Player* bot, uint32 textEmoteId)
{
    if (!bot || !textEmoteId)
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
                bot->HandleEmoteCommand(
                    EMOTE_ONESHOT_DANCESPECIAL);
                break;
            default:
                bot->HandleEmoteCommand(emoteAnim);
                break;
        }
    }

    WorldPacket data(SMSG_TEXT_EMOTE, 20 + 1);
    data << bot->GetGUID();
    data << uint32(textEmoteId);
    data << uint32(0);
    data << uint32(0);
    data << uint8(0x00);
    bot->SendMessageToSet(&data, true);
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
