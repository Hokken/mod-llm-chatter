# mod-llm-chatter - Logic Documentation

This document describes the current runtime logic of `mod-llm-chatter`.

It is meant to answer two practical questions:

1. What does the module do at runtime?
2. Where does that logic live?


---

## 1. Overview

`mod-llm-chatter` creates ambient and reactive bot chat for AzerothCore.
It combines C++ event capture and in-game delivery with a Python bridge
that builds prompts, calls an LLM, and writes final messages back to the
database.

High-level behavior:

- ambient General-channel chatter in the open world
- reactive party chatter for grouped bots
- General-channel reactions to real player chat
- world event chatter for weather, holidays, transports, and nearby
  points of interest
- battleground chatter for flag, node, PvP, milestone, and related BG
  events
- PvE raid chatter for boss encounters, lifted group features, and
  idle morale
- real-time subzone lore tracking with ~3,000 subzone descriptions
  injected into prompts (Session 74)

---

## 2. Runtime Pipeline

### C++ side

The C++ module:

- detects hooks and world events
- inserts queue rows into MySQL
- runs the message delivery tick
- plays party text emotes when appropriate

### Python side

The Python bridge:

- polls `llm_chatter_events` and `llm_chatter_queue`
- routes by event type
- builds prompt context
- calls the configured LLM provider
- writes final output rows to `llm_chatter_messages`

### Delivery

After Python writes the message rows, C++ delivers them in game on the
world tick.

Party channel may play text emotes.
General, raid, and battleground delivery do not play text emotes.

---

## 2b. Queueing, Timing, and the Main Bridge Loop

The runtime is split into three DB-backed stages, and the Python bridge
does not process all of them inline in one thread.

### The three stages

1. **Request/event creation**
   - C++ inserts either:
     - legacy ambient requests into `llm_chatter_queue`
     - reactive/event work into `llm_chatter_events`
2. **Bridge processing**
   - Python claims ready work, builds prompts, calls the LLM, and writes
     final chat rows to `llm_chatter_messages`
3. **In-game delivery**
   - C++ world tick delivers ready rows from `llm_chatter_messages`

### What the main bridge loop actually does

`llm_chatter_bridge.py` runs one long-lived coordinator loop. That loop:

- harvests completed futures
- runs periodic cleanup
- claims ready events from `llm_chatter_events`
- submits them to worker threads
- periodically submits timer-like jobs such as:
  - legacy ambient request processing
  - idle group chatter checks
  - bot-question checks
  - pre-cache refills
- sleeps for `LLMChatter.Bridge.PollIntervalSeconds` between iterations

So the bridge is:

- one coordinator loop
- a `ThreadPoolExecutor`
- multiple worker tasks running in parallel

It is **not** "one loop that processes every message end to end by
itself."

### Event workers vs timer-style jobs

Reactive/event rows from `llm_chatter_events` are claimed in priority
order and then processed in worker threads via `process_single_event()`.

Timer-style jobs are separate worker submissions launched only when
their interval elapses:

- idle chatter
- bot questions
- pre-cache refill
- legacy ambient request processing

These jobs share the same executor, but they are not fetched from the
event table.

### Group serialization

The bridge allows parallel processing overall, but events with the same
`group_id` are wrapped in a per-group lock. That means one party's work
is serialized even while different groups can process concurrently.

Session 69 refined this by separating urgent/high and filler lock lanes
for the same group so queued filler work is less likely to block queued
urgent work.

### Event queue ordering

`llm_chatter_events` is fetched with:

- `status = 'pending'`
- `react_after <= NOW()` or null
- `expires_at > NOW()` or null
- `ORDER BY priority DESC, created_at ASC`

So event priority matters at claim time.

### Legacy ambient queue ordering

`llm_chatter_queue` is the older ambient queue. It is processed FIFO:

- `ORDER BY created_at ASC`

`LLMChatter.MaxPendingRequests` currently gates this queue only.

### Final message delivery ordering

Python inserts final rows into `llm_chatter_messages` with:

- `deliver_at = NOW() + delay_seconds`

C++ delivery now has two modes:

- fallback mode:
  - `WHERE delivered = 0 AND deliver_at <= NOW()`
  - `ORDER BY deliver_at ASC LIMIT 1`
- priority mode, when
  `LLMChatter.PrioritySystem.Enable = 1` and
  `LLMChatter.PrioritySystem.DeliveryOrderEnable = 1`:
  - ready rows are `LEFT JOIN`ed back to `llm_chatter_events`
  - ordered by `COALESCE(e.priority, 0) DESC, m.deliver_at ASC`

So urgent event-backed rows can now overtake filler rows at final
delivery time, while ambient rows with `event_id = NULL` stay lowest
priority.

### Current priority behavior and remaining limits

The system now has real priority behavior across multiple stages, but it
is still not a single perfect global scheduler across:

- legacy ambient requests
- event workers
- background timer jobs
- final delivery

What Session 69 added:

- centralized C++ event priority bands
- config-backed react ranges per tier
- bridge urgent-backlog yield for filler jobs
- priority-aware final delivery ordering
- bridge safety mode that suppresses filler first under overload

