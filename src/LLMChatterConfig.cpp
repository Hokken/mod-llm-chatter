/*
 * mod-llm-chatter - Dynamic bot conversations powered by AI
 * Configuration implementation
 */

#include "LLMChatterConfig.h"
#include "Config.h"
#include "Log.h"
#include "SharedDefines.h"

#include <algorithm>
#include <array>
#include <cctype>
#include <limits>
#include <memory>
#include <sstream>
#include <unordered_set>

namespace
{
template <typename T>
T GetChatterOption(std::string const& name, T const& def)
{
    return sConfigMgr->GetOption<T>(name, def, false);
}

char ToLowerAscii(unsigned char value)
{
    if (value >= 'A' && value <= 'Z')
        return static_cast<char>(value + ('a' - 'A'));
    return static_cast<char>(value);
}

std::unordered_set<uint32> ParseCreatureEntrySet(
    std::string const& configured,
    std::string const& optionName)
{
    std::unordered_set<uint32> entries;
    std::istringstream input(configured);
    std::string token;
    while (std::getline(input, token, ','))
    {
        auto first = std::find_if_not(
            token.begin(), token.end(),
            [](unsigned char value)
            {
                return std::isspace(value) != 0;
            });
        auto last = std::find_if_not(
            token.rbegin(), token.rend(),
            [](unsigned char value)
            {
                return std::isspace(value) != 0;
            }).base();
        token = first < last
            ? std::string(first, last) : std::string();
        if (token.empty())
            continue;

        bool valid = false;
        bool digitsOnly = std::all_of(
            token.begin(), token.end(),
            [](unsigned char value)
            {
                return std::isdigit(value) != 0;
            });
        try
        {
            unsigned long value = digitsOnly
                ? std::stoul(token) : 0;
            if (digitsOnly && value > 0
                && value <= std::numeric_limits<uint32>::max())
            {
                entries.insert(static_cast<uint32>(value));
                valid = true;
            }
        }
        catch (...)
        {
            // Report below while preserving every valid token.
        }

        if (!valid)
        {
            LOG_WARN(
                "module",
                "LLMChatter: ignoring invalid creature entry "
                "'{}' in {}",
                token, optionName);
        }
    }
    return entries;
}

template <size_t Size>
std::array<uint32, Size> ParseDirectedReactorWeights(
    std::string const& configured,
    std::array<uint32, Size> const& defaults,
    char const* optionName,
    char const* defaultText)
{
    std::array<uint32, Size> weights = {};
    std::istringstream input(configured);
    std::string token;
    size_t index = 0;
    bool valid = true;

    while (std::getline(input, token, ','))
    {
        if (index >= weights.size())
        {
            valid = false;
            break;
        }

        token.erase(
            token.begin(),
            std::find_if_not(
                token.begin(), token.end(),
                [](unsigned char value)
                {
                    return std::isspace(value) != 0;
                }));
        token.erase(
            std::find_if_not(
                token.rbegin(), token.rend(),
                [](unsigned char value)
                {
                    return std::isspace(value) != 0;
                }).base(),
            token.end());

        try
        {
            size_t parsed = 0;
            unsigned long value = std::stoul(token, &parsed);
            if (parsed != token.size() || value > 100)
            {
                valid = false;
                break;
            }
            weights[index++] = static_cast<uint32>(value);
        }
        catch (...)
        {
            valid = false;
            break;
        }
    }

    uint32 total = 0;
    bool descending = valid && index == weights.size();
    for (size_t i = 0; i < weights.size(); ++i)
    {
        total += weights[i];
        if (i > 0 && weights[i - 1] <= weights[i])
            descending = false;
    }
    descending = descending && total == 100;
    if (!descending)
    {
        LOG_WARN(
            "module",
            "LLMChatter: {} must contain {} strictly descending "
            "percentages totaling 100; using {}",
            optionName, weights.size(), defaultText);
        return defaults;
    }

    return weights;
}

std::unordered_set<std::string> ParseLowerWordSet(
    std::string const& configured)
{
    std::unordered_set<std::string> words;
    std::istringstream input(configured);
    std::string token;
    while (std::getline(input, token, ','))
    {
        token.erase(
            token.begin(),
            std::find_if_not(
                token.begin(), token.end(),
                [](unsigned char value)
                {
                    return std::isspace(value) != 0;
                }));
        token.erase(
            std::find_if_not(
                token.rbegin(), token.rend(),
                [](unsigned char value)
                {
                    return std::isspace(value) != 0;
                }).base(),
            token.end());
        std::transform(
            token.begin(), token.end(), token.begin(),
            [](unsigned char value)
            {
                return static_cast<char>(std::tolower(value));
            });
        if (!token.empty())
            words.insert(token);
    }
    return words;
}

bool ContainsCreatureEntry(
    std::shared_ptr<std::unordered_set<uint32> const> const& configured,
    uint32 creatureEntry)
{
    // GCC 11 supports shared_ptr atomic functions, but not atomic<shared_ptr>.
    auto entries = std::atomic_load(&configured);
    return creatureEntry > 0 && entries
        && entries->count(creatureEntry) > 0;
}
}

bool LLMChatterConfig::IsProximitySpeakerAllowed(
    uint32 creatureEntry) const
{
    return ContainsCreatureEntry(
        _proxSpeakerAllowEntries, creatureEntry);
}

bool LLMChatterConfig::IsProximitySpeakerDenied(
    uint32 creatureEntry) const
{
    return ContainsCreatureEntry(
        _proxSpeakerDenyEntries, creatureEntry);
}

bool LLMChatterConfig::IsProximityBossSpeakerDenied(
    uint32 creatureEntry) const
{
    return ContainsCreatureEntry(
        _proxBossSpeakerDenyEntries, creatureEntry);
}

bool LLMChatterConfig::IsDirectedNameStopword(
    std::string const& word) const
{
    auto words = std::atomic_load(
        &_proxDirectedNameStopwords);
    return words && words->count(word) > 0;
}

bool LLMChatterConfig::IsCxxScriptedEmoteEntry(
    uint32 creatureEntry) const
{
    return ContainsCreatureEntry(
        _emoteCxxScriptExclusionEntries,
        creatureEntry);
}

