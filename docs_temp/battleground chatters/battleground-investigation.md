# Battleground Support Investigation

Investigation of how mod-llm-chatter can support battleground (BG) scenarios, including current gaps, available hooks, chat channels, and playerbots BG state data.

---

## Current State: No BG Awareness

The chatter module has **zero battleground awareness**. Key problems:

### Problem 1: Bot Join Spam
BGs use **raid groups** (up to 40 players). The `OnAddMember` GroupScript hook fires for every bot joining the raid. In a WSG (10v10), this means up to 9 bot-greeting messages flooding party chat at BG start. In AV (40v40), it could be 39.

### Problem 2: Wrong Chat Channel
All group chatter uses `ai->SayToParty()` which sends `CHAT_MSG_PARTY` (type 0x02). In a BG raid group, the correct channel is `CHAT_MSG_BATTLEGROUND` (type 0x2C) to reach all teammates.

### Problem 3: LLM Has No BG Context
Prompts describe bots as being in a "group" in a "zone" — the LLM doesn't know it's a battleground, what BG type it is, what objectives exist, or what the score is. Reactions to kills/deaths have no PvP flavor.

### Problem 4: Irrelevant Events Fire
Group chatter events like loot reactions, quest objectives, and level-ups would fire during BGs but are contextually wrong. BG events (flag captures, node assaults, wipes) are completely missing.

---

## Available Hooks

### AllBattlegroundScript Hooks (ScriptMgr)

These are global hooks that fire for ALL battlegrounds. We can register our own `AllBattlegroundScript` subclass (alias: `BGScript`).

| Hook | Signature | When It Fires | Chatter Use |
|------|-----------|--------------|-------------|
| `OnBattlegroundCreate` | `(Battleground* bg)` | BG instance created | Internal: initialize state tracking |
| `OnBattlegroundDestroy` | `(Battleground* bg)` | BG instance cleaned up | Internal: clean up state maps |
| `OnBattlegroundBeforeAddPlayer` | `(Battleground* bg, Player* player)` | Start of `AddPlayer()`, before group assignment | Early detection |
| `OnBattlegroundAddPlayer` | `(Battleground* bg, Player* player)` | End of `AddPlayer()`, after group assignment | Arrival comment |
| `OnBattlegroundStart` | `(Battleground* bg)` | BG transitions to `STATUS_IN_PROGRESS` | "Let's do this!" battle cry |
| `OnBattlegroundEnd` | `(Battleground* bg, TeamId winnerTeamId)` | End of `EndBattleground()` | Victory/defeat reaction |
| `OnBattlegroundEndReward` | `(Battleground* bg, Player* player, TeamId winnerTeamId)` | Per-player during reward loop | Individual win/loss reaction |
| `OnBattlegroundUpdate` | `(Battleground* bg, uint32 diff)` | Every BG tick, end of `Battleground::Update()` | State polling (scores, flags, nodes) |
| `OnBattlegroundRemovePlayerAtLeave` | `(Battleground* bg, Player* player)` | End of `RemovePlayerAtLeave()` | Farewell/ragequit comment |

**Additional hooks (queue/matchmaking — less relevant for chatter):**
`OnQueueUpdate`, `OnAddGroup`, `CanFillPlayersToBG`, `IsCheckNormalMatch`, `CanSendMessageBGQueue`, `OnBeforeSendJoinMessageArenaQueue`, `OnBeforeSendExitMessageArenaQueue`

### PlayerScript BG-Specific Hooks

These PlayerScript hooks fire specifically for BG/arena transitions — separate from the general PlayerScript hooks:

| Hook | Signature | When It Fires |
|------|-----------|--------------|
| `OnPlayerAddToBattleground` | `(Player* player, Battleground* bg)` | Player added to BG |
| `OnPlayerRemoveFromBattleground` | `(Player* player, Battleground* bg)` | Player removed from BG |
| `OnPlayerJoinBG` | `(Player* player)` | Player joins a BG |
| `OnPlayerJoinArena` | `(Player* player)` | Player joins an arena |
| `OnPlayerBattlegroundDesertion` | `(Player* player, BattlegroundDesertionType type)` | Player deserts a BG |

### PlayerScript Hooks That Fire in BGs

These existing hooks continue to fire during battlegrounds:

