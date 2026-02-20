# Immersion Enhancement: Available Hooks & Infrastructure Report

**Date:** 2026-02-07
**Purpose:** Identify existing AzerothCore and mod-playerbots infrastructure that can be leveraged to enhance bot chat immersion in mod-llm-chatter.

---

# Part 1: mod-playerbots Infrastructure

## 1.1 Communication APIs

All available in `PlayerbotAI.h` (lines 462-478):

```cpp
bool SayToGuild(const std::string& msg);
bool SayToWorld(const std::string& msg);
bool SayToChannel(const std::string& msg, const ChatChannelId& chanId);
bool SayToParty(const std::string& msg);
bool SayToRaid(const std::string& msg);
bool Yell(const std::string& msg);
bool Say(const std::string& msg);
bool Whisper(const std::string& msg, const std::string& receiverName);
bool PlayEmote(uint32 emote);
bool PlaySound(uint32 emote);
```

Implementation in `PlayerbotAI.cpp` (lines 2610-2785) uses `ChatHandler::BuildChatPacket`. Language auto-switches between LANG_COMMON (Alliance) and LANG_ORCISH (Horde).

**Chat Channel Enum** (lines 113-154):
- SRC_GUILD, SRC_WORLD, SRC_GENERAL, SRC_TRADE, SRC_LOOKING_FOR_GROUP
- SRC_LOCAL_DEFENSE, SRC_WORLD_DEFENSE, SRC_GUILD_RECRUITMENT
- SRC_SAY, SRC_WHISPER, SRC_EMOTE, SRC_TEXT_EMOTE, SRC_YELL, SRC_PARTY, SRC_RAID

## 1.2 Bot State & Context Data

### Health/Mana/Resources
File: `Ai/Base/Trigger/HealthTriggers.h` and `GenericTriggers.h`

- Health percentages (Low/Medium/Critical/AlmostFull)
- Mana status (High/Enough/AlmostFull/Low/Medium)
- Rage, Energy, Combo Points
- PartyMemberLowHealthTrigger - monitor group member health

### Combat State
File: `Ai/Base/Trigger/GenericTriggers.h`

- `BeingAttackedTrigger` - bot is being attacked
- `HasAttackersTrigger` - attacker present
- `MyAttackerCountTrigger` - numeric count of attackers
- `AoeTrigger` - multiple enemies in range
- `TargetChangedTrigger` - target switched
- `HasAggroTrigger` / `LoseAggroTrigger` - aggro state

### Inventory & Items
File: `PlayerbotAI.h` (lines 480-591)

```cpp
Item* FindPoison() const;
Item* FindBandage() const;
Item* FindConsumable(uint32 itemId) const;
std::vector<Item*> GetInventoryAndEquippedItems();
bool HasItemInInventory(uint32 itemId);
```

### Role Detection
File: `PlayerbotAI.h` (lines 419-441)

```cpp
static bool IsTank(Player* player, bool bySpec = false);
static bool IsHeal(Player* player, bool bySpec = false);
static bool IsDps(Player* player, bool bySpec = false);
static bool IsRanged(Player* player, bool bySpec = false);
static bool IsMelee(Player* player, bool bySpec = false);
static bool IsMainTank(Player* player);
```

### Bot State
```cpp
BotState GetState();  // Combat, NonCombat, Dead
std::vector<Player*> GetPlayersInGroup();
void ChangeStrategy(std::string const name, BotState type);
bool HasStrategy(std::string const name, BotState type);
```

## 1.3 Bot Access Pattern

```cpp
#define GET_PLAYERBOT_AI(object) sPlayerbotsMgr.GetPlayerbotAI(object)
PlayerbotAI* botAI = GET_PLAYERBOT_AI(player);
// Then access any value, state, or chat method
```

## 1.4 Existing Broadcast System

File: `Util/BroadcastHelper.h`

Pre-built broadcast functions (could be replaced with LLM-generated equivalents):

