/*
 * mod-llm-chatter - Dynamic bot conversations powered by AI
 * Configuration implementation
 */

#include "LLMChatterConfig.h"
#include "Config.h"
#include "Log.h"

void LLMChatterConfig::LoadConfig()
{
    _enabled = sConfigMgr->GetOption<bool>("LLMChatter.Enable", false);
    _debugLog = sConfigMgr->GetOption<bool>("LLMChatter.DebugLog", false);

    // General settings
    _triggerIntervalSeconds = sConfigMgr->GetOption<uint32>("LLMChatter.TriggerIntervalSeconds", 60);
    _conversationChance = sConfigMgr->GetOption<uint32>("LLMChatter.ConversationChance", 50);
    _triggerChance = sConfigMgr->GetOption<uint32>("LLMChatter.TriggerChance", 15);
    _cityChatterMultiplier = sConfigMgr->GetOption<uint32>("LLMChatter.CityChatterMultiplier", 2);
    _maxPendingRequests = sConfigMgr->GetOption<uint32>("LLMChatter.MaxPendingRequests", 5);
    _maxBotsPerZone = sConfigMgr->GetOption<uint32>(
        "LLMChatter.MaxBotsPerZone", 8);
    _maxMessageLength = sConfigMgr->GetOption<uint32>(
        "LLMChatter.MaxMessageLength", 250);

    // Delivery settings
    _deliveryPollMs = sConfigMgr->GetOption<uint32>("LLMChatter.DeliveryPollMs", 1000);
    _messageDelayMin = sConfigMgr->GetOption<uint32>("LLMChatter.MessageDelayMin", 1000);
    _messageDelayMax = sConfigMgr->GetOption<uint32>("LLMChatter.MessageDelayMax", 30000);

    // Event system settings
    _useEventSystem = sConfigMgr->GetOption<bool>("LLMChatter.UseEventSystem", true);
    _prioritySystemEnable =
        sConfigMgr->GetOption<bool>(
            "LLMChatter.PrioritySystem.Enable", true);
    _priorityDeliveryOrderEnable =
        sConfigMgr->GetOption<bool>(
            "LLMChatter.PrioritySystem."
            "DeliveryOrderEnable", true);
    _environmentCheckSeconds = sConfigMgr->GetOption<uint32>("LLMChatter.EnvironmentCheckSeconds", 60);
    _eventReactionChance = sConfigMgr->GetOption<uint32>("LLMChatter.EventReactionChance", 15);
    _transportEventChance = sConfigMgr->GetOption<uint32>("LLMChatter.TransportEventChance", 0);
    _weatherAmbientChance = sConfigMgr->GetOption<uint32>("LLMChatter.WeatherAmbientChance", 0);
    _transportCooldownSeconds = sConfigMgr->GetOption<uint32>("LLMChatter.TransportCooldownSeconds", 600);
    _transportCheckSeconds = sConfigMgr->GetOption<uint32>("LLMChatter.TransportCheckSeconds", 5);
    _eventExpirationSeconds = sConfigMgr->GetOption<uint32>("LLMChatter.EventExpirationSeconds", 600);
    _weatherCooldownSeconds = sConfigMgr->GetOption<uint32>("LLMChatter.WeatherCooldownSeconds", 1800);
    _weatherAmbientCooldownSeconds =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter."
            "WeatherAmbientCooldownSeconds",
            120);
    _dayNightCooldownSeconds = sConfigMgr->GetOption<uint32>("LLMChatter.DayNightCooldownSeconds", 7200);
    _holidayCooldownSeconds = sConfigMgr->GetOption<uint32>("LLMChatter.HolidayCooldownSeconds", 1800);
    _holidayCityChance = sConfigMgr->GetOption<uint32>("LLMChatter.HolidayCityChance", 10);
    _holidayZoneChance = sConfigMgr->GetOption<uint32>("LLMChatter.HolidayZoneChance", 5);
    _botSpeakerCooldownSeconds = sConfigMgr->GetOption<uint32>("LLMChatter.BotSpeakerCooldownSeconds", 900);
    _zoneFatigueThreshold = sConfigMgr->GetOption<uint32>("LLMChatter.ZoneFatigueThreshold", 3);
    _zoneFatigueCooldownSeconds = sConfigMgr->GetOption<uint32>("LLMChatter.ZoneFatigueCooldownSeconds", 900);
    _priorityReactRangeCriticalMin =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.PrioritySystem.ReactRange."
            "CriticalMin", 0);
    _priorityReactRangeCriticalMax =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.PrioritySystem.ReactRange."
            "CriticalMax", 1);
    _priorityReactRangeHighMin =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.PrioritySystem.ReactRange."
            "HighMin", 0);
    _priorityReactRangeHighMax =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.PrioritySystem.ReactRange."
            "HighMax", 2);
    _priorityReactRangeNormalMin =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.PrioritySystem.ReactRange."
            "NormalMin", 2);
    _priorityReactRangeNormalMax =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.PrioritySystem.ReactRange."
            "NormalMax", 5);
    _priorityReactRangeFillerMin =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.PrioritySystem.ReactRange."
            "FillerMin", 5);
    _priorityReactRangeFillerMax =
        sConfigMgr->GetOption<uint32>(
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
    _eventsHolidays = sConfigMgr->GetOption<bool>("LLMChatter.Events.Holidays", true);
    _eventsDayNight = sConfigMgr->GetOption<bool>("LLMChatter.Events.DayNight", true);
    _eventsWeather = sConfigMgr->GetOption<bool>("LLMChatter.Events.Weather", true);
    _eventsTransports = sConfigMgr->GetOption<bool>("LLMChatter.Events.Transports", true);
    _eventsMinor = sConfigMgr->GetOption<bool>("LLMChatter.Events.MinorEvents", true);
    _minorEventChance = sConfigMgr->GetOption<uint32>("LLMChatter.Events.MinorEventChance", 20);

    // Group chatter
    _useGroupChatter = sConfigMgr->GetOption<bool>(
        "LLMChatter.GroupChatter.Enable", true);
    _questDeduplicationWindow =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "QuestDeduplicationWindow", 30);
    _combatStateCheckInterval =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "CombatStateCheckInterval", 5);
    _lowHealthThreshold =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "LowHealthThreshold", 25);
    _oomThreshold =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "OOMThreshold", 15);

    // Group chatter - reaction chances (0-100)
    _groupKillChanceNormal = sConfigMgr->GetOption<uint32>("LLMChatter.GroupChatter.KillChanceNormal", 20);
    _groupDeathChance = sConfigMgr->GetOption<uint32>("LLMChatter.GroupChatter.DeathChance", 40);
    _groupLootChanceGreen = sConfigMgr->GetOption<uint32>("LLMChatter.GroupChatter.LootChanceGreen", 20);
    _groupLootChanceBlue = sConfigMgr->GetOption<uint32>("LLMChatter.GroupChatter.LootChanceBlue", 50);
    _groupQuestObjectiveChance = sConfigMgr->GetOption<uint32>("LLMChatter.GroupChatter.QuestObjectiveChance", 100);
    _groupQuestCompleteChance = sConfigMgr->GetOption<uint32>("LLMChatter.GroupChatter.QuestCompleteChance", 100);
    _groupQuestObjectiveCooldown = sConfigMgr->GetOption<uint32>("LLMChatter.GroupChatter.QuestObjectiveCooldown", 30);
    _groupQuestAcceptChance = sConfigMgr->GetOption<uint32>("LLMChatter.GroupChatter.QuestAcceptChance", 100);
    _groupQuestAcceptCooldown = sConfigMgr->GetOption<uint32>("LLMChatter.GroupChatter.QuestAcceptCooldown", 30);
    _groupQuestAcceptDebounceSec = sConfigMgr->GetOption<uint32>("LLMChatter.GroupChatter.QuestAcceptDebounceSec", 5);
    _groupSpellCastChance = sConfigMgr->GetOption<uint32>("LLMChatter.GroupChatter.SpellCastChance", 10);
    _groupSpellCastCooldown = sConfigMgr->GetOption<uint32>("LLMChatter.GroupChatter.SpellCastCooldown", 10);
    _groupJoinDebounceSec =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "JoinDebounceSec", 6);

    // Group chatter - per-event cooldowns (seconds)
    _groupKillCooldown = sConfigMgr->GetOption<uint32>("LLMChatter.GroupChatter.KillCooldown", 120);
    _groupDeathCooldown = sConfigMgr->GetOption<uint32>("LLMChatter.GroupChatter.DeathCooldown", 30);
    _groupLootCooldown = sConfigMgr->GetOption<uint32>("LLMChatter.GroupChatter.LootCooldown", 60);
    _groupPlayerMsgCooldown = sConfigMgr->GetOption<uint32>("LLMChatter.GroupChatter.PlayerMsgCooldown", 15);

    // Group chatter - new event settings
    _groupResurrectChance = sConfigMgr->GetOption<uint32>("LLMChatter.GroupChatter.ResurrectChance", 100);
    _groupResurrectCooldown = sConfigMgr->GetOption<uint32>("LLMChatter.GroupChatter.ResurrectCooldown", 30);
    _groupZoneChance = sConfigMgr->GetOption<uint32>("LLMChatter.GroupChatter.ZoneTransitionChance", 100);
    _groupZoneCooldown = sConfigMgr->GetOption<uint32>("LLMChatter.GroupChatter.ZoneTransitionCooldown", 120);
    _groupDungeonChance = sConfigMgr->GetOption<uint32>("LLMChatter.GroupChatter.DungeonEntryChance", 100);
    _groupDungeonCooldown = sConfigMgr->GetOption<uint32>("LLMChatter.GroupChatter.DungeonEntryCooldown", 300);
    _groupWipeChance = sConfigMgr->GetOption<uint32>("LLMChatter.GroupChatter.WipeChance", 100);
    _groupWipeCooldown = sConfigMgr->GetOption<uint32>("LLMChatter.GroupChatter.WipeCooldown", 120);
    _groupCorpseRunChance = sConfigMgr->GetOption<uint32>("LLMChatter.GroupChatter.CorpseRunChance", 80);
    _groupCorpseRunCooldown = sConfigMgr->GetOption<uint32>("LLMChatter.GroupChatter.CorpseRunCooldown", 120);
    _useFarewell = sConfigMgr->GetOption<bool>(
        "LLMChatter.GroupChatter.FarewellEnable", true);
    _groupDiscoveryChance =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "DiscoveryChance", 40);
    _groupDiscoveryCooldown =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "DiscoveryCooldown", 30);
    _groupDiscoveryChance =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "DiscoveryChance", 100);

    // Group chatter - react-after delays (seconds)
    _reactDelayJoin =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "ReactDelay.Join", 3);
    _reactDelayJoinBatch =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "ReactDelay.JoinBatch", 0);
    _reactDelayKill =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "ReactDelay.Kill", 2);
    _reactDelayWipe =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "ReactDelay.Wipe", 3);
    _reactDelayDeath =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "ReactDelay.Death", 2);
    _reactDelayLoot =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "ReactDelay.Loot", 3);
    _reactDelayCombat =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "ReactDelay.Combat", 1);
    _reactDelayPlayerMsg =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "ReactDelay.PlayerMsg", 0);
    _reactDelayLevelUp =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "ReactDelay.LevelUp", 2);
    _reactDelayQuestObjectives =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "ReactDelay.QuestObjectives", 2);
    _reactDelayQuestComplete =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "ReactDelay.QuestComplete", 2);
    _reactDelayAchievement =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "ReactDelay.Achievement", 2);
    _reactDelaySpellCast =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "ReactDelay.SpellCast", 2);
    _reactDelayResurrect =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "ReactDelay.Resurrect", 3);
    _reactDelayCorpseRun =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "ReactDelay.CorpseRun", 5);
    _reactDelayDungeonEntry =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "ReactDelay.DungeonEntry", 5);
    _reactDelayZoneTransition =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "ReactDelay.ZoneTransition", 5);
    _reactDelayStateCallout =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "ReactDelay.StateCallout", 1);
    _reactDelayDiscoveryMin =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "ReactDelay.DiscoveryMin", 5);
    _reactDelayDiscoveryMax =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "ReactDelay.DiscoveryMax", 20);
    if (_reactDelayDiscoveryMin
        > _reactDelayDiscoveryMax)
    {
        _reactDelayDiscoveryMin =
            _reactDelayDiscoveryMax;
    }
    _reactDelayNearbyObject =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "ReactDelay.NearbyObject", 2);
    _reactDelayBGEvent =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.BGChatter."
            "ReactDelay", 2);
    _reactDelayGeneralMsg =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GeneralChat."
            "ReactDelay", 5);

    // Group chatter - combat engagement chances
    _combatChanceBoss =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "CombatChance.Boss", 100);
    _combatChanceElite =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "CombatChance.Elite", 40);
    _combatChanceNormal =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "CombatChance.Normal", 15);

    // Group chatter - quest objective suppression
    _questObjSuppressWindow =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "QuestObjSuppressWindow", 10);

    // Group chatter - wipe detection
    _wipeMinGroupSize =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "WipeMinGroupSize", 2);

    // GetReactionDelaySeconds ranges
    _reactRangeDayNightMin =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.ReactRange."
            "DayNightMin", 120);
    _reactRangeDayNightMax =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.ReactRange."
            "DayNightMax", 600);
    _reactRangeHolidayMin =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.ReactRange."
            "HolidayMin", 300);
    _reactRangeHolidayMax =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.ReactRange."
            "HolidayMax", 900);
    _reactRangeWeatherMin =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.ReactRange."
            "WeatherMin", 60);
    _reactRangeWeatherMax =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.ReactRange."
            "WeatherMax", 300);
    _reactRangeWeatherAmbientMin =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.ReactRange."
            "WeatherAmbientMin", 120);
    _reactRangeWeatherAmbientMax =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.ReactRange."
            "WeatherAmbientMax", 600);
    _reactRangeTransportMin =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.ReactRange."
            "TransportMin", 5);
    _reactRangeTransportMax =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.ReactRange."
            "TransportMax", 15);
    _reactRangeQuestAcceptMin =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.ReactRange."
            "QuestAcceptMin", 5);
    _reactRangeQuestAcceptMax =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.ReactRange."
            "QuestAcceptMax", 15);
    _reactRangeDefaultMin =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.ReactRange."
            "DefaultMin", 30);
    _reactRangeDefaultMax =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.ReactRange."
            "DefaultMax", 120);

    // Group chatter - nearby object scan
    _nearbyObjectEnable =
        sConfigMgr->GetOption<bool>(
            "LLMChatter.GroupChatter."
            "NearbyObjectEnable", true);
    _nearbyObjectCheckInterval =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "NearbyObjectCheckInterval", 45);
    _nearbyObjectChance =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "NearbyObjectChance", 30);
    _nearbyObjectCooldown =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "NearbyObjectCooldown", 180);
    _nearbyObjectScanRadius =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "NearbyObjectScanRadius", 22);
    _nearbyObjectNameCooldown =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "NearbyObjectNameCooldown", 900);
    _nearbyObjectMaxObjects =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "NearbyObjectMaxObjects", 3);
    _facingEnable =
        sConfigMgr->GetOption<bool>(
            "LLMChatter.GroupChatter."
            "FacingEnable", true);

    // Group chatter - state-triggered callouts
    _stateCalloutEnabled = sConfigMgr->GetOption<bool>(
        "LLMChatter.GroupChatter.StateCalloutEnable",
        true);
    _stateCalloutLowHealth = sConfigMgr->GetOption<bool>(
        "LLMChatter.GroupChatter.StateCalloutLowHealth",
        true);
    _stateCalloutOom = sConfigMgr->GetOption<bool>(
        "LLMChatter.GroupChatter.StateCalloutOom",
        true);
    _stateCalloutAggro = sConfigMgr->GetOption<bool>(
        "LLMChatter.GroupChatter.StateCalloutAggro",
        true);
    _stateCalloutChance =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "StateCalloutChance", 60);
    _stateCalloutCooldown =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "StateCalloutCooldown", 60);

    // Pre-cached instant reactions
    _preCacheEnable = sConfigMgr->GetOption<bool>(
        "LLMChatter.GroupChatter.PreCacheEnable",
        true);
    _preCacheCombatEnable = sConfigMgr->GetOption<bool>(
        "LLMChatter.GroupChatter.PreCacheCombatEnable",
        true);
    _preCacheStateEnable = sConfigMgr->GetOption<bool>(
        "LLMChatter.GroupChatter.PreCacheStateEnable",
        true);
    _preCacheSpellEnable = sConfigMgr->GetOption<bool>(
        "LLMChatter.GroupChatter.PreCacheSpellEnable",
        true);
    _preCacheDepthCombat =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "PreCacheDepthCombat", 2);
    _preCacheDepthState =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "PreCacheDepthState", 2);
    _preCacheDepthSpell =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "PreCacheDepthSpell", 2);
    _preCacheTTLSeconds =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "PreCacheTTLSeconds", 3600);
    _preCacheGeneratePerLoop =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GroupChatter."
            "PreCacheGeneratePerLoop", 3);
    _preCacheFallbackToLive =
        sConfigMgr->GetOption<bool>(
            "LLMChatter.GroupChatter."
            "PreCacheFallbackToLive", true);

    // General chat reactions
    _useGeneralChatReact = sConfigMgr->GetOption<bool>(
        "LLMChatter.GeneralChat.Enable", true);
    _generalChatChance = sConfigMgr->GetOption<uint32>(
        "LLMChatter.GeneralChat.ReactionChance", 40);
    _generalChatQuestionChance = sConfigMgr->GetOption<uint32>(
        "LLMChatter.GeneralChat.QuestionChance", 80);
    _generalChatCooldown = sConfigMgr->GetOption<uint32>(
        "LLMChatter.GeneralChat.Cooldown", 30);
    _generalChatConversationChance = sConfigMgr->GetOption<uint32>(
        "LLMChatter.GeneralChat.ConversationChance", 30);
    _generalChatHistoryLimit =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.GeneralChat.HistoryLimit",
            15);

    // RP enrichment
    _raceLoreChance = sConfigMgr->GetOption<uint32>("LLMChatter.RaceLoreChance", 20);

    // Battleground chatter
    _bgChatterEnable = sConfigMgr->GetOption<bool>(
        "LLMChatter.BGChatter.Enable", true);
    _bgMatchStartChance = sConfigMgr->GetOption<uint32>(
        "LLMChatter.BGChatter.MatchStartChance", 100);
    _bgNodeEventChance = sConfigMgr->GetOption<uint32>(
        "LLMChatter.BGChatter.NodeEventChance", 80);
    _bgScoreMilestoneChance =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.BGChatter."
            "ScoreMilestoneChance", 80);
    _bgRaidWorkerChance = sConfigMgr->GetOption<uint32>(
        "LLMChatter.BGChatter.RaidWorkerChance", 30);
    _bgStatePollingIntervalMs =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.BGChatter."
            "StatePollingIntervalMs", 3000);
    _bgBigEventCooldownSec =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.BGChatter."
            "BigEventCooldownSec", 15);
    _bgIdleChatterChance =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.BGChatter."
            "IdleChatterChance", 25);
    _bgIdleChatterCooldownSec =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.BGChatter."
            "IdleChatterCooldownSec", 30);
    _bgRezChance =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.BGChatter."
            "RezChance", 20);

    // Raid chatter (PvE)
    _raidChatterEnable = sConfigMgr->GetOption<bool>(
        "LLMChatter.RaidChatter.Enable", true);
    _raidBossPullChance =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.RaidChatter."
            "BossPullChance", 80);
    _raidBossKillChance =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.RaidChatter."
            "BossKillChance", 100);
    _raidBossWipeChance =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.RaidChatter."
            "BossWipeChance", 100);
    _raidMoraleEnable =
        sConfigMgr->GetOption<bool>(
            "LLMChatter.RaidChatter."
            "MoraleEnable", true);
    _raidMoraleChance =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.RaidChatter."
            "MoraleChance", 15);
    _raidMoraleCooldown =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.RaidChatter."
            "MoraleCooldown", 120);

    // Zone intrusion alerts
    _zoneIntrusionEnable =
        sConfigMgr->GetOption<bool>(
            "LLMChatter.ZoneIntrusion.Enable",
            true);
    _zoneIntrusionZoneThrottleSec =
        sConfigMgr->GetOption<uint32>(
            "LLMChatter.ZoneIntrusion."
            "ZoneThrottleSec", 30);

}
