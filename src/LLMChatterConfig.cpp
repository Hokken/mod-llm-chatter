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
    _messageDelayMax = sConfigMgr->GetOption<uint32>("LLMChatter.MessageDelayMax", 8000);

    if (_enabled)
    {
        LOG_INFO("module", "LLMChatter: Module enabled");
        LOG_INFO("module", "LLMChatter: Trigger interval: {}s, Conversation chance: {}%, Trigger chance: {}%",
                 _triggerIntervalSeconds, _conversationChance, _triggerChance);
    }
}
