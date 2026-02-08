/*
 * mod-llm-chatter - Dynamic bot conversations powered by AI
 * Configuration header
 *
 * Supported events:
 * - Day/Night transitions
 * - Holiday start/stop
 * - Weather changes (future)
 * - Transport arrivals (future)
 */

#ifndef LLM_CHATTER_CONFIG_H
#define LLM_CHATTER_CONFIG_H

#include "Define.h"
#include <string>

class LLMChatterConfig
{
public:
    static LLMChatterConfig* instance()
    {
        static LLMChatterConfig instance;
        return &instance;
    }

    void LoadConfig();
    bool IsEnabled() const { return _enabled; }

    // General settings
    bool _enabled;
    uint32 _triggerIntervalSeconds;
    uint32 _conversationChance;
    uint32 _triggerChance;
    uint32 _maxPendingRequests;

    // Delivery settings
    uint32 _deliveryPollMs;
    uint32 _messageDelayMin;
    uint32 _messageDelayMax;

    // Event system settings
    bool _useEventSystem;
    uint32 _eventReactionChance;
    uint32 _transportEventChance;
    uint32 _transportCooldownSeconds;
    uint32 _eventExpirationSeconds;
    uint32 _globalMessageCap;
    uint32 _globalCapWindowSeconds;
    uint32 _botSpeakerCooldownSeconds;
    uint32 _zoneFatigueThreshold;
    uint32 _zoneFatigueCooldownSeconds;

    // Event type toggles (only safe, low-frequency events)
    bool _eventsHolidays;
    bool _eventsDayNight;
    bool _eventsWeather;      // Future: weather changes
    bool _eventsTransports;   // Future: transport arrivals

    // Group chatter
    bool _useGroupChatter;

private:
    LLMChatterConfig() = default;
};

#define sLLMChatterConfig LLMChatterConfig::instance()

#endif // LLM_CHATTER_CONFIG_H
