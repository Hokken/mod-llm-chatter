#ifndef MOD_LLM_CHATTER_GROUP_H
#define MOD_LLM_CHATTER_GROUP_H

#include "Define.h"

class Player;
class Creature;

void CheckGroupCombatState();
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