bool LLMChatterConfig::IsPlayerChatPrefixIgnored(
    std::string const& message) const
{
    auto prefixes = std::atomic_load(
        &_playerChatIgnoredPrefixes);
    if (!prefixes || prefixes->empty())
        return false;

    size_t start = message.find_first_not_of(
        " \t\n\r\f\v");
    if (start == std::string::npos)
        return false;

    for (std::string const& prefix : *prefixes)
    {
        if (message.size() - start < prefix.size())
            continue;

        bool matches = true;
        for (size_t index = 0;
             index < prefix.size(); ++index)
        {
            unsigned char value = static_cast<unsigned char>(
                message[start + index]);
            if (ToLowerAscii(value) != prefix[index])
            {
                matches = false;
                break;
            }
        }

        if (matches)
            return true;
    }

    return false;
}

void LLMChatterConfig::LoadConfig()
{
    _enabled = GetChatterOption<bool>("LLMChatter.Enable", false);
    _debugLog = GetChatterOption<bool>("LLMChatter.DebugLog", false);

    // General settings
    _triggerIntervalSeconds = GetChatterOption<uint32>("LLMChatter.TriggerIntervalSeconds", 60);
    _conversationChance = GetChatterOption<uint32>(
        "LLMChatter.ConversationChance", 40);
    _triggerChance = GetChatterOption<uint32>("LLMChatter.TriggerChance", 15);
    _ambientNpcGossipChance = GetChatterOption<uint32>(
        "LLMChatter.AmbientNpcGossipChance", 5);
    _ambientBotGossipChance = GetChatterOption<uint32>(
        "LLMChatter.AmbientBotGossipChance", 5);
    _ambientTradeQualityWeightBonus = std::min<uint32>(
        GetChatterOption<uint32>(
            "LLMChatter.AmbientTrade.QualityWeightBonus", 4),
        100);
    _cityChatterMultiplier = GetChatterOption<uint32>("LLMChatter.CityChatterMultiplier", 2);
    _maxPendingRequests = GetChatterOption<uint32>("LLMChatter.MaxPendingRequests", 5);
    _maxBotsPerZone = GetChatterOption<uint32>(
        "LLMChatter.MaxBotsPerZone", 8);
    _maxMessageLength = GetChatterOption<uint32>(
        "LLMChatter.MaxMessageLength", 250);
    std::string playerChatIgnoredPrefixes =
        GetChatterOption<std::string>(
            "LLMChatter.PlayerChat.IgnoredPrefixes", "");
    auto parsedPlayerChatIgnoredPrefixes =
        std::make_shared<std::unordered_set<std::string> const>(
            ParseLowerWordSet(playerChatIgnoredPrefixes));
    std::atomic_store(
        &_playerChatIgnoredPrefixes,
        std::move(parsedPlayerChatIgnoredPrefixes));

    // Delivery settings
    _deliveryPollMs = GetChatterOption<uint32>("LLMChatter.DeliveryPollMs", 1000);
    _messageDelayMin = GetChatterOption<uint32>("LLMChatter.MessageDelayMin", 1000);
    _messageDelayMax = GetChatterOption<uint32>("LLMChatter.MessageDelayMax", 30000);
    _partyGateEnable =
        GetChatterOption<bool>(
            "LLMChatter.PartyGate.Enable", true);
    _partyGateFillerMinGapSeconds =
        GetChatterOption<uint32>(
            "LLMChatter.PartyGate."
            "FillerMinGapSeconds", 8);
    _partyGateContextualMinGapSeconds =
        GetChatterOption<uint32>(
            "LLMChatter.PartyGate."
            "ContextualMinGapSeconds", 6);
    _partyGateResponsiveMinGapSeconds =
        GetChatterOption<uint32>(
            "LLMChatter.PartyGate."
            "ResponsiveMinGapSeconds", 2);
    _partyGateUrgentMinGapSeconds =
        GetChatterOption<uint32>(
            "LLMChatter.PartyGate."
            "UrgentMinGapSeconds", 0);

    // Event system settings
    _useEventSystem = GetChatterOption<bool>("LLMChatter.UseEventSystem", true);
    _prioritySystemEnable =
        GetChatterOption<bool>(
            "LLMChatter.PrioritySystem.Enable", true);
    _priorityDeliveryOrderEnable =
        GetChatterOption<bool>(
            "LLMChatter.PrioritySystem."
            "DeliveryOrderEnable", true);
    _environmentCheckSeconds = GetChatterOption<uint32>("LLMChatter.EnvironmentCheckSeconds", 60);
    _eventReactionChance = GetChatterOption<uint32>("LLMChatter.EventReactionChance", 15);
    _transportEventChance = GetChatterOption<uint32>("LLMChatter.TransportEventChance", 0);
    _weatherAmbientChance = GetChatterOption<uint32>("LLMChatter.WeatherAmbientChance", 0);
    _transportCooldownSeconds = GetChatterOption<uint32>("LLMChatter.TransportCooldownSeconds", 600);
    _transportCheckSeconds = GetChatterOption<uint32>("LLMChatter.TransportCheckSeconds", 5);
    _eventExpirationSeconds = GetChatterOption<uint32>("LLMChatter.EventExpirationSeconds", 600);
    _weatherCooldownSeconds = GetChatterOption<uint32>("LLMChatter.WeatherCooldownSeconds", 1800);
    _weatherAmbientCooldownSeconds =
        GetChatterOption<uint32>(
            "LLMChatter."
            "WeatherAmbientCooldownSeconds",
            120);
    _dayNightCooldownSeconds = GetChatterOption<uint32>("LLMChatter.DayNightCooldownSeconds", 7200);
    _holidayCooldownSeconds = GetChatterOption<uint32>("LLMChatter.HolidayCooldownSeconds", 1800);
    _holidayCityChance = GetChatterOption<uint32>("LLMChatter.HolidayCityChance", 10);
    _holidayZoneChance = GetChatterOption<uint32>("LLMChatter.HolidayZoneChance", 5);
    _botSpeakerCooldownSeconds = GetChatterOption<uint32>("LLMChatter.BotSpeakerCooldownSeconds", 900);
    _zoneFatigueThreshold = GetChatterOption<uint32>("LLMChatter.ZoneFatigueThreshold", 3);
    _zoneFatigueCooldownSeconds = GetChatterOption<uint32>("LLMChatter.ZoneFatigueCooldownSeconds", 900);
    _priorityReactRangeCriticalMin =
        GetChatterOption<uint32>(
            "LLMChatter.PrioritySystem.ReactRange."
            "CriticalMin", 0);
    _priorityReactRangeCriticalMax =
        GetChatterOption<uint32>(
            "LLMChatter.PrioritySystem.ReactRange."
            "CriticalMax", 1);
    _priorityReactRangeHighMin =
        GetChatterOption<uint32>(
            "LLMChatter.PrioritySystem.ReactRange."
            "HighMin", 0);
    _priorityReactRangeHighMax =
        GetChatterOption<uint32>(
            "LLMChatter.PrioritySystem.ReactRange."
            "HighMax", 2);
    _priorityReactRangeNormalMin =
        GetChatterOption<uint32>(
            "LLMChatter.PrioritySystem.ReactRange."
            "NormalMin", 2);
    _priorityReactRangeNormalMax =
        GetChatterOption<uint32>(
            "LLMChatter.PrioritySystem.ReactRange."
            "NormalMax", 5);
    _priorityReactRangeFillerMin =
        GetChatterOption<uint32>(
            "LLMChatter.PrioritySystem.ReactRange."
            "FillerMin", 5);
    _priorityReactRangeFillerMax =
        GetChatterOption<uint32>(
            "LLMChatter.PrioritySystem.ReactRange."
            "FillerMax", 15);
    auto clampRange =
        [](uint32& minValue, uint32& maxValue,
           char const* rangeName)
        {
            if (minValue > maxValue)
            {
                minValue = maxValue;
            }
        };
    clampRange(
        _priorityReactRangeCriticalMin,
        _priorityReactRangeCriticalMax,
        "PrioritySystem.ReactRange.Critical");
    clampRange(
        _priorityReactRangeHighMin,
        _priorityReactRangeHighMax,
        "PrioritySystem.ReactRange.High");
    clampRange(
        _priorityReactRangeNormalMin,
        _priorityReactRangeNormalMax,
        "PrioritySystem.ReactRange.Normal");
    clampRange(
        _priorityReactRangeFillerMin,
        _priorityReactRangeFillerMax,
        "PrioritySystem.ReactRange.Filler");

    // Event type toggles (only safe, low-frequency events)
    _eventsHolidays = GetChatterOption<bool>("LLMChatter.Events.Holidays", true);
    _eventsDayNight = GetChatterOption<bool>("LLMChatter.Events.DayNight", true);
    _eventsWeather = GetChatterOption<bool>("LLMChatter.Events.Weather", true);
    _eventsTransports = GetChatterOption<bool>("LLMChatter.Events.Transports", true);
    _eventsMinor = GetChatterOption<bool>("LLMChatter.Events.MinorEvents", true);
    _minorEventChance = GetChatterOption<uint32>("LLMChatter.Events.MinorEventChance", 20);

    // Group chatter
    _useGroupChatter = GetChatterOption<bool>(
        "LLMChatter.GroupChatter.Enable", true);
    _questDeduplicationWindow =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "QuestDeduplicationWindow", 30);
    _combatStateCheckInterval =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "CombatStateCheckInterval", 5);
    _lowHealthThreshold =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "LowHealthThreshold", 40);
    _oomThreshold =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "OOMThreshold", 30);

    // Group chatter - reaction chances (0-100)
    _groupKillChanceNormal = GetChatterOption<uint32>("LLMChatter.GroupChatter.KillChanceNormal", 20);
    _groupDeathChance = GetChatterOption<uint32>("LLMChatter.GroupChatter.DeathChance", 40);
    _groupLootChanceGreen = GetChatterOption<uint32>("LLMChatter.GroupChatter.LootChanceGreen", 20);
    _groupLootChanceBlue = GetChatterOption<uint32>("LLMChatter.GroupChatter.LootChanceBlue", 60);
    _groupLootChancePurple =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "LootChancePurple", 100);
    _groupLootChanceOrange =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "LootChanceOrange", 100);
    _groupQuestObjectiveChance = GetChatterOption<uint32>("LLMChatter.GroupChatter.QuestObjectiveChance", 100);
    _groupQuestCompleteChance = GetChatterOption<uint32>("LLMChatter.GroupChatter.QuestCompleteChance", 100);
    _groupQuestObjectiveCooldown = GetChatterOption<uint32>("LLMChatter.GroupChatter.QuestObjectiveCooldown", 30);
    _groupQuestAcceptChance = GetChatterOption<uint32>("LLMChatter.GroupChatter.QuestAcceptChance", 100);
    _groupQuestAcceptCooldown = GetChatterOption<uint32>("LLMChatter.GroupChatter.QuestAcceptCooldown", 30);
    _groupQuestAcceptDebounceSec = GetChatterOption<uint32>("LLMChatter.GroupChatter.QuestAcceptDebounceSec", 5);
    _groupSpellCastChance = GetChatterOption<uint32>("LLMChatter.GroupChatter.SpellCastChance", 10);
    _groupSpellCastCooldown = GetChatterOption<uint32>("LLMChatter.GroupChatter.SpellCastCooldown", 10);
    _groupJoinDebounceSec =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "JoinDebounceSec", 6);

    // Group chatter - per-event cooldowns (seconds)
    _groupKillCooldown = GetChatterOption<uint32>("LLMChatter.GroupChatter.KillCooldown", 120);
    _groupDeathCooldown = GetChatterOption<uint32>("LLMChatter.GroupChatter.DeathCooldown", 30);
    _groupLootCooldown = GetChatterOption<uint32>("LLMChatter.GroupChatter.LootCooldown", 60);
    _groupPlayerMsgCooldown = GetChatterOption<uint32>("LLMChatter.GroupChatter.PlayerMsgCooldown", 0);

    // Group chatter - new event settings
    _groupResurrectChance = GetChatterOption<uint32>("LLMChatter.GroupChatter.ResurrectChance", 100);
    _groupResurrectCooldown = GetChatterOption<uint32>("LLMChatter.GroupChatter.ResurrectCooldown", 30);
    _groupZoneChance = GetChatterOption<uint32>("LLMChatter.GroupChatter.ZoneTransitionChance", 30);
    _groupZoneCooldown = GetChatterOption<uint32>("LLMChatter.GroupChatter.ZoneTransitionCooldown", 120);
    _groupDungeonChance = GetChatterOption<uint32>("LLMChatter.GroupChatter.DungeonEntryChance", 100);
    _groupDungeonCooldown = GetChatterOption<uint32>("LLMChatter.GroupChatter.DungeonEntryCooldown", 300);
    _groupWipeChance = GetChatterOption<uint32>("LLMChatter.GroupChatter.WipeChance", 100);
    _groupWipeCooldown = GetChatterOption<uint32>("LLMChatter.GroupChatter.WipeCooldown", 120);
    _groupCorpseRunChance = GetChatterOption<uint32>("LLMChatter.GroupChatter.CorpseRunChance", 80);
    _groupCorpseRunCooldown = GetChatterOption<uint32>("LLMChatter.GroupChatter.CorpseRunCooldown", 120);
    _useFarewell = GetChatterOption<bool>(
        "LLMChatter.GroupChatter.FarewellEnable", true);


    // Group chatter - react-after delays (seconds)
    _reactDelayJoin =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "ReactDelay.Join", 3);
    _reactDelayJoinBatch =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "ReactDelay.JoinBatch", 0);
    _reactDelayKill =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "ReactDelay.Kill", 2);
    _reactDelayWipe =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "ReactDelay.Wipe", 3);
    _reactDelayDeath =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "ReactDelay.Death", 2);
    _reactDelayLoot =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "ReactDelay.Loot", 3);
    _reactDelayCombat =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "ReactDelay.Combat", 1);
    _reactDelayPlayerMsg =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "ReactDelay.PlayerMsg", 0);
    _reactDelayLevelUp =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "ReactDelay.LevelUp", 2);
    _reactDelayQuestObjectives =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "ReactDelay.QuestObjectives", 2);
    _reactDelayQuestComplete =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "ReactDelay.QuestComplete", 2);
    _reactDelayAchievement =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "ReactDelay.Achievement", 2);
    _reactDelaySpellCast =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "ReactDelay.SpellCast", 2);
    _reactDelayResurrect =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "ReactDelay.Resurrect", 3);
    _reactDelayCorpseRun =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "ReactDelay.CorpseRun", 5);
    _reactDelayDungeonEntry =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "ReactDelay.DungeonEntry", 5);
    _reactDelayZoneTransition =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "ReactDelay.ZoneTransition", 5);
    _reactDelayStateCallout =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "ReactDelay.StateCallout", 1);

    _reactDelayNearbyObject =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "ReactDelay.NearbyObject", 2);
    _reactDelayBGEvent =
        GetChatterOption<uint32>(
            "LLMChatter.BGChatter."
            "ReactDelay", 2);
    _reactDelayGeneralMsg =
        GetChatterOption<uint32>(
            "LLMChatter.GeneralChat."
            "ReactDelay", 5);
    _reactDelayEmote =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "EmoteReactDelay", 2);

    // Group chatter - combat engagement chances
    _combatChanceBoss =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "CombatChance.Boss", 100);
    _combatChanceElite =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "CombatChance.Elite", 40);
    _combatChanceNormal =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "CombatChance.Normal", 15);

    // Group chatter - quest objective suppression
    _questObjSuppressWindow =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "QuestObjSuppressWindow", 10);

    // Group chatter - wipe detection
    _wipeMinGroupSize =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "WipeMinGroupSize", 2);

    // GetReactionDelaySeconds ranges
    _reactRangeDayNightMin =
        GetChatterOption<uint32>(
            "LLMChatter.ReactRange."
            "DayNightMin", 120);
    _reactRangeDayNightMax =
        GetChatterOption<uint32>(
            "LLMChatter.ReactRange."
            "DayNightMax", 600);
    _reactRangeHolidayMin =
        GetChatterOption<uint32>(
            "LLMChatter.ReactRange."
            "HolidayMin", 300);
    _reactRangeHolidayMax =
        GetChatterOption<uint32>(
            "LLMChatter.ReactRange."
            "HolidayMax", 900);
    _reactRangeWeatherMin =
        GetChatterOption<uint32>(
            "LLMChatter.ReactRange."
            "WeatherMin", 60);
    _reactRangeWeatherMax =
        GetChatterOption<uint32>(
            "LLMChatter.ReactRange."
            "WeatherMax", 300);
    _reactRangeWeatherAmbientMin =
        GetChatterOption<uint32>(
            "LLMChatter.ReactRange."
            "WeatherAmbientMin", 120);
    _reactRangeWeatherAmbientMax =
        GetChatterOption<uint32>(
            "LLMChatter.ReactRange."
            "WeatherAmbientMax", 600);
    _reactRangeTransportMin =
        GetChatterOption<uint32>(
            "LLMChatter.ReactRange."
            "TransportMin", 5);
    _reactRangeTransportMax =
        GetChatterOption<uint32>(
            "LLMChatter.ReactRange."
            "TransportMax", 15);
    _reactRangeQuestAcceptMin =
        GetChatterOption<uint32>(
            "LLMChatter.ReactRange."
            "QuestAcceptMin", 5);
    _reactRangeQuestAcceptMax =
        GetChatterOption<uint32>(
            "LLMChatter.ReactRange."
            "QuestAcceptMax", 15);
    _reactRangeDefaultMin =
        GetChatterOption<uint32>(
            "LLMChatter.ReactRange."
            "DefaultMin", 30);
    _reactRangeDefaultMax =
        GetChatterOption<uint32>(
            "LLMChatter.ReactRange."
            "DefaultMax", 120);

    // Group chatter - nearby object scan
    _nearbyObjectEnable =
        GetChatterOption<bool>(
            "LLMChatter.GroupChatter."
            "NearbyObjectEnable", true);
    _nearbyObjectCheckInterval =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "NearbyObjectCheckInterval", 45);
    _nearbyObjectChance =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "NearbyObjectChance", 30);
    _nearbyObjectCooldown =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "NearbyObjectCooldown", 180);
    _nearbyObjectScanRadius =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "NearbyObjectScanRadius", 22);
    _nearbyObjectNameCooldown =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "NearbyObjectNameCooldown", 900);
    _nearbyObjectMaxObjects =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "NearbyObjectMaxObjects", 3);
    _facingEnable =
        GetChatterOption<bool>(
            "LLMChatter.GroupChatter."
            "FacingEnable", true);

    // Group chatter - state-triggered callouts
    _stateCalloutEnabled = GetChatterOption<bool>(
        "LLMChatter.GroupChatter.StateCalloutEnable",
        true);
    _stateCalloutLowHealth = GetChatterOption<bool>(
        "LLMChatter.GroupChatter.StateCalloutLowHealth",
        true);
    _stateCalloutOom = GetChatterOption<bool>(
        "LLMChatter.GroupChatter.StateCalloutOom",
        true);
    _stateCalloutAggro = GetChatterOption<bool>(
        "LLMChatter.GroupChatter.StateCalloutAggro",
        true);
    _stateCalloutChance =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "StateCalloutChance", 60);
    _stateCalloutCooldown =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "StateCalloutCooldown", 60);

    // Pre-cached instant reactions
    _preCacheEnable = GetChatterOption<bool>(
        "LLMChatter.GroupChatter.PreCacheEnable",
        true);
    _preCacheCombatEnable = GetChatterOption<bool>(
        "LLMChatter.GroupChatter.PreCacheCombatEnable",
        true);
    _preCacheStateEnable = GetChatterOption<bool>(
        "LLMChatter.GroupChatter.PreCacheStateEnable",
        true);
    _preCacheSpellEnable = GetChatterOption<bool>(
        "LLMChatter.GroupChatter.PreCacheSpellEnable",
        true);
    _preCacheDepthCombat =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "PreCacheDepthCombat", 2);
    _preCacheDepthState =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "PreCacheDepthState", 2);
    _preCacheDepthSpell =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "PreCacheDepthSpell", 2);
    _preCacheTTLSeconds =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "PreCacheTTLSeconds", 3600);
    _preCacheGeneratePerLoop =
        GetChatterOption<uint32>(
            "LLMChatter.GroupChatter."
            "PreCacheGeneratePerLoop", 3);
    _preCacheFallbackToLive =
        GetChatterOption<bool>(
            "LLMChatter.GroupChatter."
            "PreCacheFallbackToLive", true);

    // General channel master toggle — one switch to disable all
    // General-channel chatter (ambient, world events, player replies)
    _generalChannelEnable = GetChatterOption<bool>(
        "LLMChatter.GeneralChannel.Enable", true);

    // General chat reactions
    _useGeneralChatReact = GetChatterOption<bool>(
        "LLMChatter.GeneralChat.PlayerReplyEnable", true);
    _generalChatChance = GetChatterOption<uint32>(
        "LLMChatter.GeneralChat.ReactionChance", 100);
    _generalChatQuestionChance = GetChatterOption<uint32>(
        "LLMChatter.GeneralChat.QuestionChance", 100);
    _generalChatCooldown = GetChatterOption<uint32>(
        "LLMChatter.GeneralChat.Cooldown", 0);
    _generalChatConversationChance = GetChatterOption<uint32>(
        "LLMChatter.GeneralChat.ConversationChance", 30);
    _generalChatHistoryLimit =
        GetChatterOption<uint32>(
            "LLMChatter.GeneralChat.HistoryLimit",
            15);

    _generalLootEnable = GetChatterOption<bool>(
        "LLMChatter.GeneralLoot.Enable", true);
    _generalLootAggregationDelayMs = std::max<uint32>(
        100,
        GetChatterOption<uint32>(
            "LLMChatter.GeneralLoot."
            "AggregationDelayMilliseconds",
            2500));
    _generalLootZoneCooldownSeconds =
        GetChatterOption<uint32>(
            "LLMChatter.GeneralLoot.ZoneCooldownSeconds",
            180);
    _generalLootMinQuality = std::min<uint32>(
        GetChatterOption<uint32>(
            "LLMChatter.GeneralLoot.MinQuality", 2),
        MAX_ITEM_QUALITY - 1);

    // RP enrichment
    _raceLoreChance = GetChatterOption<uint32>("LLMChatter.RaceLoreChance", 20);

    // Battleground chatter
    _bgChatterEnable = GetChatterOption<bool>(
        "LLMChatter.BGChatter.Enable", true);
    _bgMatchStartChance = GetChatterOption<uint32>(
        "LLMChatter.BGChatter.MatchStartChance", 100);
    _bgNodeEventChance = GetChatterOption<uint32>(
        "LLMChatter.BGChatter.NodeEventChance", 80);
    _bgScoreMilestoneChance =
        GetChatterOption<uint32>(
            "LLMChatter.BGChatter."
            "ScoreMilestoneChance", 80);
    _bgRaidWorkerChance = GetChatterOption<uint32>(
        "LLMChatter.BGChatter.RaidWorkerChance", 30);
    _bgStatePollingIntervalMs =
        GetChatterOption<uint32>(
            "LLMChatter.BGChatter."
            "StatePollingIntervalMs", 3000);
    _bgBigEventCooldownSec =
        GetChatterOption<uint32>(
            "LLMChatter.BGChatter."
            "BigEventCooldownSec", 15);
    _bgIdleChatterChance =
        GetChatterOption<uint32>(
            "LLMChatter.BGChatter."
            "IdleChatterChance", 25);
    _bgIdleChatterCooldownSec =
        GetChatterOption<uint32>(
            "LLMChatter.BGChatter."
            "IdleChatterCooldownSec", 30);
    _bgRezChance =
        GetChatterOption<uint32>(
            "LLMChatter.BGChatter."
            "RezChance", 20);

    // Raid chatter (PvE)
    _raidChatterEnable = GetChatterOption<bool>(
        "LLMChatter.RaidChatter.Enable", true);
    _raidBossPullChance =
        GetChatterOption<uint32>(
            "LLMChatter.RaidChatter."
            "BossPullChance", 80);
    _raidBossKillChance =
        GetChatterOption<uint32>(
            "LLMChatter.RaidChatter."
            "BossKillChance", 100);
    _raidBossWipeChance =
        GetChatterOption<uint32>(
            "LLMChatter.RaidChatter."
            "BossWipeChance", 100);
    _raidMoraleEnable =
        GetChatterOption<bool>(
            "LLMChatter.RaidChatter."
            "MoraleEnable", true);
    _raidMoraleChance =
        GetChatterOption<uint32>(
            "LLMChatter.RaidChatter."
            "MoraleChance", 15);
    _raidMoraleCooldown =
        GetChatterOption<uint32>(
            "LLMChatter.RaidChatter."
            "MoraleCooldown", 120);

    // Guild chatter (ambient guild-channel banter)
    _guildChatterEnable = GetChatterOption<bool>(
        "LLMChatter.GuildChatter.Enable", true);
    _guildChatterChance =
        GetChatterOption<uint32>(
            "LLMChatter.GuildChatter."
            "Chance", 15);
    _guildChatterCooldown =
        GetChatterOption<uint32>(
            "LLMChatter.GuildChatter."
            "Cooldown", 300);
    _guildChatterScanInterval =
        GetChatterOption<uint32>(
            "LLMChatter.GuildChatter."
            "ScanInterval", 30);
    _guildChatterConversationChance =
        std::min(
            GetChatterOption<uint32>(
                "LLMChatter.GuildChatter."
                "ConversationChance", 50),
            100u);
    _guildChatterMaxParticipants =
        std::max(
            2u,
            std::min(
                GetChatterOption<uint32>(
                    "LLMChatter.GuildChatter."
                    "MaxParticipants", 3),
                3u));
    _guildPlayerRepliesEnable =
        GetChatterOption<bool>(
            "LLMChatter.GuildChatter."
            "PlayerReplies.Enable", true);
    _guildPlayerReplyDebounceSeconds =
        std::min(
            GetChatterOption<uint32>(
                "LLMChatter.GuildChatter."
                "PlayerReplies.DebounceSeconds", 1),
            10u);
    _guildPlayerIdleSuppressionSeconds =
        GetChatterOption<uint32>(
            "LLMChatter.GuildChatter."
            "PlayerReplies.IdleSuppressionSeconds",
            90);
    _guildPlayerReplyMaxCandidates =
        std::max(
            1u,
            std::min(
                GetChatterOption<uint32>(
                    "LLMChatter.GuildChatter."
                    "PlayerReplies.MaxCandidates", 12),
                30u));
    _guildLoginGreetingEnable =
        GetChatterOption<bool>(
            "LLMChatter.GuildChatter."
            "LoginGreeting.Enable", true);
    _guildLoginGreetingChance =
        std::min(
            GetChatterOption<uint32>(
                "LLMChatter.GuildChatter."
                "LoginGreeting.Chance", 100),
            100u);
    _guildLoginGreetingQuickChance =
        std::min(
            GetChatterOption<uint32>(
                "LLMChatter.GuildChatter."
                "LoginGreeting.QuickChance", 20),
            100u);
    _guildLoginGreetingBusyChance =
        std::min(
            GetChatterOption<uint32>(
                "LLMChatter.GuildChatter."
                "LoginGreeting.BusyChance", 25),
            100u - _guildLoginGreetingQuickChance);
    _guildLoginGreetingRetryInterval =
        std::max(
            1u,
            GetChatterOption<uint32>(
                "LLMChatter.GuildChatter."
                "LoginGreeting.RetryInterval", 5));
    _guildLoginGreetingReadinessTimeout =
        std::max(
            45u,
            std::max(
                _guildLoginGreetingRetryInterval,
                GetChatterOption<uint32>(
                    "LLMChatter.GuildChatter."
                    "LoginGreeting.ReadinessTimeout",
                    90)));
    _guildLoginGreetingMaxCandidates =
        std::max(
            1u,
            std::min(
                GetChatterOption<uint32>(
                    "LLMChatter.GuildChatter."
                    "LoginGreeting.MaxCandidates", 12),
                30u));

    // Zone intrusion alerts
    _zoneIntrusionEnable =
        GetChatterOption<bool>(
            "LLMChatter.ZoneIntrusion.Enable",
            true);
    _zoneIntrusionZoneThrottleSec =
        GetChatterOption<uint32>(
            "LLMChatter.ZoneIntrusion."
            "ZoneThrottleSec", 30);

    // Proximity chatter
    _proxChatterEnable =
        GetChatterOption<bool>(
            "LLMChatter.ProximityChatter.Enable",
            true);
    _proxChatterEnableInDungeons =
        GetChatterOption<bool>(
            "LLMChatter.ProximityChatter."
            "EnableInDungeons", true);
    _proxChatterEnableInRaids =
        GetChatterOption<bool>(
            "LLMChatter.ProximityChatter."
            "EnableInRaids", true);
    _proxChatterScanInterval =
        GetChatterOption<uint32>(
            "LLMChatter.ProximityChatter."
            "ScanIntervalSeconds", 30);
    _proxChatterOutdoorScanInterval =
        GetChatterOption<uint32>(
            "LLMChatter.ProximityChatter."
            "OutdoorScanIntervalSeconds",
            _proxChatterScanInterval);
    _proxChatterInstanceScanInterval =
        GetChatterOption<uint32>(
            "LLMChatter.ProximityChatter."
            "InstanceScanIntervalSeconds",
            _proxChatterScanInterval);
    _proxChatterScanRadius =
        GetChatterOption<uint32>(
            "LLMChatter.ProximityChatter."
            "ScanRadius", 40);
    _proxChatterPlayerSayScanRadius =
        GetChatterOption<uint32>(
            "LLMChatter.ProximityChatter."
            "PlayerSayScanRadius", 40);
    _proxChatterChance =
        GetChatterOption<uint32>(
            "LLMChatter.ProximityChatter."
            "Chance", 30);
    _proxChatterOutdoorChance =
        GetChatterOption<uint32>(
            "LLMChatter.ProximityChatter."
            "OutdoorChance", _proxChatterChance);
    _proxChatterInstanceChance =
        GetChatterOption<uint32>(
            "LLMChatter.ProximityChatter."
            "InstanceChance", _proxChatterChance);
    _proxChatterEntityCooldown =
        std::min(
            GetChatterOption<uint32>(
                "LLMChatter.ProximityChatter."
                "EntityCooldown", 1),
            3u);
    _proxChatterZoneFatigueThreshold =
        GetChatterOption<uint32>(
            "LLMChatter.ProximityChatter."
            "ZoneFatigueThreshold", 3);
    _proxChatterZoneFatigueDecay =
        GetChatterOption<uint32>(
            "LLMChatter.ProximityChatter."
            "ZoneFatigueDecay", 20);
    _proxChatterConversationChance =
        GetChatterOption<uint32>(
            "LLMChatter.ProximityChatter."
            "ConversationChance", 40);
    _proxChatterPlayerAddressChance =
        GetChatterOption<uint32>(
            "LLMChatter.ProximityChatter."
            "PlayerAddressChance", 30);
    _proxChatterMaxConversationLines =
        GetChatterOption<uint32>(
            "LLMChatter.ProximityChatter."
            "MaxConversationLines", 4);
    _proxChatterConversationLineDelay =
        GetChatterOption<uint32>(
            "LLMChatter.ProximityChatter."
            "ConversationLineDelay", 2);
    _proxChatterReplyWindowSeconds =
        GetChatterOption<uint32>(
            "LLMChatter.ProximityChatter."
            "ReplyWindowSeconds", 30);
    _proxChatterReplyMaxTurns =
        GetChatterOption<uint32>(
            "LLMChatter.ProximityChatter."
            "ReplyMaxTurns", 5);
    _proxChatterMaxTokensPerLine =
        GetChatterOption<uint32>(
            "LLMChatter.ProximityChatter."
            "MaxTokensPerLine", 120);
    _proxChatterFacingResetDelay =
        GetChatterOption<uint32>(
            "LLMChatter.ProximityChatter."
            "FacingResetDelay", 8);
    _proxDirectedMaxExtraReactors =
        std::min(
            GetChatterOption<uint32>(
                "LLMChatter.ProximityChatter."
                "DirectedMaxExtraReactors", 2),
            2u);
    _proxDirectedBotMaxParticipants =
        std::clamp(
            GetChatterOption<uint32>(
                "LLMChatter.ProximityChatter."
                "DirectedBotMaxParticipants", 3),
            1u, 3u);
    _proxDirectedExtraReactorWeights =
        ParseDirectedReactorWeights(
            GetChatterOption<std::string>(
                "LLMChatter.ProximityChatter."
                "DirectedExtraReactorWeights",
                "60,30,10,0"),
            std::array<uint32, 4>{60, 30, 10, 0},
            "DirectedExtraReactorWeights",
            "60,30,10,0");
    _proxDirectedWitnessReactorWeights =
        ParseDirectedReactorWeights(
            GetChatterOption<std::string>(
                "LLMChatter.ProximityChatter."
                "DirectedWitnessReactorWeights",
                "70,30"),
            std::array<uint32, 2>{70, 30},
            "DirectedWitnessReactorWeights",
            "70,30");
    _proxDirectedNPCAsideChance =
        std::min(
            GetChatterOption<uint32>(
                "LLMChatter.ProximityChatter."
                "DirectedNPCAsideChance", 35),
            100u);
    _proxDirectedMaxLines =
        std::min(
            8u,
            std::max(
                1u,
                GetChatterOption<uint32>(
                    "LLMChatter.ProximityChatter."
                    "DirectedMaxLines", 5)));
    _proxDirectedExpirySeconds =
        std::max(
            1u,
            GetChatterOption<uint32>(
                "LLMChatter.ProximityChatter."
                "DirectedExpirySeconds", 30));
    std::string directedNameStopwords =
        GetChatterOption<std::string>(
            "LLMChatter.ProximityChatter."
            "DirectedNameStopwords",
            "guard,city,mountaineer,innkeeper,vendor,trainer,"
            "quartermaster,merchant,stablemaster,banker,auctioneer,"
            "flight,master,officer,captain,stormwind,ironforge,"
            "orgrimmar,darnassus,undercity,silvermoon,exodar");
    auto parsedDirectedNameStopwords =
        std::make_shared<std::unordered_set<std::string> const>(
            ParseLowerWordSet(directedNameStopwords));
    std::atomic_store(
        &_proxDirectedNameStopwords,
        std::move(parsedDirectedNameStopwords));
    std::string speakerAllowEntries =
        GetChatterOption<std::string>(
            "LLMChatter.ProximityChatter."
            "SpeakerAllowEntries", "");
    auto parsedSpeakerAllowEntries =
        std::make_shared<std::unordered_set<uint32> const>(
            ParseCreatureEntrySet(
                speakerAllowEntries,
                "SpeakerAllowEntries"));
    std::atomic_store(&_proxSpeakerAllowEntries,
        std::move(parsedSpeakerAllowEntries));
    std::string speakerDenyEntries =
        GetChatterOption<std::string>(
            "LLMChatter.ProximityChatter."
            "SpeakerDenyEntries", "");
    auto parsedSpeakerDenyEntries =
        std::make_shared<std::unordered_set<uint32> const>(
            ParseCreatureEntrySet(
                speakerDenyEntries,
                "SpeakerDenyEntries"));
    std::atomic_store(&_proxSpeakerDenyEntries,
        std::move(parsedSpeakerDenyEntries));
    _proxBossDialogueEnable =
        GetChatterOption<bool>(
            "LLMChatter.ProximityChatter."
            "EnableBossDialogue", false);
    _proxBossApproachCheckInterval =
        GetChatterOption<uint32>(
            "LLMChatter.ProximityChatter."
            "BossApproachCheckIntervalSeconds", 2);
    _proxBossApproachMaxRadius =
        GetChatterOption<uint32>(
            "LLMChatter.ProximityChatter."
            "BossApproachMaxRadius", 80);
    _proxBossAggroSafetyMargin =
        GetChatterOption<uint32>(
            "LLMChatter.ProximityChatter."
            "BossAggroSafetyMargin", 0);
    _proxBossInitialDelayMin =
        GetChatterOption<uint32>(
            "LLMChatter.ProximityChatter."
            "BossInitialDelayMinSeconds", 2);
    _proxBossInitialDelayMax =
        GetChatterOption<uint32>(
            "LLMChatter.ProximityChatter."
            "BossInitialDelayMaxSeconds", 6);
    _proxBossRepeatDelayMin =
        GetChatterOption<uint32>(
            "LLMChatter.ProximityChatter."
            "BossRepeatDelayMinSeconds", 20);
    _proxBossRepeatDelayMax =
        GetChatterOption<uint32>(
            "LLMChatter.ProximityChatter."
            "BossRepeatDelayMaxSeconds", 60);
    _proxBossRepeatChance =
        GetChatterOption<uint32>(
            "LLMChatter.ProximityChatter."
            "BossRepeatChance", 80);
    _proxBossRepeatChanceDecay =
        GetChatterOption<uint32>(
            "LLMChatter.ProximityChatter."
            "BossRepeatChanceDecayPercent", 50);
    _proxBossRepeatChanceFloor =
        GetChatterOption<uint32>(
            "LLMChatter.ProximityChatter."
            "BossRepeatChanceFloor", 10);
    _proxBossUnlimitedAutomaticLines =
        GetChatterOption<bool>(
            "LLMChatter.ProximityChatter."
            "BossUnlimitedAutomaticLines", true);
    _proxBossMaxAutomaticLines =
        GetChatterOption<uint32>(
            "LLMChatter.ProximityChatter."
            "BossMaxAutomaticLines", 3);
    _proxBossPresenceReset =
        GetChatterOption<uint32>(
            "LLMChatter.ProximityChatter."
            "BossPresenceResetSeconds", 90);
    _proxBossDirectedReplyCooldown =
        std::min(
            GetChatterOption<uint32>(
                "LLMChatter.ProximityChatter."
                "BossDirectedReplyCooldownSeconds", 1),
            3u);
    _proxBossDirectedScanCooldown =
        GetChatterOption<uint32>(
            "LLMChatter.ProximityChatter."
            "BossDirectedScanCooldownSeconds", 1);
    std::string bossSpeakerDenyEntries =
        GetChatterOption<std::string>(
            "LLMChatter.ProximityChatter."
            "BossSpeakerDenyEntries", "");
    auto parsedBossSpeakerDenyEntries =
        std::make_shared<std::unordered_set<uint32> const>(
            ParseCreatureEntrySet(
                bossSpeakerDenyEntries,
                "BossSpeakerDenyEntries"));
    std::atomic_store(&_proxBossSpeakerDenyEntries,
        std::move(parsedBossSpeakerDenyEntries));

    // Emote reaction system
    _emoteReactionsEnable =
        GetChatterOption<bool>(
            "LLMChatter.EmoteReactions.Enable",
            true);
    _emoteMirrorChance =
        std::min(
            GetChatterOption<uint32>(
                "LLMChatter.EmoteReactions."
                "MirrorChance", 80),
            100u);
    _emoteMirrorCooldown =
        GetChatterOption<uint32>(
            "LLMChatter.EmoteReactions."
            "MirrorCooldown", 15);
    _emoteReactionChance =
        std::min(
            GetChatterOption<uint32>(
                "LLMChatter.EmoteReactions."
                "ReactionChance", 80),
            100u);
    _emoteUngroupedBotMirrorChance =
        std::min(
            GetChatterOption<uint32>(
                "LLMChatter.EmoteReactions."
                "UngroupedBotMirrorChance", 80),
            100u);
    _emoteUngroupedBotVerbalReactionChance =
        std::min(
            GetChatterOption<uint32>(
                "LLMChatter.EmoteReactions."
                "UngroupedBotVerbalReactionChance", 80),
            100u);
    _emoteUngroupedBotWitnessReactionChance =
        std::min(
            GetChatterOption<uint32>(
                "LLMChatter.EmoteReactions."
                "UngroupedBotWitnessReactionChance", 50),
            100u);
    _emoteObserverChance =
        std::min(
            GetChatterOption<uint32>(
                "LLMChatter.EmoteReactions."
                "ObserverChance", 50),
            100u);
    _emoteObserverCooldown =
        GetChatterOption<uint32>(
            "LLMChatter.EmoteReactions."
            "ObserverCooldown", 30);
    _emoteMoodSpreadChance =
        GetChatterOption<uint32>(
            "LLMChatter.EmoteReactions."
            "MoodSpreadChance", 50);
    _emoteNPCMirrorEnable =
        GetChatterOption<bool>(
            "LLMChatter.EmoteReactions."
            "NPCMirrorEnable", true);
    _emoteNPCVerbalReactionChance =
        std::min(
            GetChatterOption<uint32>(
                "LLMChatter.EmoteReactions."
                "NPCVerbalReactionChance", 80),
            100u);
    _emoteNPCVerbalCooldown =
        std::min(
            GetChatterOption<uint32>(
                "LLMChatter.EmoteReactions."
                "NPCVerbalCooldown", 3),
            3u);
    std::string cxxScriptExclusionEntries =
        GetChatterOption<std::string>(
            "LLMChatter.EmoteReactions."
            "CxxScriptExclusionEntries",
            "620,25305,33211,33224,6626,7233,3401");
    auto parsedCxxScriptExclusionEntries =
        std::make_shared<std::unordered_set<uint32> const>(
            ParseCreatureEntrySet(
                cxxScriptExclusionEntries,
                "CxxScriptExclusionEntries"));
    std::atomic_store(
        &_emoteCxxScriptExclusionEntries,
        std::move(parsedCxxScriptExclusionEntries));

}
