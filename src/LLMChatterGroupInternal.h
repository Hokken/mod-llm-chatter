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
 *   LLMChatterGroupPvP.cpp
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
class Unit;

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
extern std::mutex _emoteCooldownMutex;

// -- Pending rejoin queue (relog) --
struct PendingRejoin
{
    uint32 groupId;
    uint32 playerGuid;
    time_t loginTime;
};
extern std::mutex _rejoinMutex;
extern std::vector<PendingRejoin> _pendingRejoins;

// ============================================================
// Shared helper functions (defined in
// LLMChatterGroup.cpp)
// ============================================================

bool GroupHasRealPlayer(Group* group);
// requireAlive=false is for reactions that dead bots may
// deliver in party chat, such as a full group wipe.
Player* GetRandomBotInGroup(
    Group* group, Player* exclude = nullptr,
    bool requireAlive = true);
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

// ============================================================
// Overworld PvP domain (LLMChatterGroupPvP.cpp)
// ============================================================

// An opposing-faction enemy. `enemy` is always the
// player; `unit` is the unit actually involved (the
// player or its pet). Real players and playerbots are
// both Player objects and are handled alike.
struct PvPEnemyRef
{
    Player* enemy{nullptr};
    Unit* unit{nullptr};
    bool viaPet{false};
};

enum class PvPEventKind : uint8
{
    Combat = 1,
    Kill = 2,
    Death = 3,
};

// Returns the opposing-faction player behind `unit`
// (itself or its owner), or nullptr for creatures,
// same-team players, duel opponents, and anything in
// a battleground or arena.
Player* ResolveOpposingFactionPlayer(
    Player* member, Unit* unit);
// Single identity gate; delegates to the shared
// IsUnitPerceivableBy() (map/instance, visibility range,
// distance-aware CanSeeOrDetect).
bool IsPvPEnemyPerceivable(
    Player* reactor, Unit* unit);
// Group bot on the enemy's map, preferring bots that
// can perceive it. nullptr when none is on that map.
Player* SelectPvPReactor(
    Group* group, Player* exclude,
    Unit* enemyUnit, bool requireAlive);
// Enemy name the reactor may know: the player's name,
// else the visible pet's name, else empty.
std::string GetPerceivedPvPEnemyName(
    Player* reactor, PvPEnemyRef const& ref);
char const* DetectPvPInitiator(
    Player* member, Player* enemy);
// JSON fragment (no surrounding braces or trailing
// comma). Identity fields only when perceivable.
std::string BuildPvPEnemyFields(
    Player* reactor, Player* reference,
    PvPEnemyRef const& ref, char const* initiator);
bool TryConsumePvPCooldown(
    uint32 groupId, uint32 enemyGuid,
    PvPEventKind kind, time_t now);
void ClearPvPCooldownsForGroup(uint32 groupId);

// Returns true when the enemy is an opposing-faction
// player, whether or not an event was queued, so the
// caller never falls through to the creature path.
bool HandleGroupPvPEnterCombat(
    Player* player, Unit* enemyUnit);
void HandleGroupPvPKillImpl(
    Player* killer, Player* killed);
// Returns true when a pet owned by an opposing-faction
// player killed `killed` (handled as PvP).
bool HandleGroupPetPvPKill(
    Creature* killer, Player* killed);

// Shared death/wipe path (LLMChatterGroupCombat.cpp).
// pvpEnemy is null for creature deaths.
void QueueGroupDeathOrWipe(
    Player* killed, Group* group,
    std::string const& creatureKillerName,
    uint32 killerEntry,
    PvPEnemyRef const* pvpEnemy);

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

// Free-text /e and /me reach the module through the chat
// hook, not OnPlayerTextEmote, so the chat handler needs this
// ahead of its definition further down LLMChatterGroupCombat.
void HandleGroupPlayerCustomEmoteImpl(
    Player* player, std::string const& text);

// Emote domain (LLMChatterGroupEmote.cpp)
//
// customText carries a free-text /e or /me. When it is
// non-empty textEmote is meaningless (there is no id for a
// custom emote) and only verbal reactions are produced,
// since there is no animation to mirror.
void HandleEmoteAtGroupBot(
    Player* player, Player* targetBot,
    uint32 textEmote, Group* group,
    std::string const& customText = "");
bool HasPlayerbotMirrorEmote(uint32 textEmote);
uint32 HandleEmoteAtUngroupedBot(
    Player* player, Player* targetBot,
    uint32 textEmote);
uint32 HandleEmoteAtCreature(
    Player* player, Creature* creature,
    uint32 textEmote);
// targetPlayer is the emote's target when it is a player
// outside the group, so the observing bot can be told who
// it is looking at rather than just a bare name.
void HandleEmoteObserver(
    Player* player, uint32 textEmote,
    Group* group,
    uint32 tgtType,
    const std::string& targetName,
    uint32 npcRank, uint32 npcType,
    uint32 npcEntry,
    const std::string& npcSubName,
    std::vector<Player*> const& candidates,
    std::string const& customText = "",
    Player* targetPlayer = nullptr);

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
    EMOTE_TGT_UNGROUPED_BOT,
};

#endif