Also, `GlobalMessageCap` and `TransportBypassGlobalCap` are currently
legacy config values. They are no longer the intended main control path;
the active design direction is priority tiers plus provider-safety
suppression.

### Timing layers

There are two separate delays that are easy to confuse:

- **Reaction delay**: C++ sets `react_after` when queueing an event
- **Delivery delay**: Python sets `deliver_at` when writing the final
  message row

Most delivery delays use `calculate_dynamic_delay()` in
`chatter_shared.py`:

- `responsive=True` for player-directed replies
- ambient/group conversation paths can also include reading time from
  `prev_message_length`

This separation is important if you plan to redesign priorities, because
priority currently influences claim order more than final speak order.

---

## 3. C++ File Ownership

### `src/LLMChatterScript.cpp`

Registration coordinator only. Calls:

- `AddLLMChatterWorldScripts()`
- `AddLLMChatterGroupScripts()`
- `AddLLMChatterPlayerScripts()`
- `AddLLMChatterBGScripts()`

### `src/LLMChatterShared.cpp`

Owns shared helpers used across domains:

- `EscapeString()`
- `JsonEscape()`
- `QueueChatterEvent()`
- `BuildBotStateJson()`
- `AppendRaidContext()`
- `GroupHasBots()`
- shared link conversion helpers
- shared emote and delivery helpers

Critical contract:

- direct callers of `QueueChatterEvent()` must provide `extraData` that
  is already SQL-safe for insertion into a single-quoted SQL string

### `src/LLMChatterWorld.cpp`

Owns world and environment behavior:

- `LLMChatterWorldScript`
- `LLMChatterGameEventScript`
- `LLMChatterALEScript`
- delivered-message polling and dispatch
- holiday, day/night, transport, and weather events
- nearby-object and nearby-creature scanning
- world-private `QueueEvent()`

### `src/LLMChatterGroup.cpp`

Owns party/group subsystem behavior:

- `LLMChatterGroupScript`
- `LLMChatterGroupPlayerScript`
- `LLMChatterCreatureScript`
- `CleanupGroupSession()`
- group join batching
- quest accept batching
- named-boss cache
- group combat state and state callouts
- group-owned cooldown and state maps

### `src/LLMChatterPlayer.cpp`

Owns player General-channel behavior:

- `LLMChatterPlayerScript`
- `EnsureBotInGeneralChannel()`
- General chat cooldowns
- `OnPlayerCanUseChat(..., Channel*)`
- writes to `llm_general_chat_history`

### `src/LLMChatterBG.cpp`

Owns battleground-specific hooks and BG queue helpers.

---

## 4. Current Python File Ownership

### Bridge and orchestration

- `tools/llm_chatter_bridge.py`
- `tools/chatter_ambient.py`

### Group domain

- `tools/chatter_group.py`
- `tools/chatter_group_handlers.py`
- `tools/chatter_group_prompts.py`
- `tools/chatter_group_state.py`

### General/shared support

- `tools/chatter_general.py`
- `tools/chatter_shared.py`
- `tools/chatter_text.py`
- `tools/chatter_llm.py`
- `tools/chatter_db.py`
- `tools/chatter_links.py`
- `tools/chatter_events.py`
- `tools/chatter_prompts.py`
- `tools/chatter_constants.py`
- `tools/chatter_cache.py`
- `tools/talent_catalog.py`
- `tools/spell_names.py`

### BG / raid support

- `tools/chatter_battlegrounds.py`
- `tools/chatter_bg_prompts.py`
- `tools/chatter_raid_base.py`
- `tools/chatter_raids.py`
- `tools/chatter_raid_prompts.py`

### Development tools

- `tools/chatter_request_logger.py`
- `tools/chatter_log_viewer.py`

---

## 4b. Config Pipeline

C++ and Python read configuration independently. There is no C++ →
Python config relay.

- **C++ config**: `LLMChatterConfig.cpp` loads values from
  `mod_llm_chatter.conf` via the AzerothCore `sConfigMgr` API. These
  are values that C++ needs at runtime (cooldowns, chances for C++
  hooks, thresholds). Stored as member variables in `LLMChatterConfig`.

- **Python config**: `parse_config()` in `chatter_shared.py` reads the
  same `.conf` file directly from disk on bridge startup. Values are
  stored in a Python dict and accessed via `config.get('Key', default)`.
  Python-only config keys (e.g., `BotQuestionChance`, `IdleChance`,
  `ActionChance`, `ConversationBias`) are never loaded by C++ — they
  exist only in the `.conf` file and are read only by Python.

When adding a new Python-only config key:
1. Add the key + comment to `conf/mod_llm_chatter.conf.dist`
2. Add the key to your active server config file
3. Read it in Python via `config.get('LLMChatter.GroupChatter.KeyName', default)`
4. No C++ changes needed

---

## 5. Supported Providers

Configured through:

- `LLMChatter.Provider`
- `LLMChatter.Model`

Supported providers:

- Anthropic
- OpenAI
- Ollama

Examples:

```ini
LLMChatter.Provider = anthropic
LLMChatter.Model = haiku
```

```ini
LLMChatter.Provider = openai
LLMChatter.Model = gpt4o-mini
```

```ini
LLMChatter.Provider = ollama
LLMChatter.Model = qwen3:4b
```