```cpp
static bool BroadcastQuestAccepted(PlayerbotAI* ai, Player* bot, const Quest* quest);
static bool BroadcastQuestUpdateComplete(PlayerbotAI* ai, Player* bot, const Quest* quest);
static bool BroadcastQuestTurnedIn(PlayerbotAI* ai, Player* bot, const Quest* quest);
static bool BroadcastKill(PlayerbotAI* ai, Player* bot, Creature* creature);
static bool BroadcastLevelup(PlayerbotAI* ai, Player* bot);
static bool BroadcastLootingItem(PlayerbotAI* ai, Player* bot, const ItemTemplate* proto);
static bool BroadcastGuildMemberPromotion(PlayerbotAI* ai, Player* bot, Player* player);
static bool BroadcastSuggestInstance(PlayerbotAI* ai, std::vector<std::string>& allowedInstances, Player* bot);
static bool BroadcastSuggestQuest(PlayerbotAI* ai, std::vector<uint32>& quests, Player* bot);
```

## 1.5 Trigger System (70+ Types)

### Combat Triggers
- `BeingAttackedTrigger`, `HasAttackersTrigger`, `LoseAggroTrigger`
- `InterruptSpellTrigger`, `MediumThreatTrigger`, `AoeTrigger`

### Health/Death Triggers
- `LowHealthTrigger`, `CriticalHealthTrigger`, `DeadTrigger`
- `PartyMemberDeadTrigger`, `PartyMemberLowHealthTrigger`

### Loot Triggers
- `LootAvailableTrigger`, `CanLootTrigger`, `FarFromCurrentLootTrigger`

### Status Triggers
- `IsMountedTrigger`, `IsSwimmingTrigger`, `IsFallingTrigger`
- `HasPetTrigger`, `NoPetTrigger`, `CorpseNearTrigger`

### Chat Triggers
- `ChatCommandTrigger` - chat commands trigger bot actions

## 1.6 Key Files

| File | Purpose |
|------|---------|
| `src/Bot/PlayerbotAI.h` | Main bot AI interface - chat APIs, state queries |
| `src/Bot/PlayerbotAI.cpp` | Say/Yell/Whisper implementation |
| `src/Bot/Engine/Action/Action.h` | Action framework with priorities |
| `src/Ai/Base/Trigger/GenericTriggers.h` | 100+ trigger types |
| `src/Ai/Base/Trigger/HealthTriggers.h` | Health/death events |
| `src/Ai/Base/Trigger/LootTriggers.h` | Loot events |
| `src/Bot/Cmd/ChatHelper.h` | Format items/quests/spells for display |
| `src/Util/BroadcastHelper.h` | Pre-made broadcast functions |
| `src/Script/Playerbots.cpp` | Script hooks, chat interception |
| `Playerbots.h` | Macros: AI_VALUE, GET_PLAYERBOT_AI |

---

# Part 2: AzerothCore Core Hooks

## 2.1 Already In Use (by mod-llm-chatter)

- **WorldScript** - Day/night transitions, server startup
- **ALEScript** - Weather changes (OnWeatherChange)
- **GameEventScript** - Holiday events (OnStart/OnStop)

## 2.2 PlayerScript Hooks (Highest Value)

File: `src/server/game/Scripting/ScriptDefines/PlayerScript.h`

### Chat & Social

| Hook | Use Case |
|------|----------|
| `OnPlayerBeforeSendChatMessage(Player*, uint32& type, uint32& lang, std::string& msg)` | **HIGH PRIORITY** - React to nearby player chat |
| `OnPlayerEmote(Player*, uint32 emote)` | React when players use emotes |
| `OnPlayerTextEmote(Player*, uint32 textEmote, uint32 emoteNum, ObjectGuid guid)` | React to /wave, /greet, etc. |
| `OnPlayerLogin(Player*)` | Bot greeting on player login |
| `OnPlayerLogout(Player*)` | Bot farewell on logout |

### Milestones & Achievements

| Hook | Use Case |
|------|----------|
| `OnPlayerLevelChanged(Player*, uint8 oldlevel)` | Congratulate level ups |
| `OnPlayerAchievementComplete(Player*, AchievementEntry const*)` | Achievement congratulations |
| `OnPlayerCompleteQuest(Player*, Quest const*)` | Quest completion reactions |
| `OnPlayerReputationRankChange(Player*, uint32 factionID, ReputationRank new, ReputationRank old, bool increased)` | Faction rank up acknowledgment |
| `OnPlayerLearnSpell(Player*, uint32 spellID)` | Spell learning reactions |

