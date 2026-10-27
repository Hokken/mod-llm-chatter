#ifndef MOD_LLM_CHATTER_GROUP_H
#define MOD_LLM_CHATTER_GROUP_H

#include "Define.h"

#include <string>

class Player;
class Creature;

void CheckGroupCombatState();
void CheckGroupLootRolls();
// Delivery-time check for a bot_group_loot_roll comment:
// nullptr while its roll is open and the bot is still in
// that group with its vote; otherwise the drop reason, so
// the line never arrives late or in another party.
char const* LootRollCommentDropReason(
    std::string const& eventExtraData, uint32 botGuid);
void FlushQuestAcceptBatches();
void FlushGroupJoinBatches();
void HandleGroupPlayerUpdateZone(
    Player* player, uint32 newZone,
    uint32 newArea);
void EvictEmoteCooldowns();
void LoadScriptedEmoteExclusions();
bool IsCreatureEmoteScripted(
    Creature const* creature, uint32 textEmote);
void AddLLMChatterGroupScripts();

#endif
