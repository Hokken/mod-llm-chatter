# mod-llm-chatter Architecture

Last updated: 2026-04-03 (added proximity chatter subsystem)

## Purpose

Reference architecture for humans and LLMs editing
`modules/mod-llm-chatter`.

This document reflects the current source architecture.

For new work, route by ownership first. If you are unsure where a
change belongs, use "Where To Edit What" in this file before touching
code.

## Guiding Principle: Separation of Concerns

New features or subsystems must go in their own file(s) — never dump
unrelated logic into an existing file just because it is convenient.
Shared utilities belong in the dedicated shared layer
(`LLMChatterShared.cpp/h` for C++, `chatter_shared.py` /
`chatter_constants.py` for Python). Each file should have one clear
ownership domain.

This rule exists because the original monolithic layout caused real
problems (see "Why The C++ Split Happened" below) and because keeping
files focused allows AI agents to work on a single file without
loading the entire module into context.

## Repository Boundaries

- **AzerothCore root repo**: the parent AzerothCore server repo where
  this module is installed under `modules/mod-llm-chatter`
- **Module repo**: `modules/mod-llm-chatter` — all runtime Python and
  C++ code lives here
- Runtime code changes belong in the module repo
- This architecture doc lives in `docs/` inside the module repo

## Docker Bind Mounts

The chatter bridge container has two relevant volume mounts:

| Host path | Container path | Mode | Purpose |
|---|---|---|---|
| `modules/mod-llm-chatter/tools/` | `/app/tools/` | `:ro` | Python source (read-only) |
| `modules/mod-llm-chatter/logs/` | `/logs/` | `:rw` | LLM request log output |

The `/logs` mount is defined in `docker-compose.override.yml` under
`ac-llm-chatter-bridge`. The log path config key
`LLMChatter.RequestLog.Path` must point inside `/logs/` to write to
the host filesystem.

**Important**: adding or changing volume mounts requires container
recreation (`docker compose --profile dev up -d ac-llm-chatter-bridge`),
not just `docker restart`.

## High-Level Runtime Flow

1. C++ scripts queue ambient requests and event rows in MySQL.
2. Python bridge polls pending work and routes by event type.
3. Python generates messages and writes them to
   `llm_chatter_messages`.
4. C++ world tick delivers messages in game.
5. Party-channel delivery may play text emotes; General/Raid/BG
   delivery does not.

### Screenshot vision data flow

The screenshot vision feature adds a second event source outside the
C++ server:

1. Host-side `screenshot_agent.py` captures the WoW game window.
2. Agent sends the JPEG to a vision LLM (OpenAI or Anthropic).
3. Vision LLM returns structured JSON (description, atmosphere,
   canonical tags).
4. Agent inserts a `bot_group_screenshot_observation` row into
   `llm_chatter_events` via direct MySQL connection.
5. Bridge claims the event and routes to
   `chatter_screenshot_handler.py`.
6. Handler generates in-character bot comments using existing
   personality, zone context, and vision description.
7. Messages are written to `llm_chatter_messages` for normal C++
   delivery.

The agent runs on the host machine (not in Docker) and connects to
MySQL directly. It is configured via the same `.conf` file and is
disabled by default.

### Proximity chatter data flow

Proximity chatter creates ambient `/say` conversations between bots,
NPCs, and real players as they move through the world:

1. C++ `CheckProximityChatter()` runs on a configurable timer
   (default 30s) in `LLMChatterWorld.cpp`.
2. `LLMChatterProximity.cpp` scans around each real player within
   a 40-yard radius for eligible humanoid NPCs and party bots.
3. One or more speakers are selected from the candidate pool.
   If all candidates are party bots, the scan is skipped (idle chat
   handles that case).
4. A `proximity_say` (single statement) or `proximity_conversation`
   (multi-speaker) event is queued to `llm_chatter_events` with
   NPC spawn GUIDs and nearby entity names in `extra_data`.
5. Python `chatter_proximity.py` claims the event, builds prompts
   with zone context and a topic from the 250+ entry topic pool,
   and generates messages.
6. Messages are written to `llm_chatter_messages` with channel
   `"say"` (for bots) or `"msay"` (for NPCs).
7. C++ delivery dispatches bot messages via `CHAT_MSG_SAY` and NPC
   messages via `CHAT_MSG_MONSTER_SAY` (speech bubbles). Speakers
   face each other via `SetFacingToObject()`, and NPC orientation
   resets after delivery via `BasicEvent`.
8. When a real player speaks in `/say` near a recent proximity scene,
   `HandleProximityPlayerSay()` in `LLMChatterGroupCombat.cpp`
   detects the reply and queues a `proximity_reply` event, enabling
   natural player-to-NPC/bot exchanges.

NPCs are identified by spawn GUID (`Creature::GetSpawnId()`) rather
than entry ID, allowing per-instance entity cooldowns. The
`ProximityScene` struct tracks active conversations for reply matching.

## System Prompt Architecture

All prompt builders return a `PromptParts` object (defined in
`chatter_shared.py`). `PromptParts` subclasses `str` so it is
backward-compatible with code that treats prompts as plain strings.
It carries two extra attributes:

- `.system_prompt` — persona, rules, format instructions
- `.user_prompt` — event context, chat history, the actual task

### Flow