---

## 6. Chatter Modes

Configured through:

- `LLMChatter.ChatterMode`

Modes:

- `normal`: casual MMO-style chat
- `roleplay`: in-character, race/class-influenced chat

The Python prompt builders are mode-aware and choose different tone,
mood, and style guidance based on the configured mode.

---

## 7. Ambient Open-World Chatter

Ambient chatter is the original module behavior.

### Trigger shape

The system periodically:

1. checks for a valid real player in the open world
2. finds eligible bots in the same zone
3. filters to bots that can actually speak in that zone's General
   channel
4. queues either a one-line statement or a multi-bot conversation

### Eligibility rules

Ambient chatter candidates must:

- be bots
- be in the same zone as the real player
- be in the world and alive
- not be grouped with a real player
- be members of the current General channel

### Message families

Ambient requests can become:

- plain statements
- quest statements
- loot statements
- quest + reward statements
- trade-style statements
- multi-bot conversations

Prompt generation and runtime logic live mainly in:

- `tools/chatter_ambient.py`
- `tools/chatter_prompts.py`
- `tools/chatter_shared.py`

---

## 8. General-Channel Player Reactions

When a real player speaks in General, the module can queue a
`player_general_msg` event.

### C++ ownership

Current C++ ownership lives in:

- `LLMChatterPlayer.cpp`

Relevant responsibilities:

- `OnPlayerCanUseChat(..., Channel*)`
- bot membership enforcement for General
- per-zone General cooldown handling
- writing/retaining `llm_general_chat_history`

### Python ownership

Python handling lives in:

- `tools/chatter_general.py`

That path:

- selects responding bot(s)
- builds the player-reaction prompt
- dispatches the reaction through the bridge path

### Relevant files

| File | Purpose |
|---|---|
| `LLMChatterPlayer.cpp` | General-channel hook, cooldowns, history writes |
| `LLMChatterConfig.h/.cpp` | General-channel config |
| `chatter_general.py` | Prompt building and event handler |
| `chatter_shared.py` | Addressed-bot detection and quick LLM analysis |
| `llm_chatter_bridge.py` | Event dispatch entry |

---

## 9. Group Chatter

Group chatter covers party-channel bot reactions when bots are grouped
with a real player.

### Event families

Examples include:

- bot group join
- group player message
- kill and wipe reactions
- death and resurrection reactions
- loot reactions
- spell cast reactions
- quest accept/objective/complete reactions
- zone transitions
- discovery reactions
- dungeon entry reactions
- nearby-object observations

### C++ ownership

Current group-side ownership is in:

- `LLMChatterGroup.cpp`

Important responsibilities:

- batch accumulation and flush
- per-group cooldown and dedup state
- named-boss cache loading
- combat state callouts
- direct event queue inserts for many `bot_group_*` events

### Python ownership

Current Python group ownership is split across:

- `chatter_group.py`
- `chatter_group_handlers.py`
- `chatter_group_prompts.py`
- `chatter_group_state.py`

### Pre-cache path

Some group reactions use a pre-cache path for faster replies.

That path is separate from live event generation and lives mainly in:

- `tools/chatter_cache.py`
- `tools/chatter_group_prompts.py`

---

## 10. World Events

World-owned C++ logic now lives in `LLMChatterWorld.cpp`.

### Main categories

- holiday events
- day/night transitions
- weather changes and weather ambient chatter
- transport arrivals triggered by transport objects entering a new
  player-relevant zone, with delivery in General channel
- pending message delivery
- nearby-object / nearby-creature scan events

### World-to-group boundary

The world layer intentionally calls a narrow group-owned surface:

- `LoadNamedBossCache()`
- `CheckGroupCombatState()`
- `FlushQuestAcceptBatches()`
- `FlushGroupJoinBatches()`

That surface is declared in `LLMChatterGroup.h`.

---

## 11. Nearby Object / Creature Awareness

Bots can notice nearby points of interest and comment on them or start a
short group conversation.

### C++ ownership

Current C++ scanning logic lives in:

- `LLMChatterWorld.cpp`

Specifically:

- `CheckNearbyGameObjects()`
- `NearbyGameObjectCheck`
- `NearbyCreatureCheck`

### Scanned interest types

The scan can surface things like:

- quest NPCs
- rare mobs
- trainers
- vendors
- innkeepers
- flightmasters
- chests
- text / book objects
- spell-focus objects
- critters and beasts

### Suppression

The feature is gated by:

- RNG chance
- per-group per-zone cooldown
- per-bot per-name cooldown
- combat suppression
- mounted/flying/BG suppression

### Python handling

Python handling lives in:

- `chatter_group_handlers.py`
- `chatter_group_prompts.py`

That path can produce either:

- a single reaction
- a short nearby-object conversation

---

## 12. Weather, Transport, and Holiday Behavior

### Weather

The world layer tracks current weather state per zone and queues:

- `weather_change`
- `weather_ambient`

Python can then naturally reference weather in prompts and event
reactions.

### Transport

Transport arrivals are world-owned C++ events with verified bot GUIDs in
`extra_data` so Python only uses bots that can actually speak in the
zone channel.

Current transport logic is:

1. poll live transport objects on the world timer
2. detect an actual zone/map transition per live transport GUID
3. ignore the transition unless the destination zone currently contains
   a real player
4. choose eligible General-channel bots already in that zone
5. write those GUIDs into `verified_bots`
6. suppress redispatch for the same transport entry until the transport
   cooldown window expires

This is intentionally an early-warning model. The message should appear
while the boat or zeppelin is approaching, not only after it has fully
docked.

### Holidays

Holiday chatter is also world-owned and queues zone/city-specific event
rows instead of speaking directly.

---

## 13. Battleground Chatter

Battleground-specific logic remains isolated from the later split.

### C++ ownership

- `LLMChatterBG.cpp`
- `LLMChatterBG.h`

### Python ownership

- `chatter_battlegrounds.py`
- `chatter_bg_prompts.py`
- `chatter_raid_base.py`

### Typical BG events

- match start / end
- flag pickup / drop / capture / return
- node assault / capture
- PvP kill
- score milestones
- arrival greetings
- BG idle chatter

### Current BG routing policy

The older broad "party plus battleground" duplication is no longer the
intended behavior.

BG-wide only:

- match start
- match end
- flag pickup / drop / capture / return

Subgroup/party only:

- PvP kills
- node assault / capture chatter
- score milestones
- spell/state chatter
- idle chatter
- flag-carrier self-messages

This keeps strategic objective callouts visible to the whole team while
reducing duplicated tactical chatter.

### BG brevity tuning

BG prompts now use a dedicated token cap plus stricter brevity
instructions so chatter stays short and tactical.

| Key | Default | Purpose |
|---|---|---|
| `BGChatter.MaxTokens` | 32 | Max token cap for BG prompt paths |

### Flag-carrier context persistence

BG prompts continue to receive both:

- `friendly_flag_carrier`
- `enemy_flag_carrier`

from `AppendBGContext()` in `LLMChatterBG.cpp`.

That means if a real player is carrying the enemy flag, later BG prompt
requests continue to know that until the flag is dropped, returned, or
captured.

---

## 13a. PvE Raid Chatter

Raid chatter extends group features into raid instances and adds
raid-specific events.

### Phase 1 (Session 70b): Boss Encounters

C++ `LLMChatterRaid.cpp` owns raid-specific boss hooks:

- `raid_boss_pull` — fires on boss engage
- `raid_boss_kill` — fires on boss death
- `raid_boss_wipe` — fires on raid wipe during boss encounter

Python handling lives in:

- `chatter_raids.py` — event handlers
- `chatter_raid_prompts.py` — prompt builders with instance/wing context

### Phase 2 (Session 71): Lifted Guards and Morale

Five suppression guards were changed from `IsRaid() || IsBattleground()`
to BG-only, allowing existing group features to fire inside raids:

- **Loot** — epic quality gate (quality >= 4) for raids
- **Nearby objects** — `CheckNearbyGameObjects()` no longer suppressed
- **Quest objectives** — now BG-only guard
- **Quest complete** — now BG-only guard
- **Quest accept batch** — now BG-only guard
- **Join batch** — now BG-only guard

Guards kept suppressed (not suitable for raids):
OnAddMember, OnRemoveMember, LevelUp, Discovery, ZoneTransition.

New event: `raid_idle_morale` — ambient morale chatter between boss
encounters. `CheckRaidIdleMorale()` in `LLMChatterWorld.cpp` fires on
the world timer. Suppressed during combat and wipe recovery (dead/ghost
bots).

### C++ ownership

| File | Responsibility |
|---|---|
| `LLMChatterRaid.cpp` | Boss pull/kill/wipe hooks |
| `LLMChatterWorld.cpp` | `CheckRaidIdleMorale()` |
| `LLMChatterGroup.cpp` | Lifted guards for loot/quest/join-batch |
| `LLMChatterShared.cpp` | `AppendRaidContext()` |
| `LLMChatterConfig.h/.cpp` | 3 morale config keys |

### Python ownership

| File | Responsibility |
|---|---|
| `chatter_raids.py` | Boss and morale event handlers |
| `chatter_raid_prompts.py` | Boss and morale prompt builders |
| `chatter_raid_base.py` | Shared dispatch, subgroup workers |
| `llm_chatter_bridge.py` | Event routing for `raid_*` types |

### Config keys

| Key | Default | Purpose |
|---|---|---|
| `MoraleEnable` | 1 | Enable/disable morale chatter |
| `MoraleCooldown` | 300 | Per-group cooldown (seconds) |
| `MoraleChance` | 30 | % chance per check |

### Dispatch model

Raid events use `dual_worker_dispatch()` from `chatter_raid_base.py`
for sub-group (party chat) delivery. Boss cooldown is enforced with
per-group, event-type-specific keys including `groupCounter` for
multi-group instances.

---

## 13b. Player Message Conversations (Multi-Bot Replies)

When a player speaks in party chat, the system can trigger a multi-bot
conversation instead of a single-bot reply. This makes groups feel
more socially dynamic.

Known playerbot control commands are not supposed to reach this
conversation path in current source:

- C++ now blocks them before creating `bot_group_player_msg` events
- Python keeps `_is_playerbot_command()` as a fallback skip layer

