/*
 * mod-llm-chatter - Dynamic bot conversations powered by AI
 * Configuration header
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

private:
    LLMChatterConfig() = default;
};

#define sLLMChatterConfig LLMChatterConfig::instance()

#endif // LLM_CHATTER_CONFIG_H