1. Prompt builder calls `PromptParts(system_prompt, user_prompt)`.
2. `call_llm()` or `quick_llm_analyze()` in `chatter_llm.py`
   auto-detects `PromptParts` via `_split_prompt()`.
3. Provider dispatch:
   - **Anthropic**: native `system=` parameter + user message
   - **OpenAI / Ollama**: system role message + user role message
4. If a plain string is passed instead of `PromptParts`, the entire
   string is sent as a single user message (backward compatibility).

### Token-Saving Gates

Two config-driven RNG checks control optional prompt sections:

- `EmoteChance` - gates inclusion of the ~244-emote list (~500 tokens).
  Checked once per prompt build. Does NOT apply to General channel
  (emotes are proximity-based animations; General is zone-wide text,
  so emotes are intentionally suppressed via `skip_emote=True`).
- `ActionChance` - controls whether action narrations appear. Two
  strategies depending on path:
  - **Single statements**: pre-call RNG in `append_json_instruction()`
    decides before the LLM call whether to ask for an action (saves
    tokens when disabled).
  - **Conversations** (General, Proximity, Group idle, Group handlers,
    Screenshot vision): prompts always tell the LLM to include actions
    (in RP mode). `strip_conversation_actions()` in `chatter_shared.py`
    enforces ActionChance per-message post-parse. This avoids trusting
    the LLM to randomize naturally.

If the prompt/output parser yields `"emote": null`, Python insert paths
must preserve that null value. Do not synthesize a fallback emote during
DB insert. `LLMChatter.EmoteChance` is the source of truth for whether
the LLM is even asked for an emote.

## Queue Model, Timing, and Priority

The module currently uses three separate DB-backed queues. They do not
share one global scheduler.

### 1) `llm_chatter_queue` - legacy ambient request queue

- used for legacy ambient General chatter requests
- inserted by C++ in `LLMChatterWorld.cpp`
- consumed by `process_pending_requests()` in
  `llm_chatter_bridge.py`
- fetched FIFO: `ORDER BY created_at ASC`
- gated by `LLMChatter.MaxPendingRequests`, which currently limits only
  this queue, not the event queue

### 2) `llm_chatter_events` - reactive/event queue

- used for `bot_group_*`, `bg_*`, `player_general_msg`, weather,
  transport, holiday, and related event-driven work
- rows carry `priority`, `react_after`, and `expires_at`
- fetched by the bridge only when:
  - `status = 'pending'`
  - `react_after <= NOW()` or null
  - `expires_at > NOW()` or null
- claim order is:
  - `ORDER BY priority DESC, created_at ASC`
- workers claim via compare-and-swap update to `processing`

### 3) `llm_chatter_messages` - outbound delivery queue

- Python writes final chat rows here with a `deliver_at` timestamp
- C++ delivery polls one ready row at a time
- when `LLMChatter.PrioritySystem.Enable = 1` and
  `LLMChatter.PrioritySystem.DeliveryOrderEnable = 1`, delivery joins
  back to `llm_chatter_events` and orders by:
  `COALESCE(e.priority, 0) DESC, m.deliver_at ASC`
- ambient rows with `event_id = NULL` therefore remain lowest priority
- when the delivery-order feature is disabled, fallback order remains
  `deliver_at ASC`

### Timing layers

There are two separate timing stages:

- **Event reaction delay**: C++ sets `react_after` when the event row is
  inserted. This delays when Python is allowed to process the event.
  The shared C++ implementation now uses table-driven priority and delay
  registries rather than long conditional chains.
- **Message delivery delay**: Python sets `deliver_at` when it inserts
  the final message row. This delays when C++ is allowed to speak it in
  game.

`calculate_dynamic_delay()` in `chatter_shared.py` controls the second
stage for most Python-generated messages. Player-directed replies use
`responsive=True`; ambient/group conversations can also include reading
time from the previous message length.

### Group serialization

The bridge processes many events in parallel, but it uses a per-group
lock so events sharing the same `group_id` do not run concurrently. This
avoids cross-talk and state races inside a single party.

Session 69 refined this with two lock lanes:

- urgent/high events and filler events for the same `group_id` no longer
  share the same queued lock lane
- this reduces the chance that queued filler work blocks queued urgent
  work for the same group

### Current priority behavior and remaining limits

The module now has meaningful end-to-end priority behavior, but it is
still not a perfect single global scheduler across every queue and
worker lane.

What priority now affects:

- event claim order from `llm_chatter_events`
- bridge scheduling, where urgent backlog suppresses or defers filler
  jobs
- pre-cache fairness during urgent backlog
- final in-game delivery ordering when priority delivery is enabled

What is still limited:

- `llm_chatter_queue` is FIFO and has no priority field
- same-executor saturation can still delay work even when claim order is
  correct
- same-group serialization still exists inside each urgency lane
- `GlobalMessageCap` and `TransportBypassGlobalCap` remain legacy config
  values and are not the main protection mechanism anymore
- provider-safety mode is bridge-side suppression logic, not a hard DB
  queue partitioning system

This is why future work should focus on validation and tuning more than
on inventing a first priority system from scratch.

## Main Bridge Loop

The bridge is **not** a single-threaded "process everything inline"
loop. It is a coordinator loop plus a worker pool.

### Coordinator thread

