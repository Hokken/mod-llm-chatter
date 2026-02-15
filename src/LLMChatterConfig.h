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
    uint32 _cityChatterMultiplier;
    uint32 _maxPendingRequests;

    // Delivery settings
    uint32 _deliveryPollMs;
    uint32 _messageDelayMin;
    uint32 _messageDelayMax;

    // Event system settings
    bool _useEventSystem;
    uint32 _environmentCheckSeconds;
    uint32 _eventReactionChance;
    uint32 _transportEventChance;
    uint32 _transportCooldownSeconds;
    uint32 _transportCheckSeconds;
    uint32 _eventExpirationSeconds;
    uint32 _weatherCooldownSeconds;
    uint32 _dayNightCooldownSeconds;
    uint32 _holidayCooldownSeconds;
    uint32 _holidayCityChance;
    uint32 _holidayZoneChance;
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
    bool _eventsMinor;        // Call to Arms, fishing, etc.
    uint32 _minorEventChance; // % chance for minor events

    // Group chatter
    bool _useGroupChatter;

    // Group chatter - reaction chances (0-100)
    uint32 _groupKillChanceNormal;
    uint32 _groupDeathChance;
    uint32 _groupLootChanceGreen;
    uint32 _groupLootChanceBlue;
    uint32 _groupQuestObjectiveChance;
    uint32 _groupQuestObjectiveCooldown;
    uint32 _groupSpellCastChance;

    // Group chatter - per-event cooldowns (seconds)
    uint32 _groupKillCooldown;
    uint32 _groupDeathCooldown;
    uint32 _groupLootCooldown;
    uint32 _groupPlayerMsgCooldown;

    // Group chatter - new event settings
    uint32 _groupResurrectChance;
    uint32 _groupResurrectCooldown;
    uint32 _groupZoneChance;
    uint32 _groupZoneCooldown;
    uint32 _groupDungeonChance;
    uint32 _groupDungeonCooldown;
    uint32 _groupWipeChance;
    uint32 _groupWipeCooldown;
    uint32 _groupCorpseRunChance;
    uint32 _groupCorpseRunCooldown;
    bool _useFarewell;

    // Group chatter - state-triggered callouts
    bool _stateCalloutEnabled;
    bool _stateCalloutLowHealth;
    bool _stateCalloutOom;
    bool _stateCalloutAggro;
    uint32 _stateCalloutChance;   // 0-100
    uint32 _stateCalloutCooldown; // seconds per bot

    // General chat reactions
    bool _useGeneralChatReact;
    uint32 _generalChatChance;
    uint32 _generalChatQuestionChance;
    uint32 _generalChatCooldown;
    uint32 _generalChatConversationChance;

    // RP enrichment
    uint32 _raceLoreChance;

private:
    LLMChatterConfig() = default;
};

#define sLLMChatterConfig LLMChatterConfig::instance()

#endif // LLM_CHATTER_CONFIG_H
