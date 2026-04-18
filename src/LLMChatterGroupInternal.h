/*
 * mod-llm-chatter - group internal shared state
 *
 * Declarations for structs, maps, mutexes, and helpers
 * shared between group compilation units.  This header
 * is NOT part of the public module API -- it exists
 * solely to bridge state across the split group TUs:
 *   LLMChatterGroup.cpp
 *   LLMChatterGroupCombat.cpp
 *   LLMChatterGroupJoin.cpp
 *   LLMChatterGroupEmote.cpp
 *   LLMChatterGroupQuest.cpp
 */

#ifndef MOD_LLM_CHATTER_GROUP_INTERNAL_H
#define MOD_LLM_CHATTER_GROUP_INTERNAL_H

#include "Define.h"
#include "ObjectGuid.h"

#include <ctime>
#include <map>
#include <mutex>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

class Creature;
class Group;
class Player;

// ============================================================
// Group join batching structs
// ============================================================

struct GroupJoinEntry {
    uint32 botGuid{0};
    std::string botName;
    uint8 botClass{0};
    uint8 botRace{0};
    uint8 botGender{0};
    uint8 botLevel{0};
    std::string role;
    uint32 zoneId{0};
    uint32 mapId{0};
};

struct GroupJoinBatch {
    uint32 groupId{0};
    uint32 playerGuid{0};
    std::string playerName;
    uint32 zoneId{0};
    uint32 areaId{0};
    uint32 mapId{0};
    time_t lastJoinTime{0};
    std::vector<GroupJoinEntry> bots;
};

// ============================================================
// Quest accept batching structs
// ============================================================

struct QuestAcceptEntry {
    uint32 questId;
    std::string questName;
    int32 questLevel;
};

struct QuestAcceptBatch {
    uint32 reactorGuid;
    std::string reactorName;
    uint8 reactorClass;
    uint8 reactorRace;
    uint8 reactorGender;
    uint32 reactorLevel;
    std::string acceptorName;
    uint32 zoneId;
    std::string zoneName;
    uint32 mapId;
    uint32 groupId;
    time_t lastAcceptTime;
    std::vector<QuestAcceptEntry> quests;
    // Store details/objectives for single-quest path
    std::string firstQuestDetails;
    std::string firstQuestObjectives;
};

// ============================================================
// Shared mutable state -- extern declarations
//
// Definitions live in LLMChatterGroup.cpp (the
// remaining group glue file).
// ============================================================

// -- Group join batching --
extern std::unordered_map<uint32, GroupJoinBatch>
    _groupJoinBatches;
extern std::mutex _groupJoinBatchMutex;
extern std::unordered_set<uint32>
    _groupJoinFlushed;
extern std::unordered_set<uint32>
    _greetedBotGuids;
extern std::unordered_map<uint32,
    std::vector<uint32>> _groupGreetedBots;

// -- Quest accept batching --
extern std::unordered_map<uint32, QuestAcceptBatch>
    _questAcceptBatches;
extern std::mutex _questBatchMutex;

// -- Per-group+quest timestamp/dedup maps --
extern std::unordered_map<uint64, time_t>
    _questAcceptTimestamps;
extern std::unordered_map<uint64, time_t>
    _questCompleteCd;

// -- Per-group cooldown maps --
extern std::map<uint32, time_t>
    _groupKillCooldowns;
extern std::map<uint32, time_t>
    _groupDeathCooldowns;
extern std::map<uint32, time_t>
    _groupLootCooldowns;
extern std::map<uint32, time_t>
    _groupPlayerMsgCooldowns;
extern std::map<uint32, time_t>
    _groupCombatCooldowns;
extern std::unordered_map<uint32, time_t>
    _groupSpellCooldowns;
extern std::map<uint32, time_t>
    _groupQuestObjCooldowns;
extern std::map<uint32, time_t>
    _groupResurrectCooldowns;
extern std::map<uint32, time_t>
    _groupZoneCooldowns;
extern std::map<uint32, time_t>
    _groupDungeonCooldowns;
extern std::map<uint32, time_t>
    _groupWipeCooldowns;
extern std::map<uint32, time_t>
    _groupCorpseRunCooldowns;

// -- Per-bot state callout cooldowns --
extern std::map<uint32, time_t>
    _botLowHealthCooldowns;
extern std::map<uint32, time_t>
    _botOomCooldowns;
extern std::map<uint32, time_t>
    _botAggroCooldowns;

// -- Emote cooldown maps --
extern std::unordered_map<uint32, time_t>
    _emoteReactCooldowns;
extern std::unordered_map<uint32, time_t>
    _emoteObserverCooldowns;
extern std::unordered_map<uint32, time_t>
    _emoteVerbalCooldowns;
extern std::unordered_map<uint32, time_t>
    _creatureEmoteCooldowns;

// -- Pending rejoin queue (relog) --
struct PendingRejoin
{
    uint32 groupId;
    uint32 playerGuid;
    time_t loginTime;
};
extern std::mutex _rejoinMutex;
extern std::vector<PendingRejoin> _pendingRejoins;

// -- Named boss cache --
extern std::unordered_set<uint32>
    _namedBossEntries;

// ============================================================
// Shared helper functions (defined in
// LLMChatterGroup.cpp)
// ============================================================

bool GroupHasRealPlayer(Group* group);
Player* GetRandomBotInGroup(
    Group* group, Player* exclude = nullptr);
uint32 CountBotsInGroup(Group* group);
bool IsLikelyPlayerbotControlCommand(
    std::string const& message);

// Pre-cache instant reaction helpers
bool TryConsumeCachedReaction(
    uint32 groupId, uint32 botGuid,
    const std::string& category,
    std::string& outMessage,
    std::string& outEmote);
void ResolvePlaceholders(
    std::string& message,
    const std::string& target,
    const std::string& caster,
    const std::string& spell);
void RecordCachedChatHistory(
    uint32 groupId, uint32 botGuid,
    const std::string& botName,
    const std::string& message);

// Cleanup coordinator
void CleanupGroupSession(uint32 groupId);

// Delayed rejoin processing (relog)
void ProcessPendingRejoins();

// ============================================================
// Domain entry-point declarations used by
// LLMChatterGroup.cpp script registration
// ============================================================

// Join domain (LLMChatterGroupJoin.cpp)
void QueueBotGreetingEvent(
    Player* bot, Group* group);
void EnsureGroupJoinQueued(
    Player* bot, Group* group);

// Emote domain (LLMChatterGroupEmote.cpp)
void HandleEmoteAtGroupBot(
    Player* player, Player* targetBot,
    uint32 textEmote, Group* group);
void HandleEmoteAtCreature(
    Player* player, Creature* creature,
    uint32 textEmote);
void HandleEmoteObserver(
    Player* player, uint32 textEmote,
    Group* group,
    uint32 tgtType,
    const std::string& targetName,
    uint32 npcRank, uint32 npcType,
    uint32 npcEntry,
    const std::string& npcSubName,
    const std::vector<Player*>& candidates);

// Emote statics (used by PlayerScript dispatch)
extern const std::unordered_set<uint32>
    s_ignoredEmotes;
extern const std::unordered_set<uint32>
    s_combatCalloutEmotes;

// Emote target type enum (shared between group
// and emote TUs)
enum EmoteTargetType
{
    EMOTE_TGT_NONE,
    EMOTE_TGT_GROUP_BOT,
    EMOTE_TGT_GROUP_PLAYER,
    EMOTE_TGT_EXT_PLAYER,
    EMOTE_TGT_CREATURE,
};

#endif
