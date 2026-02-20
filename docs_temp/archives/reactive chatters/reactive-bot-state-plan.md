# Reactive Bot State Integration — Implementation Plan

## Context

Currently, bot chatter is "theater" — bots react to events (kills, deaths, loot) but know nothing about their actual state. A Priest at 10% mana reacts the same as one at full mana. A Warrior who lost aggro says the same things as one holding it perfectly. The `PlayerbotAI` API already exposes rich real-time state (health, mana, role, combat target, BotState) and we already `#include "Playerbots.h"` in `LLMChatterScript.cpp`. This plan enriches group event reactions with real bot state so the LLM generates **truthful, grounded** reactions.

**User's key directive**: Focus on reactive chatter based on real bot state, NOT command execution. Bots should comment on what they're actually experiencing.

---

## Approach: Two-Layer Enrichment

### Layer 1: C++ State Snapshot (5 handlers)

Add a `BuildBotStateJson()` helper function that reads real-time bot state via `PlayerbotAI` and `Player` APIs. Append its output as a `"bot_state"` object inside the `extra_data` JSON for 5 of the 6 group event handlers. This is a single helper called from multiple handlers — no per-handler logic needed.

### Layer 2: Python Prompt Injection (5 prompt builders)

Extract `bot_state` from `extra_data` in Python and inject a natural-language state description into prompts. Replace the static `CLASS_ROLE_MAP` guessing with the real role from C++ when available.

---

## Scope Decisions

### Death Handler — EXCLUDED from Phase 1

The C++ death handler stores the **dead player** as `subject_guid`/`subject_name`. The reactor (living bot who speaks) is selected later in Python via `get_other_group_bot()`. We cannot inject the reactor's state in C++ because we don't know who it is yet. The dead player's state is useless (`health_pct: 0`, `bot_ai_state: "dead"`).

**Deferred to Phase 2A**: C++ picks the reactor in the death handler (same pattern as kill handler) and includes their state via `BuildBotStateJson()` in extra_data.

### Idle Banter — EXCLUDED from Phase 1

Idle banter is purely Python-triggered (timer-based in the bridge). No C++ event exists, so there's no `extra_data` to enrich. Bot state (health, mana, combat status) lives in C++ memory only and is not accessible from Python. The most useful piece for idle banter is **role** (health/mana are typically full during idle).

**Deferred to Phase 2B**: C++ detects bot role on group join, passes in greeting event's extra_data. Python stores role in `llm_group_bot_traits` during `assign_bot_traits()`. Idle banter reads it from the traits table.

### Death Prompt Builder — Still Modified

Although the death C++ handler doesn't inject `bot_state`, the Python `build_death_reaction_prompt()` is still modified to accept `extra_data=None`. This is forward-compatible — when Phase 2 adds state, the prompt builder is already wired. For now it gracefully returns empty state context.

---

## Verified API Surface

All APIs below have been verified against the actual AzerothCore + mod-playerbots source code:

| API | Location | Verified |
|-----|----------|----------|
| `Player::GetHealthPct()` | `Unit.h:1095` | Returns float 0-100 |
| `Player::GetPowerPct(POWER_MANA)` | `Unit.h:1122` | Returns float 0-100 |
| `Player::IsInCombat()` | `Unit.h` | Returns bool |
| `Player::GetVictim()` | `Unit.h` | Returns `Unit*` or nullptr |
| `GET_PLAYERBOT_AI(player)` | `Playerbots.h` | Returns `PlayerbotAI*` or nullptr |
| `PlayerbotAI::IsTank(player)` | `PlayerbotAI.cpp:2094` | Static, talent-based |
| `PlayerbotAI::IsHeal(player)` | `PlayerbotAI.cpp:2132` | Static, talent-based |
| `PlayerbotAI::IsRanged(player)` | `PlayerbotAI.cpp:1745` | Static, talent-based |
| `ai->GetState()` | `PlayerbotAI.h:414` | Returns `BotState` enum |
| `BOT_STATE_COMBAT/NON_COMBAT/DEAD` | `PlayerbotAI.h:72` | Enum values 0/1/2 |

**Thread safety**: All PlayerbotAI access runs on the world thread (single-threaded). No mutexes needed.

**Compilation coupling**: `GET_PLAYERBOT_AI` returns nullptr if playerbots isn't compiled. Code gracefully degrades.

---

## Files to Change

### 1. `modules/mod-llm-chatter/src/LLMChatterScript.cpp` (C++)

**New helper function** `BuildBotStateJson(Player* player)` — returns a JSON fragment string:

```cpp
static std::string BuildBotStateJson(Player* player)
{
    if (!player)
        return "";

    // Health & power
    float healthPct = player->GetHealthPct();
    float manaPct =
        player->GetPowerPct(POWER_MANA);
    bool inCombat = player->IsInCombat();

    // Real role from PlayerbotAI (talent-based)
    std::string role = "dps"; // default
    PlayerbotAI* ai = GET_PLAYERBOT_AI(player);
    if (ai)
    {
        if (PlayerbotAI::IsTank(player))
            role = "tank";
        else if (PlayerbotAI::IsHeal(player))
            role = "healer";
        else if (PlayerbotAI::IsRanged(player))
            role = "ranged_dps";
        else
            role = "melee_dps";
    }

    // Current target
    std::string targetName = "";
    Unit* victim = player->GetVictim();
    if (victim)
        targetName = victim->GetName();

    // Bot state (combat/non-combat/dead)
    std::string botState = "non_combat";
    if (ai)
    {
        BotState state = ai->GetState();
        if (state == BOT_STATE_COMBAT)
            botState = "combat";
        else if (state == BOT_STATE_DEAD)
            botState = "dead";
    }

    return
        "\"bot_state\":{"
        "\"health_pct\":" +
            std::to_string((int)healthPct) + ","
        "\"mana_pct\":" +
            std::to_string((int)manaPct) + ","
        "\"role\":\"" + role + "\","
        "\"in_combat\":" +
            std::string(
                inCombat ? "true" : "false")
            + ","
        "\"target\":\"" +
            JsonEscape(targetName) + "\","
        "\"bot_ai_state\":\"" + botState + "\""
        "}";
}
```

**Inject into 5 handlers' extra_data JSON** — change the closing of each handler's JSON from:

```cpp
"\"group_id\":" + std::to_string(groupId) + "}";
```

to:

```cpp
"\"group_id\":" + std::to_string(groupId) + ","
+ BuildBotStateJson(reactor) + "}";
```

Where `reactor` is the bot `Player*` that's reacting (varies by handler).

**5 injection points** (with verified line numbers and reactor variable names):

| # | Handler | Event Type | Line ~ | Reactor Variable | Notes |
|---|---------|-----------|--------|-----------------|-------|
| 1 | Kill | `bot_group_kill` | 2777 | `reactor` | Always a bot (killer if bot, else `GetRandomBotInGroup`) |
| 2 | Wipe | `bot_group_wipe` | 2940 | `wipeReactor` | Random living bot reacting to wipe |
| 3 | Loot | `bot_group_loot` | 3189 | `player` | **Only when `isBot=true`** (see note below) |
| 4 | Combat | `bot_group_combat` | 3346 | `player` | Bot entering combat (always a bot at this point) |
| 5 | Spell | `bot_group_spell_cast` | 4387 | `reactor` | Always a bot (caster if bot, else `GetRandomBotInGroup`) |

**NOT injected**:
- Death handler (line 3024) — `killed` is the dead player, reactor chosen in Python. Covered in Phase 2A.
- Loot handler when `isBot=false` — `player` is the **real player** who looted. Python picks a random bot to react, so injecting the player's state would be wrong. Use conditional injection:

```cpp
// Loot handler: only inject bot state when the
// looter IS a bot (they react about their own loot)
"\"group_id\":" + std::to_string(groupId) +
(IsPlayerBot(player)
    ? ("," + BuildBotStateJson(player))
    : "")
+ "}";
```

When a real player loots, the bot state is omitted from extra_data. Python's `build_bot_state_context()` gracefully returns empty string when `bot_state` is missing.

### 2. `modules/mod-llm-chatter/tools/chatter_shared.py` (Python)

**New function** `build_bot_state_context(extra_data)` (~35 lines):

```python
def build_bot_state_context(extra_data):
    """Build natural-language state description
    from C++ bot_state data in extra_data."""
    if not extra_data:
        return ""
    state = extra_data.get('bot_state')
    if not state or not isinstance(state, dict):
        return ""

    parts = []

    # Real role (replaces CLASS_ROLE_MAP guessing)
    role = state.get('role', '')
    if role:
        role_labels = {
            'tank': 'the tank',
            'healer': 'the healer',
            'melee_dps': 'melee DPS',
            'ranged_dps': 'ranged DPS',
            'dps': 'DPS',
        }
        parts.append(
            f"Your role in this group is "
            f"{role_labels.get(role, role)}."
        )

    # Health
    hp = state.get('health_pct')
    if hp is not None:
        hp = int(hp)
        if hp <= 20:
            parts.append(
                f"You are critically wounded "
                f"({hp}% health)."
            )
        elif hp <= 50:
            parts.append(
                f"You are injured "
                f"({hp}% health)."
            )
        # 50%+ = no comment (normal state)

    # Mana (only meaningful for mana users)
    mp = state.get('mana_pct')
    if mp is not None:
        mp = int(mp)
        if mp <= 15:
            parts.append(
                f"You are almost out of mana "
                f"({mp}%)."
            )
        elif mp <= 35:
            parts.append(
                f"Your mana is getting low "
                f"({mp}%)."
            )
        # 35%+ = no comment (normal state)

    # Current target
    target = state.get('target', '')
    if target:
        parts.append(
            f"You are currently fighting "
            f"{target}."
        )

    return ' '.join(parts)
```

**Modify `build_race_class_context()`** (line 170) to accept optional `actual_role` parameter:

```python
def build_race_class_context(
    race, class_name, actual_role=None
):
```

When `actual_role` is provided, use it instead of `CLASS_ROLE_MAP` lookup for `ROLE_COMBAT_PERSPECTIVES`. This means the talent-based role from PlayerbotAI takes priority over the static class-based guess. `CLASS_ROLE_MAP` remains as fallback when `actual_role` is None (e.g., non-bot players, events without bot_state).

### 3. `modules/mod-llm-chatter/tools/chatter_group.py` (Python)

**Add import**: `build_bot_state_context` from `chatter_shared` (line 33-48, existing import block).

**Modify 5 prompt builders** — add `extra_data=None` parameter, inject state context:

