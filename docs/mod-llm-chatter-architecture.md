# mod-llm-chatter Architecture

Last updated: 2026-03-29 (through screenshot vision feature)

## Purpose

Reference architecture for humans and LLMs editing
`modules/mod-llm-chatter`.

This document reflects the current source architecture.

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

Two config-driven RNG checks in `append_json_instruction()` and
`append_conversation_json_instruction()` control optional prompt
sections:

- `EmoteChance` — gates inclusion of the ~244-emote list (~500 tokens)
- `ActionChance` — gates the action field instruction

These are checked once per prompt build and apply uniformly to all
prompt paths (group, General, BG, raid).

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
| `src/LLMChatterScript.cpp` | 13 | Registration coordinator only |
| `src/LLMChatterShared.cpp` | 803 | Shared helpers: SQL/JSON escaping, queue insert helper, link/emote/delivery helpers, `GetTextEmoteName()` reverse lookup, `SendUnitTextEmote()` consolidated emote packet helper, cross-domain formatting helpers |
| `src/LLMChatterShared.h` | 42 | Shared declarations still used across domains; `class Unit` forward-declared for `SendUnitTextEmote()`; currently also declares world/player registration |
| `src/LLMChatterWorld.cpp` | 2220 | WorldScript ownership, delivery tick, world/private `QueueEvent()`, holiday/weather/transport events, nearby-object scanning, world-private state |
| `src/LLMChatterGroup.cpp` | 4311 | Group batching, cooldown/state maps, combat-state checks, named-boss cache, group/player/creature party-side hooks, emote reaction system (`OnPlayerTextEmote`, mirror/verbal/observer paths, `DelayedMirrorEmoteEvent`, `DelayedCreatureMirrorEmoteEvent`), direct group event queueing |
| `src/LLMChatterGroup.h` | 12 | World-to-group cross-call surface plus group registration |
| `src/LLMChatterPlayer.cpp` | 445 | Player General-channel hooks, General cooldowns, `EnsureBotInGeneralChannel()`, player registration |
| `src/LLMChatterRaid.cpp` | 777 | Raid boss hooks (pull/kill/wipe), boss lookup table (80+ entries across Classic/TBC/WotLK), `IsDatabaseBound() override`, raid registration |
| `src/LLMChatterBG.cpp` | 1166 | Battleground hooks, BG state polling, BG queue helpers, BG registration |
| `src/LLMChatterBG.h` | 14 | BG registration declaration |
| `src/LLMChatterConfig.h/.cpp` | 739 | Config loading and config struct |
| `src/llm_chatter_loader.cpp` | 10 | Module entry point, calls `AddLLMChatterScripts()` |

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
| `tools/llm_chatter_bridge.py` | Main loops, event claiming, routing, worker orchestration |
| `tools/chatter_ambient.py` | Ambient statement/conversation generation |

### Group domain

| File | Primary ownership |
|---|---|
| `tools/chatter_group.py` | Group join, group player message flow, idle chatter |
| `tools/chatter_group_handlers.py` | `bot_group_*` reaction handlers, `execute_player_msg_conversation()` |
| `tools/chatter_group_prompts.py` | Group prompt builders, nearby-object prompts, pre-cache prompt builders, `build_player_msg_conversation_prompt()`. All major party chatter builders accept `map_id=0` and inject `get_dungeon_flavor(map_id)` as location context when inside a dungeon instance, replacing zone/subzone lore. Excluded: OOM, low-health, level-up. |
| `tools/chatter_group_state.py` | Group mood/traits/history state |

### Shared and support layers

| File | Primary ownership |
|---|---|
| `tools/chatter_shared.py` | Compatibility facade, residual shared helpers, `PromptParts(str)` class for system/user prompt separation, `find_addressed_bot()` (with multi-addressed intent detection), `calculate_dynamic_delay()` (with responsive mode), `should_include_action()` (single RNG roll for narrator action gating at conversation delivery sites) |
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
| `tools/screenshot_agent.py` | Host-side capture agent (runs outside Docker). Captures WoW window via Win32 API, light-crops UI clutter (bottom 15%, sides 5%), sends JPEG to vision LLM (OpenAI or Anthropic), receives structured JSON with environment description, atmosphere, and canonical tags. Queues `bot_group_screenshot_observation` events directly into `llm_chatter_events`. Configurable interval, chance, and vision provider/model |
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

### Raid/BG domain

| File | Primary ownership |
|---|---|
| `tools/chatter_raid_base.py` | Dual-worker dispatch and suppression logic |
| `tools/chatter_raids.py` | PvE raid event handlers (boss, morale) |
| `tools/chatter_raid_prompts.py` | Raid prompt builders (boss, morale) |
| `tools/chatter_battlegrounds.py` | BG event handlers |
| `tools/chatter_bg_prompts.py` | BG prompt builders and lore tables |

## Ownership Boundaries That Matter

### Shared C++ ownership