### Combat

| Hook | Use Case |
|------|----------|
| `OnPlayerCreatureKill(Player*, Creature*)` | Kill reactions |
| `OnPlayerEnterCombat(Player*, Unit* enemy)` | Combat encouragement |
| `OnPlayerLeaveCombat(Player*)` | Post-combat banter |
| `OnPlayerDuelStart(Player*, Player*)` | Duel commentary |
| `OnPlayerDuelEnd(Player*, Player*, DuelCompleteType)` | Duel outcome reactions |
| `OnPlayerResurrect(Player*, float restore_percent, bool applySickness)` | Resurrection reactions |

### Location & Discovery

| Hook | Use Case |
|------|----------|
| `OnPlayerUpdateZone(Player*, uint32 newZone, uint32 newArea)` | Zone change reactions |
| `OnPlayerUpdateArea(Player*, uint32 oldArea, uint32 newArea)` | Area discovery comments |
| `OnPlayerMapChanged(Player*)` | Map change events |

### Economy & Loot

| Hook | Use Case |
|------|----------|
| `OnPlayerLootItem(Player*, Item*, uint32 count, ObjectGuid lootguid)` | Loot reactions |
| `OnPlayerMoneyChanged(Player*, int32& amount)` | Rich/poor comments |
| `OnPlayerEquip(Player*, Item*, uint8 bag, uint8 slot, bool update)` | Gear equip reactions |

### Skills

| Hook | Use Case |
|------|----------|
| `OnPlayerUpdateGatheringSkill(Player*, uint32 skill_id, ...)` | Mining/herb gathering chatter |
| `OnPlayerUpdateCraftingSkill(Player*, SkillLineAbilityEntry const*, ...)` | Crafting skill reactions |
| `OnPlayerUpdateFishingSkill(Player*, int32 skill, ...)` | Fishing comments |

## 2.3 Group & Guild Hooks

### GroupScript
File: `src/server/game/Scripting/ScriptDefines/GroupScript.h`

| Hook | Use Case |
|------|----------|
| `OnAddMember(Group*, ObjectGuid guid)` | Greet new group members |
| `OnRemoveMember(Group*, ObjectGuid guid, RemoveMethod, ...)` | React to member departure |
| `OnChangeLeader(Group*, ObjectGuid new, ObjectGuid old)` | Leadership change comments |
| `OnDisband(Group*)` | Group disbanding reactions |

### GuildScript
File: `src/server/game/Scripting/ScriptDefines/GuildScript.h`

| Hook | Use Case |
|------|----------|
| `OnAddMember(Guild*, Player*, uint8& plRank)` | Guild join announcements |
| `OnRemoveMember(Guild*, Player*, bool isDisbanding, bool isKicked)` | Guild departure reactions |
| `OnMOTDChanged(Guild*, const std::string& newMotd)` | MOTD comments |
| `OnEvent(Guild*, uint8 eventType, ...)` | Promotions/demotions |

## 2.4 Auction House Hooks

File: `src/server/game/Scripting/ScriptDefines/AuctionHouseScript.h`

| Hook | Use Case |
|------|----------|
| `OnAuctionAdd(AuctionHouseObject*, AuctionEntry*)` | Auction posting reactions |
| `OnAuctionSuccessful(AuctionHouseObject*, AuctionEntry*)` | Auction win celebrations |
| `OnAuctionExpire(AuctionHouseObject*, AuctionEntry*)` | Auction expiry comments |

## 2.5 Unit & Combat Hooks

File: `src/server/game/Scripting/ScriptDefines/UnitScript.h`

| Hook | Use Case |
|------|----------|
| `OnHeal(Unit* healer, Unit* receiver, uint32& gain)` | Healing comments |
| `OnDamage(Unit* attacker, Unit* victim, uint32& damage)` | Big hit reactions |
| `OnUnitDeath(Unit*, Unit* killer)` | Death reactions |
| `OnAuraApply(Unit*, Aura*)` | Buff/debuff reactions |

