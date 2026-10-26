#ifndef MOD_LLM_CHATTER_GROUP_H
#define MOD_LLM_CHATTER_GROUP_H

#include "Define.h"

#include <string>

class Player;
class Creature;

void CheckGroupCombatState();
void CheckGroupLootRolls();
// Delivery-time check for a bot_group_loot_roll comment:
// false once its roll has closed, so the line is dropped
// instead of arriving after the roll was decided.
bool IsLootRollCommentStillOpen(
    std::string const& eventExtraData);
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