| Hook | BG Relevance |
|------|-------------|
| `OnPlayerPVPKill(killer, killed)` | Player kills player - core BG event |
| `OnPlayerKilledByCreature(creature, killed)` | Killed by NPC (AV bosses, guards) |
| `OnPlayerCreatureKill(killer, creature)` | Killing AV NPCs, bosses |
| `OnPlayerSpellCast(player, spell, skipCheck)` | Heals, buffs during combat |
| `OnPlayerBeforeSendChatMessage(player, type, lang, msg)` | Player types in BG chat |

### BG-Specific Virtual Methods (Not Directly Hookable)

These fire inside specific BG subclasses. We can't hook them via ScriptMgr, but we CAN detect their effects via `OnBattlegroundUpdate`:

| Method | BG | What Happens |
|--------|-----|-------------|
| `EventPlayerCapturedFlag(player)` | WSG | Flag scored (3 caps = win) |
| `EventPlayerDroppedFlag(player)` | WSG/EY | Flag carrier died/dropped flag |
| `EventPlayerClickedOnFlag(player, go)` | WSG/AB/AV/EY | Flag pickup or node click |
| `EventPlayerAssaultsPoint(player, obj)` | AV | Tower/GY assault started |
| `EventPlayerDefendsPoint(player, obj)` | AV | Tower/GY defended |
| `EventPlayerDestroyedPoint(node)` | AV | Tower burned down |
| `HandleKillPlayer(victim, killer)` | All | PvP kill in BG |
| `HandleKillUnit(creature, killer)` | AV | Boss/captain killed |

---

## Chat Channels in BGs

```
CHAT_MSG_PARTY             = 0x02  // Party (sub-group only, NOT full BG team)
CHAT_MSG_RAID              = 0x03  // Raid group (all 10-40 in team)
CHAT_MSG_BATTLEGROUND      = 0x2C  // All BG players on same team
CHAT_MSG_BATTLEGROUND_LEADER = 0x2D // BG leader announcement
CHAT_MSG_BG_SYSTEM_NEUTRAL = 0x24  // Yellow system message (both teams)
CHAT_MSG_BG_SYSTEM_ALLIANCE = 0x25 // Blue system message (Alliance)
CHAT_MSG_BG_SYSTEM_HORDE   = 0x26  // Red system message (Horde)
```

**Recommendation**: Use `CHAT_MSG_BATTLEGROUND` (0x2C) for bot chatter in BGs — this reaches all teammates, which is the equivalent of "party chat" in a BG context.

### PlayerbotAI Chat Methods

| Method | Chat Type | Works in BG? |
|--------|-----------|-------------|
| `SayToParty(msg)` | `CHAT_MSG_PARTY` | Yes, but only reaches sub-group |
| `SayToRaid(msg)` | `CHAT_MSG_RAID` | **BUG**: returns false if `isRaidGroup()` — broken for BGs |

**Note**: There is no `SayToBattleground()` method. We would need to either:
1. Add a new method to PlayerbotAI (modifying mod-playerbots)
2. Build and send the `CHAT_MSG_BATTLEGROUND` packet directly from our module
3. Use `SayToParty()` and accept it only reaches the sub-group (still visible to the real player)

Option 3 is simplest and still works — the real player sees messages from bots in their sub-group. BGs auto-assign sub-groups, so the player's bots would typically be in the same sub-group.

---

## Player BG Detection

