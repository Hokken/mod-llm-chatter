# mod-llm-chatter Architecture

Last updated: 2026-03-18 (through Session 77 - LLM request logging system)

## Purpose

Reference architecture for humans and LLMs editing
`modules/mod-llm-chatter`.

This document reflects the post-split C++ layout that now exists in the
repo. The old assumption that almost all C++ ownership lives in
`LLMChatterScript.cpp` is no longer true.

Important status note:

- the source-level split is complete through Phase 4
- the split passed phased source review
- compile and linker validation passed on 2026-03-09 (two minor fixes:
  removed invalid `TEXT_EMOTE_FAREWELL`/`TEXT_EMOTE_MASSAGE`, made
  `GetReactionDelaySeconds()` non-static so Group could call it)
- the module has remained in active runtime use after that validation
- this document now reflects the current source architecture through
  Session 77
- the Session 69 priority-system rollout was compiled and validated
  later on 2026-03-12
- later source work also restored transport detection, narrowed
  transport dispatch to real-player zones, changed transport cooldown
  semantics to one dispatch per transport entry window, and cleaned up
  BG channel routing plus score/spell prompt behavior
- Session 71 added PvE raid chatter Phase 2: `LLMChatterRaid.cpp` for
  boss hooks, lifted guards in Group/World, `raid_idle_morale` event,
  and new Python raid handler/prompt files
- Session 77 added LLM request logging: `chatter_request_logger.py`
  (thread-safe JSONL logger), `chatter_log_viewer.py` (stdlib web UI),
  `label=` parameter on all `call_llm()` call sites, Docker bind mount
  at `/logs`, and 3 new `RequestLog.*` config keys

## Why The C++ Split Happened

The original `LLMChatterScript.cpp` had grown into a monolithic file
mixing:

- world tick delivery
- event queue insertion
- transport and weather state
- nearby object scanning
- group batching
- group cooldown and combat state
- player General-channel hooks
- shared helper functions
- registration wiring

That made ownership hard to reason about and made refactors risky. The
split was done to separate real domains, not just to reduce line count.

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

- AzerothCore root repo:
  `C:\azerothcore-wotlk`
- Module repo:
  `C:\azerothcore-wotlk\modules\mod-llm-chatter`
- Runtime code changes usually belong in the module repo
- This architecture doc lives under root `docs/` for shared reference

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
| `src/LLMChatterShared.cpp` | 803 | Shared helpers: SQL/JSON escaping, queue insert helper, link/emote/delivery helpers, cross-domain formatting helpers |
| `src/LLMChatterShared.h` | 42 | Shared declarations still used across domains; currently also declares world/player registration |
| `src/LLMChatterWorld.cpp` | 2220 | WorldScript ownership, delivery tick, world/private `QueueEvent()`, holiday/weather/transport events, nearby-object scanning, world-private state |
| `src/LLMChatterGroup.cpp` | 4311 | Group batching, cooldown/state maps, combat-state checks, named-boss cache, group/player/creature party-side hooks, direct group event queueing |
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
| `tools/chatter_group_prompts.py` | Group prompt builders, nearby-object prompts, pre-cache prompt builders, `build_player_msg_conversation_prompt()` |
| `tools/chatter_group_state.py` | Group mood/traits/history state |

### Shared and support layers

| File | Primary ownership |
|---|---|
| `tools/chatter_shared.py` | Compatibility facade, residual shared helpers, `find_addressed_bot()` (with multi-addressed intent detection), `calculate_dynamic_delay()` (with responsive mode) |
| `tools/chatter_text.py` | Parsing, sanitization, anti-repetition |
| `tools/chatter_llm.py` | Provider/model calls; `label=` param logs every call via `chatter_request_logger` |
| `tools/chatter_db.py` | DB access, inserts, zone/cache queries |
| `tools/chatter_links.py` | WoW link parsing and prompt-side link enrichment for player messages |
| `tools/chatter_prompts.py` | Ambient/event prompt builders |
| `tools/chatter_general.py` | `player_general_msg` Python path |
| `tools/chatter_cache.py` | Pre-cache refill |
| `tools/chatter_events.py` | Event context building and cleanup |
| `tools/chatter_constants.py` | Static constants and lore data |
| `tools/talent_catalog.py` | Talent description catalog used by prompt-side talent injection |
| `tools/spell_names.py` | Spell name/description loader used by DB and link helpers |

### Development tools

| File | Primary ownership |
|---|---|
| `tools/chatter_request_logger.py` | Thread-safe JSONL logger; `init_request_logger(config)` + `log_request(label, prompt, response, model, provider, duration_ms)`; rotation at `MaxSizeMB`; writes to `/logs/llm_requests.jsonl` inside container |
| `tools/chatter_log_viewer.py` | Zero-dependency stdlib web UI (`python chatter_log_viewer.py --log PATH --port 5555`); routes `/`, `/api/logs`, `/api/stats`; semantic prompt-section parser with colored sections; draggable column/row dividers |

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

### Post-Split Feature Paths Added After Session 64

These did not change the core split, but they do change where real
runtime behavior lives:

- **Bot-initiated questions**: timer-driven group behavior in
  `chatter_group.py`, scheduled from `llm_chatter_bridge.py`
- **Quest conversations**: conversation fallback path in
  `chatter_group_handlers.py` with prompt builders in
  `chatter_group_prompts.py`
- **Achievement batching**: duplicate suppression and batch ownership in
  `chatter_group_handlers.py`
- **Talent-context injection**: shared prompt-context construction in
  `chatter_shared.py`, invoked from group/general/BG paths
- **BG talent dispatch glue**: `chatter_raid_base.py` and
  `chatter_battlegrounds.py`
