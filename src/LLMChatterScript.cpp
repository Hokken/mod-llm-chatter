/*
 * mod-llm-chatter - registration coordinator
 */

#include "LLMChatterBG.h"
#include "LLMChatterGuild.h"
#include "LLMChatterGroup.h"
#include "LLMChatterRaid.h"
#include "LLMChatterShared.h"

void AddLLMChatterCommandScripts();

void AddLLMChatterScripts()
{
    AddLLMChatterWorldScripts();
    AddLLMChatterGuildScripts();
    AddLLMChatterGroupScripts();
    AddLLMChatterPlayerScripts();
    AddLLMChatterWhisperScripts();
    AddLLMChatterBGScripts();
    AddLLMChatterRaidScripts();
    AddLLMChatterCommandScripts();
}