```cpp
// Is player in a battleground?
player->InBattleground()                    // bool
player->GetBattleground()                   // Battleground* (or nullptr)
player->GetBattlegroundTypeId()             // BattlegroundTypeId enum

// BG type identification (from DBCEnums.h)
enum BattlegroundTypeId {
    BATTLEGROUND_AV  = 1,   // Alterac Valley (40v40, PvE+PvP)
    BATTLEGROUND_WS  = 2,   // Warsong Gulch (10v10, CTF)
    BATTLEGROUND_AB  = 3,   // Arathi Basin (15v15, nodes)
    BATTLEGROUND_NA  = 4,   // Nagrand Arena
    BATTLEGROUND_BE  = 5,   // Blade's Edge Arena
    BATTLEGROUND_AA  = 6,   // All Arenas
    BATTLEGROUND_EY  = 7,   // Eye of the Storm (15v15, flag+nodes)
    BATTLEGROUND_RL  = 8,   // Ruins of Lordaeron Arena
    BATTLEGROUND_SA  = 9,   // Strand of the Ancients (15v15, siege)
    BATTLEGROUND_DS  = 10,  // Dalaran Sewers Arena
    BATTLEGROUND_RV  = 11,  // Ring of Valor Arena
    BATTLEGROUND_IC  = 30,  // Isle of Conquest (40v40, vehicles)
    BATTLEGROUND_RB  = 32,  // Random Battleground
};

// Map-level detection (Map.h) — delegates to MapEntry DBC data
map->Instanceable()            // true for Dungeons, Raids, BGs, Arenas
map->IsDungeon()               // true for Dungeons AND Raids
map->IsNonRaidDungeon()        // true for 5-man dungeons only
map->IsRaid()                  // true for raids only (10/25-man)
map->IsBattleground()          // true for BGs only (AV, WSG, AB, EY, SA, IC)
map->IsBattleArena()           // true for arenas only
map->IsBattlegroundOrArena()   // true for both BGs and arenas

// NOTE: The ambient General channel chatter already checks !map->Instanceable()
// which correctly blocks it in BGs. Group chatter does NOT have this check
// and will fire in BGs — this is the desired behavior for the group worker.

// Team in BG
player->GetBgTeamId()                       // TEAM_ALLIANCE or TEAM_HORDE

// BG state
bg->GetStatus()                             // STATUS_IN_PROGRESS, etc.
bg->GetTeamScore(TEAM_ALLIANCE)             // Score
bg->GetTeamScore(TEAM_HORDE)
bg->GetPlayersCountByTeam(teamId)           // Player count
bg->GetAlivePlayersCountByTeam(teamId)      // Alive count
bg->GetName()                               // "Warsong Gulch", etc.
```

---

## Battleground State Data Available

### WSG (Warsong Gulch) - Capture The Flag
```cpp
BattlegroundWS* wsg = bg->ToBattlegroundWS();
wsg->GetFlagPickerGUID(TEAM_ALLIANCE)       // Who carries Alliance flag
wsg->GetFlagPickerGUID(TEAM_HORDE)          // Who carries Horde flag
wsg->GetFlagState(teamId)                   // ON_BASE, ON_PLAYER, ON_GROUND
// Score: first to 3 captures wins
```

### AB (Arathi Basin) - Node Control
```cpp
BattlegroundAB* ab = bg->ToBattlegroundAB();
ab->GetCapturePointInfo(nodeId)._ownerTeamId  // Who owns node
ab->GetCapturePointInfo(nodeId)._state         // NEUTRAL, CONTESTED, CAPTURED
// 5 nodes: Stables, Blacksmith, Farm, Lumber Mill, Gold Mine
// First to 1600 points wins
```

### AV (Alterac Valley) - Large-Scale PvE+PvP
```cpp
BattlegroundAV* av = bg->ToBattlegroundAV();
// 16 capturable nodes (graveyards + towers)
// Bosses: Vanndar Stormpike (Alliance), Drek'Thar (Horde)
// Kill enemy boss to win
```

### EY (Eye of the Storm) - Flag + Nodes Hybrid
```cpp
BattlegroundEY* ey = bg->ToBattlegroundEY();
ey->GetFlagPickerGUID()                      // Central flag carrier
ey->GetCapturePointInfo(point)._ownerTeamId  // Base ownership
// 4 bases + 1 central flag, first to 1600 wins
```

---

## Prerequisite: Raid Awareness (Before BG Work)

BGs use raid groups (`GROUPTYPE_BGRAID = 0x03`). The existing group chatter system assumes small parties (2-5 players). Before implementing BG-specific features, raid-aware group chatter must work correctly. This is a natural stepping stone because:

- The same GroupScript hooks (`OnAddMember`, `OnRemoveMember`, `OnDisband`) fire identically for parties, raids, and BG raids — there are no separate raid-specific hooks
- All PlayerScript hooks (`OnPlayerCreatureKill`, `OnPlayerLootItem`, spell casts, etc.) fire regardless of group type
- `SayToParty()` already works in raids — it sends `CHAT_MSG_PARTY` which reaches the sub-group (the 5-person party within the raid), and the real player is in the same sub-group as their bots
- The existing group chatter is essentially **plug-and-play in raids** — it just needs volume tuning

