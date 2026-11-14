#ifndef MOD_LLM_CHATTER_GROUP_AWARENESS_H
#define MOD_LLM_CHATTER_GROUP_AWARENESS_H

/*
 * mod-llm-chatter - group awareness for non-party speech
 *
 * A grouped bot that speaks outside party/raid chat (proximity
 * /say, General, Guild, yells) is told about its own group, and a
 * line written for it is never spoken after that group changed.
 *
 * Owns, in memory and under one mutex:
 *   - a process-unique epoch,
 *   - per-group membership revisions drawn from one global,
 *     never-reset counter,
 *   - per-membership start times (member_since).
 *
 * The pure guard comparison lives in LLMChatterGroupGuard.h.
 */

#include "Define.h"
#include "ObjectGuid.h"

#include <string>
#include <vector>

class Group;
class Player;

// Group hook bookkeeping. Call as the first statement of the
// GroupScript hooks, before any feature gate, so every
// membership change invalidates queued lines.
void NoteGroupMemberAdded(Group* group, ObjectGuid guid);
void NoteGroupMemberRemoved(Group* group, ObjectGuid guid);
void NoteGroupDisbanded(Group* group);

// The "group" object for a bot speaker; "{}" when ungrouped.
std::string BuildSpeakerGroupJson(Player* bot);

// `"speaker_groups":{"<guid>":{...},...}` for the given speakers
// (no leading comma). Non-bot or null entries are skipped; an
// empty list yields `"speaker_groups":{}`.
std::string BuildSpeakerGroupsField(
    std::vector<Player*> const& speakers);

// Inserts the speaker_groups field into a compact JSON object
// string just before its closing brace. No-op when the object
// is empty or malformed.
void AppendSpeakerGroups(
    std::string& extraJson,
    std::vector<Player*> const& speakers);

// `"bot_groups":{"<guid>":<group object>,...}` for the grouped bots
// of a candidate list (ungrouped bots are left out; no leading
// comma). Used where the payload has guid lists instead of per-bot
// objects (General replies, transport arrivals).
std::string BuildBotGroupsField(std::vector<Player*> const& bots);

// Inserts both bot_groups and speaker_groups for a candidate list,
// like AppendSpeakerGroups. Every candidate gets a guard, grouped
// or not, since any of them may end up speaking.
void AppendCandidateGroups(
    std::string& extraJson,
    std::vector<Player*> const& candidates);

// Delivery check: "speaker_group_changed" when extra_data
// carries a guard for this bot that no longer matches the live
// group state, else nullptr.
char const* SpeakerGroupDropReason(
    std::string const& extraData, uint32 botGuid, Player* bot);

#endif // MOD_LLM_CHATTER_GROUP_AWARENESS_H
