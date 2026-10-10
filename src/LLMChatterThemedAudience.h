/*
 * mod-llm-chatter - listener JSON for themed topics and rumors
 */

#ifndef MOD_LLM_CHATTER_THEMED_AUDIENCE_H
#define MOD_LLM_CHATTER_THEMED_AUDIENCE_H

#include <string>
#include <vector>

class Player;

// One listener object: guid, name, level, team, race and class.
std::string BuildAudienceJson(Player* player);

// JSON array of listener objects; "[]" when there are none.
std::string BuildAudienceListJson(std::vector<Player*> const& players);

#endif
