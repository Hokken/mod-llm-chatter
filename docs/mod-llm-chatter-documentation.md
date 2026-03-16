# mod-llm-chatter - Logic Documentation

This document describes the current runtime logic of `mod-llm-chatter`
after the C++ script split that landed through Phase 4 on 2026-03-08,
including the later runtime features added through Session 68.

It is meant to answer two practical questions:

1. What does the module do at runtime?
2. Where does that logic live now?

Important status note:

- the source refactor is complete through Phase 4
- the split passed phased source review
- compile and linker validation passed on 2026-03-09 (two minor fixes
  applied)
- the module has stayed in active runtime use after that validation, and
  this document reflects the current shipped logic through Session 68

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

C++ delivery then polls:

- `WHERE delivered = 0 AND deliver_at <= NOW()`
- `ORDER BY deliver_at ASC LIMIT 1`

So once a message has been created, delivery is time-based, not
priority-based.

### Current priority limitation

The system has event priority, but it does **not** yet have a unified
global message scheduler across:

- legacy ambient requests
- event workers
- background timer jobs
- final message delivery

Also, `GlobalMessageCap` and `TransportBypassGlobalCap` are currently
loaded/logged config values, but they are not enforced by the active
runtime path.

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

## 3. Current C++ File Ownership

The old assumption that almost everything lives in
`LLMChatterScript.cpp` is no longer correct.

### `src/LLMChatterScript.cpp`

Current role:

- registration coordinator only

It now just calls:

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
2. Add the key to the active `env/dist/etc/modules/mod_llm_chatter.conf`
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
- transport arrivals
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

---

## 13b. Player Message Conversations (Multi-Bot Replies)

When a player speaks in party chat, the system can trigger a multi-bot
conversation instead of a single-bot reply. This makes groups feel
more socially dynamic.

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

---

## 16. Important Editing Rules

### Separation of Concerns

New features or subsystems must go in their own file(s). Never dump
unrelated logic into an existing file. Shared utilities belong in the
dedicated shared layer (`LLMChatterShared.cpp/h` for C++,
`chatter_shared.py` / `chatter_constants.py` for Python). Each file
should have one clear ownership domain.

The original monolithic layout caused real problems — the split exists
to enforce domain boundaries, not just to reduce line count. Keeping
files focused also allows AI agents to work on a single file without
loading the entire module into context.

### `enabledHooks`

Any new or changed C++ hook override must add the correct enum to the
constructor's `enabledHooks` vector or it will silently never fire.

### Do not keep editing `LLMChatterScript.cpp` by habit

That file is now just a coordinator.

Use:

- `LLMChatterWorld.cpp` for world/delivery/environment logic
- `LLMChatterGroup.cpp` for group/state/batching logic
- `LLMChatterPlayer.cpp` for General-channel player logic
- `LLMChatterShared.cpp` for shared helper contracts

### Compile policy

Do not compile automatically.
Wait for explicit user approval before running build steps.

---

## 17. Validation Status

What is complete:

- source-level C++ split through Phase 4
- per-phase external review
- final focused review for the `QueueChatterEvent()` cleanup
- compile and linker validation (2026-03-09, two minor fixes applied)
- runtime feature work continued on top of the split through Session 68

What is still pending:

- exhaustive in-game validation of every event path and tuning edge case

---

## 18. Related Docs

- `docs/plans/llm-chatter-script-splitting-plan.md`
- `docs/investigations/llm-chatter-phase-0-5-ownership-investigation.md`
- `docs/reviews/llm-chatter-phase-1-shared-infrastructure-review.md`
- `docs/reviews/llm-chatter-phase-2-world-and-event-hooks-review.md`
- `docs/reviews/llm-chatter-phase-3-group-subsystem-review.md`
- `docs/reviews/llm-chatter-phase-4-player-subsystem-review.md`
- `docs/reviews/llm-chatter-queuechatterevent-callsite-cleanup-review.md`
