#ifndef MOD_LLM_CHATTER_BG_DELIVERY_H
#define MOD_LLM_CHATTER_BG_DELIVERY_H

#include "Define.h"
#include <string>

class Battleground;
class Player;

// Objective status uses bg_idle_chatter with an ab_objective_status marker.
bool BGEventUsesABSnapshot(std::string const& eventType);

// Lifecycle hooks publish value-only identity under a short mutex.
void EnsureBGDeliveryLifetime(Battleground* bg);
void ResetBGDeliveryLifetime(uint32 instanceId);
Player* GetBGChatterRecipient(Battleground* bg, Player* subject);
void AppendBGDeliveryContext(Battleground* bg, Player* subject,
    std::string& json);

// World-thread final-send check. Empty means allowed (including non-BG).
std::string ValidateBGDelivery(Player* speaker, std::string const& channel,
    std::string const& owner, std::string const& eventType,
    uint32 eventMapId, uint32 rowGroupId, std::string const& json);

#endif
