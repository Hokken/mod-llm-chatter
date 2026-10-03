/*
 * mod-llm-chatter - listener JSON for themed topics and rumors
 */

#ifndef MOD_LLM_CHATTER_THEMED_AUDIENCE_H
#define MOD_LLM_CHATTER_THEMED_AUDIENCE_H

#include <string>
#include <vector>

class Player;

// One listener object: level, team, race, class and the
// mod-individual-progression state when that module is active.
std::string BuildAudienceJson(Player* player);

// JSON array of listener objects; "[]" when there are none.
std::string BuildAudienceListJson(std::vector<Player*> const& players);

#endif
