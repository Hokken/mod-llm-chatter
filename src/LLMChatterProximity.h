#ifndef MOD_LLM_CHATTER_PROXIMITY_H
#define MOD_LLM_CHATTER_PROXIMITY_H

#include "Define.h"

#include <string>

class Player;

void CheckProximityChatter();
void HandleProximityPlayerSay(
    Player* player, uint32 type,
    std::string const& msg);
void RecordDeliveredProximityLine(
    uint32 eventId, uint32 playerGuid,
    uint32 zoneId, uint32 botGuid,
    uint32 npcSpawnId,
    bool replyEligible,
    std::string const& speakerName,
    std::string const& message);

#endif