**Performance warning**: OnHeal/OnDamage fire very frequently during combat.

## 2.6 Global/Instance Hooks

File: `src/server/game/Scripting/ScriptDefines/GlobalScript.h`

| Hook | Use Case |
|------|----------|
| `OnBeforeSetBossState(uint32 id, EncounterState new, EncounterState old, Map*)` | Boss kill reactions |
| `OnAfterUpdateEncounterState(Map*, EncounterCreditType, ...)` | Raid event reactions |

## 2.7 Emote System

100+ emote types available in `SharedDefines.h`:
- `EMOTE_ONESHOT_WAVE`, `EMOTE_ONESHOT_CHEER`, `EMOTE_ONESHOT_BOW`
- `EMOTE_ONESHOT_LAUGH`, `EMOTE_ONESHOT_CRY`, `EMOTE_ONESHOT_DANCE`
- `EMOTE_ONESHOT_ROAR`, `EMOTE_ONESHOT_POINT`, `EMOTE_ONESHOT_SALUTE`
- And 90+ more

Usage: `player->HandleEmoteCommand(EMOTE_ONESHOT_WAVE);`

Bots could physically emote alongside chat messages for extra immersion.

## 2.8 Game Event System

File: `src/server/game/Events/GameEventMgr.h`

```cpp
ActiveEvents const& GetActiveEventList() const;
bool IsActiveEvent(uint16 eventId);
```

Seasonal events: Hallow's End, Winter Veil, Lunar Festival, Brewfest, Midsummer Fire Festival, Love Festival, fishing tournaments, etc.

Bots could reference active holidays in their chatter.

---

# Part 3: Prioritized Opportunities

## Tier 1 - High Impact, Low Effort