`llm_chatter_bridge.py` owns one long-running `while True` loop that:

- opens a DB connection for fast coordinator work
- harvests finished futures
- runs periodic cleanup SQL
- claims ready event rows from `llm_chatter_events`
- submits claimed work to worker threads
- launches background timer-like tasks when their intervals elapse
- sleeps for `LLMChatter.Bridge.PollIntervalSeconds` between iterations

### Worker pool

The bridge creates a `ThreadPoolExecutor` with:

- `max_concurrent = LLMChatter.Bridge.MaxConcurrent` for event workers
- `max_workers = max_concurrent + 4` total threads

Event rows claimed from `llm_chatter_events` run in worker threads via
`process_single_event()`, each with its own DB connection.

### Group serialization inside the worker model

Event processing is parallel by default, but group-scoped events are
submitted through `_run_with_group_lock(...)` so only one event per
`group_id` executes at a time.

### Background timer-style tasks

These are not processed inline in the same event loop body once due;
they are scheduled onto the worker pool as separate jobs:

- legacy ambient request processing from `llm_chatter_queue`
- idle group chatter checks
- bot-question checks
- pre-cache refills

So the current architecture is:

- one coordinator loop
- multiple event workers
- several interval-driven background jobs using the same executor

Session 69 added two scheduling controls around that model:

- **bridge yield mode**: legacy ambient requests, idle chatter, and bot
  questions can yield when urgent backlog exists
- **safety mode**: under sustained backlog, the bridge suppresses
  filler-first launches before sacrificing urgent work

## Current C++ Module Map

| File | Approx lines | Primary ownership |
|---|---:|---|
| `src/LLMChatterScript.cpp` | 17 | Registration coordinator only |
| `src/LLMChatterShared.cpp` | ~1900 | Shared helpers: SQL/JSON escaping, canonical shared lookup helpers (`GetZoneName()`, `GetClassName()`, `GetRaceName()`), `BuildBotIdentityFields()` / `BuildBotStateJson()`, queue insert helper, shared event cooldown helper, table-driven event priority/reaction-delay registries, link/emote/delivery helpers, `GetTextEmoteName()` reverse lookup, `SendUnitTextEmote()` consolidated emote packet helper, cross-domain formatting helpers, General-channel membership check helper, `FindCreatureBySpawnId()` spawn-GUID creature lookup, `GetCreatureRoleName()` NPC role description helper |
| `src/LLMChatterShared.h` | 83 | Shared declarations still used across domains; `class Unit` forward-declared for `SendUnitTextEmote()`; currently also declares world/player registration |
| `src/LLMChatterDelivery.cpp` | ~500 | Outbound message delivery implementation: DB polling, facing selection, party/raid/BG/General/yell/say/msay dispatch, spawn-GUID creature lookup for NPC delivery, NPC orientation reset via BasicEvent, sequence-based facing for multi-speaker proximity scenes, post-send delivery state updates |
| `src/LLMChatterDelivery.h` | 4 | Narrow delivery extraction declaration used by `LLMChatterWorld.cpp` |
| `src/LLMChatterAmbient.cpp` | 963 | Ambient world/event ownership: day/night transitions, holiday start/stop routing, weather state tracking, weather reactions, zone-level ambient chatter selection, ambient request queue writes |
| `src/LLMChatterAmbient.h` | 24 | Narrow ambient declarations consumed by `LLMChatterWorld.cpp` |
| `src/LLMChatterNearby.cpp` | 691 | Nearby-object and nearby-creature scanning, POI scoring, nearby direct event queueing, nearby-local cooldowns |
| `src/LLMChatterNearby.h` | 6 | Narrow nearby scan declaration consumed by `LLMChatterWorld.cpp` |
| `src/LLMChatterWorld.cpp` | ~800 | WorldScript ownership, thin ambient/nearby/delivery/proximity delegation, transport polling and route announcements, transport-private state, retained world-private `QueueEvent()` helper |
| `src/LLMChatterGroup.cpp` | 842 | Shared group state definitions, shared helpers (`GroupHasRealPlayer`, `GetRandomBotInGroup`, `CountBotsInGroup`, pre-cache helpers), named-boss cache, `CleanupGroupSession()` coordinator, thin `LLMChatterGroupPlayerScript` shell wrappers, registration |
| `src/LLMChatterGroupCombat.cpp` | 2525 | Remaining group PlayerScript implementation bodies (kill/death/loot/combat/chat/level/quest/achievement/spell/resurrect/corpse-run/dungeon-entry/emote dispatch), text-emote target classification and group gating, zone transition handling, combat state callouts, file-local `QueueStateCallout()` |
| `src/LLMChatterGroupInternal.h` | 239 | Shared group internal header: struct definitions (`GroupJoinEntry`, `GroupJoinBatch`, `QuestAcceptEntry`, `QuestAcceptBatch`), extern declarations for all shared cooldown maps, batch containers, mutexes, emote cooldowns, named boss cache; shared helper declarations; domain entry-point declarations; `EmoteTargetType` enum |
| `src/LLMChatterGroupJoin.cpp` | 866 | Group join batching: `QueueBotGreetingEvent()`, `EnsureGroupJoinQueued()`, `FlushGroupJoinBatches()`, `LLMChatterGroupScript` (GroupScript: `OnAddMember`, `OnRemoveMember` with farewell, `OnDisband`) |
| `src/LLMChatterGroupEmote.cpp` | 529 | Emote reaction system: `DelayedMirrorEmoteEvent`, `DelayedCreatureMirrorEmoteEvent`, emote static data (mirror map, denylist, combat callouts, contagious set), `HandleEmoteAtGroupBot()`, `HandleEmoteAtCreature()`, `HandleEmoteObserver()`, `EvictEmoteCooldowns()` |
| `src/LLMChatterGroupQuest.cpp` | 520 | Quest accept batching: `FlushQuestAcceptBatches()`, `LLMChatterCreatureScript` (AllCreatureScript: `CanCreatureQuestAccept` with debounce/immediate paths) |
| `src/LLMChatterGroup.h` | 18 | World-to-group cross-call surface plus group registration |
| `src/LLMChatterPlayer.cpp` | 1103 | Player General-channel hooks, General cooldowns, `EnsureBotInGeneralChannel()`, player registration |
| `src/LLMChatterRaid.cpp` | 767 | Raid boss hooks (pull/kill/wipe), boss lookup table (80+ entries across Classic/TBC/WotLK), `IsDatabaseBound() override`, raid registration |
| `src/LLMChatterProximity.cpp` | ~800 | Proximity chatter: periodic scan around real players, NPC/bot eligibility filtering, candidate scoring, `proximity_say`/`proximity_conversation` event queueing, `ProximityScene` tracking for player reply detection, entity cooldown management |
| `src/LLMChatterProximity.h` | ~20 | Proximity scan and player-say hook declarations consumed by `LLMChatterWorld.cpp` and `LLMChatterGroupCombat.cpp` |
| `src/LLMChatterBG.cpp` | 1348 | Battleground hooks, BG state polling, BG queue helpers, BG registration |
| `src/LLMChatterBG.h` | 14 | BG registration declaration |
| `src/LLMChatterConfig.h/.cpp` | 839 | Config loading and config struct |
| `src/llm_chatter_loader.cpp` | 11 | Module entry point, calls `AddLLMChatterScripts()` |

