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
    _triggerChance = sConfigMgr->GetOption<uint32>("LLMChatter.TriggerChance", 30);
    _cityChatterMultiplier = sConfigMgr->GetOption<uint32>("LLMChatter.CityChatterMultiplier", 3);
    _maxPendingRequests = sConfigMgr->GetOption<uint32>("LLMChatter.MaxPendingRequests", 5);

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

    // Group chatter
    _useGroupChatter = sConfigMgr->GetOption<bool>("LLMChatter.GroupChatter.Enable", false);

    // Group chatter - reaction chances (0-100)
    _groupKillChanceNormal = sConfigMgr->GetOption<uint32>("LLMChatter.GroupChatter.KillChanceNormal", 20);
    _groupDeathChance = sConfigMgr->GetOption<uint32>("LLMChatter.GroupChatter.DeathChance", 40);
    _groupLootChanceGreen = sConfigMgr->GetOption<uint32>("LLMChatter.GroupChatter.LootChanceGreen", 20);
    _groupLootChanceBlue = sConfigMgr->GetOption<uint32>("LLMChatter.GroupChatter.LootChanceBlue", 50);
    _groupQuestObjectiveChance = sConfigMgr->GetOption<uint32>("LLMChatter.GroupChatter.QuestObjectiveChance", 50);
    _groupSpellCastChance = sConfigMgr->GetOption<uint32>("LLMChatter.GroupChatter.SpellCastChance", 15);

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

    // General chat reactions
    _useGeneralChatReact = sConfigMgr->GetOption<bool>(
        "LLMChatter.GeneralChat.Enable", false);
    _generalChatChance = sConfigMgr->GetOption<uint32>(
        "LLMChatter.GeneralChat.ReactionChance", 80);
    _generalChatQuestionChance = sConfigMgr->GetOption<uint32>(
        "LLMChatter.GeneralChat.QuestionChance", 100);
    _generalChatCooldown = sConfigMgr->GetOption<uint32>(
        "LLMChatter.GeneralChat.Cooldown", 60);
    _generalChatConversationChance = sConfigMgr->GetOption<uint32>(
        "LLMChatter.GeneralChat.ConversationChance", 30);

    // RP enrichment
    _raceLoreChance = sConfigMgr->GetOption<uint32>("LLMChatter.RaceLoreChance", 15);

    if (_enabled)
    {
        LOG_INFO("module", "LLMChatter: Module enabled");
        LOG_INFO("module", "LLMChatter: Trigger interval: {}s, Conversation chance: {}%, Trigger chance: {}%",
                 _triggerIntervalSeconds, _conversationChance, _triggerChance);
        if (_useEventSystem)
        {
            LOG_INFO("module", "LLMChatter: Event system enabled (reaction chance: {}%)", _eventReactionChance);
        }
        if (_useGroupChatter)
        {
            LOG_INFO("module", "LLMChatter: Group chatter enabled");
        }
        if (_useGeneralChatReact)
        {
            LOG_INFO("module",
                "LLMChatter: General chat reactions "
                "enabled (chance: {}%, cooldown: {}s)",
                _generalChatChance,
                _generalChatCooldown);
        }
    }
}