### Trigger logic

1. `find_addressed_bot()` in `chatter_shared.py` always fires an LLM
   call (even when name matching succeeds) to assess whether the
   message is `multi_addressed` — i.e., directed at the group rather
   than a single bot. Returns a dict:
   `{"bot": name, "multi_addressed": bool}`.
2. When `multi_addressed=True` and at least 2 bots are available,
   the conversation path is forced (bypasses the RNG gate).
3. Otherwise, the conversation path fires with probability
   `PlayerMsgConversationChance` (default 30%), scaled by bot count
   in the group.

### Multi-addressed detection

The LLM intent check detects plural pronouns ("you guys", "everyone",
"team"), group-directed questions ("what should we do?"), and messages
mentioning multiple bot names. This ensures group-directed speech
gets multi-bot replies without relying on RNG.

### Architecture

Uses Architecture B: a single LLM call returns a JSON array of 2-3
bot replies. `PlayerMsgSecondBotChance` (default 25%) controls whether
a third bot participates beyond the guaranteed two.

### Relevant files

| File | Responsibility |
|---|---|
| `chatter_shared.py` | `find_addressed_bot()` with multi-addressed intent |
| `chatter_group_prompts.py` | `build_player_msg_conversation_prompt()` |
| `chatter_group_handlers.py` | `execute_player_msg_conversation()` |
| `chatter_group.py` | Routing: single reply vs conversation |

### Config keys

| Key | Default | Purpose |
|---|---|---|
| `PlayerMsgConversationChance` | 30 | % chance of multi-bot reply to player message |
| `PlayerMsgSecondBotChance` | 25 | % chance a 3rd bot joins the conversation |

---

## 13d. Bot-Initiated Questions

Bots can periodically ask the real player creative questions in party
chat, making them feel socially interested in the player rather than
only reacting to events.

### Trigger logic

A Python timer fires every `BotQuestionCheckInterval` (default 30s).
Each tick:

1. Randomly selects one active group
2. Checks cooldown (10 min default) and inflight guard
3. Rolls `BotQuestionChance` (default 1%)
4. Combat suppression: checks for recent combat/kill/spell/death
   events (90s window via JSON_EXTRACT on `llm_chatter_events`)
5. Gets player name from `get_group_player_name()` or join event
   fallback
6. Selects a random bot, builds prompt with player context
7. Validates response ends with `?` (retry once if not)
8. Delivers via `insert_chat_message()` and stores in chat history

### Reply path (existing, no changes)

When the player replies, it fires `bot_group_player_msg`. The
original question is in `llm_group_chat_history`, so the bot's
reply is contextually aware. `PlayerMsgSecondBotChance` (25%)
can trigger a second bot chiming in.

### Config keys

| Key | Default | Purpose |
|---|---|---|
| `BotQuestionEnable` | 1 | Enable/disable feature |
| `BotQuestionChance` | 1 | % chance per tick |
| `BotQuestionCooldown` | 600 | Per-group cooldown (seconds) |
| `BotQuestionCheckInterval` | 30 | Timer interval (seconds) |

### Relevant files

| File | Responsibility |
|---|---|
| `chatter_group.py` | `check_bot_questions()` main logic |
| `chatter_group_prompts.py` | `build_bot_question_prompt()`, `BOT_QUESTION_TOPICS` |
| `llm_chatter_bridge.py` | Timer integration in main loop |

---

## 13e. Quest Conversations

Quest events (complete, objectives, accept) can trigger multi-bot
conversations instead of single-statement reactions, controlled by
`QuestConversationChance` (default 30%).

### Decision flow

Each of the 3 single-quest handlers (not `quest_accept_batch`)
checks after marking the event as `processing`:

1. Read `QuestConversationChance` from config
2. Call `get_group_members()` to count bots
3. Gate: `len(members) >= 2 and roll <= chance`
4. If conversation: call `_quest_*_conversation()` helper
5. If statement: existing `run_single_reaction()` path

### Conversation helpers

Two shared functions avoid code triplication:

- `_quest_conversation_pick_bots()` — picks 2-3 bots (reactor
  always included), looks up traits + class/race from DB. Returns
  `(bots, traits_map, bot_guids)` or `None`.
- `_quest_conversation_deliver()` — per-message cleanup
  (`strip_speaker_prefix`, `cleanup_message`, 255-char clamp),
  staggered delays via `calculate_dynamic_delay()`, first message
  gets action, stores chat history, marks event completed.

Three orchestration functions call these shared helpers:

- `_quest_complete_conversation()` — includes turn-in NPC lookup
- `_quest_objectives_conversation()` — no NPC, no mood update
- `_quest_accept_conversation()` — includes quest_level/zone_name

### Failure handling

If `call_llm()` fails or `parse_conversation_response()` returns
empty, the helper returns `False` and the handler falls through to
the existing statement path.

### Prompt builders

Three new functions in `chatter_group_prompts.py`:

| Function | Quest context |
|---|---|
| `build_quest_complete_conversation_prompt()` | "TRANSACTION COMPLETE", turn-in NPC, celebration |
| `build_quest_objectives_conversation_prompt()` | "PENDING TURN-IN", relief, readiness |
| `build_quest_accept_conversation_prompt()` | "PREPARATION", quest level, zone, anticipation |

