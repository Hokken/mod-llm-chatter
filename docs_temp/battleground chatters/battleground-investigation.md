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

These are global hooks that fire for ALL battlegrounds. We can register our own `AllBattlegroundScript` subclass.

| Hook | When It Fires | Chatter Use |
|------|--------------|-------------|
| `OnBattlegroundStart(bg)` | Match begins | "Let's do this!" battle cry |
| `OnBattlegroundEnd(bg, winnerTeamId)` | Match ends | Victory/defeat reaction |
| `OnBattlegroundAddPlayer(bg, player)` | Player joins BG instance | Arrival comment (replaces group join) |
| `OnBattlegroundRemovePlayerAtLeave(bg, player)` | Player leaves BG | Farewell/ragequit comment |
| `OnBattlegroundUpdate(bg, diff)` | Every world tick | Periodic state checks (score changes, flag state) |

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

// BG type identification
enum BattlegroundTypeId : uint8 {
    BATTLEGROUND_WS = 1,   // Warsong Gulch (10v10, CTF)
    BATTLEGROUND_AB = 2,   // Arathi Basin (15v15, nodes)
    BATTLEGROUND_AV = 3,   // Alterac Valley (40v40, PvE+PvP)
    BATTLEGROUND_EY = 4,   // Eye of the Storm (15v15, flag+nodes)
    BATTLEGROUND_SA = 5,   // Strand of the Ancients (15v15, siege)
    BATTLEGROUND_IC = 6,   // Isle of Conquest (40v40, vehicles)
};

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