## Current Registration Shape

`llm_chatter_loader.cpp` calls:

- `AddLLMChatterScripts()`

`LLMChatterScript.cpp` is now the coordinator and calls:

- `AddLLMChatterWorldScripts()`
- `AddLLMChatterGroupScripts()`
- `AddLLMChatterPlayerScripts()`
- `AddLLMChatterBGScripts()`
- `AddLLMChatterRaidScripts()`

Current header topology is intentionally functional, not perfectly
uniform:

- `LLMChatterShared.h` declares shared helpers plus
  `AddLLMChatterWorldScripts()` and `AddLLMChatterPlayerScripts()`
- `LLMChatterGroup.h` declares `AddLLMChatterGroupScripts()` plus the
  explicit world-to-group cross-call surface
- `LLMChatterBG.h` declares BG registration

This asymmetry is known and acceptable in the shipped source state.

## Current Python Module Map

### Entry and orchestration

| File | Primary ownership |
|---|---|
| `tools/llm_chatter_bridge.py` | Main loops, event claiming, registry-driven routing, worker orchestration |
| `tools/chatter_event_registry.py` | Central Python event registry: handler module/function resolution, producer notes, payload field docs, dead-event tracking |
| `tools/chatter_ambient.py` | Ambient statement/conversation generation |

### Group domain

| File | Primary ownership |
|---|---|
| `tools/chatter_group.py` | Group join, group player message flow, idle chatter, and group-side message inserts for those paths |
| `tools/chatter_group_handlers.py` | `bot_group_*` reaction handlers, `execute_player_msg_conversation()`, thin wrappers around the shared handler pipeline for most single-reaction group events |
| `tools/chatter_handler_pipeline.py` | Shared `run_group_handler()` pipeline: extra_data parsing, guard checks, traits lookup, context assembly, prompt dispatch, chat storage, mood update, event completion/failure handling |
| `tools/chatter_group_prompts.py` | Group prompt builders, nearby-object prompts, pre-cache prompt builders, `build_player_msg_conversation_prompt()`. All major party chatter builders accept `map_id=0` and inject `get_dungeon_flavor(map_id)` as location context when inside a dungeon instance, replacing zone/subzone lore. Excluded: OOM, low-health, level-up. |
| `tools/chatter_group_state.py` | Group mood/traits/history state |

### Shared and support layers

