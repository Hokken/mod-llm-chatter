/*
 * mod-llm-chatter - Dynamic bot conversations powered by AI
 * Configuration implementation
 */

#include "LLMChatterConfig.h"
#include "Config.h"
#include "Log.h"

namespace
{
template <typename T>
T GetChatterOption(std::string const& name, T const& def)
{
    return sConfigMgr->GetOption<T>(name, def, false);
}
}

void LLMChatterConfig::LoadConfig()
{
    _enabled = GetChatterOption<bool>("LLMChatter.Enable", false);
    _debugLog = GetChatterOption<bool>("LLMChatter.DebugLog", false);

    // General settings
    _triggerIntervalSeconds = GetChatterOption<uint32>("LLMChatter.TriggerIntervalSeconds", 60);
    _conversationChance = GetChatterOption<uint32>("LLMChatter.ConversationChance", 50);
    _triggerChance = GetChatterOption<uint32>("LLMChatter.TriggerChance", 15);
    _cityChatterMultiplier = GetChatterOption<uint32>("LLMChatter.CityChatterMultiplier", 2);
    _maxPendingRequests = GetChatterOption<uint32>("LLMChatter.MaxPendingRequests", 5);
    _maxBotsPerZone = GetChatterOption<uint32>(
        "LLMChatter.MaxBotsPerZone", 8);
    _maxMessageLength = GetChatterOption<uint32>(
        "LLMChatter.MaxMessageLength", 250);

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
    _groupLootChanceBlue = GetChatterOption<uint32>("LLMChatter.GroupChatter.LootChanceBlue", 50);
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
    _groupPlayerMsgCooldown = GetChatterOption<uint32>("LLMChatter.GroupChatter.PlayerMsgCooldown", 15);

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

    // General chat reactions
    _useGeneralChatReact = GetChatterOption<bool>(
        "LLMChatter.GeneralChat.Enable", true);
    _generalChatChance = GetChatterOption<uint32>(
        "LLMChatter.GeneralChat.ReactionChance", 40);
    _generalChatQuestionChance = GetChatterOption<uint32>(
        "LLMChatter.GeneralChat.QuestionChance", 80);
    _generalChatCooldown = GetChatterOption<uint32>(
        "LLMChatter.GeneralChat.Cooldown", 30);
    _generalChatConversationChance = GetChatterOption<uint32>(
        "LLMChatter.GeneralChat.ConversationChance", 30);
    _generalChatHistoryLimit =
        GetChatterOption<uint32>(
            "LLMChatter.GeneralChat.HistoryLimit",
            15);

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
            false);
    _proxChatterScanInterval =
        GetChatterOption<uint32>(
            "LLMChatter.ProximityChatter."
            "ScanIntervalSeconds", 30);
    _proxChatterScanRadius =
        GetChatterOption<uint32>(
            "LLMChatter.ProximityChatter."
            "ScanRadius", 80);
    _proxChatterPlayerSayScanRadius =
        GetChatterOption<uint32>(
            "LLMChatter.ProximityChatter."
            "PlayerSayScanRadius", 40);
    _proxChatterChance =
        GetChatterOption<uint32>(
            "LLMChatter.ProximityChatter."
            "Chance", 65);
    _proxChatterEntityCooldown =
        GetChatterOption<uint32>(
            "LLMChatter.ProximityChatter."
            "EntityCooldown", 300);
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
            "ConversationLineDelay", 4);
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
            "MaxTokensPerLine", 40);
    _proxChatterFacingResetDelay =
        GetChatterOption<uint32>(
            "LLMChatter.ProximityChatter."
            "FacingResetDelay", 8);

    // Emote reaction system
    _emoteReactionsEnable =
        GetChatterOption<bool>(
            "LLMChatter.EmoteReactions.Enable",
            true);
    _emoteMirrorChance =
        GetChatterOption<uint32>(
            "LLMChatter.EmoteReactions."
            "MirrorChance", 90);
    _emoteMirrorCooldown =
        GetChatterOption<uint32>(
            "LLMChatter.EmoteReactions."
            "MirrorCooldown", 15);
    _emoteReactionChance =
        GetChatterOption<uint32>(
            "LLMChatter.EmoteReactions."
            "ReactionChance", 60);
    _emoteObserverChance =
        GetChatterOption<uint32>(
            "LLMChatter.EmoteReactions."
            "ObserverChance", 40);
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

}
