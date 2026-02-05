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
    _maxPendingRequests = sConfigMgr->GetOption<uint32>("LLMChatter.MaxPendingRequests", 5);

    // Delivery settings
    _deliveryPollMs = sConfigMgr->GetOption<uint32>("LLMChatter.DeliveryPollMs", 1000);
    _messageDelayMin = sConfigMgr->GetOption<uint32>("LLMChatter.MessageDelayMin", 1000);
    _messageDelayMax = sConfigMgr->GetOption<uint32>("LLMChatter.MessageDelayMax", 30000);

    // Event system settings
    _useEventSystem = sConfigMgr->GetOption<bool>("LLMChatter.UseEventSystem", true);
    _eventReactionChance = sConfigMgr->GetOption<uint32>("LLMChatter.EventReactionChance", 15);
    _transportEventChance = sConfigMgr->GetOption<uint32>("LLMChatter.TransportEventChance", 0);
    _transportCooldownSeconds = sConfigMgr->GetOption<uint32>("LLMChatter.TransportCooldownSeconds", 600);
    _eventExpirationSeconds = sConfigMgr->GetOption<uint32>("LLMChatter.EventExpirationSeconds", 600);
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

    if (_enabled)
    {
        LOG_INFO("module", "LLMChatter: Module enabled");
        LOG_INFO("module", "LLMChatter: Trigger interval: {}s, Conversation chance: {}%, Trigger chance: {}%",
                 _triggerIntervalSeconds, _conversationChance, _triggerChance);
        if (_useEventSystem)
        {
            LOG_INFO("module", "LLMChatter: Event system enabled (reaction chance: {}%)", _eventReactionChance);
        }
    }
}