### Config

| Key | Default | Purpose |
|---|---|---|
| `QuestConversationChance` | 30 | % chance per quest event |

### Relevant files

| File | Responsibility |
|---|---|
| `chatter_group_handlers.py` | 3 handler mods + 5 helpers |
| `chatter_group_prompts.py` | 3 conversation prompt builders |

---

## 13f. Achievement Event Batching

When multiple bots in the same group earn the same achievement within a
2-second window, the module can collapse those duplicate events into a
single congratulatory reaction.

### Why this exists

Without batching, simultaneous achievement events produce repetitive
party spam and can trigger multiple nearly identical LLM calls.

### Batch logic

`_check_achievement_batch()` in `chatter_group_handlers.py`:

1. queries neighboring `bot_group_achievement` rows for the same
   `group_id` and `achievement_name`
2. considers both `pending` and `processing` rows to avoid ownership
   races
3. assigns the batch to the lowest event ID
4. marks duplicate rows completed
5. returns either:
   - `None` for normal single processing
   - `'already_batched'` for a duplicate row
   - `list[str]` of achiever names for the batch owner

### Relevant files

| File | Responsibility |
|---|---|
| `chatter_group_handlers.py` | `_check_achievement_batch()` and achievement event routing |
| `chatter_group_prompts.py` | Group achievement reaction prompt builder |
| `chatter_bg_prompts.py` | BG-side achievement prompt path |

---

## 13g. Talent Context Injection

The bridge can inject talent-based context into prompts so bots sound
more like their build and spec without literally naming talents.

### Shared construction

`build_talent_context()` in `chatter_shared.py`:

1. loads the character's talents from the DB
2. finds the dominant talent tree
3. picks one talent from that tree
4. looks up a short natural-language description from
   `talent_catalog.py`
5. rewrites wording for `speaker` or `target` perspective
6. adds a guardrail telling the LLM not to name the talent directly

### Injection points

Talent context is invoked from:

- group event handlers
- group player-message paths
- General-channel player reactions
- battleground paths through `chatter_raid_base.py` and
  `chatter_battlegrounds.py`

### Config

| Key | Default | Purpose |
|---|---|---|
| `TalentInjectionChance` | 40 | % chance a given prompt gets talent context |

### Relevant files

| File | Responsibility |
|---|---|
| `chatter_shared.py` | `build_talent_context()` and catalog lookup |
| `chatter_group_handlers.py` | `_maybe_talent_context()` for group events |
| `chatter_group.py` | Talent-aware player/idle/group paths |
| `chatter_general.py` | Talent-aware General prompts |
| `chatter_raid_base.py` | Shared BG/raid talent injection path |
| `talent_catalog.py` | Static talent descriptions |

---

## 13h. Humor Hints and Conversation Pacing

Two later prompt/delivery changes affect how messages feel even though
they did not introduce new event types.

### Humor hints

`_pick_length_hint()` in `chatter_group_prompts.py` now optionally adds
humor guidance through `_maybe_humor_hint()`:

- 40% chance in normal mode
- 35% chance in roleplay mode

This applies across the group prompt builders that use the shared length
hint path. General-channel prompts were also retuned in the same period
to encourage humor more often.

### Ambient conversation pacing

Ambient multi-bot conversations in `chatter_ambient.py` now pass
`prev_message_length` into `calculate_dynamic_delay()`. That gives later
participants a reading delay before they reply to the previous message,
instead of only reacting to their own output length.

---

## 13i. LLM Request Logging

Every `call_llm()` invocation can be recorded to a JSONL log file for
debugging and analysis. This is a Python-only development feature with
no C++ involvement.

### Files

| File | Purpose |
|---|---|
| `tools/chatter_request_logger.py` | Thread-safe JSONL logger |
| `tools/chatter_log_viewer.py` | Zero-dependency stdlib web UI |

### Logger

`chatter_request_logger.py` provides:

- `init_request_logger(config)` — called once at bridge startup; reads
  config, creates the log directory, sets up the global state
- `log_request(label, prompt, response, model, provider, duration_ms)` —
  called from `call_llm()` via lazy import in `finally` block; writes
  one JSONL line per call
- Rotation: when the log file exceeds `MaxSizeMB`, it is renamed to
  `.1.jsonl` and a fresh file begins

Each JSONL record contains:

```json
{
  "timestamp": "2026-03-18T12:34:56.789",
  "label": "group_join",
  "model": "claude-haiku-4-5",
  "provider": "anthropic",
  "duration_ms": 421,
  "zone_name": "Elwynn Forest",
  "zone_flavor": "A peaceful woodland...",
  "subzone_name": "Goldshire",
  "subzone_lore": "A small hamlet...",
  "speaker_talent": "...",
  "target_talent": "...",
  "prompt": "...",
  "response": "..."
}
```

Metadata fields (zone_name, zone_flavor, subzone_name, subzone_lore,
speaker_talent, target_talent) are only written when non-empty — absent
fields mean the context was not available for that call.

### Labels

Every `call_llm()` call site passes a descriptive `label=` keyword
argument so log entries can be filtered by feature. All 27 call sites
are labelled:

| Label | Source |
|---|---|
| `event_conv` / `event_statement` | `llm_chatter_bridge.py` |
| `ambient_statement` / `ambient_conv` | `chatter_ambient.py` |
| `precache` | `chatter_cache.py` |
| `general_player_msg` / `general_followup` / `general_conv` | `chatter_general.py` |
| `group_join` / `group_welcome` / `group_player_msg` / `group_composition` / `group_idle` / `group_idle_conv` / `group_bot_question` | `chatter_group.py` |
| `group_nearby_obj` / `group_player_msg_conv` / `group_quest_conv` | `chatter_group_handlers.py` |
| `group_farewell` | `chatter_group_state.py` |
| `single_reaction` | `chatter_shared.py` |

### Web viewer

`chatter_log_viewer.py` is a standalone script with no external
dependencies (Python stdlib only). Run it on the host:

```bash
python modules/mod-llm-chatter/tools/chatter_log_viewer.py \
    --log modules/mod-llm-chatter/logs/llm_requests.jsonl \
    --port 5555
```

Then open `http://localhost:5555`.

Features:

- entry list (left panel) + detail view (right panel)
- draggable vertical column divider and horizontal prompt/response divider
- semantic prompt section highlighting with colored left borders:
  IDENTITY, TRAITS, CONTEXT, TASK, RULES, FORMAT, STYLE
- section pill badges in the prompt header
- JSON pretty-print for structured responses
- copy buttons for prompt and response
- filtering by label and text search
- pagination
- auto-refresh every 30s (toggleable)

### Docker bind mount

The log file is written inside the container at `/logs/llm_requests.jsonl`
and mapped to the host at `modules/mod-llm-chatter/logs/` via a bind
mount in `docker-compose.override.yml`:

```yaml
volumes:
  - ./modules/mod-llm-chatter/logs:/logs:rw
```

**Applying mount changes** requires container recreation, not just restart:

```bash
docker compose --profile dev up -d ac-llm-chatter-bridge
```

### Config keys

All three keys are `[BRIDGE]` scope (Python-only; no server restart needed).

| Key | Default | Purpose |
|---|---|---|
| `LLMChatter.RequestLog.Enable` | 1 | Enable/disable logging |
| `LLMChatter.RequestLog.Path` | `/logs/llm_requests.jsonl` | Log file path inside container |
| `LLMChatter.RequestLog.MaxSizeMB` | 50 | Rotation threshold |

---

## 13c. Responsive Delays

Player-directed replies use faster timing than ambient chatter. The
`calculate_dynamic_delay()` function in `chatter_shared.py` accepts a
`responsive=True` parameter that:

- skips distraction simulation
- uses shorter reaction and typing windows
- enforces a 2-second floor (vs 4 seconds for ambient)
- skips reading time for multi-bot conversation follow-up messages

All player message paths (single reply, conversation, multi-addressed)
use responsive delays. Ambient chatter, idle banter, and world events
continue to use standard timing.

---

## 13c. Persistent Bot–Player Memory

### Overview

Bots accumulate a bounded journal of shared moments with real players.
On re-invite, the bot delivers a reunion greeting that references past
experiences rather than treating the player as a stranger.

### Memory lifecycle

1. **Group join** (`process_group_join_event` / `process_group_join_batch_event`)
   - `start_session()` registers the bot in the in-memory session tracker
   - `get_bot_memories()` fetches up to 3 random `active=1` memories for this
     bot–player pair
   - If memories exist: `player_name_known=True` → reunion greeting mode
   - If no memories (first meeting): a `first_meeting` memory is inserted
     directly with `active=1` and `memory_type='first_meeting'`, guarded by
     `INSERT...SELECT...WHERE NOT EXISTS` to prevent duplicates on re-join.
     This memory is immune to both short-session discard and cap pruning.

2. **During the session** — event handlers may call `_generate_and_store_memory()`
   to produce LLM-generated memories (boss kills, notable events). These are
   inserted with `active=0` until flush.

3. **Group farewell** (`process_group_farewell_event` → `flush_session_memories()`)
   - If session was long enough (`SessionMinutes` threshold): activates `active=0`
     rows and prunes oldest memories to the `MaxPerBotPlayer` cap.
     `first_meeting` rows are excluded from the prune DELETE.
   - If session was too short: deletes all `active=0` rows for this session.
     `first_meeting` rows are `active=1` and unaffected.

4. **Reunion greeting** — when `get_bot_memories()` returns a non-empty list,
   the greeting prompt enters reunion mode: injects `<past_memories>` block,
   uses familiar tone, optionally recalls a specific memory (`recall_memory`).
   The `is_reunion` flag is `bool(memories and player_name_known)`, so a first
   meeting (where `memories=[]`) always produces a fresh greeting even though
   `player_name_known` is set to `True` for internal tracking.

### Files

| File | Role |
|------|------|
| `chatter_memory.py` | Session tracking, memory generation, flush, retrieval |
| `chatter_group.py` | Calls `start_session`, `get_bot_memories`, first-meeting insert |
| `chatter_group_prompts.py` | `build_bot_greeting_prompt` — reunion mode and `<past_memories>` injection |

