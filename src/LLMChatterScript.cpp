/*
 * mod-llm-chatter - registration coordinator
 */

#include "LLMChatterBG.h"
#include "LLMChatterGroup.h"
#include "LLMChatterRaid.h"
#include "LLMChatterShared.h"

void AddLLMChatterScripts()
{
    AddLLMChatterWorldScripts();
    AddLLMChatterGroupScripts();
    AddLLMChatterPlayerScripts();
    AddLLMChatterBGScripts();
    AddLLMChatterRaidScripts();
}
