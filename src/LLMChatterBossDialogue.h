#ifndef MOD_LLM_CHATTER_BOSS_DIALOGUE_H
#define MOD_LLM_CHATTER_BOSS_DIALOGUE_H

#include "Define.h"

#include <string>

class Creature;
class Player;

void CheckBossProximityDialogue();
bool HandleBossProximityPlayerSay(
    Player* player, std::string const& message);
bool IsBossDialogueSpeakerEligible(
    Player* player, Creature* creature, float radius);
bool IsBossDialogueEntryDenied(uint32 creatureEntry);

#endif
