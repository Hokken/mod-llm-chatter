#ifndef MOD_LLM_CHATTER_PROXIMITY_H
#define MOD_LLM_CHATTER_PROXIMITY_H

#include "Define.h"

#include <string>

class Player;
class Creature;

bool IsProximityAnchorEligible(Player* player);
bool IsProximityPlayerbotEligible(
    Player* player, Player* bot, float radius,
    bool allowMounted);
bool IsProximityDirectedPlayerbotEligible(
    Player* player, Player* bot, float radius);
bool IsProximityPlayerbotEmoteRouteEnabled();
bool IsProximityNPCEligible(
    Player* player, Creature* creature, float radius);

void CheckProximityChatter(bool instanceMaps);
void HandleProximityPlayerSay(
    Player* player, uint32 type, uint32 language,
    std::string const& msg);
void HandleProximityPlayerEmote(
    Player* player, Creature* creature,
    uint32 textEmote, uint32 mirrorEmote);
bool HandleProximityPlayerbotEmote(
    Player* player, Player* bot,
    uint32 textEmote, uint32 mirrorEmote);
void RecordDeliveredProximityLine(
    uint32 eventId, uint32 playerGuid,
    uint32 zoneId, uint32 mapId,
    uint32 instanceId, uint32 botGuid,
    uint32 npcSpawnId,
    bool replyEligible,
    std::string const& speakerName,
    std::string const& message);

#endif