| File | Primary ownership |
|---|---|
| `tools/chatter_shared.py` | Compatibility facade and residual shared helpers only: `PromptParts(str)` class for system/user prompt separation, `find_addressed_bot()` (with multi-addressed intent detection), `calculate_dynamic_delay()` (with responsive mode), `should_include_action()` (single RNG roll for narrator action gating at conversation delivery sites). Avoid adding new domain-specific handler logic here unless it is truly cross-domain. |
| `tools/chatter_text.py` | Parsing, sanitization, anti-repetition |
| `tools/chatter_llm.py` | Provider/model calls; `get_llm_client()` shared client factory; `_split_prompt()`, `_build_chat_messages()`, `_ollama_user_msg()` for system/user prompt separation; `label=` param logs every call via `chatter_request_logger` |
| `tools/chatter_db.py` | DB access, inserts, zone/cache queries, `any_real_players_online()`, `cleanup_stale_groups()`, `cleanup_all_session_data()` |
| `tools/chatter_links.py` | WoW link parsing and prompt-side link enrichment for player messages |
| `tools/chatter_prompts.py` | Ambient/event prompt builders |
| `tools/chatter_general.py` | `player_general_msg` Python path |
| `tools/chatter_memory.py` | Persistent memory system: session tracking, background memory generation via `queue_memory()`, flush/activate on farewell, orphan recovery. Key helpers: `_resolve_location()`, `_ensure_cap_and_insert()`, `_count_active_memories()`, `_evict_one_used()` |
| `tools/chatter_cache.py` | Pre-cache refill |
| `tools/chatter_events.py` | Event context building and cleanup |
| `tools/chatter_constants.py` | Static constants and lore data |
| `tools/talent_catalog.py` | Talent description catalog used by prompt-side talent injection |
| `tools/spell_names.py` | Spell name/description loader used by DB and link helpers |

### Screenshot vision domain

| File | Primary ownership |
|---|---|
| `tools/screenshot_agent.py` | Host-side capture agent (runs outside Docker). Captures WoW window via Win32 API, crops UI clutter (bottom 20%, sides 12%), sends JPEG to vision LLM (OpenAI or Anthropic), receives structured JSON with environment description, atmosphere, and canonical tags. Queues `bot_group_screenshot_observation` events directly into `llm_chatter_events`. Configurable interval, chance, and vision provider/model |
| `tools/chatter_screenshot_handler.py` | Bridge handler for `bot_group_screenshot_observation` events. Generates in-character bot comments using personality traits, zone/subzone context, and the vision description. Supports single statements via `run_single_reaction()` and multi-bot conversations via `append_conversation_json_instruction()` / `parse_conversation_response()`. Canonical tag dedup prevents repetitive observations |

### Development tools

| File | Primary ownership |
|---|---|
| `tools/chatter_request_logger.py` | Thread-safe JSONL logger; `init_request_logger(config)` + `log_request(label, prompt, response, model, provider, duration_ms, system_prompt)`; rotation at `MaxSizeMB`; writes to `/logs/llm_requests.jsonl` inside container |
| `tools/chatter_log_viewer.py` | Zero-dependency stdlib web UI (`python chatter_log_viewer.py --log PATH --port 5555`); routes `/`, `/api/logs`, `/api/stats`; semantic prompt-section parser with colored sections; draggable column/row dividers |

### Emote reaction domain

| File | Primary ownership |
|---|---|
| `tools/chatter_emote_reaction.py` | Directed verbal reaction handler (`bot_group_emote_reaction` event) — bot responds verbally when player emotes at them |
| `tools/chatter_emote_observer.py` | Observer comment handler (`bot_group_emote_observer` event) — random group bot remarks when player emotes at a creature or nobody |

### Proximity chatter domain

| File | Primary ownership |
|---|---|
| `tools/chatter_proximity.py` | Handlers and prompt builders for `proximity_say`, `proximity_conversation`, and `proximity_reply` events. Builds prompts with zone context, nearby entity names, and topic pool. Supports single NPC/bot statements and multi-speaker conversations |

### Raid/BG domain

| File | Primary ownership |
|---|---|
| `tools/chatter_raid_base.py` | Dual-worker dispatch and suppression logic |
| `tools/chatter_raids.py` | PvE raid event handlers (boss, morale) |
| `tools/chatter_raid_prompts.py` | Raid prompt builders (boss, morale, battle cry, banter) |
| `tools/chatter_battlegrounds.py` | BG event handlers |
| `tools/chatter_bg_prompts.py` | BG prompt builders and lore tables |

## Ownership Boundaries That Matter

### Shared C++ ownership

`LLMChatterShared.cpp` owns cross-domain helpers such as:

- `EscapeString()`
- `JsonEscape()`
- `GetZoneName()`
- `GetClassName()`
- `GetRaceName()`
- `BuildBotIdentityFields()`
- `QueueChatterEvent()`
- `BuildBotStateJson()`
- `AppendRaidContext()`
- `GroupHasBots()`
- `CanSpeakInGeneralChannel()`
- `GetTextEmoteName()` — reverse emote ID-to-name lookup (170+ entries)
- `SendUnitTextEmote(Unit*, uint32, const std::string&)` — consolidated
  emote packet helper; `SendBotTextEmote` overloads delegate to it
- `IsEventOnCooldown()` / `SetEventCooldown()` — shared event cooldown
  helper (cache-first, DB fallback) used by world, ambient, and nearby
- `FindCreatureBySpawnId(Map*, uint32)` — spawn-GUID creature lookup
  used by delivery and proximity
- `GetCreatureRoleName(Creature*)` — NPC role description from subname
  or NPC flags, used by proximity and nearby
- link conversion helpers
- emote/delivery helpers

Critical contract:

- direct callers of `QueueChatterEvent()` must pass `extraData` that is
  already valid JSON text and SQL-safe for insertion into a single-
  quoted SQL string literal

That contract is enforced by convention and comments, not by the type
system.

### Delivery ownership

`LLMChatterDelivery.cpp` owns:

