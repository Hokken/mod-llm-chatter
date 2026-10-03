/*
 * mod-llm-chatter - registration coordinator
 */

#include "LLMChatterAB.h"
#include "LLMChatterBG.h"
#include "LLMChatterGuild.h"
#include "LLMChatterGuildWorld.h"
#include "LLMChatterGroup.h"
#include "LLMChatterLoot.h"
#include "LLMChatterProximityFight.h"
#include "LLMChatterRaid.h"
#include "LLMChatterReplyHold.h"
#include "LLMChatterShared.h"

void AddLLMChatterCommandScripts();

void AddLLMChatterScripts()
{
    AddLLMChatterWorldScripts();
    AddLLMChatterGuildScripts();
    AddLLMChatterGroupScripts();
    AddLLMChatterPlayerScripts();
    AddLLMChatterGuildWorldScripts();
    AddLLMChatterLootScripts();
    AddLLMChatterBGScripts();
    AddLLMChatterABScripts();
    AddLLMChatterRaidScripts();
    AddLLMChatterProximityFightScripts();
    AddLLMChatterCommandScripts();
    AddLLMChatterReplyHoldScripts();
}
