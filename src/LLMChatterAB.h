#ifndef MOD_LLM_CHATTER_AB_H
#define MOD_LLM_CHATTER_AB_H

#include "Define.h"
#include <string>
#include <string_view>
#include <vector>

class Battleground;

// World-thread mutation only; no live object is retained by these helpers.
void ObserveABContext(Battleground* bg, uint32 diff);
void ResetABContext(uint32 instanceId);
void QueueABNodeBatch(Battleground* bg);
void QueueABScoreMilestone(Battleground* bg);
bool TryABObjectiveStatus(Battleground* bg);

// Registers the verified banner-interaction hooks (map threads).
void AddLLMChatterABScripts();

// Copies a published value under a short lock; safe for player/map hooks.
// Appends to a complete JSON object, preserving its closing brace.
void AppendABContext(uint32 instanceId, std::string& json);

// World-thread guard: checks revisions and live nodes, not just cached state.
bool IsABNodeEventCurrent(Battleground* bg, std::string_view json);
bool IsABSnapshotCurrent(Battleground* bg, std::string_view snapshot,
    uint64 nowMs, uint32 maxAgeSec);

#endif