| # | Function | Line ~ | Notes |
|---|----------|--------|-------|
| 1 | `build_kill_reaction_prompt()` | 774 | Kill/boss reactions |
| 2 | `build_loot_reaction_prompt()` | 863 | Item loot reactions |
| 3 | `build_combat_reaction_prompt()` | 980 | Combat entry reactions |
| 4 | `build_wipe_reaction_prompt()` | 5358 | Group wipe reactions |
| 5 | `build_spell_cast_reaction_prompt()` | 1506 | Spell/buff reactions |

Also modify `build_death_reaction_prompt()` (line 1070) for forward-compatibility, even though death handler doesn't inject state yet.

Each builder gets this pattern inserted near the top:

```python
state_ctx = ""
actual_role = None
if extra_data:
    state_ctx = build_bot_state_context(extra_data)
    actual_role = (
        extra_data.get('bot_state', {})
        .get('role')
    )
```

- `state_ctx` is appended to the prompt body (before the final instruction to respond)
- `actual_role` is passed to `build_race_class_context()` for accurate role identity in RP mode

**Modify 5 caller sites** — pass `extra_data=extra_data` to prompt builders:

| # | Function | Line ~ | Event Type |
|---|----------|--------|------------|
| 1 | `process_group_kill_event()` | ~2141 | bot_group_kill |
| 2 | `process_group_loot_event()` | ~2251 | bot_group_loot |
| 3 | `process_group_combat_event()` | ~2400 | bot_group_combat |
| 4 | `process_group_wipe_event()` | ~5400 | bot_group_wipe |
| 5 | `process_group_spell_cast_event()` | ~3772 | bot_group_spell_cast |

`extra_data` is already parsed at the top of each `process_group_*_event()` function — it just needs to be threaded through to the prompt builder call.

### 4. No changes needed to:

- **Database schema** — `extra_data` is JSON type, no column changes needed (nested `bot_state` object is valid JSON)
- **`chatter_constants.py`** — `CLASS_ROLE_MAP` stays as fallback for non-bot players
- **`chatter_prompts.py`** — ambient prompts don't have combat state
- **`chatter_general.py`** — General channel doesn't use group events
- **`chatter_events.py`** — Environment events don't have combat state
- **Config files** — no new config variables needed
- **SQL migrations** — no schema changes

---

## Mana Handling for Non-Mana Classes

`GetPowerPct(POWER_MANA)` returns 0 for classes that don't use mana (Warriors use Rage, Rogues use Energy, Death Knights use Runic Power). The Python `build_bot_state_context()` only generates mana-related text when `mana_pct <= 35`, so Warriors/Rogues/DKs will naturally get no mana commentary (their `mana_pct` will be 0, but the "almost out of mana" message at 0% would be wrong).

**Fix**: In the Python function, also check if the bot's class is a mana user before generating mana text. Alternatively, in C++, only include `mana_pct` when `player->GetMaxPower(POWER_MANA) > 0`. The C++ approach is cleaner — it keeps the data accurate at the source:

```cpp
// Only include mana_pct for mana-using classes
int manaPctInt = 0;
if (player->GetMaxPower(POWER_MANA) > 0)
    manaPctInt = (int)player->GetPowerPct(
        POWER_MANA);
else
    manaPctInt = -1; // sentinel: not a mana user
```

Python then skips mana text when `mana_pct == -1` or `mana_pct is None`.

---

## Example Results

**Before** (kill reaction, Priest healer at 15% mana):
> "Nice work taking that one down!"

**After** (same situation, with bot state):
> "That was close... I'm running on fumes here, barely any mana left. Need a moment before we pull again."

**Before** (combat entry, Warrior tank):
> "Let's fight this thing!"

**After** (Warrior tank at full health, targeting Hogger):
> "I've got Hogger, stay behind me."

**Before** (loot reaction, Rogue DPS at 40% health):
> "Nice find!"

**After** (same situation, with bot state):
> "Good drop. But I took a beating back there — let me bandage up first."

---

## Phased Delivery

### Phase 1 (this session): Core State Injection
- `BuildBotStateJson()` helper in C++
- Inject into 5 handlers (kill, wipe, loot, combat, spell)
- `build_bot_state_context()` in Python
- Thread `extra_data` to all 6 prompt builders (including death for forward-compat)
- Replace `CLASS_ROLE_MAP` with real role when `actual_role` is available

### Phase 2 (this session): Death Coverage + Idle Role + State-Triggered Callouts

Three sub-features that complete the reactive bot state system:

- **Phase 2A**: Death handler enrichment — pick reactor in C++, include their state
- **Phase 2B**: Role storage for idle banter — persist detected role in traits table
- **Phase 2C**: Proactive state-triggered callouts — "I'm going down!", "Out of mana!", "Lost aggro!"

### Phase 3 (future): Strategy Awareness
- Read `ai->GetStrategies(BOT_STATE_COMBAT)` for active strategies
- Bots mention what they're doing: "Switching to heal spec", "Going defensive"

---

## Phase 2A: Death Handler Enrichment

### Problem

The death handler stores the **dead player** as subject. Python picks the reactor via `get_other_group_bot()`. Since the reactor is unknown in C++, Phase 1 couldn't inject their state.

### Solution