| Feature | Hooks Needed | Description | Status |
|---------|-------------|-------------|--------|
| **Chat reactions** | `OnPlayerBeforeSendChatMessage` | Bots respond to nearby player chat in General | [x] Implemented (player_general_msg + group player_msg) |
| **Emotes** | `PlayEmote()` from PlayerbotAI | Bots wave, cheer, dance alongside chat | [x] Implemented (243 TEXT_EMOTE_* emotes, JSON emote field, keyword fallback) |
| **Level congrats** | `OnPlayerLevelChanged` | Nearby bots congratulate level ups | [x] Implemented (bot_group_levelup) |
| **Seasonal chatter** | `GameEventMgr::GetActiveEventList()` | Holiday-themed messages (Brewfest, Hallow's End) | [x] Implemented (GameEventScript + holiday detection) |

## Tier 2 - Medium Impact

| Feature | Hooks Needed | Description | Status |
|---------|-------------|-------------|--------|
| **Quest reactions** | `OnPlayerCompleteQuest` | Bots comment on quest turn-ins | [x] Implemented (bot_group_quest_complete, bot_group_quest_accept, bot_group_quest_objectives) |
| **Zone awareness** | `OnPlayerUpdateZone` | Comments when entering new zones | [x] Implemented (bot_group_zone_transition, bot_group_discovery, bot_group_dungeon_entry) |
| **Login/logout** | `OnPlayerLogin` / `OnPlayerLogout` | Greetings and farewells | [ ] Not implemented |
| **Combat context** | `OnPlayerEnterCombat/LeaveCombat` | Post-combat banter with bot state (health, mana) | [x] Implemented (bot_group_combat, bot_group_low_health, bot_group_oom, bot_group_aggro_loss) |
| **Duel commentary** | `OnPlayerDuelStart/End` | Bots react to nearby duels | [ ] Not implemented |

## Tier 3 - Nice to Have

| Feature | Hooks Needed | Description | Status |
|---------|-------------|-------------|--------|
| **Achievement praise** | `OnPlayerAchievementComplete` | Bots congratulate achievements | [x] Implemented (bot_group_achievement) |
| **Emote responses** | `OnPlayerTextEmote` | Bot responds to /wave with /wave + comment | [ ] Not implemented |
| **Loot reactions** | `OnPlayerLootItem` | Bots react to nearby loot | [x] Implemented (bot_group_loot + group roll) |
| **Skill chatter** | `OnPlayerUpdateGatheringSkill` | Fishing/mining/herb gathering comments | [ ] Not implemented |
| **Reputation milestones** | `OnPlayerReputationRankChange` | Acknowledge faction rank ups | [ ] Not implemented |
| **Guild events** | `GuildScript::OnEvent` | Promotion/demotion reactions | [ ] Not implemented |

## Tier 4 - Future / Group Chatter (see grouped-bot-chatter-feasibility-report.md)

| Feature | Hooks Needed | Description | Status |
|---------|-------------|-------------|--------|
| **Group chatter** | GroupScript + PlayerScript | Full party chat with conversation memory | [x] Implemented (21 event types, idle chatter, pre-cache, group join/leave) |
| **Boss reactions** | `OnBeforeSetBossState` | Boss kill/wipe reactions in dungeons | [x] Partially (bot_group_dungeon_entry + bot_group_wipe, no direct boss state hook yet) |
| **Combat callouts** | UnitScript OnHeal/OnDamage | Real-time combat banter (performance concern) | [x] Partially (bot_group_spell_cast for spells, bot_group_resurrect for rez; no per-heal/damage hooks) |

---

# Part 4: Performance Notes

## Safe Hooks (Event-Based, Low Overhead)
- All PlayerScript event hooks (login, quest, achievement, level, zone change)
- GameEventScript callbacks
- ALEScript weather changes
- GroupScript/GuildScript membership changes
- AuctionHouseScript callbacks

## Dangerous Hooks (High Frequency, Use With Gates)
- `WorldScript::OnUpdate` - called every server tick (~100ms)
- `MovementHandlerScript::OnPlayerMove` - every player movement packet
- `UnitScript::OnHeal/OnDamage` - every heal/damage event in combat
- `OnPlayerBeforeUpdate` - every frame per player

**Mitigation**: Always use cooldowns, chance rolls, and early-exit checks before any expensive logic.

---

# Part 5: Key File References

## AzerothCore Core
| Path | Content |
|------|---------|
| `src/server/game/Scripting/ScriptDefines/PlayerScript.h` | All player hooks |
| `src/server/game/Scripting/ScriptDefines/GroupScript.h` | Group hooks |
| `src/server/game/Scripting/ScriptDefines/GuildScript.h` | Guild hooks |
| `src/server/game/Scripting/ScriptDefines/ALEScript.h` | Weather/area hooks |
| `src/server/game/Scripting/ScriptDefines/GameEventScript.h` | Holiday hooks |
| `src/server/game/Scripting/ScriptDefines/UnitScript.h` | Combat hooks |
| `src/server/game/Scripting/ScriptDefines/GlobalScript.h` | Boss/instance hooks |
| `src/server/game/Scripting/ScriptDefines/AuctionHouseScript.h` | AH hooks |
| `src/server/game/Events/GameEventMgr.h` | Seasonal event system |
| `src/server/game/Weather/Weather.h` | Weather states |
| `src/server/shared/SharedDefines.h` | Emote constants |

## mod-playerbots
| Path | Content |
|------|---------|
| `modules/mod-playerbots/src/Bot/PlayerbotAI.h` | Chat APIs, state queries, role detection |
| `modules/mod-playerbots/src/Bot/PlayerbotAI.cpp` | Chat implementation |
| `modules/mod-playerbots/src/Ai/Base/Trigger/GenericTriggers.h` | 100+ triggers |
| `modules/mod-playerbots/src/Ai/Base/Trigger/HealthTriggers.h` | Health/death |
| `modules/mod-playerbots/src/Util/BroadcastHelper.h` | Pre-made broadcasts |
| `modules/mod-playerbots/src/Script/Playerbots.cpp` | Script hooks |
| `modules/mod-playerbots/Playerbots.h` | GET_PLAYERBOT_AI macro |

## mod-llm-chatter (current)
| Path | Content |
|------|---------|
| `modules/mod-llm-chatter/src/LLMChatterScript.cpp` | Current C++ hooks |
| `modules/mod-llm-chatter/tools/llm_chatter_bridge.py` | Python bridge |