### Raid Group Type Detection

```cpp
// Group type flags (GroupType enum)
GROUPTYPE_NORMAL  = 0x00  // Normal party (2-5)
GROUPTYPE_BG      = 0x01  // BG flag
GROUPTYPE_RAID    = 0x02  // Raid flag
GROUPTYPE_BGRAID  = 0x03  // BG + Raid (all BG groups)

// Detection methods
group->isRaidGroup()  // true for raids AND BG raids (checks GROUPTYPE_RAID flag)
group->isBGGroup()    // true ONLY for BG groups (checks m_bgGroup != nullptr)
group->isBFGroup()    // true ONLY for Battlefield groups (Wintergrasp)

// Clean distinction:
// Normal raid (dungeon/raid instance): isRaidGroup()=true, isBGGroup()=false
// BG raid: isRaidGroup()=true, isBGGroup()=true
```

### What Needs Tuning for Raids

The philosophy: **sub-group = the social unit, raid-wide = epic moments only**. Most chatter stays intimate within the player's sub-group. Rare, impactful events (boss kills, wipes) get raid-wide reactions that make the player feel the scale.

**Scoping to sub-groups:**
```cpp
uint8 playerSubGroup = player->GetSubGroup();
// Only pick bots from the same sub-group for reactions
// SayToParty() already delivers to sub-group only — this is correct
```

**Events that should work at sub-group level (existing logic, just scoped):**
- Greetings (throttled — pick 1-2 bots from sub-group, not all raid members)
- Kill/death reactions
- Loot reactions
- Spell cast reactions
- Player chat responses

**Events that should be disabled in raids:**
- Idle chatter / ambient banter
- Group composition commentary

**Events that deserve raid-wide delivery (epic moments):**
- Boss kills
- Wipes
- Legendary/epic loot (raid-wide celebration)

### Dual-Worker Architecture for Raids and BGs

Two separate processing layers react to the same events:

**Raid Worker** — the "crowd"
- Listens to raid-scope events: boss kills, wipes, phase transitions, epic loot
- Picks random bots from **across the whole raid** (outside the player's sub-group) to speak
- Delivers via raid chat (`CHAT_MSG_RAID`) — requires building the packet manually since `SayToRaid()` is broken
- Low frequency, high impact — makes the player feel surrounded by a living raid
- Lightweight bot identity — race/class is enough for personality, no full trait generation needed

**Group Worker** — the "squad" (existing system, sub-group scoped)
- All current group chatter logic: greetings, kills, loot, spells, player responses
- Also reacts to raid events — so a boss kill triggers both a raid-wide callout AND a sub-group personal comment
- Scoped to the player's sub-group only
- Delivers via `SayToParty()` as today
- Higher frequency, intimate feel

**Coordination between workers:**
- The bot picked by the raid worker for a given event must NOT also be the one reacting in the group worker
- Separate cooldowns per worker, but a shared "big event" cooldown to prevent 5+ simultaneous messages from one event
- Both workers can access mood drift data — a bot who's been dying all raid sounds frustrated regardless of which worker picks them

This dual-worker model applies to both normal raids AND battlegrounds. In BGs, the raid worker handles BG-specific events (flag captures, match start/end) while the group worker handles combat events (kills, deaths, spells) scoped to the sub-group.

### SayToRaid Packet Construction

Since `PlayerbotAI::SayToRaid()` has an inverted condition bug and cannot be relied on, the raid worker must build `CHAT_MSG_RAID` packets directly:

```cpp
// Same pattern as SayToParty but with CHAT_MSG_RAID
WorldPacket data;
ChatHandler::BuildChatPacket(data, CHAT_MSG_RAID, msg.c_str(),
    LANG_UNIVERSAL, CHAT_TAG_NONE, bot->GetGUID(), bot->GetName());
// Send to each real player in the group via GetRealPlayersInGroup()
```

For BG-specific team chat, use `CHAT_MSG_BATTLEGROUND` (0x2C) instead of `CHAT_MSG_RAID`.

### Performance Note: GetRealPlayersInGroup()

`PlayerbotAI::GetRealPlayersInGroup()` iterates ALL group members on every call. In a 40-player AV this means 40 iterations per message delivery. For the raid worker, consider caching the real player list per tick or using an early-exit pattern since most raids have only 1 real player.

---

## Proposed Architecture

### Phase 1: BG Awareness (Minimum Viable)

**Goal**: Make existing group chatter BG-aware without adding BG-specific events.

1. **Detect BG context in C++**: Add `player->InBattleground()` checks
2. **Suppress irrelevant events**: Skip bot-greeting spam, loot reactions, quest events in BGs
3. **Add BG context to extra_data**: Include `in_battleground`, `bg_type`, `bg_name` in event JSON
4. **Python prompt awareness**: When `in_battleground` is true, adjust prompts for PvP context
5. **Chat channel**: Keep `SayToParty()` for now (works, reaches sub-group)

### Phase 2: BG-Specific Events

**Goal**: Add exciting BG events using AllBattlegroundScript hooks.

#### New Events (via AllBattlegroundScript)

| Event Type | Hook | Trigger |
|-----------|------|---------|
| `bg_match_start` | `OnBattlegroundStart` | Match begins |
| `bg_match_end` | `OnBattlegroundEnd` | Match ends (win/lose) |
| `bg_pvp_kill` | `OnPlayerPVPKill` (PlayerScript) | Bot kills enemy player |
| `bg_pvp_death` | `OnPlayerKilledByCreature`/`OnPlayerPVPKill` | Bot dies to enemy |

#### New Events (via OnBattlegroundUpdate polling)

Since we can't directly hook flag/node events, we poll state changes in `OnBattlegroundUpdate`:

| Event Type | Detection Method | Trigger |
|-----------|-----------------|---------|
| `bg_flag_captured` | Track `GetTeamScore()` changes | Score increased = flag captured |
| `bg_flag_picked_up` | Track `GetFlagPickerGUID()` changes | Flag goes from base to player |
| `bg_flag_dropped` | Track `GetFlagState()` changes | Flag goes to ground |
| `bg_node_captured` | Track `GetCapturePointInfo()` changes | Node ownership changed |
| `bg_node_contested` | Track node state changes | Node being captured |

This polling approach in `OnBattlegroundUpdate` is clean because:
- It runs every world tick, so detection is near-instant
- We store previous state and compare to detect transitions
- No need to modify BG subclasses or playerbots code

### Phase 3: Rich BG Prompts

**Goal**: Give the LLM full BG context for exciting reactions.

Extra data passed to Python for BG events:
```json
{
    "bg_type": "Warsong Gulch",
    "bg_type_id": 1,
    "team": "Alliance",
    "score_alliance": 1,
    "score_horde": 2,
    "players_alive_team": 7,
    "players_alive_enemy": 9,
    "flag_carrier_team": "Dralidan",
    "flag_carrier_enemy": "",
    "event_detail": "Your team captured the Horde flag!"
}
```

The LLM would generate contextually rich reactions:
- "One more capture and we've got this!"
- "Protect Dralidan, he's got the flag!"
- "They're only up by one, we can still win!"
- "Stables is under attack, someone get back there!"

---

## Implementation Complexity

| Phase | Scope | Files Changed | Difficulty |
|-------|-------|--------------|------------|
| Phase 1 | BG awareness + suppression | 2 C++, 1 Python | Low |
| Phase 2 | BG-specific events | 2 C++, 2 Python, 1 SQL | Medium |
| Phase 3 | Rich BG prompts | 1 Python (prompts) | Low |

### Phase 1 Changes (Recommended First Step)

**C++ (LLMChatterScript.cpp)**:
- Add `player->InBattleground()` check in `OnAddMember` — skip greeting or heavily throttle
- Add `bot->InBattleground()` check in kill/death/loot handlers — skip or tag as PvP
- Add BG context to `extra_data` JSON in existing handlers

**Python (chatter_group.py)**:
- Check `in_battleground` flag in event extra_data
- Adjust prompts for PvP context when in BG
- Skip non-PvP events (loot quality checks, quest objectives)

### Phase 2 Changes

**C++ (LLMChatterScript.cpp)**:
- New `LLMChatterBGScript : public AllBattlegroundScript` class
- State tracking maps for flag/node/score per BG instance
- `OnBattlegroundUpdate` polling loop with change detection
- Event queue insertion for BG events

**Python (chatter_group.py)**:
- New `build_bg_*_prompt()` functions for each BG event type
- New `process_bg_*_event()` handlers
- BG-specific prompt context (scores, objectives, team)

**SQL**:
- New ENUM values: `bg_match_start`, `bg_match_end`, `bg_pvp_kill`, `bg_flag_captured`, `bg_node_captured`, etc.

---

## Key Technical Notes

### SayToRaid Bug in Playerbots
`PlayerbotAI::SayToRaid()` at line 2728 has an inverted condition:
```cpp
if (!bot->GetGroup() || bot->GetGroup()->isRaidGroup())
    return false;  // BUG: returns false when IS raid group
```
This means `SayToRaid()` is broken for BGs. We should NOT rely on it. Use `SayToParty()` instead (still works, just reaches sub-group not full team).

### BG Groups Are Raid Groups
`Group::isRaidGroup()` returns true in BGs. Our existing `GroupHasRealPlayer()` iterates all members — in a 40-player AV raid, this iterates 40 players every hook call. Performance consideration for high-frequency hooks.

### OnBattlegroundUpdate Frequency
`OnBattlegroundUpdate` fires every world server tick (~50ms). State polling must be lightweight:
- Store previous state in a static map keyed by BG instance ID
- Compare only when diff accumulates past a threshold (e.g., every 1-2 seconds)
- Clean up when `OnBattlegroundDestroy` fires

### Bot Sub-Group Assignment
In BGs, the raid is split into sub-groups. The real player's bots are typically in the same sub-group. `SayToParty()` sends to the party (sub-group), so the real player still sees the messages. This is actually desirable — full BG chat with 40 people would be too noisy.

### Arena Exclusion
Arenas (2v2, 3v3, 5v5) are also "battlegrounds" technically (`bg->isArena()` returns true). Chatter should probably be disabled in arenas — they're short, intense, and chat would be distracting. Always check `bg->isBattleground()` (true for BGs, false for arenas) rather than `player->InBattleground()` (true for both).

### BG Queue/Join Transition Flow

When a player accepts a BG queue pop, this sequence occurs:

1. **Bots do NOT follow masters into BGs** — they queue independently via playerbots `BGJoinAction` and accept via `CMSG_BATTLEFIELD_PORT`. There is no automatic "follow master" mechanic for BGs.
2. **Original world group is preserved** — `player->GetOriginalGroup()` stores the pre-BG group. It's restored on BG exit.
3. **A new BG raid group is created** per team via `AddOrSetPlayerToCorrectBgGroup()`. This calls `group->AddMember(player)` which fires `OnAddMember` GroupScript hooks — this is the source of greeting spam.
4. **On BG exit**, the player returns to their original world group automatically.

**Transition concerns:**
- The `OnRemoveMember` hook does NOT fire during BG entry for the original group — the group is preserved, not disbanded
- However, if bots are removed from the world group for other reasons during BG, farewell messages could fire incorrectly — suppress farewells when `player->InBattleground()` or `player->InBattlegroundQueue()`
- `OnAddMember` fires for each bot joining the BG raid — this is where greeting suppression must happen for BG groups (check `group->isBGGroup()`)

### BG Battleground Status Enum

```cpp
enum BattlegroundStatus
{
    STATUS_NONE       = 0,  // not instanced
    STATUS_WAIT_QUEUE = 1,  // empty, waiting for queue
    STATUS_WAIT_JOIN  = 2,  // players entering, countdown (pre-gate phase)
    STATUS_IN_PROGRESS = 3, // running
    STATUS_WAIT_LEAVE = 4   // winner declared, ending
};
```

### TeamId vs PvPTeamId Gotcha

```cpp
// IMPORTANT: These have OPPOSITE ordinals for Alliance/Horde
enum TeamId    { TEAM_ALLIANCE = 0, TEAM_HORDE = 1, TEAM_NEUTRAL = 2 };
enum PvPTeamId { PVP_TEAM_HORDE = 0, PVP_TEAM_ALLIANCE = 1, PVP_TEAM_NEUTRAL = 2 };

// EndBattleground() takes PvPTeamId internally, but the OnBattlegroundEnd hook
// receives TeamId (converted via GetTeamId()). Always use the hook parameter directly.
```

### Anti-Repetition: Instance ID vs Zone ID

The existing anti-repetition system uses `zone_id` for cooldown keys. Multiple concurrent BG instances share the same zone ID (all WSG instances are zone 3277). This means a cooldown triggered in one WSG instance would incorrectly suppress messages in a different WSG instance. **Extend the cooldown key to include `bg->GetInstanceID()`** for BG events.

### AV Turn-In Items Exception

Loot reactions are suppressed in BGs, but Alterac Valley has collectible turn-in items (Armor Scraps, Storm Crystals, Frostwolf Medallions, etc.) that are core BG objectives. Consider a BG-specific loot allowlist for AV rather than blanket suppression.

### Flag Carrier Death Optimization

In addition to polling `GetFlagState()` in `OnBattlegroundUpdate`, the `OnPlayerPVPKill` hook can provide instant flag-drop detection by comparing the victim's GUID against `GetFlagPickerGUID()`. This gives a more precise and immediate reaction: "Dropped their carrier!" rather than the generic "Flag's down!" from state polling.

### SotA Round Swap Detection

Strand of the Ancients has two rounds where teams swap attacker/defender roles. The `OnBattlegroundUpdate` polling needs to detect this phase transition and pass the current role (attacking/defending) to the LLM — the tone is completely different between offense and defense. Track `bg->GetStatus()` transitions and team role assignments.

### IoC Vehicle Context

Isle of Conquest has siege engines, demolishers, glaive throwers, and catapults. `player->GetVehicle()` can detect if a bot is in a vehicle. Not critical for initial implementation but would add depth for IoC-specific reactions.

### Dynamic Scaling in Raids/BGs

The existing dynamic trigger scaling (chance divided by number of bots in group) already reduces reaction chances as group size grows. This same logic must apply at the **sub-group level** for the group worker in raids, not the full raid size. The goal: **message volume should stay constant regardless of how many bots are in the raid**. A player in a 5-bot party and a player in a 40-bot raid should experience roughly the same frequency of sub-group chatter.

For the group worker:
- Scale chances by sub-group bot count (typically 4), not total raid bot count
- Idle chatter disabled entirely in raids — no scaling needed

For the raid worker:
- Scale by total raid size to stay subtle at any scale
- A 10-man and a 40-man raid should produce similar raid-wide message rates
- Low base frequency (much lower than group worker) ensures it stays background atmosphere

### Emote Delivery for Raid/BG Channels

The current emote system only delivers emotes for `channel=="party"`. For the raid worker's messages delivered via `CHAT_MSG_RAID` or `CHAT_MSG_BATTLEGROUND`, the emote delivery guard in C++ needs to be extended to also allow emotes for these channels. Without this, emotes like `/charge` at gates opening or `/cheer` on boss kills would silently be dropped.

### Pre-Cache Candidates for BG

The highest-value pre-cache categories for BGs are:
- **Match start** — gates open, multiple bots need battle cries simultaneously. Zero-latency critical.
- **PvP kills** — happen fast and frequently. Pre-cached "Got one!" / "Nice kill!" feels much more responsive than 3-8s LLM latency.
- **Flag captures** — team-wide celebration moments, should feel instant.

These are predictable events with templatable responses — ideal pre-cache candidates.

### Mood Initialization for BG

The mood system initializes at neutral and drifts based on events. In BGs, bots join fresh with no mood history. Consider personality-based initialization: a warrior starts "fired up", a priest starts "cautious". The pre-gate waiting room phase is the natural window for this.

### Consecutive BG Memory

The "Consecutive Match Memory" feature (Gaps and Enrichments section) should track per-bot-GUID, not just per-player-GUID. Each bot should remember their own BG experience ("I died 8 times last match" vs "I went on a killing spree") for more immersive cross-match references.

---

## Summary of BG Types

| BG | Size | Objectives | Key Events |
|----|------|-----------|------------|
| Warsong Gulch | 10v10 | Capture the Flag | Flag pickup, drop, capture, return |
| Arathi Basin | 15v15 | 5 control nodes | Node assault, capture, defense |
| Alterac Valley | 40v40 | Kill enemy boss + towers | Node capture, boss pull, tower burn |
| Eye of the Storm | 15v15 | 4 bases + 1 flag | Base capture, flag grab, flag cap |
| Strand of the Ancients | 15v15 | Gate destruction | Gate damage, gate destroyed, round swap |
| Isle of Conquest | 40v40 | Workshops + vehicles | Vehicle combat, base capture, boss kill |