Change the death handler to **also pick a reactor** in C++ (same pattern as kill handler), store their GUID/name and `BuildBotStateJson(reactor)` in `extra_data`. Python uses the pre-selected reactor from extra_data instead of querying `get_other_group_bot()`.

### C++ Changes — `LLMChatterScript.cpp`

In the death handler (line ~2968, after cooldown/RNG checks), add reactor selection:

```cpp
// Pick a living bot to react (exclude dead player)
Player* reactor = GetRandomBotInGroup(
    group, killed);
if (!reactor)
    return;

uint32 reactorGuid =
    reactor->GetGUID().GetCounter();
std::string reactorName = reactor->GetName();
```

Modify `extraData` JSON to include reactor info + state:

```cpp
std::string extraData = "{"
    "\"bot_guid\":" +
        std::to_string(deadGuid) + ","
    "\"bot_name\":\"" +
        JsonEscape(deadName) + "\","
    "\"killer_name\":\"" +
        JsonEscape(killerName) + "\","
    "\"killer_entry\":" +
        std::to_string(killerEntry) + ","
    "\"group_id\":" +
        std::to_string(groupId) + ","
    "\"is_player_death\":" +
        std::string(
            isPlayerDeath ? "true" : "false")
    + ","
    "\"reactor_guid\":" +
        std::to_string(reactorGuid) + ","
    "\"reactor_name\":\"" +
        JsonEscape(reactorName) + "\","
    + BuildBotStateJson(reactor) + "}";
```