- **Humor hint injection**: length-hint/prompt shaping in
  `chatter_group_prompts.py` and the General-channel prompt path
- **Ambient conversation pacing**: previous-message reading delay in
  `chatter_ambient.py`
- **Transport speaker verification**: `transport_arrives` now resolves
  speaker candidates from `verified_bots` GUIDs in
  `llm_chatter_bridge.py`, so grouped dockside bots survive the Python
  path
- **BG routing cleanup**: `chatter_raid_base.py` and
  `chatter_battlegrounds.py` now separate BG-wide-only events from
  subgroup-only tactical chatter
- **PvE raid chatter Phase 2**: `LLMChatterRaid.cpp` for boss hooks,
  `chatter_raids.py` and `chatter_raid_prompts.py` for Python handlers
  and prompts, `raid_idle_morale` in `LLMChatterWorld.cpp`, lifted
  guards in `LLMChatterGroup.cpp`

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
| C++ registration wiring | `src/LLMChatterScript.cpp`, `src/llm_chatter_loader.cpp` |

## Confusion Traps

### 1) Two repos in one workspace

- chatter runtime code is in `modules/mod-llm-chatter`
- root docs are reference material, not the module runtime itself

### 2) `chatter_shared.py` is partly facade

Many helpers imported from `chatter_shared.py` are actually implemented
in:

- `chatter_text.py`
- `chatter_llm.py`
- `chatter_db.py`

### 3) Bridge ambient wrappers are delegates

If ambient behavior changes, edit `chatter_ambient.py`, not the bridge
wrapper first.

### 4) General chat handler signature is still different

Keep `_dispatch_player_general_msg` unless you standardize signatures
everywhere.

### 5) Pre-cache path is separate from live event path

Pre-cache generation does not use the same runtime path as live group
event reactions.

### 6) enabledHooks still matters

Any new C++ hook override must add the correct enum to its constructor's
`enabledHooks` vector or it will silently never fire.

### 7) C++ ownership is no longer centered in `LLMChatterScript.cpp`

The old monolith is gone.

- `LLMChatterScript.cpp` is now just a coordinator
- world logic lives in `LLMChatterWorld.cpp`
- group logic lives in `LLMChatterGroup.cpp`
- player General-channel logic lives in `LLMChatterPlayer.cpp`
- shared helpers live in `LLMChatterShared.cpp`

Do not keep editing `LLMChatterScript.cpp` out of habit.

### 8) The split is source-level accepted, not build-validated

This was true during the split review period, but it is no longer the
current state. The split compiled and linked successfully on 2026-03-09.
When touching this document, do not reintroduce "build still pending"
language unless a new unresolved build break actually exists.

### 9) Battleground routing is no longer "party + raid for almost
everything"

Current intent:

- BG-wide only:
  - match start
  - match end
  - all flag events
- subgroup/party only:
  - kills
  - node chatter
  - score milestones
  - spell/state chatter
  - idle chatter
  - flag-carrier self-messages

This reduces duplicate near-identical lines across party and raid.

## Database Tables

| Table | Producer | Consumer | Notes |
|---|---|---|---|
| `llm_chatter_events` | C++ | Python | Event queue |
| `llm_chatter_queue` | C++ | Python | Ambient statement/conversation queue |
| `llm_chatter_messages` | Python | C++ | Outbound message delivery queue |
| `llm_group_cached_responses` | Python | C++ | Instant reaction pre-cache |
| `llm_group_bot_traits` | Python | Python | Group traits/state |
| `llm_group_chat_history` | Python | Python | Group anti-repetition history |
| `llm_general_chat_history` | C++/Python read path | Python/C++ | General-channel history |

## Validation State

What is complete:

- C++ split through Phase 4
- phased review after each step
- focused cleanup for final `QueueChatterEvent()` callsite migration
- compile and linker verification (2026-03-09, two minor fixes applied)
- runtime feature work continued on top of the split through Session 69
- Session 69 source implementation added priority-aware claim, bridge
  yield, safety mode, and final delivery ordering
- the Session 69 priority rollout was compiled and runtime-validated on
  2026-03-12
- Astranaar testing confirmed live urgent-backlog yield plus prompt
  delivery for combat, nearby-object, quest-objective, zone-transition,
  and quest-complete paths
- Session 70 transport restoration was tested live in Auberdine and the
  timing was judged good for early-warning boat callouts
- Session 71 PvE raid chatter Phase 2 compiled, reviewed (13 fixes),
  and tested live in ICC 10-man

What is not complete:

- exhaustive in-game validation of every event path and tuning edge case
- the deeper hostile multi-target spell-attribution edge case after the
  Session 70 hardening pass
- Phase 1 boss events (pull/kill/wipe) need live in-game testing via
  actual boss encounters (not `.die`)

## Related Artifacts

- `docs/plans/llm-chatter-script-splitting-plan.md`
- `docs/investigations/llm-chatter-phase-0-5-ownership-investigation.md`
- `docs/reviews/llm-chatter-phase-1-shared-infrastructure-review.md`
- `docs/reviews/llm-chatter-phase-2-world-and-event-hooks-review.md`
- `docs/reviews/llm-chatter-phase-3-group-subsystem-review.md`
- `docs/reviews/llm-chatter-phase-4-player-subsystem-review.md`
- `docs/reviews/llm-chatter-queuechatterevent-callsite-cleanup-review.md`
- `docs/plans/raid-chatter-phase-2-plan.md`
- `docs/reviews/raid-chatter-phase-2-review.md`
- `docs/reviews/raid-chatter-implementation-review.md`
- `docs/mod-llm-chatter/raid-chatter-implementation.md`