- `DeliverPendingMessagesImpl()`
- outbound message polling from `llm_chatter_messages`
- facing selection before speech delivery
- final chat-channel dispatch for party, raid, BG, yell, General,
  say (bot `CHAT_MSG_SAY`), and msay (NPC `CHAT_MSG_MONSTER_SAY`
  with speech bubbles)
- spawn-GUID creature lookup for NPC delivery via
  `FindCreatureBySpawnId()`
- NPC orientation reset after speech via `BasicEvent`
- delivery success/retry marking

### Ambient ownership

`LLMChatterAmbient.cpp` owns:

- holiday processing
- day/night processing
- weather state and transitions
- ambient zone discovery and faction selection
- ambient chatter request queue writes

### Nearby ownership

`LLMChatterNearby.cpp` owns:

- nearby-object / nearby-creature scanning
- nearby POI helper structs and scoring helpers
- nearby-local cooldown state
- direct nearby event queue insertion path

### Proximity ownership

`LLMChatterProximity.cpp` owns:

- periodic proximity scan around real players (40-yard radius)
- humanoid NPC eligibility filtering (guards, vendors, trainers,
  innkeepers, citizens, sentinels, children)
- bot eligibility filtering (party bots only, all-bot guard rail)
- candidate selection and `proximity_say`/`proximity_conversation`
  event queueing
- `ProximityScene` struct for tracking active conversations
- player `/say` reply detection (`HandleProximityPlayerSay()`)
- per-entity cooldown management via spawn GUID

`FindCreatureBySpawnId()` and `GetCreatureRoleName()` were extracted
to `LLMChatterShared.cpp` as shared helpers used by both proximity
and delivery code.

### World ownership

`LLMChatterWorld.cpp` owns:

- `LLMChatterWorldScript`
- `LLMChatterGameEventScript`
- `LLMChatterALEScript`
- thin delivery tick delegation
- thin ambient delegation
- thin nearby delegation
- world-private `QueueEvent()`
- transport state and route announcements via transport-object zone
  transitions, but only when the destination zone currently contains a
  real player; eligible zone bots speak in General

`QueueEvent()` SQL-escapes its `extraData` before forwarding to
`QueueChatterEvent()`.

### Group ownership (split across five TUs)

`LLMChatterGroupInternal.h` declares shared state across the group TUs:

- struct definitions: `GroupJoinEntry`, `GroupJoinBatch`,
  `QuestAcceptEntry`, `QuestAcceptBatch`
- extern declarations for all shared cooldown maps, batch containers,
  mutexes, emote cooldowns, named boss cache
- `EmoteTargetType` enum
- shared helper and domain entry-point declarations

`LLMChatterGroup.cpp` retains:

- shared state variable definitions (all cooldown maps, batch containers,
  mutexes, emote cooldowns, named boss entries)
- shared helpers: `GroupHasRealPlayer`, `GetRandomBotInGroup`,
  `CountBotsInGroup`, `IsLikelyPlayerbotControlCommand`, pre-cache
  helpers
- `LoadNamedBossCache()`
- `CleanupGroupSession()` coordinator
 - thin `LLMChatterGroupPlayerScript` wrappers
 - `AddLLMChatterGroupScripts()` registration

`LLMChatterGroupCombat.cpp` owns:

- the remaining `LLMChatterGroupPlayerScript` implementation bodies for
  kill, death, loot, combat, chat, level, quest objectives, quest
  complete, achievement, spell, resurrect, corpse run, dungeon entry,
  and emote dispatch
- text-emote target classification and the decision of which paths still
  require group/bot context
- `HandleGroupPlayerUpdateZone()`
- `CheckGroupCombatState()`
- file-local `QueueStateCallout()`

`LLMChatterGroupJoin.cpp` owns:

- `QueueBotGreetingEvent()`
- `EnsureGroupJoinQueued()`
- `FlushGroupJoinBatches()`
- `LLMChatterGroupScript` (GroupScript: `OnAddMember`, `OnRemoveMember`
  with farewell, `OnDisband`)

`LLMChatterGroupEmote.cpp` owns:

- `DelayedMirrorEmoteEvent`, `DelayedCreatureMirrorEmoteEvent`
- emote static data: `s_mirrorEmoteMap`, `s_ignoredEmotes`,
  `s_combatCalloutEmotes`, `s_contagiousEmotes`
- `HandleEmoteAtGroupBot()`, `HandleEmoteAtCreature()`,
  `HandleEmoteObserver()`
- `EvictEmoteCooldowns()`

Important split:

- `LLMChatterGroupCombat.cpp` decides who/what the text emote targeted
  and whether the follow-up path is group-gated
- `LLMChatterGroupEmote.cpp` owns the actual mirror execution,
  cooldowns, and observer event queueing
- creature mirror emotes can now fire even when the player is solo;
  observer chatter still requires eligible grouped bots

`LLMChatterGroupQuest.cpp` owns:

- `FlushQuestAcceptBatches()`
- `LLMChatterCreatureScript` (AllCreatureScript:
  `CanCreatureQuestAccept` with debounce/immediate paths)

Important: the creature quest-accept hook is group-owned, not in a
separate creature file.

### Player ownership

`LLMChatterPlayer.cpp` owns:

