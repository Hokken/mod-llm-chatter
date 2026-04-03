/*
 * mod-llm-chatter - Dynamic bot conversations powered by AI
 * Configuration header
 *
 * Supported events:
 * - Day/Night transitions
 * - Holiday start/stop
 * - Weather changes
 * - Transport arrivals
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
    bool IsDebugLog() const { return _debugLog; }

    // General settings
    bool _enabled;
    bool _debugLog;
    uint32 _triggerIntervalSeconds;
    uint32 _conversationChance;
    uint32 _triggerChance;
    uint32 _cityChatterMultiplier;
    uint32 _maxPendingRequests;
    uint32 _maxBotsPerZone;
    uint32 _maxMessageLength;

    // Delivery settings
    uint32 _deliveryPollMs;
    uint32 _messageDelayMin;
    uint32 _messageDelayMax;

    // Event system settings
    bool _useEventSystem;
    bool _prioritySystemEnable;
    bool _priorityDeliveryOrderEnable;
    uint32 _environmentCheckSeconds;
    uint32 _eventReactionChance;
    uint32 _transportEventChance;
    uint32 _weatherAmbientChance;
    uint32 _transportCooldownSeconds;
    uint32 _transportCheckSeconds;
    uint32 _eventExpirationSeconds;
    uint32 _weatherCooldownSeconds;
    uint32 _weatherAmbientCooldownSeconds;
    uint32 _dayNightCooldownSeconds;
    uint32 _holidayCooldownSeconds;
    uint32 _holidayCityChance;
    uint32 _holidayZoneChance;
    uint32 _botSpeakerCooldownSeconds;
    uint32 _zoneFatigueThreshold;
    uint32 _zoneFatigueCooldownSeconds;
    uint32 _priorityReactRangeCriticalMin;
    uint32 _priorityReactRangeCriticalMax;
    uint32 _priorityReactRangeHighMin;
    uint32 _priorityReactRangeHighMax;
    uint32 _priorityReactRangeNormalMin;
    uint32 _priorityReactRangeNormalMax;
    uint32 _priorityReactRangeFillerMin;
    uint32 _priorityReactRangeFillerMax;

    // Event type toggles (only safe, low-frequency events)
    bool _eventsHolidays;
    bool _eventsDayNight;
    bool _eventsWeather;      // Future: weather changes
    bool _eventsTransports;   // Future: transport arrivals
    bool _eventsMinor;        // Call to Arms, fishing, etc.
    uint32 _minorEventChance; // % chance for minor events

    // Group chatter
    bool _useGroupChatter;
    uint32 _questDeduplicationWindow;
    uint32 _combatStateCheckInterval;
    uint32 _lowHealthThreshold;
    uint32 _oomThreshold;

    // Group chatter - reaction chances (0-100)
    uint32 _groupKillChanceNormal;
    uint32 _groupDeathChance;
    uint32 _groupLootChanceGreen;
    uint32 _groupLootChanceBlue;
    uint32 _groupQuestObjectiveChance;
    uint32 _groupQuestCompleteChance;
    uint32 _groupQuestObjectiveCooldown;
    uint32 _groupQuestAcceptChance;
    uint32 _groupQuestAcceptCooldown;
    uint32 _groupQuestAcceptDebounceSec;
    uint32 _groupSpellCastChance;
    uint32 _groupSpellCastCooldown;
    uint32 _groupJoinDebounceSec;

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


    // Group chatter - react-after delays (seconds)
    uint32 _reactDelayJoin;
    uint32 _reactDelayJoinBatch;
    uint32 _reactDelayKill;
    uint32 _reactDelayWipe;
    uint32 _reactDelayDeath;
    uint32 _reactDelayLoot;
    uint32 _reactDelayCombat;
    uint32 _reactDelayPlayerMsg;
    uint32 _reactDelayLevelUp;
    uint32 _reactDelayQuestObjectives;
    uint32 _reactDelayQuestComplete;
    uint32 _reactDelayAchievement;
    uint32 _reactDelaySpellCast;
    uint32 _reactDelayResurrect;
    uint32 _reactDelayCorpseRun;
    uint32 _reactDelayDungeonEntry;
    uint32 _reactDelayZoneTransition;
    uint32 _reactDelayStateCallout;

    uint32 _reactDelayNearbyObject;
    uint32 _reactDelayBGEvent;
    uint32 _reactDelayGeneralMsg;
    uint32 _reactDelayEmote;

    // Group chatter - combat engagement chances (0-100)
    uint32 _combatChanceBoss;
    uint32 _combatChanceElite;
    uint32 _combatChanceNormal;

    // Group chatter - quest objective suppression
    uint32 _questObjSuppressWindow;

    // Group chatter - wipe detection
    uint32 _wipeMinGroupSize;

    // Group chatter - GetReactionDelaySeconds ranges
    uint32 _reactRangeDayNightMin;
    uint32 _reactRangeDayNightMax;
    uint32 _reactRangeHolidayMin;
    uint32 _reactRangeHolidayMax;
    uint32 _reactRangeWeatherMin;
    uint32 _reactRangeWeatherMax;
    uint32 _reactRangeWeatherAmbientMin;
    uint32 _reactRangeWeatherAmbientMax;
    uint32 _reactRangeTransportMin;
    uint32 _reactRangeTransportMax;
    uint32 _reactRangeQuestAcceptMin;
    uint32 _reactRangeQuestAcceptMax;
    uint32 _reactRangeDefaultMin;
    uint32 _reactRangeDefaultMax;

    // Group chatter - nearby object scan
    bool     _nearbyObjectEnable;
    uint32   _nearbyObjectCheckInterval;
    uint32   _nearbyObjectChance;
    uint32   _nearbyObjectCooldown;
    uint32   _nearbyObjectScanRadius;
    uint32   _nearbyObjectNameCooldown;
    uint32   _nearbyObjectMaxObjects;
    bool     _facingEnable;

    // Group chatter - state-triggered callouts
    bool _stateCalloutEnabled;
    bool _stateCalloutLowHealth;
    bool _stateCalloutOom;
    bool _stateCalloutAggro;
    uint32 _stateCalloutChance;   // 0-100
    uint32 _stateCalloutCooldown; // seconds per bot

    // Pre-cached instant reactions
    bool _preCacheEnable;
    bool _preCacheCombatEnable;
    bool _preCacheStateEnable;
    bool _preCacheSpellEnable;
    uint32 _preCacheDepthCombat;
    uint32 _preCacheDepthState;
    uint32 _preCacheDepthSpell;
    uint32 _preCacheTTLSeconds;
    uint32 _preCacheGeneratePerLoop;
    bool _preCacheFallbackToLive;

    // General chat reactions
    bool _useGeneralChatReact;
    uint32 _generalChatChance;
    uint32 _generalChatQuestionChance;
    uint32 _generalChatCooldown;
    uint32 _generalChatConversationChance;
    uint32 _generalChatHistoryLimit;

    // RP enrichment
    uint32 _raceLoreChance;

    // Battleground chatter
    bool _bgChatterEnable;
    uint32 _bgMatchStartChance;
    uint32 _bgNodeEventChance;
    uint32 _bgScoreMilestoneChance;
    uint32 _bgRaidWorkerChance;
    uint32 _bgStatePollingIntervalMs;
    uint32 _bgBigEventCooldownSec;
    uint32 _bgIdleChatterChance{25};
    uint32 _bgIdleChatterCooldownSec{30};
    uint32 _bgRezChance{20};

    // Raid chatter (PvE)
    bool _raidChatterEnable;
    uint32 _raidBossPullChance;
    uint32 _raidBossKillChance;
    uint32 _raidBossWipeChance;
    bool _raidMoraleEnable;
    uint32 _raidMoraleChance;
    uint32 _raidMoraleCooldown;

    // Zone intrusion alerts
    bool _zoneIntrusionEnable;
    uint32 _zoneIntrusionZoneThrottleSec;

    // Proximity chatter
    bool _proxChatterEnable;
    uint32 _proxChatterScanInterval;
    uint32 _proxChatterScanRadius;
    uint32 _proxChatterChance;
    uint32 _proxChatterEntityCooldown;
    uint32 _proxChatterZoneFatigueThreshold;
    uint32 _proxChatterZoneFatigueDecay;
    uint32 _proxChatterConversationChance;
    uint32 _proxChatterPlayerAddressChance;
    uint32 _proxChatterMaxConversationLines;
    uint32 _proxChatterConversationLineDelay;
    uint32 _proxChatterReplyWindowSeconds;
    uint32 _proxChatterReplyMaxTurns;
    uint32 _proxChatterMaxTokensPerLine;
    uint32 _proxChatterFacingResetDelay;

    // Emote reaction system
    bool   _emoteReactionsEnable;
    uint32 _emoteMirrorChance;
    uint32 _emoteMirrorCooldown;
    uint32 _emoteReactionChance;
    uint32 _emoteObserverChance;
    uint32 _emoteObserverCooldown;
    uint32 _emoteMoodSpreadChance;
    bool   _emoteNPCMirrorEnable;

private:
    LLMChatterConfig() = default;
};

#define sLLMChatterConfig LLMChatterConfig::instance()

#endif // LLM_CHATTER_CONFIG_H
