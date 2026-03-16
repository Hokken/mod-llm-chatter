#ifndef MOD_LLM_CHATTER_GROUP_H
#define MOD_LLM_CHATTER_GROUP_H

#include "Define.h"

class Player;

void LoadNamedBossCache();
void CheckGroupCombatState();
void FlushQuestAcceptBatches();
void FlushGroupJoinBatches();
void HandleGroupPlayerUpdateZone(
    Player* player, uint32 newZone,
    uint32 newArea);
void AddLLMChatterGroupScripts();

#endif
