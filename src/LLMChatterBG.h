#ifndef MOD_LLM_CHATTER_BG_H
#define MOD_LLM_CHATTER_BG_H

class Battleground;
class Player;

#include <string>

void AppendBGContext(
    Battleground* bg, Player* player,
    std::string& json);
void QueueBGEvent(
    Player* player,
    const std::string& eventType,
    const std::string& extraJson);
void AddLLMChatterBGScripts();

#endif
