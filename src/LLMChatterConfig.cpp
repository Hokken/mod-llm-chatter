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
    _environmentCheckSeconds = sConfigMgr->GetOption<uint32>("LLMChatter.EnvironmentCheckSeconds", 60);
    _eventReactionChance = sConfigMgr->GetOption<uint32>("LLMChatter.EventReactionChance", 15);
    _transportEventChance = sConfigMgr->GetOption<uint32>("LLMChatter.TransportEventChance", 0);
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
    _globalMessageCap = sConfigMgr->GetOption<uint32>("LLMChatter.GlobalMessageCap", 8);
    _globalCapWindowSeconds = sConfigMgr->GetOption<uint32>("LLMChatter.GlobalCapWindowSeconds", 300);
    _botSpeakerCooldownSeconds = sConfigMgr->GetOption<uint32>("LLMChatter.BotSpeakerCooldownSeconds", 900);
    _zoneFatigueThreshold = sConfigMgr->GetOption<uint32>("LLMChatter.ZoneFatigueThreshold", 3);
    _zoneFatigueCooldownSeconds = sConfigMgr->GetOption<uint32>("LLMChatter.ZoneFatigueCooldownSeconds", 900);

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
    _groupQuestObjectiveCooldown = sConfigMgr->GetOption<uint32>("LLMChatter.GroupChatter.QuestObjectiveCooldown", 30);
    _groupQuestAcceptChance = sConfigMgr->GetOption<uint32>("LLMChatter.GroupChatter.QuestAcceptChance", 100);
    _groupQuestAcceptCooldown = sConfigMgr->GetOption<uint32>("LLMChatter.GroupChatter.QuestAcceptCooldown", 30);
    _groupSpellCastChance = sConfigMgr->GetOption<uint32>("LLMChatter.GroupChatter.SpellCastChance", 15);
    _groupSpellCastCooldown = sConfigMgr->GetOption<uint32>("LLMChatter.GroupChatter.SpellCastCooldown", 10);

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
            "PreCacheGeneratePerLoop", 2);
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

    if (_enabled)
    {
        LOG_INFO("module",
            "LLMChatter: Module enabled");
        LOG_INFO("module",
            "LLMChatter: Trigger interval: {}s, "
            "Conversation chance: {}%, "
            "Trigger chance: {}%",
            _triggerIntervalSeconds,
            _conversationChance, _triggerChance);
        LOG_INFO("module",
            "LLMChatter: MaxBotsPerZone: {}, "
            "MaxMessageLength: {}",
            _maxBotsPerZone, _maxMessageLength);
        if (_useEventSystem)
        {
            LOG_INFO("module",
                "LLMChatter: Event system enabled "
                "(reaction chance: {}%, "
                "weather cooldown: {}s, "
                "ambient weather cooldown: {}s)",
                _eventReactionChance,
                _weatherCooldownSeconds,
                _weatherAmbientCooldownSeconds);
        }
        if (_useGroupChatter)
        {
            LOG_INFO("module",
                "LLMChatter: Group chatter enabled "
                "(SpellCastCooldown: {}s, "
                "QuestDeduplicationWindow: {}s)",
                _groupSpellCastCooldown,
                _questDeduplicationWindow);
            if (_stateCalloutEnabled)
            {
                LOG_INFO("module",
                    "LLMChatter: State callouts "
                    "enabled (chance: {}%, "
                    "cooldown: {}s, "
                    "LowHealthThreshold: {}%, "
                    "OOMThreshold: {}%, "
                    "CombatStateCheckInterval: "
                    "{}s)",
                    _stateCalloutChance,
                    _stateCalloutCooldown,
                    _lowHealthThreshold,
                    _oomThreshold,
                    _combatStateCheckInterval);
            }
        }
        if (_preCacheEnable)
        {
            LOG_INFO("module",
                "LLMChatter: Pre-cache enabled "
                "(combat={}, state={}, spell={}, "
                "depth={}/{}/{}, TTL={}s, "
                "perLoop={}, fallback={})",
                _preCacheCombatEnable ? 1 : 0,
                _preCacheStateEnable ? 1 : 0,
                _preCacheSpellEnable ? 1 : 0,
                _preCacheDepthCombat,
                _preCacheDepthState,
                _preCacheDepthSpell,
                _preCacheTTLSeconds,
                _preCacheGeneratePerLoop,
                _preCacheFallbackToLive ? 1 : 0);
        }
        if (_useGeneralChatReact)
        {
            LOG_INFO("module",
                "LLMChatter: General chat reactions "
                "enabled (chance: {}%, cooldown: {}s"
                ", HistoryLimit: {})",
                _generalChatChance,
                _generalChatCooldown,
                _generalChatHistoryLimit);
        }
    }
}