Also update `subject_guid`/`subject_name` in the INSERT to use `reactorGuid`/`reactorName` (the reactor is the one who speaks, matching other handlers' convention).

### Python Changes — `chatter_group.py`

Modify `process_group_death_event()` (line ~2584):

```python
# Use pre-selected reactor from C++ if available
reactor_guid = extra_data.get('reactor_guid')
reactor_name = extra_data.get('reactor_name')

if reactor_guid and reactor_name:
    # C++ already picked the reactor — use it
    reactor_guid = int(reactor_guid)
    trait_data = get_bot_traits(
        db, group_id, reactor_guid
    )
    if not trait_data:
        # Fallback to old method
        reactor_data = get_other_group_bot(
            db, group_id, dead_guid
        )
        ...
    else:
        reactor_traits = trait_data['traits']
        # Query class/race as before
        ...
else:
    # Legacy path: no reactor in extra_data
    reactor_data = get_other_group_bot(
        db, group_id, dead_guid
    )
    ...
```

Pass `extra_data=extra_data` to `build_death_reaction_prompt()` (already forward-compat from Phase 1).

---

## Phase 2B: Role Storage for Idle Banter

### Problem

Idle banter is Python-triggered with no C++ event. Bot state lives in C++ memory. The only valuable state for idle banter is **role** (a healer shouldn't talk like a tank). Health/mana are typically full during idle (that's why it's idle).

### Solution

**Two-step approach**: C++ detects the role and passes it in the greeting event's `extra_data`. Python's `assign_bot_traits()` reads it and stores it in `llm_group_bot_traits`. This keeps the existing trait write path in Python (where all INSERTs happen) and only adds role detection to C++.

**Important**: Traits are written in Python's `assign_bot_traits()` (`chatter_group.py:233`), NOT in C++. C++ only inserts events into `llm_chatter_events`. We must not add C++ writes to `llm_group_bot_traits` — that would create a dual-write conflict.

### SQL Migration

Add `role` column to `llm_group_bot_traits`:

```sql
ALTER TABLE `llm_group_bot_traits`
    ADD COLUMN `role` VARCHAR(16) DEFAULT NULL
    AFTER `trait3`;
```

### C++ Changes — `LLMChatterScript.cpp`

In `QueueBotGreetingEvent()` (line ~2044), add role detection and include in the greeting event's `extra_data` JSON. The role is detected using `PlayerbotAI` static methods (same as `BuildBotStateJson()` uses):

```cpp
// Detect bot role for Python trait storage
std::string role = "dps";
PlayerbotAI* ai = GET_PLAYERBOT_AI(bot);
if (ai)
{
    if (PlayerbotAI::IsTank(bot))
        role = "tank";
    else if (PlayerbotAI::IsHeal(bot))
        role = "healer";
    else if (PlayerbotAI::IsRanged(bot))
        role = "ranged_dps";
    else
        role = "melee_dps";
}
```

Add to existing `extraData` JSON in `QueueBotGreetingEvent()`:

```cpp
"\"role\":\"" + role + "\","
```

This makes the role available in the `bot_group_join` event's `extra_data` when Python processes it.

### Python Changes — `chatter_group.py`

**Modify `assign_bot_traits()`** (line 233) to accept and store `role`:

```python
def assign_bot_traits(
    db, group_id, bot_guid, bot_name,
    role=None
):
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO llm_group_bot_traits
        (group_id, bot_guid, bot_name,
         trait1, trait2, trait3, role)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            trait1 = VALUES(trait1),
            trait2 = VALUES(trait2),
            trait3 = VALUES(trait3),
            role = VALUES(role),
            assigned_at = CURRENT_TIMESTAMP
    """, (
        group_id, bot_guid, bot_name,
        traits[0], traits[1], traits[2],
        role
    ))
    db.commit()
```

**Modify caller** in `process_group_event()` (line 1848, handles `bot_group_join`) to extract role from extra_data:

```python
role = extra_data.get('role')  # from C++ detection
traits = assign_bot_traits(
    db, group_id, bot_guid, bot_name,
    role=role
)
```

**Modify idle banter — both paths**:

Idle chatter has two code paths that both need role threading:

1. **`_idle_conversation()`** (line 6547) — multi-bot conversation
2. **`_idle_single_statement()`** (line 6400) — single bot statement

Both are called from `check_idle_group_chatter()` (line 6239).

**Step 1**: Update ALL traits SELECT queries in idle paths to include `role`:

```sql
SELECT bot_guid, bot_name,
    trait1, trait2, trait3, role
FROM llm_group_bot_traits
WHERE group_id = %s
```

**Step 2**: In `_idle_conversation()` (line ~6575), pass role when building bot dicts:

```python
bot = {
    'guid': br['bot_guid'],
    'name': br['bot_name'],
    'class': get_class_name(char['class']),
    'race': get_race_name(char['race']),
    'level': char['level'],
    'role': br.get('role'),  # from traits table
}
```

Thread into `build_idle_conversation_prompt()` where it calls `build_race_class_context()` for each bot.

**Step 3**: Two `build_race_class_context()` call sites in the idle paths need `actual_role`:

- `build_idle_chatter_prompt()` (line 6083) — called by `_idle_single_statement()`, builds the single-statement prompt. Pass `actual_role=bot.get('role')`.
- `build_idle_conversation_prompt()` (line ~6083 equivalent for conversations) — called by `_idle_conversation()`. Pass `actual_role=bot.get('role')` per bot.

Both require the bot dict to carry `role` from the traits query (Step 1 ensures this).

### Base Schema Update

Update `llm_chatter_tables.sql` to include `role` column in the CREATE TABLE.

---

## Phase 2C: State-Triggered Proactive Callouts

### Concept

Bots proactively call out dangerous situations instead of only reacting to events. A healer running out of mana shouts "I'm running dry!" A tank losing aggro warns "I can't hold it!" A DPS at critical health cries "I need heals!"

These are **new events** generated by periodic C++ state checks, not enrichments to existing handlers.

### New Event Types

| Event Type | Trigger | Who Speaks | Cooldown |
|-----------|---------|-----------|----------|
| `bot_group_low_health` | Bot health drops below 25% while in combat | The low-health bot | 60s per bot |
| `bot_group_oom` | Mana-user mana drops below 15% while in combat | The OOM bot | 60s per bot |
| `bot_group_aggro_loss` | Tank's target is attacking someone else in group | The tank | 60s per bot |

### C++ Changes — `LLMChatterScript.cpp`

**New periodic check** `CheckGroupCombatState()` added to `OnUpdate`:

```cpp
// In OnUpdate, after existing checks:
if (now - _lastCombatStateCheckTime >=
        _combatStateCheckMs)
{
    _lastCombatStateCheckTime = now;
    CheckGroupCombatState();
}
```

New member variables:

```cpp
uint32 _lastCombatStateCheckTime = 0;
static constexpr uint32 _combatStateCheckMs = 5000; // 5 seconds

// Per-bot cooldowns: bot_guid -> last trigger time
static std::map<uint32, time_t>
    _botLowHealthCooldowns;
static std::map<uint32, time_t>
    _botOomCooldowns;
static std::map<uint32, time_t>
    _botAggroCooldowns;
```

**`CheckGroupCombatState()` implementation** (~80 lines):

```cpp
void CheckGroupCombatState()
{
    // Top-level enable guard
    if (!sLLMChatterConfig->_stateCalloutEnabled)
        return;

    time_t now = time(nullptr);

    // Iterate all online players to find groups
    // with real players where bots are in combat
    SessionMap const& sessions =
        sWorld->GetAllSessions();

    // Track visited groups to avoid duplicates
    std::set<uint32> visitedGroups;

    for (auto const& [id, session] : sessions)
    {
        Player* player = session->GetPlayer();
        if (!player || !player->IsInWorld())
            continue;
        if (IsPlayerBot(player))
            continue;  // Only start from real players

        Group* group = player->GetGroup();
        if (!group)
            continue;

        uint32 groupId =
            group->GetGUID().GetCounter();
        if (visitedGroups.count(groupId))
            continue;
        visitedGroups.insert(groupId);

        // Iterate group members
        for (GroupReference* itr =
                 group->GetFirstMember();
             itr; itr = itr->next())
        {
            Player* bot = itr->GetSource();
            if (!bot || !IsPlayerBot(bot))
                continue;
            if (!bot->IsInCombat())
                continue;

            uint32 botGuid =
                bot->GetGUID().GetCounter();

            // --- Low Health Check ---
            if (sLLMChatterConfig
                    ->_stateCalloutLowHealth)
            {
                float hp = bot->GetHealthPct();
                if (hp > 0 && hp <= 25)
                {
                    auto it = _botLowHealthCooldowns
                        .find(botGuid);
                    if (it == _botLowHealthCooldowns
                            .end()
                        || (now - it->second) >=
                            (time_t)sLLMChatterConfig
                                ->_stateCalloutCooldown)
                    {
                        // RNG check
                        if (urand(1, 100) <=
                            sLLMChatterConfig
                                ->_stateCalloutChance)
                        {
                            QueueStateCallout(
                                bot, group,
                                "bot_group_low_health",
                                groupId);
                        }
                        _botLowHealthCooldowns
                            [botGuid] = now;
                    }
                }
            }

            // --- OOM Check (mana users only) ---
            if (sLLMChatterConfig
                    ->_stateCalloutOom)
            {
                if (bot->GetMaxPower(POWER_MANA) > 0)
                {
                    float mp = bot->GetPowerPct(
                        POWER_MANA);
                    if (mp <= 15)
                    {
                        auto it = _botOomCooldowns
                            .find(botGuid);
                        if (it == _botOomCooldowns
                                .end()
                            || (now - it->second) >=
                                (time_t)sLLMChatterConfig
                                    ->_stateCalloutCooldown)
                        {
                            if (urand(1, 100) <=
                                sLLMChatterConfig
                                    ->_stateCalloutChance)
                            {
                                QueueStateCallout(
                                    bot, group,
                                    "bot_group_oom",
                                    groupId);
                            }
                            _botOomCooldowns
                                [botGuid] = now;
                        }
                    }
                }
            }

            // --- Aggro Loss Check (tanks only) ---
            if (sLLMChatterConfig
                    ->_stateCalloutAggro)
            {
                PlayerbotAI* ai =
                    GET_PLAYERBOT_AI(bot);
                if (ai
                    && PlayerbotAI::IsTank(bot))
                {
                    Unit* victim = bot->GetVictim();
                    if (victim
                        && victim->GetVictim()
                        && victim->GetVictim() != bot)
                    {
                        // Tank's target is hitting
                        // someone else = aggro lost
                        Player* threatened =
                            victim->GetVictim()
                                ->ToPlayer();
                        if (threatened
                            && group->IsMember(
                                threatened->GetGUID()))
                        {
                            auto it =
                                _botAggroCooldowns
                                    .find(botGuid);
                            if (it ==
                                _botAggroCooldowns
                                    .end()
                                || (now - it->second)
                                    >= (time_t)
                                    sLLMChatterConfig
                                        ->_stateCalloutCooldown)
                            {
                                if (urand(1, 100) <=
                                    sLLMChatterConfig
                                        ->_stateCalloutChance)
                                {
                                    QueueStateCallout(
                                        bot, group,
                                        "bot_group_aggro_loss",
                                        groupId);
                                }
                                _botAggroCooldowns
                                    [botGuid] = now;
                            }
                        }
                    }
                }
            }
        }
    }
}
```

**New helper** `QueueStateCallout()`:

```cpp
void QueueStateCallout(
    Player* bot, Group* group,
    const char* eventType, uint32 groupId)
{
    std::string botName = bot->GetName();
    uint32 botGuid =
        bot->GetGUID().GetCounter();

    // Get target name for context
    std::string targetName = "";
    Unit* victim = bot->GetVictim();
    if (victim)
        targetName = victim->GetName();

    // Get who has aggro (for aggro_loss)
    std::string aggroTarget = "";
    if (victim && victim->GetVictim()
        && victim->GetVictim() != bot)
    {
        aggroTarget =
            victim->GetVictim()->GetName();
    }

    std::string extraData = "{"
        "\"bot_guid\":" +
            std::to_string(botGuid) + ","
        "\"bot_name\":\"" +
            JsonEscape(botName) + "\","
        "\"group_id\":" +
            std::to_string(groupId) + ","
        "\"target_name\":\"" +
            JsonEscape(targetName) + "\","
        "\"aggro_target\":\"" +
            JsonEscape(aggroTarget) + "\","
        + BuildBotStateJson(bot) + "}";

    extraData = EscapeString(extraData);

    CharacterDatabase.Execute(
        "INSERT INTO llm_chatter_events "
        "(event_type, event_scope, zone_id, "
        "map_id, priority, cooldown_key, "
        "subject_guid, subject_name, "
        "extra_data, status, "
        "react_after, expires_at) "
        "VALUES ('{}', 'player', "
        "{}, {}, 2, "
        "'state:{}:{}', "
        "{}, '{}', '{}', 'pending', "
        "DATE_ADD(NOW(), INTERVAL 1 SECOND), "
        "DATE_ADD(NOW(), INTERVAL 60 SECOND))",
        eventType,
        bot->GetZoneId(),
        bot->GetMapId(),
        eventType, botGuid,
        botGuid,
        EscapeString(botName),
        extraData);

    LOG_INFO("module",
        "LLMChatter: Queued {} for {} "
        "(hp={:.0f}%, mp={:.0f}%)",
        eventType, botName,
        bot->GetHealthPct(),
        bot->GetPowerPct(POWER_MANA));
}
```

### Config Changes — `LLMChatterConfig.h` / `LLMChatterConfig.cpp` / `mod_llm_chatter.conf.dist`

New config variables:

```
LLMChatter.GroupChatter.StateCalloutEnable = 1
LLMChatter.GroupChatter.StateCalloutLowHealth = 1
LLMChatter.GroupChatter.StateCalloutOom = 1
LLMChatter.GroupChatter.StateCalloutAggro = 1
LLMChatter.GroupChatter.StateCalloutChance = 60
LLMChatter.GroupChatter.StateCalloutCooldown = 60
```

Config.h members:

```cpp
bool _stateCalloutEnabled;
bool _stateCalloutLowHealth;
bool _stateCalloutOom;
bool _stateCalloutAggro;
uint32 _stateCalloutChance;   // 0-100
uint32 _stateCalloutCooldown; // seconds per bot
```

### SQL Migration

New ENUM values for `llm_chatter_events.event_type`. The full current ENUM must be repeated with the 3 new values appended:

```sql
ALTER TABLE `llm_chatter_events`
    MODIFY COLUMN `event_type` ENUM(
        'weather_change',
        'holiday_start',
        'holiday_end',
        'creature_death_boss',
        'creature_death_rare',
        'creature_death_guard',
        'player_enters_zone',
        'bot_pvp_kill',
        'bot_level_up',
        'bot_achievement',
        'bot_quest_complete',
        'world_boss_spawn',
        'rare_spawn',
        'transport_arrives',
        'day_night_transition',
        'enemy_player_near',
        'bot_loot_item',
        'bot_group_join',
        'bot_group_kill',
        'bot_group_death',
        'bot_group_loot',
        'bot_group_player_msg',
        'bot_group_combat',
        'bot_group_levelup',
        'bot_group_quest_complete',
        'bot_group_achievement',
        'bot_group_spell_cast',
        'bot_group_quest_objectives',
        'bot_group_resurrect',
        'bot_group_zone_transition',
        'bot_group_dungeon_entry',
        'bot_group_wipe',
        'bot_group_corpse_run',
        'player_general_msg',
        'minor_event',
        'bot_group_low_health',
        'bot_group_oom',
        'bot_group_aggro_loss'
    ) NOT NULL;

ALTER TABLE `llm_group_bot_traits`
    ADD COLUMN `role` VARCHAR(16) DEFAULT NULL
    AFTER `trait3`;
```

Also update base schema `llm_chatter_tables.sql` with the same 3 new ENUM values and the `role` column.

### Python Changes — `chatter_group.py`

**3 new prompt builders**:

```python
def build_low_health_callout_prompt(
    bot, traits, target_name, mode,
    chat_history="", extra_data=None
):
    """Bot is critically wounded in combat."""
    state_ctx = ""
    if extra_data:
        state_ctx = build_bot_state_context(
            extra_data
        )
    # Prompt: "You are {name}, a {class}.
    # {state_ctx}
    # You are in serious danger — react with
    # urgency. Call for help, express pain, or
    # show desperation. ONE short sentence."
    ...

def build_oom_callout_prompt(
    bot, traits, target_name, mode,
    chat_history="", extra_data=None
):
    """Bot is running out of mana in combat."""
    # Prompt: "You are running out of mana in
    # combat. Alert your group — ask for a
    # moment, warn the tank, or express
    # frustration. ONE short sentence."
    ...

def build_aggro_loss_callout_prompt(
    bot, traits, target_name, aggro_target,
    mode, chat_history="", extra_data=None
):
    """Tank lost aggro — mob attacking someone
    else in group."""
    # Prompt: "You are the tank but {target}
    # is now attacking {aggro_target}. React
    # with urgency — warn the group, try to
    # get attention back. ONE short sentence."
    ...
```

**3 new event processors** (following existing pattern):

```python
def process_group_low_health_event(
    db, client, config, event
):
    """Handle bot_group_low_health callout."""
    # Same structure as other group event
    # processors: parse extra_data, get traits,
    # build prompt, call LLM, insert message
    ...

def process_group_oom_event(
    db, client, config, event
):
    ...

def process_group_aggro_loss_event(
    db, client, config, event
):
    ...
```

**Bridge routing** — `llm_chatter_bridge.py`:

```python
if event_type == 'bot_group_low_health':
    return process_group_low_health_event(
        db, client, config, event
    )
if event_type == 'bot_group_oom':
    return process_group_oom_event(
        db, client, config, event
    )
if event_type == 'bot_group_aggro_loss':
    return process_group_aggro_loss_event(
        db, client, config, event
    )
```

### Example Results

**Low health** (Rogue at 18% HP fighting a Scarlet Crusader):
> "I need heals! This Crusader is tearing me apart!"

**OOM** (Priest healer at 12% mana):
> "I'm out of mana — stop pulling, I need to drink!"

**Aggro loss** (Warrior tank, Hogger targeting the Mage):
> "Hogger's on the Mage! Get behind me!"

---

## Phase 2C Performance Considerations

The `CheckGroupCombatState()` loop runs every 5 seconds. It:
1. Iterates online sessions to find real players (existing pattern used by `TryTriggerChatter`)
2. For each group, iterates members (typically 2-5 bots)
3. Checks 3 conditions per bot (health, mana, aggro) — all O(1) reads
4. Per-bot cooldowns prevent event flooding

Total cost: ~5-20 bot checks every 5 seconds. Negligible compared to the existing `OnUpdate` work.

**Cooldown cleanup**: Add `_botLowHealthCooldowns`, `_botOomCooldowns`, `_botAggroCooldowns` to the group cleanup in `OnRemoveMember` (line ~2187). Use the existing pattern — iterate and erase entries matching the group's bots.

**Session iteration**: Uses `sWorld->GetAllSessions()` which is the same pattern as `TryTriggerChatter()` already uses. Thread-safe on world thread.

---

## Deployment (Both Phases)

Phase 1 + Phase 2 together require:
1. **SQL migration** — add `role` column to traits, add 3 new ENUM values to events
2. **C++ compilation** — all changes in `LLMChatterScript.cpp` + config files
3. **Bridge restart** — `docker restart ac-llm-chatter-bridge`

```bash
# 1. Run SQL migration
powershell.exe -Command "docker exec ac-database mysql -uroot -ppassword acore_characters -e 'SOURCE /path/to/migration.sql'"

# 2. Compile (after all C++ changes)
# ... standard incremental build ...

# 3. Restart bridge
docker restart ac-llm-chatter-bridge
```

---

## Verification (Both Phases)

### Phase 1 Verification
1. Check bridge logs for clean startup (no import errors)
2. Join group with bots of different specs (tank warrior, heal priest, dps rogue)
3. Enter combat and check bridge logs for `bot_state` in extra_data JSON:
   - Verify `health_pct`, `mana_pct`, `role`, `target`, `in_combat` are present
   - Verify `mana_pct` is -1 for Warriors/Rogues
4. Trigger a kill at low health — bot should reference being wounded
5. Trigger spell cast when healer is low mana — should mention mana concerns
6. Compare reactions with previous generic ones — should feel grounded and situational

### Phase 2A Verification
7. Trigger a group member death — check extra_data contains `reactor_guid`, `reactor_name`, `bot_state`
8. Verify the reactor speaks (not the dead player)
9. Reactor's state should influence the death reaction prompt

### Phase 2B Verification
10. Form a new group — check `llm_group_bot_traits` table has `role` column populated
11. Wait for idle banter — verify bots' RP context uses the correct role (not CLASS_ROLE_MAP guess)

### Phase 2C Verification
12. Enter combat and let healer run low on mana — should see `bot_group_oom` event in logs
13. Let a DPS take heavy damage — should see `bot_group_low_health` callout
14. Have tank lose aggro (pull multiple mobs) — should see `bot_group_aggro_loss`
15. Verify cooldowns: same bot shouldn't fire the same callout within 60 seconds
16. Verify no callouts fire outside of combat

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| `GetVictim()` returns dangling pointer | Crash | Called on world thread, Player* is valid. `GetVictim()` returns nullptr if no target — null-checked. |
| `GET_PLAYERBOT_AI` returns nullptr for real player | Wrong state | Null-checked, defaults to `role="dps"`, `botState="non_combat"`. Falls back gracefully. |
| `GetPowerPct(POWER_MANA)` for non-mana class | Wrong data | Sentinel value -1 when `GetMaxPower(POWER_MANA) == 0`. Python skips mana text. |
| LLM over-fixates on state | Repetitive messages | State is injected as context, not instruction. Prompt wording keeps it as background info. |
| extra_data JSON grows larger | Slight perf impact | Adds ~120 bytes per event. Negligible for JSON column. |
| `CheckGroupCombatState()` perf | Tick delay | 5s interval, ~20 bot checks per cycle. O(1) reads per bot. Negligible. |
| State callout spam | Chat flooding | Per-bot 60s cooldowns + RNG chance (default 60%). Max 1 callout per bot per minute per type. |
| `victim->GetVictim()` chain for aggro check | Nullptr | Both levels null-checked. `victim->GetVictim()` returns nullptr if mob has no target. |
| Stale per-bot cooldown maps | Memory growth | Cleaned up in `OnRemoveMember` group cleanup block. Also bounded by bot count (finite). |

---

## Complete File Change Summary

| File | Phase | Changes |
|------|-------|---------|
| `modules/mod-llm-chatter/src/LLMChatterScript.cpp` | 1+2 | `BuildBotStateJson()`, inject in 5→6 handlers, `CheckGroupCombatState()`, `QueueStateCallout()`, role in greeting extra_data |
| `modules/mod-llm-chatter/src/LLMChatterConfig.h` | 2C | 6 new config members |
| `modules/mod-llm-chatter/src/LLMChatterConfig.cpp` | 2C | 6 new config reads |
| `modules/mod-llm-chatter/conf/mod_llm_chatter.conf.dist` | 2C | 6 new config variables |
| `modules/mod-llm-chatter/tools/chatter_shared.py` | 1 | `build_bot_state_context()`, `actual_role` param |
| `modules/mod-llm-chatter/tools/chatter_group.py` | 1+2 | Thread extra_data to 6 prompt builders, 3 new prompt builders, 3 new processors, idle role |
| `modules/mod-llm-chatter/tools/llm_chatter_bridge.py` | 2C | 3 new event routing entries |
| `modules/mod-llm-chatter/data/sql/db-characters/base/llm_chatter_tables.sql` | 2 | `role` column, 3 new ENUM values |
| SQL migration file | 2 | ALTER TABLE for `role` column + ENUM values |

---

*Created: 2026-02-14*
*Updated: 2026-02-15 — Phase 1 refined after codebase verification. Phase 2 fully designed with death enrichment, idle role storage, and proactive state-triggered callouts.*
*Updated: 2026-02-15b — Fixed 6 review findings: (1) loot handler conditional state injection for player-loot path, (2) Phase 2B role writes anchored to Python assign_bot_traits() not C++, (3) extra_data type corrected to JSON, (4) StateCalloutEnable guard added to CheckGroupCombatState(), (5) ENUM migration written with full value list, (6) scope decisions text matches actual Phase 2 mechanisms.*
*Updated: 2026-02-15c — Fixed function names and idle path coverage. Corrected build_race_class_context() call site to build_idle_chatter_prompt() (line 6083), not _idle_single_statement() (line 6400).*