### Database tables

| Table | Purpose |
|-------|---------|
| `llm_bot_memories` | Per-bot-per-player memory journal. `memory_type` includes `first_meeting`, `boss_kill`, `party_member`, etc. |
| `llm_bot_identities` | Persistent personality traits keyed by `bot_guid`. Regenerated only on `IdentityVersion` bump. |

### Config keys

| Key | Default | Purpose |
|-----|---------|---------|
| `LLMChatter.Memory.Enable` | `1` | Master toggle |
| `LLMChatter.Memory.SessionMinutes` | `15` | Minimum session length to activate memories |
| `LLMChatter.Memory.MaxPerBotPlayer` | `50` | Cap on active memories per bot–player pair |
| `LLMChatter.Memory.RecallChance` | `30` | % chance a specific memory is highlighted in reunion greeting |
| `LLMChatter.Memory.IdentityVersion` | `1` | Bump to force personality regeneration for all bots |

---

## 13d. Queue and Message Cleanup

The system has four cleanup layers that work together to ensure stale
queue entries and undelivered messages are never visible to players after
a group ends.

| Layer | Trigger | Scope | Mechanism |
|-------|---------|-------|-----------|
| `OnRemoveMember` | Bot removed from group | That bot only | Cancels queue entries containing `bot_guid`; marks messages delivered |
| `CleanupGroupSession` | Group disbands or no real player remains | Full group | Cancels all queue entries for group bots; marks messages delivered. Runs **before** deleting `llm_group_bot_traits` so IN-subqueries resolve correctly |
| Bridge TTL | Every poll cycle | Global (5-min window) | Cancels `llm_chatter_queue` entries `> 5 MINUTE` old; marks messages `> 5 MINUTE` past `deliver_at` |
| `OnPlayerLogin` | Real player logs in | Global (30-second grace) | Crash-recovery only. Cancels queue entries `> 30 SECOND` old; marks messages `> 30 SECOND` past `deliver_at`. Protects freshly-queued entries from other online players |

The 30-second grace in `OnPlayerLogin` means other players' active entries
(queued < 30 seconds ago) are safe. In normal operation `CleanupGroupSession`
handles everything; `OnPlayerLogin` only matters after a server crash.

---

## 14. JSON and Queue Contracts

### `QueueChatterEvent()`

Shared C++ insert helper:

- implemented in `LLMChatterShared.cpp`
- declared in `LLMChatterShared.h`

Critical rule:

- direct callers must pass JSON text that is already SQL-safe

Wrappers like world-private `QueueEvent()` handle that escaping
internally.

The nearby-object direct world path now explicitly escapes `extraJson`
before calling `QueueChatterEvent()`.

### Statement response contract

Typical single-message JSON shape:

```json
{"message": "...", "emote": null, "action": null}
```

### Conversation response contract

Typical multi-message JSON shape:

```json
[
  {"speaker": "BotA", "message": "...", "emote": null, "action": null},
  {"speaker": "BotB", "message": "...", "emote": null, "action": null}
]
```

---

## 15. Database Tables

| Table | Producer | Consumer | Purpose |
|---|---|---|---|
| `llm_chatter_events` | C++ | Python | Event queue |
| `llm_chatter_queue` | C++ | Python | Ambient request queue |
| `llm_chatter_messages` | Python | C++ | Outbound delivery queue |
| `llm_group_cached_responses` | Python | C++ | Pre-cached instant reactions |
| `llm_group_bot_traits` | Python | Python | Group personality state |
| `llm_group_chat_history` | Python | Python | Group anti-repetition history |
| `llm_general_chat_history` | C++/Python read path | Python/C++ | General-channel history |
| `llm_bot_memories` | Python | Python | Per-bot-per-player memory journal (active=1 persists; first_meeting immune to prune) |
| `llm_bot_identities` | Python | Python | Persistent bot personality traits; regenerated on IdentityVersion bump |

---

## 16. Important Editing Rules

### Separation of Concerns

New features or subsystems must go in their own file(s). Never dump
unrelated logic into an existing file. Shared utilities belong in the
dedicated shared layer (`LLMChatterShared.cpp/h` for C++,
`chatter_shared.py` / `chatter_constants.py` for Python). Each file
should have one clear ownership domain.

### `enabledHooks`

Any new or changed C++ hook override must add the correct enum to the
constructor's `enabledHooks` vector or it will silently never fire.

### C++ file routing

- `LLMChatterWorld.cpp` for world/delivery/environment logic
- `LLMChatterGroup.cpp` for group/state/batching logic
- `LLMChatterPlayer.cpp` for General-channel player logic
- `LLMChatterShared.cpp` for shared helper contracts
- `LLMChatterScript.cpp` is registration only — do not add features here

### Compile policy

Do not compile automatically.
Wait for explicit user approval before running build steps.

---

## 17. Known Gaps

- Boss pull/kill/wipe events need live in-game testing via actual boss
  encounters
- Hostile multi-target spell-attribution edge case not fully covered
- Exhaustive in-game validation of every event path is ongoing

---

## 18. Related Docs

- `docs/mod-llm-chatter-architecture.md` — architecture reference,
  file map, dependency tree, data flow