- `LLMChatterPlayerScript`
- `EnsureBotInGeneralChannel()`
- `_generalChatCooldowns`
- `OnPlayerCanUseChat(..., Channel*)`
- General-channel bot history storage

### BG ownership

`LLMChatterBG.cpp` still owns battleground-specific hooks and BG queue
helpers. The later split phases did not move BG code again.

### Transport detection shape

The current transport path is intentionally an early-warning system, not
an exact dock-stop detector:

1. `LLMChatterWorld.cpp` polls live transport objects.
2. It tracks last-seen zone/map per live transport GUID.
3. A dispatch is considered only when a transport actually enters a new
   zone or map.
4. The new zone must currently contain at least one real player.
5. Eligible General-channel bot GUIDs in that zone are written into
   `extra_data.verified_bots`.
6. Cooldown is keyed by transport entry, not `transport + zone`, so one
   transport does not redispatch repeatedly during the same route cycle.

This is why transport chatter is both early enough to warn players and
cheap enough to avoid world-wide noise.

## World-To-Group Cross-Boundary

The world layer intentionally calls only a small group-owned surface via
`LLMChatterGroup.h`:

- `LoadNamedBossCache()`
- `CheckGroupCombatState()`
- `FlushQuestAcceptBatches()`
- `FlushGroupJoinBatches()`

Player-zone updates also cross from player to group via:

- `HandleGroupPlayerUpdateZone(Player*, uint32)`

The world layer also delegates to the proximity subsystem via
`LLMChatterProximity.h`:

- `CheckProximityChatter(uint32 diff)` — periodic scan timer

And `LLMChatterGroupCombat.cpp` calls into proximity via:

- `HandleProximityPlayerSay(Player*, const std::string&)` — player
  `/say` reply detection

That explicit boundary is one of the main reasons the split is easier to
reason about now.

## Event Routing Ownership

Bridge routing is registry-driven.

`tools/chatter_event_registry.py` is the Python-side source of truth for
live event routing metadata. At bridge startup,
`build_handler_map()` dynamically imports handler functions from that
registry and `llm_chatter_bridge.py` uses the resulting map at runtime.

- `bot_group_*` events route to group handlers
- `bot_group_emote_reaction` routes to `chatter_emote_reaction.py`
- `bot_group_emote_observer` routes to `chatter_emote_observer.py`
- `bot_group_screenshot_observation` routes to
  `chatter_screenshot_handler.py`
- `proximity_say`, `proximity_conversation`, `proximity_reply` route to
  `chatter_proximity.py`
- `bg_*` events route to battleground handlers
- `player_general_msg` routes through the adapter path to
  `chatter_general.py`
- unmapped ambient work still flows through the ambient path

Signature trap that still matters:

- group handlers use `(db, client, config, event)`
- `process_general_player_msg_event` uses
  `(event, db, client, config)`
- `_dispatch_player_general_msg` exists to reorder arguments

Do not remove that adapter without standardizing the signatures.

### Player message conversation path

When a player speaks in party chat, the group player-message handler
may trigger a multi-bot conversation instead of a single-bot reply:

Known playerbot control commands do not enter this path in current
source:

- C++ `IsLikelyPlayerbotControlCommand()` in `LLMChatterGroup.cpp`
  blocks them before `bot_group_player_msg` is queued
- Python `_is_playerbot_command()` in `chatter_group.py` remains as a
  fallback skip layer

1. `find_addressed_bot()` in `chatter_shared.py` always fires an LLM
   call to assess `multi_addressed` (boolean). When true and >=2 bots
   are available, the conversation path is forced (bypasses RNG).
2. Otherwise, `PlayerMsgConversationChance` (default 30%, scaled by
   bot count) gates whether a conversation fires.
3. `build_player_msg_conversation_prompt()` in
   `chatter_group_prompts.py` builds a prompt requesting a JSON array
   of 2-3 bot replies (Architecture B — single LLM call).
4. `execute_player_msg_conversation()` in `chatter_group_handlers.py`
   dispatches the call and inserts the resulting messages.
5. Delays use `calculate_dynamic_delay(responsive=True)` for faster
   player-directed timing (2s floor vs 4s ambient).

## Where To Edit What

