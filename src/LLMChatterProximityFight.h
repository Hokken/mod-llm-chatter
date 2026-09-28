#ifndef MOD_LLM_CHATTER_PROXIMITY_FIGHT_H
#define MOD_LLM_CHATTER_PROXIMITY_FIGHT_H

#include <string>

// World-thread driver: rolls duel moments, fires due
// moments and PvP kill scenes, and plays staggered emotes.
void ProcessPendingFightMoments();

// Delivery-time revalidation for proximity rows whose event
// carries `fight_kind`. False means the scene is stale (the
// challenge was cancelled, the duel ended or was replaced by
// a rematch, or the line is too old) and the row is dropped.
bool IsProximityFightLineStillValid(
    std::string const& eventExtraData);

void AddLLMChatterProximityFightScripts();

#endif