`LLMChatterShared.cpp` owns cross-domain helpers such as:

- `EscapeString()`
- `JsonEscape()`
- `QueueChatterEvent()`
- `BuildBotStateJson()`
- `AppendRaidContext()`
- `GroupHasBots()`
- `GetTextEmoteName()` — reverse emote ID-to-name lookup (170+ entries)
- `SendUnitTextEmote(Unit*, uint32, const std::string&)` — consolidated
  emote packet helper; `SendBotTextEmote` overloads delegate to it
- link conversion helpers
- emote/delivery helpers

Critical contract:

- direct callers of `QueueChatterEvent()` must pass `extraData` that is
  already valid JSON text and SQL-safe for insertion into a single-
  quoted SQL string literal

That contract is enforced by convention and comments, not by the type
system.

### World ownership

`LLMChatterWorld.cpp` owns:

- `LLMChatterWorldScript`
- `LLMChatterGameEventScript`
- `LLMChatterALEScript`
- `DeliverPendingMessages()`
- world-private `QueueEvent()`
- holiday processing
- day/night processing
- weather state and transitions
- transport state and route announcements via transport-object zone
  transitions, but only when the destination zone currently contains a
  real player; eligible zone bots speak in General
- nearby-object / nearby-creature scanning

`QueueEvent()` SQL-escapes its `extraData` before forwarding to
`QueueChatterEvent()`.

The nearby-object path is the one intentional direct world caller of
`QueueChatterEvent()`. It now explicitly SQL-escapes `extraJson` before
calling the shared insert helper.

### Group ownership

`LLMChatterGroup.cpp` owns:

- `LLMChatterGroupScript`
- `LLMChatterGroupPlayerScript`
- `LLMChatterCreatureScript`
- `CleanupGroupSession()`
- `LoadNamedBossCache()`
- `FlushGroupJoinBatches()`
- `FlushQuestAcceptBatches()`
- `CheckGroupCombatState()`
- `HandleGroupPlayerUpdateZone()`
- `QueueStateCallout()`
- emote reaction system: `OnPlayerTextEmote`, `HandleEmoteAtGroupBot`,
  `HandleEmoteObserver`, `DelayedMirrorEmoteEvent`,
  `DelayedCreatureMirrorEmoteEvent`, `EvictEmoteCooldowns()`
- emote state maps: `_emoteReactCooldowns`, `_emoteVerbalCooldowns`,
  `_emoteObserverCooldowns`, `s_mirrorEmoteMap`, `s_contagiousEmotes`,
  `s_combatCalloutEmotes`, `s_ignoredEmotes`
- group cooldown/state maps
- group join and quest-accept batch structs/maps/mutexes

Important: the creature quest-accept hook ended up group-owned, not in a
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

That explicit boundary is one of the main reasons the split is easier to
reason about now.

## Event Routing Ownership

Bridge routing is map-driven in `tools/llm_chatter_bridge.py`.

- `bot_group_*` events route to group handlers
- `bot_group_emote_reaction` routes to `chatter_emote_reaction.py`
- `bot_group_emote_observer` routes to `chatter_emote_observer.py`
- `bot_group_screenshot_observation` routes to
  `chatter_screenshot_handler.py`
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
| Ambient statement/conversation runtime logic | `tools/chatter_ambient.py` |
| Group join/player-msg/idle behavior | `tools/chatter_group.py` |
| Group reaction runtime behavior | `tools/chatter_group_handlers.py` |
| Group prompt wording | `tools/chatter_group_prompts.py` |
| General-channel Python behavior | `tools/chatter_general.py` |
| DB inserts, history tables, zone/query cache behavior | `tools/chatter_db.py` |
| Shared parsing/sanitization | `tools/chatter_text.py` |
| Provider/model calls | `tools/chatter_llm.py` |
| Shared compatibility helpers | `tools/chatter_shared.py` |
| Emote reaction verbal responses | `tools/chatter_emote_reaction.py` |
| Emote observer comments | `tools/chatter_emote_observer.py` |
| Emote C++ hooks, mirror maps, cooldowns | `src/LLMChatterGroup.cpp` |
| BG event handling | `tools/chatter_battlegrounds.py` |
| BG prompt wording/lore | `tools/chatter_bg_prompts.py` |
| Raid event handling | `tools/chatter_raids.py` |
| Raid prompt wording | `tools/chatter_raid_prompts.py` |
| C++ raid boss hooks | `src/LLMChatterRaid.cpp` |
| C++ shared helper contracts | `src/LLMChatterShared.cpp`, `src/LLMChatterShared.h` |
| C++ delivery/world/environment logic | `src/LLMChatterWorld.cpp` |
| C++ group batching/combat/state logic | `src/LLMChatterGroup.cpp`, `src/LLMChatterGroup.h` |
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

- world logic lives in `LLMChatterWorld.cpp`
- group logic lives in `LLMChatterGroup.cpp`
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