| If you need to change... | Primary file |
|---|---|
| LLM request log format / rotation / config | `tools/chatter_request_logger.py` |
| LLM request log web viewer | `tools/chatter_log_viewer.py` |
| Main polling loops, event claim logic, worker behavior | `tools/llm_chatter_bridge.py` |
| Python event registry / handler resolution metadata | `tools/chatter_event_registry.py` |
| Ambient statement/conversation runtime logic | `tools/chatter_ambient.py` |
| Group join/player-msg/idle behavior | `tools/chatter_group.py` |
| Group reaction runtime behavior | `tools/chatter_group_handlers.py` |
| Shared group-handler pipeline behavior | `tools/chatter_handler_pipeline.py` |
| Group prompt wording | `tools/chatter_group_prompts.py` |
| Group message insert behavior / preserve `emote: null` | `tools/chatter_group.py`, `tools/chatter_shared.py`, `tools/chatter_cache.py` |
| General-channel Python behavior | `tools/chatter_general.py` |
| DB inserts, history tables, zone/query cache behavior | `tools/chatter_db.py` |
| Shared parsing/sanitization | `tools/chatter_text.py` |
| Provider/model calls | `tools/chatter_llm.py` |
| Shared compatibility helpers | `tools/chatter_shared.py` |
| Python event-to-handler ownership map | `tools/chatter_event_registry.py` |
| Emote reaction verbal responses | `tools/chatter_emote_reaction.py` |
| Emote observer comments | `tools/chatter_emote_observer.py` |
| Proximity chatter Python handlers/prompts | `tools/chatter_proximity.py` |
| Proximity chatter C++ scan/scene logic | `src/LLMChatterProximity.cpp`, `src/LLMChatterProximity.h` |
| C++ text-emote target classification / solo-vs-group pathing | `src/LLMChatterGroupCombat.cpp` |
| Emote C++ hooks, mirror maps, cooldowns | `src/LLMChatterGroupEmote.cpp` |
| BG event handling | `tools/chatter_battlegrounds.py` |
| BG prompt wording/lore | `tools/chatter_bg_prompts.py` |
| Raid event handling | `tools/chatter_raids.py` |
| Raid prompt wording | `tools/chatter_raid_prompts.py` |
| C++ raid boss hooks | `src/LLMChatterRaid.cpp` |
| C++ shared helper contracts | `src/LLMChatterShared.cpp`, `src/LLMChatterShared.h` |
| C++ delivery logic | `src/LLMChatterDelivery.cpp`, `src/LLMChatterDelivery.h` |
| C++ ambient world/event logic | `src/LLMChatterAmbient.cpp`, `src/LLMChatterAmbient.h` |
| C++ nearby scan logic | `src/LLMChatterNearby.cpp`, `src/LLMChatterNearby.h` |
| C++ world transport/dispatcher logic | `src/LLMChatterWorld.cpp` |
| C++ group batching/combat/state logic | `src/LLMChatterGroup.cpp`, `src/LLMChatterGroupCombat.cpp`, `src/LLMChatterGroupJoin.cpp`, `src/LLMChatterGroupEmote.cpp`, `src/LLMChatterGroupQuest.cpp`, `src/LLMChatterGroup.h`, `src/LLMChatterGroupInternal.h` |
| C++ General-channel player logic | `src/LLMChatterPlayer.cpp` |
| C++ BG logic | `src/LLMChatterBG.cpp`, `src/LLMChatterBG.h` |
| Screenshot vision capture agent (host-side) | `tools/screenshot_agent.py` |
| Screenshot vision bridge handler | `tools/chatter_screenshot_handler.py` |
| C++ registration wiring | `src/LLMChatterScript.cpp`, `src/llm_chatter_loader.cpp` |

## Common Pitfalls

### `chatter_shared.py` is partly a facade

Many helpers imported from `chatter_shared.py` are actually implemented
in:

- `chatter_text.py`
- `chatter_llm.py`
- `chatter_db.py`

Do not treat `chatter_shared.py` as the default place for new Python
features just because it is imported widely. New domain logic should
usually go in the owning domain file and only small cross-domain helpers
should live here.

### Bridge ambient wrappers are delegates

If ambient behavior changes, edit `chatter_ambient.py`, not the bridge
wrapper first.

### General chat handler signature is different

Keep `_dispatch_player_general_msg` unless you standardize signatures
everywhere.

### Pre-cache path is separate from live event path

Pre-cache generation does not use the same runtime path as live group
event reactions.

### `enabledHooks` still matters

Any new C++ hook override must add the correct enum to its constructor's
`enabledHooks` vector or it will silently never fire.

### `LLMChatterScript.cpp` is registration-only

- world transport/dispatcher logic lives in `LLMChatterWorld.cpp`
- ambient world/event logic lives in `LLMChatterAmbient.cpp`
- nearby scan logic lives in `LLMChatterNearby.cpp`
- group logic lives in `LLMChatterGroup.cpp`,
  `LLMChatterGroupCombat.cpp`, `LLMChatterGroupJoin.cpp`,
  `LLMChatterGroupEmote.cpp`, `LLMChatterGroupQuest.cpp`
- player General-channel logic lives in `LLMChatterPlayer.cpp`
- shared helpers live in `LLMChatterShared.cpp`

Do not edit `LLMChatterScript.cpp` for new features.

### Battleground routing

BG-wide only:
- match start / end
- all flag events

Subgroup/party only:
- kills, node chatter, score milestones, spell/state chatter,
  idle chatter, flag-carrier self-messages

This reduces duplicate near-identical lines across party and raid.

## Database Tables

| Table | Producer | Consumer | Notes |
|---|---|---|---|
| `llm_chatter_events` | C++ / screenshot agent | Python | Event queue |
| `llm_chatter_queue` | C++ | Python | Ambient statement/conversation queue |
| `llm_chatter_messages` | Python | C++ | Outbound message delivery queue |
| `llm_group_cached_responses` | Python | C++ | Instant reaction pre-cache |
| `llm_group_bot_traits` | Python | Python | Group traits/state |
| `llm_group_chat_history` | Python | Python | Group anti-repetition history |
| `llm_general_chat_history` | C++/Python read path | Python/C++ | General-channel history |

## Known Gaps

- exhaustive in-game validation of every event path and tuning edge case
- hostile multi-target spell-attribution edge case not yet fully covered
- boss pull/kill/wipe events need live in-game testing via actual boss
  encounters
